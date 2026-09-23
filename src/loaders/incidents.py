"""Special Traffic News -> one row per incident, with a start and a clearance time (component A2).

The STN feed is a snapshot of what is happening *now*, not a history. An
incident appears as a NEW message, is replaced by UPDATED messages as it
changes, ends with a CLOSED message, and then vanishes from the feed. So a
timeline has to be reassembled from archived snapshots.

Two things make that work better than the 4-minute snapshot cadence suggests:

  * each message carries its own ANNOUNCEMENT_DATE, so once we have caught a
    message its time is exact, not rounded to when we happened to look;
  * messages are immutable -- a new status means a new message ID -- so
    keeping every distinct ID per INCIDENT_NUMBER reconstructs the sequence.

The cadence still costs us: a message issued and superseded inside one gap is
never archived. That shows up as an incident with no NEW or no CLOSED, which
is why every row carries `left_censored` / `right_censored` flags rather than
a silently wrong duration.

Clearance time = CLOSED time - NEW time (docs/02-data.md section 2).

    python -m src.loaders.fetch incidents --start 2026-06-22 --end 2026-09-21
"""
from __future__ import annotations

import datetime as dt
import xml.etree.ElementTree as ET
from pathlib import Path

from src.loaders import archive, common
from src.loaders.common import HK, MIN_DURATION_MIN
from src.loaders.corridor import on_corridor

OUT_DIR = Path("data")

# Statuses the feed uses. Anything else is passed through untouched so a new
# one shows up in the data instead of being silently dropped.
STATUS_NEW, STATUS_CLOSED = "NEW", "CLOSED"


def parse_snapshot(xml_bytes: bytes) -> list[dict[str, str]]:
    """Every <message> in one snapshot, as {field name: text}, '' for empty fields."""
    root = ET.fromstring(xml_bytes)
    return [{field.tag: (field.text or "").strip() for field in message}
            for message in root.findall("message")]


def _announced_at(message: dict[str, str]) -> dt.datetime | None:
    """ANNOUNCEMENT_DATE as a timezone-aware datetime, or None if unparseable."""
    raw = message.get("ANNOUNCEMENT_DATE", "")
    try:
        return dt.datetime.fromisoformat(raw).replace(tzinfo=HK)
    except ValueError:
        return None


def collect_messages(timestamps: list[str]) -> dict[str, dict]:
    """Every distinct STN message across these snapshots, keyed by message ID.

    Streams the cache one snapshot at a time; three months is ~11,000 files and
    we only keep the messages, not the XML.
    """
    messages: dict[str, dict] = {}
    for archive_time, xml_bytes in archive.iter_snapshots("stn", timestamps):
        for stn in parse_snapshot(xml_bytes):
            message_id = stn.get("ID", "")
            if not message_id:
                continue
            seen = messages.get(message_id)
            if seen is None:
                messages[message_id] = {"first_seen": archive_time,
                                        "last_seen": archive_time, "stn": stn}
            else:
                seen["last_seen"] = archive_time
    return messages


def build_incidents(messages: dict[str, dict]) -> list[dict]:
    """Group messages into incidents and work out when each started and cleared.

    One row per INCIDENT_NUMBER. Every status row is kept in `statuses` so a
    timeline can be re-derived without re-reading the archive.
    """
    grouped: dict[str, list[dict]] = {}
    for record in messages.values():
        number = record["stn"].get("INCIDENT_NUMBER", "")
        if number:
            grouped.setdefault(number, []).append(record)

    incidents = []
    for number, records in sorted(grouped.items()):
        records.sort(key=lambda r: (_announced_at(r["stn"]) or dt.datetime.min.replace(tzinfo=HK),
                                    int(r["stn"].get("ID") or 0)))
        first, last = records[0]["stn"], records[-1]["stn"]
        statuses = [r["stn"].get("INCIDENT_STATUS_EN", "") for r in records]

        new_at = next((_announced_at(r["stn"]) for r in records
                       if r["stn"].get("INCIDENT_STATUS_EN") == STATUS_NEW), None)
        closed_at = next((_announced_at(r["stn"]) for r in reversed(records)
                          if r["stn"].get("INCIDENT_STATUS_EN") == STATUS_CLOSED), None)

        # No NEW message means the incident was already running when our window
        # opened (or its NEW fell in a snapshot gap); no CLOSED means it was
        # still running when the window shut. Either way we did not see its
        # duration, so duration_min stays blank; observed_span_min is the lower
        # bound we did see, under a name that says so.
        left_censored = new_at is None
        right_censored = closed_at is None
        first_at, last_at = _announced_at(first), _announced_at(last)
        duration_min = (round((closed_at - new_at).total_seconds() / 60)
                        if new_at and closed_at else None)
        observed_span_min = (round((last_at - first_at).total_seconds() / 60)
                             if first_at and last_at else None)

        # Scope from every message, not just the first: a terse NEW followed by
        # an UPDATED that names the road is still our incident.
        corridor_road = on_corridor(*(r["stn"].get(field, "") for r in records
                                      for field in ("LOCATION_EN", "CONTENT_EN",
                                                    "NEAR_LANDMARK_EN")))

        incidents.append({
            "incident_number": number,
            "heading_en": first.get("INCIDENT_HEADING_EN", ""),
            "detail_en": first.get("INCIDENT_DETAIL_EN", ""),
            "location_en": first.get("LOCATION_EN", ""),
            "location_cn": first.get("LOCATION_CN", ""),
            "direction_en": first.get("DIRECTION_EN", ""),
            "near_landmark_en": first.get("NEAR_LANDMARK_EN", ""),
            "district_en": first.get("DISTRICT_EN", ""),          # usually empty
            "new_at": new_at.isoformat() if new_at else "",
            "closed_at": closed_at.isoformat() if closed_at else "",
            "duration_min": duration_min if duration_min is not None else "",
            "first_announced_at": first_at.isoformat() if first_at else "",
            "last_announced_at": last_at.isoformat() if last_at else "",
            "observed_span_min": observed_span_min if observed_span_min is not None else "",
            "left_censored": left_censored,
            "right_censored": right_censored,
            "n_messages": len(records),
            "statuses": "|".join(statuses),
            "corridor_road": corridor_road or "",
            # Across every message: the last-announced one is not always the
            # last one we saw in the feed.
            "first_seen": min(r["first_seen"] for r in records),
            "last_seen": max(r["last_seen"] for r in records),
            "content_en": first.get("CONTENT_EN", ""),
            "content_cn": first.get("CONTENT_CN", ""),
        })
    return incidents


def load(start: str, end: str) -> list[dict]:
    """Every incident announced between two dates, newest fields first seen kept."""
    timestamps = archive.list_versions("stn", start, end)
    if not timestamps:
        raise RuntimeError(
            f"the archive has no STN snapshots for {start}..{end}. Its latest "
            "available day is yesterday -- check the dates.")
    return build_incidents(collect_messages(timestamps))


def write_csv(incidents: list[dict], path: Path) -> Path:
    """One row per incident. utf-8-sig so Excel on Windows shows the Chinese."""
    return common.write_csv(incidents, path, encoding="utf-8-sig")


def usable_corridor_incidents(incidents: list[dict],
                              min_duration_min: int = MIN_DURATION_MIN) -> list[dict]:
    """Corridor incidents with a clear start and clearance, long enough to simulate.

    The role brief asks for a clear NEW and CLOSED at least MIN_DURATION_MIN apart
    (roles/data-experiments.md), so censored rows are excluded here rather than
    quietly carried into the shortlist.
    """
    return [i for i in incidents
            if i["corridor_road"]
            and not i["left_censored"] and not i["right_censored"]
            and isinstance(i["duration_min"], int)
            and i["duration_min"] >= min_duration_min]
