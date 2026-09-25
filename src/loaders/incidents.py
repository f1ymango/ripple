"""Special Traffic News -> one row per incident, with a start and a clearance time (component A2).

The STN feed is a snapshot of what is happening *now*, not a history, and
each copy of it holds a single message. An incident appears as a NEW message,
is replaced by UPDATED messages as it changes, ends with a CLOSED message, and
then vanishes from the feed. So a timeline has to be reassembled from archived
snapshots -- of all three language files, since the archive saves each at
different moments (docs/02-data.md section 2).

Two things make that work better than the 4-minute snapshot cadence suggests:

  * each message carries its own ANNOUNCEMENT_DATE, so once we have caught a
    message its time is exact, not rounded to when we happened to look;
  * keeping every distinct message ID per INCIDENT_NUMBER reconstructs the
    sequence. A new status is usually a new message, with one exception: TD
    switches messages to CLOSED under the same ID -- the last one when the
    incident ends, and the NEW one too -- so a later CLOSED on a known ID is
    kept (collect_messages) and read with care (build_incidents).

The cadence still costs us: a message issued and superseded inside one gap is
never archived. That shows up as an incident with no NEW or no CLOSED, which
is why every row carries `left_censored` / `right_censored` flags rather than
a silently wrong duration.

Clearance time = CLOSED time - NEW time (docs/02-data.md section 2).

    python -m src.loaders.fetch incidents --start 2026-03-22 --end 2026-09-21
"""
from __future__ import annotations

import datetime as dt
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from src.loaders import archive, common
from src.loaders.common import HK, MIN_DURATION_MIN
from src.loaders.corridor import on_corridor

OUT_DIR = Path("data")

# Statuses the feed uses. Anything else is passed through untouched so a new
# one shows up in the data instead of being silently dropped.
STATUS_NEW, STATUS_CLOSED = "NEW", "CLOSED"

# Special Traffic News is published as three files, one per page language
# (archive.FEEDS). They carry the same messages -- same ID, times, status and
# English text -- but each file holds one message at a time and the archive
# saves the three at different moments, so together they catch messages and
# CLOSED switches that one file missed. English first: its record is kept.
STN_FEEDS = ("stn", "stn_tc", "stn_sc")
# The /sc/ file's Chinese text is in simplified script. Its sightings and
# statuses are used; its Chinese text never is, so no row mixes the two.
TEXT_FEEDS = ("stn", "stn_tc")
# The only fields that legitimately differ between copies of one message.
STATUS_FIELDS = ("INCIDENT_STATUS_EN", "INCIDENT_STATUS_CN")
# Two copies that differ in these are not the same message.
IDENTITY_FIELDS = ("INCIDENT_NUMBER", "ANNOUNCEMENT_DATE")

# A message announcing the end of a closure. Used as the clearance only when
# the CLOSED status itself was never archived -- and never when the same
# message says something is still shut ("the slow lane remains closed").
REOPENED = re.compile(r"re-?opened|resumed|now cancelled|has been cleared", re.IGNORECASE)
STILL_CLOSED = re.compile(r"remain(s|ing)? closed|still (being )?closed", re.IGNORECASE)


def parse_snapshot(xml_bytes: bytes) -> list[dict[str, str]]:
    """Every <message> in one snapshot, as {field name: text}, '' for empty fields."""
    root = common.parse_xml(xml_bytes)
    return [{field.tag: (field.text or "").strip() for field in message}
            for message in root.findall("message")]


def _announced_at(message: dict[str, str]) -> dt.datetime | None:
    """ANNOUNCEMENT_DATE as a timezone-aware datetime, or None if unparseable."""
    raw = message.get("ANNOUNCEMENT_DATE", "")
    try:
        return dt.datetime.fromisoformat(raw).replace(tzinfo=HK)
    except ValueError:
        return None


def collect_messages(timestamps: list[str], log=print, feed: str = "stn",
                     messages: dict[str, dict] | None = None,
                     conflicts: list[dict] | None = None) -> dict[str, dict]:
    """Every distinct STN message across these snapshots, keyed by message ID.

    Streams the cache one snapshot at a time; six months is ~18,400 files and
    we only keep the messages, not the XML. A snapshot that does not parse is
    skipped and named in the run summary (see archive.read_summary).

    **A message's status changes under the same ID.** TD marks an incident
    finished by switching its last message -- usually the "...is re-opened to
    all traffic" one -- from UPDATED to CLOSED; the ID, text and
    ANNOUNCEMENT_DATE stay the same. Keeping each message as first seen threw
    away about 70% of closures, so a later CLOSED is kept. A CLOSED is never
    undone: the feed can serve an out-of-date copy saying UPDATED for a few
    minutes after the switch.

    Pass `messages` to add another language's file to what is already
    collected (see load). Copies that disagree are never silently merged:
    each disagreement is appended to `conflicts` (see _add_sighting).
    """
    messages = {} if messages is None else messages
    read, unparseable = 0, []
    for archive_time, xml_bytes in archive.iter_snapshots(feed, timestamps):
        try:
            snapshot = parse_snapshot(xml_bytes)
        except ET.ParseError:
            unparseable.append(archive_time)
            continue
        read += 1
        for stn in snapshot:
            message_id = stn.get("ID", "")
            if not message_id:
                continue
            if feed not in TEXT_FEEDS:
                stn = {k: ("" if k.endswith("_CN") else v) for k, v in stn.items()}
            seen = messages.get(message_id)
            if seen is None:
                messages[message_id] = {"first_seen": archive_time, "last_seen": archive_time,
                                        "stn": stn, "feeds": {feed},
                                        "statuses": {stn.get("INCIDENT_STATUS_EN", "")},
                                        "text_feed": feed if feed in TEXT_FEEDS else ""}
            else:
                _add_sighting(seen, stn, feed, archive_time, conflicts)
    log(archive.read_summary(feed, len(timestamps), read, unparseable))
    return messages


def _add_sighting(seen: dict, stn: dict[str, str], feed: str, archive_time: str,
                  conflicts: list[dict] | None) -> None:
    """Fold one more copy of a message already collected into its record.

    A copy with a different INCIDENT_NUMBER or ANNOUNCEMENT_DATE is not the
    same message and is never merged. TD does sometimes edit a message's text
    in place (a location filled in later, say): such a copy still counts as a
    sighting, the first text is kept, and the edit is reported. /sc/ copies are
    compared on those two fields only -- TD converts every Chinese character in
    them to simplified script, including Chinese inside the English text.
    """
    kept = seen["stn"]
    if feed in TEXT_FEEDS and seen.get("text_feed", "stn"):
        compared = [k for k in set(kept) | set(stn) if k not in STATUS_FIELDS]
    else:
        compared = list(IDENTITY_FIELDS)
    differs = sorted(k for k in compared if kept.get(k, "") != stn.get(k, ""))
    if differs and conflicts is not None:
        conflicts.append({"id": stn.get("ID", ""), "feed": feed, "archive_time": archive_time,
                          "fields": differs,
                          "kind": "conflict" if set(differs) & set(IDENTITY_FIELDS) else "edited"})
    if set(differs) & set(IDENTITY_FIELDS):
        return
    seen["first_seen"] = min(seen["first_seen"], archive_time)
    seen["last_seen"] = max(seen["last_seen"], archive_time)
    seen.setdefault("feeds", set()).add(feed)
    seen.setdefault("statuses", set()).add(stn.get("INCIDENT_STATUS_EN", ""))
    if feed in TEXT_FEEDS and not seen.get("text_feed", "stn"):
        # Seen before only in the /sc/ file: take the traditional Chinese now.
        kept.update({k: v for k, v in stn.items() if k.endswith("_CN") and k not in STATUS_FIELDS})
        seen["text_feed"] = feed
    if stn.get("INCIDENT_STATUS_EN") == STATUS_CLOSED:
        kept["INCIDENT_STATUS_EN"] = STATUS_CLOSED


# TD's own words for which lanes are shut, most specific first. A summary for
# screening only: reading a message properly is the Incident Reader's job.
LANE_WORDING = [
    (re.compile(r"\ball lanes\b", re.I), "all lanes"),
    (re.compile(r"one-lane-two-way", re.I), "one-lane-two-way"),
    (re.compile(r"only lane of the slip road", re.I), "only lane of a slip road"),
    (re.compile(r"\b(tunnel tube )?(fast|slow|middle) lane( \d)?\b", re.I), None),
    (re.compile(r"part of the lanes", re.I), "part of the lanes"),
]


def lane_wording(contents: list[str]) -> str:
    """The closure wording of each message, in order, repeats dropped:
    "part of the lanes -> all lanes". Re-opening messages are left out."""
    said = []
    for text in contents:
        if REOPENED.search(text) and not STILL_CLOSED.search(text):
            continue
        # Only the sentences about what is shut: not "Only the fast lane is
        # available", not "the fast lane is re-opened" in a partial re-opening.
        closed = " ".join(s for s in re.split(r"(?<=\.)\s+", text)
                          if not s.lstrip().lower().startswith("only") and not REOPENED.search(s))
        for pattern, label in LANE_WORDING:
            found = [m.group(0).lower() for m in pattern.finditer(closed)]
            if found:
                phrase = label or " + ".join(dict.fromkeys(found))
                if not said or said[-1] != phrase:
                    said.append(phrase)
                break
    return " -> ".join(said)


def _was(record: dict, status: str) -> bool:
    """True if any copy of this message was seen with this status."""
    return status in record.get("statuses", ()) or record["stn"].get("INCIDENT_STATUS_EN") == status


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

        # The start is the message published as NEW, even if TD has since
        # switched it to CLOSED: it does that to the NEW message as well.
        start = next((r for r in records if _was(r, STATUS_NEW)), None)
        new_at = _announced_at(start["stn"]) if start else None

        # The clearance is read only from the incident's latest message, and
        # never from the NEW one. TD switches the NEW message to CLOSED too,
        # sometimes half an hour before the incident ends, and an incident
        # number can carry on after one of its messages is closed; either way
        # that CLOSED says "over" without saying when. The latest message's
        # CLOSED status wins; failing that, its re-opening wording (the CLOSED
        # switch fell in an archive gap), which gives the same time.
        last_at = _announced_at(last)
        final = [r for r in records
                 if r is not start and last_at and _announced_at(r["stn"]) == last_at]
        closed_at, clearance_source = None, ""
        if any(r["stn"].get("INCIDENT_STATUS_EN") == STATUS_CLOSED for r in final):
            closed_at, clearance_source = last_at, "CLOSED status"
        elif any(REOPENED.search(r["stn"].get("CONTENT_EN", ""))
                 and not STILL_CLOSED.search(r["stn"].get("CONTENT_EN", "")) for r in final):
            closed_at, clearance_source = last_at, "re-opened message"
        if closed_at and new_at and closed_at <= new_at:
            # TD reuses the NEW message's time on a later message now and then
            # (IN-26-05880: both 13:34, closed around 20:11). A clearance at or
            # before the start is not one.
            closed_at, clearance_source = None, ""

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
            "clearance_source": clearance_source,
            "duration_min": duration_min if duration_min is not None else "",
            "first_announced_at": first_at.isoformat() if first_at else "",
            "last_announced_at": last_at.isoformat() if last_at else "",
            "observed_span_min": observed_span_min if observed_span_min is not None else "",
            "left_censored": left_censored,
            "right_censored": right_censored,
            "n_messages": len(records),
            "lane_wording": lane_wording([r["stn"].get("CONTENT_EN", "") for r in records]),
            # Which of the three STN files the incident's messages were seen in.
            "seen_in": "|".join(f for f in STN_FEEDS
                                if any(f in r.get("feeds", ()) for r in records)),
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


def load(start: str, end: str, feeds: tuple[str, ...] = STN_FEEDS, log=print) -> list[dict]:
    """Every incident announced between two dates, from all three STN files.

    Pass feeds=("stn",) for the English file alone, as before 25 Sep.
    """
    messages: dict[str, dict] = {}
    conflicts: list[dict] = []
    listed = 0
    for feed in feeds:
        timestamps = archive.list_versions(feed, start, end)
        listed += len(timestamps)
        collect_messages(timestamps, log=log, feed=feed, messages=messages, conflicts=conflicts)
    if not listed:
        raise RuntimeError(
            f"the archive has no STN snapshots for {start}..{end}. Its latest "
            "available day is yesterday -- check the dates.")
    if len(feeds) > 1:
        english_only = sum(1 for m in messages.values() if "stn" in m.get("feeds", ()))
        clashes = [c for c in conflicts if c["kind"] == "conflict"]
        log(f"stn merged: {len(messages)} distinct messages from {', '.join(feeds)} "
            f"({english_only} in the English file), {len(clashes)} conflicting copies, "
            f"{len(conflicts) - len(clashes)} with text edited by TD")
    for c in conflicts[:10]:
        what = ("not merged" if c["kind"] == "conflict"
                else "counted as a sighting, first text kept")
        log(f"  {c['kind']}: message {c['id']} in {c['feed']} {c['archive_time']} "
            f"differs in {', '.join(c['fields'])}; {what}")
    return build_incidents(messages)


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
