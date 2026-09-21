"""The one place where Ripple talks to an LLM (Reader, Plan Generator, Briefing Writer).

Every call is appended to evidence/ai-log/<date>.jsonl with the prompt, the
reply, the model and a timestamp (CLAUDE.md rule 5).

No provider has been chosen yet. `_send` is the only function to fill in.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HKT = timezone(timedelta(hours=8))
LOG_DIR = Path("evidence/ai-log")


def complete_json(*, component: str, model: str, system: str, user: str,
                  schema: dict, temperature: float) -> str:
    """Ask the model for one JSON reply that follows `schema`, and return the raw text.

    The reply is only a candidate: validating it is the caller's job.
    """
    sent_at = datetime.now(HKT)
    reply = _send(model=model, system=system, user=user, schema=schema, temperature=temperature)
    _log({
        "timestamp": sent_at.isoformat(timespec="seconds"),
        "component": component,
        "model": model,
        "temperature": temperature,
        "system": system,
        "user": user,
        "response": reply,
    })
    return reply


def _send(*, model: str, system: str, user: str, schema: dict, temperature: float) -> str:
    """Send one request to the chosen provider and return the model's reply text.

    Use the provider's strict structured-output (JSON schema) mode with `schema`.
    The schema already closes every object (additionalProperties: false) and
    requires every field. Strip keywords the provider's strict mode rejects
    (e.g. minimum, maximum, uniqueItems): the caller re-checks them locally.
    """
    raise NotImplementedError(
        "No LLM provider chosen yet: implement _send() in src/llm.py "
        "and pin MODEL in src/reader/reader.py.")


def _log(entry: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / f"{entry['timestamp'][:10]}.jsonl").open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
