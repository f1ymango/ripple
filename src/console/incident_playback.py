"""Read archived TD prose for historical playback; no closure inference."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")


def local_time(value: str) -> datetime | None:
    """TD's zone-less announcement timestamps are Hong Kong local time."""
    if not isinstance(value, str) or "T" not in value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return (parsed.replace(tzinfo=HKT) if parsed.tzinfo is None
                else parsed.astimezone(HKT))
    except ValueError:
        return None


@dataclass(frozen=True)
class Message:
    incident_id: str
    message_id: str
    published: datetime
    status: str
    english: str
    chinese: str
    archive_time: str
    source_feed: str


def read_messages(path: Path) -> tuple[list[Message], list[str]]:
    """Keep valid archived messages and report unreadable records visibly."""
    if not path.exists():
        return [], []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [], [f"Archived messages unavailable: {path.name} ({exc})"]
    messages, errors = [], []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            raw = record["stn"]
            published = local_time(raw.get("ANNOUNCEMENT_DATE"))
            incident_id = raw.get("INCIDENT_NUMBER")
            english, chinese = raw.get("CONTENT_EN", ""), raw.get("CONTENT_CN", "")
            if (published is None or not isinstance(incident_id, str) or not incident_id
                    or not isinstance(english, str) or not isinstance(chinese, str)
                    or not (english.strip() or chinese.strip())):
                raise ValueError("missing message text, incident identity or publication time")
            messages.append(Message(
                incident_id, str(raw.get("ID", "")), published,
                str(raw.get("INCIDENT_STATUS_EN", "")), english, chinese,
                str(record.get("archive_time", "")), str(record.get("source_feed", "")),
            ))
        except (ValueError, KeyError, TypeError, AttributeError):
            errors.append(f"Skipped unreadable archived message: {path.name}, line {line_number}.")
    return sorted(set(messages), key=lambda m: (m.published, m.incident_id, m.message_id)), errors


def for_window(messages: list[Message], first_bin: str, last_bin: str) -> list[Message]:
    """Include this day's earlier reports; never import another day's demo."""
    first, last = local_time(first_bin), local_time(last_bin)
    if first is None or last is None:
        return []
    day_start = first.replace(hour=0, minute=0, second=0, microsecond=0)
    return [message for message in messages if day_start <= message.published <= last]


def latest_at(messages: list[Message], incident_id: str, current_bin: str) -> Message | None:
    """The cursor is the bin start, not its end; future prose stays withheld."""
    current = local_time(current_bin)
    eligible = [m for m in messages if m.incident_id == incident_id
                and current is not None and m.published <= current]
    return max(eligible, key=lambda m: (m.published, m.message_id)) if eligible else None
