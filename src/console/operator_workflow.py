"""Read F's saved draft and append operator decisions using G's audit contract."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from src.briefing.schema import BRIEFING_SCHEMA
from src.briefing.writer import check_vms
from src.console import recommendation
from src.generation import load_json, validate

HK = timezone(timedelta(hours=8))
ACTIONS = {"viewed", "approved", "rejected"}


@contextmanager
def audit_lock(path: Path):
    """Serialize writers on a persistent sibling file on Windows and Unix.

    Lock byte zero on Windows, independent of the audit file's append offset.
    Keep the lock file after releasing it so waiting writers share one file.
    Failure to acquire a lock raises before any audit record is written.
    """
    with path.with_name(path.name + ".lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def load_briefing(path: Path, comparison: dict) -> dict:
    """Require the winning run, all current evidence sources and valid sign text."""
    briefing = load_json(path)
    validate(briefing, BRIEFING_SCHEMA)
    winner = comparison["winner"]
    if (briefing["run_id"] != winner["run_id"] or
            briefing["recommended_plan_id"] != winner["plan_id"]):
        raise ValueError("Briefing belongs to a different recommended run or plan.")
    if set(briefing["sources"]) != set(comparison["sources"]):
        raise ValueError("Briefing sources do not match the current comparison.")
    signs = [message["sign_id"] for message in briefing["vms_messages"]]
    expected = {sign["sign_id"] for sign in comparison["plans"][winner["plan_id"]]["vms"]}
    if len(signs) != len(set(signs)) or set(signs) != expected:
        raise ValueError("Briefing signs do not match the recommended plan.")
    for message in briefing["vms_messages"]:
        check_vms(message["text_en"])
        check_vms(message["text_zh"])
        if message["chars_en"] != len(message["text_en"]):
            raise ValueError("Briefing sign character count is incorrect.")
    return briefing


def evidence_key(comparison: dict, briefing: dict) -> str:
    """Bind a displayed decision to the exact compared artifacts and draft."""
    return recommendation.fingerprint({"comparison": comparison, "briefing": briefing})


def append_action(path: Path, comparison: dict, briefing: dict, action: str,
                  operator: str, note: str) -> dict:
    if action not in ACTIONS:
        raise ValueError("Unknown operator action.")
    if not operator.strip():
        raise ValueError("Enter the operator's name before recording a decision.")
    record = {
        "timestamp": datetime.now(HK).isoformat(timespec="seconds"),
        "incident_id": comparison["incident_id"],
        "run_id": comparison["winner"]["run_id"],
        "plan_id": comparison["winner"]["plan_id"],
        "action": action, "operator": operator.strip(),
        "note": (note.strip() + "\nEvidence SHA-256: " +
                 evidence_key(comparison, briefing)).strip(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with audit_lock(path):
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    return record


def record_decision(*, results_dir: Path, plans_dir: Path, briefing_path: Path,
                    incident_id: str, scenario: tuple, displayed_key: str,
                    audit_path: Path, action: str, operator: str, note: str) -> dict:
    """Re-read inputs at the click; changes require reviewing the updated draft."""
    comparison, reason = recommendation.load_comparison(
        results_dir, plans_dir, incident_id, scenario)
    if comparison is None:
        raise ValueError("Decision unavailable: " + reason)
    briefing = load_briefing(briefing_path, comparison)
    if evidence_key(comparison, briefing) != displayed_key:
        raise ValueError("Inputs changed. Review the updated briefing before deciding.")
    return append_action(audit_path, comparison, briefing, action, operator, note)
