"""Shortlist corridor incidents to replay, on evidence the detectors saw them.

A demo incident has to show up in the detector data, or the twin has nothing
to be validated against. Picking the worst 5-minute bin was not evidence: one
noisy detector (AID01108) was "worst" for 8 of 22 incidents. So every
candidate is compared with ordinary days instead:

  control day  the same weekday and clock time 1-6 weeks earlier that is not
               a public holiday (data/hk_holidays.csv) and has no corridor
               incident of any kind in the window -- from all three STN files,
               so incidents only the Chinese files caught count too. Incidents
               are loaded from 6 weeks before --start, so a control day before
               the screened range is checked like any other
  noise floor  a second control day compared with the first. Whatever differs
               between two ordinary days is not this incident's doing.
  credited     a detector at least SLOW_KMH below the control day for at least
               RUN_BINS consecutive bins, and for longer than the two ordinary
               days ever differed that way (a tunnel detector that dips for 10
               minutes on an ordinary day is not dismissed for a 40-minute
               closure; one that dips as long on ordinary days is)
  no traffic   a detector carrying no vehicles for NO_TRAFFIC_BINS bins with
               every lane reporting, while the control day had traffic: a
               closure seen directly, which a speed cannot show

Three detector windows per incident, read from the cache, plus STN from 6
weeks before --start; on a fresh cache six months takes over an hour, most of
it downloading.

    python -m src.loaders.fetch candidates --start 2026-03-22 --end 2026-09-21
"""
from __future__ import annotations

import datetime as dt
import io
from pathlib import Path

from src.loaders import archive, detectors, holidays, incidents
from src.loaders.common import MIN_DURATION_MIN
from src.loaders.corridor import LEG

OUT_PATH = Path("data/candidates.md")

# Road time around an incident: the pre-incident hour to calibrate on, and the
# recovery after clearance (docs/02-data.md).
BEFORE_MIN, AFTER_MIN = 90, 60
# Where the incident is looked for: queues build before TD's report, so from
# LOOK_BEFORE_MIN before NEW to LOOK_AFTER_MIN after CLOSED.
LOOK_BEFORE_MIN, LOOK_AFTER_MIN = 30, 15
CONTROL_WEEKS = (1, 2, 3, 4, 5, 6)
# How far back control days reach. Incidents are loaded from this far before
# --start: before 29 Sep 2026 they were not, so a control day before the
# screened range always looked clean, whatever happened on it.
LOOKBACK = dt.timedelta(weeks=max(CONTROL_WEEKS), days=1)
SLOW_KMH, RUN_BINS = 20, 2          # 20 km/h below an ordinary day, for 10 minutes
NO_TRAFFIC_BINS = 3                 # 15 minutes without a vehicle
EARLY_ONSET_MIN = 30                # a slowdown this long before the report may be something else
# What the demo replays: an unplanned accident (team decision, 23 Sep), short
# enough for a two-hour simulation to hold it with room either side.
KINDS = ("Traffic Accident",)
MAX_DURATION_MIN = 240


def _t(text: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def window_for(incident: dict) -> tuple[dt.datetime, dt.datetime] | None:
    """The (start, end) of detector data we would need for this incident."""
    new_at, closed_at = _t(incident.get("new_at")), _t(incident.get("closed_at"))
    if new_at is None or closed_at is None:
        return None
    return new_at - dt.timedelta(minutes=BEFORE_MIN), closed_at + dt.timedelta(minutes=AFTER_MIN)


def _span(incident: dict) -> tuple[dt.datetime, dt.datetime] | None:
    """When an incident was running, as far as its messages say (at least 30 min)."""
    start = _t(incident.get("new_at")) or _t(incident.get("first_announced_at"))
    if start is None:
        return None
    end = _t(incident.get("closed_at")) or _t(incident.get("last_announced_at")) or start
    return start, max(end, start + dt.timedelta(minutes=30))


def others_in(start: dt.datetime, end: dt.datetime, corridor: list[dict],
              skip: str = "") -> list[str]:
    """Corridor incidents, of any kind, running at some point in [start, end)."""
    found = []
    for other in corridor:
        span = _span(other)
        if other.get("incident_number") != skip and span and span[0] < end and span[1] > start:
            found.append(other["incident_number"])
    return found


def holiday_in(start: dt.datetime, end: dt.datetime, holiday_table: dict) -> str:
    """The public holiday any part of [start, end) falls on, or "" if none does."""
    day = start.date()
    while day <= end.date():
        if day in holiday_table:
            return holiday_table[day]
        day += dt.timedelta(days=1)
    return ""


def control_days(incident: dict, corridor: list[dict], holiday_table: dict,
                 n: int = 2) -> list[int]:
    """The nearest `n` same-weekday days back that are ordinary: not a public
    holiday, and no corridor incident in the window."""
    start, end = window_for(incident)
    days = []
    for weeks in CONTROL_WEEKS:
        back = dt.timedelta(weeks=weeks)
        if (not holiday_in(start - back, end - back, holiday_table)
                and not others_in(start - back, end - back, corridor)):
            days.append(weeks * 7)
        if len(days) == n:
            break
    return days


def _bins(start: dt.datetime, end: dt.datetime, minutes: int) -> dict:
    # Download in parallel first (a no-op when cached): load_window alone fetches one by one.
    archive.prefetch("detectors", detectors.window_timestamps(start, end), log=io.StringIO())
    rows = detectors.load_window(start, end, log=lambda line: None)
    grid = detectors.bin_window(rows, minutes, start=start, end=end)
    return {(b["detector_id"], _t(b["bin_start"])): b for b in grid}


def _speed(b: dict | None) -> float | None:
    return None if not b or b["speed_kmh"] == "" else float(b["speed_kmh"])


def compare(day: dict, ref: dict, slots: list[dt.datetime], shift: dt.timedelta,
            ref_shift: dt.timedelta, minutes: int) -> dict[str, dict]:
    """Per detector: how far `day` ran below `ref`, slot by slot, and for how long."""
    out = {}
    for detector_id in LEG:
        run = longest = 0
        onset = None
        diffs = []
        for slot in slots:
            a = _speed(day.get((detector_id, slot - shift)))
            b = _speed(ref.get((detector_id, slot - ref_shift)))
            d = a - b if a is not None and b is not None else None
            if d is not None:
                diffs.append(d)
            run = run + 1 if d is not None and d <= -SLOW_KMH else 0
            if run == RUN_BINS and onset is None:
                onset = slot - dt.timedelta(minutes=minutes * (RUN_BINS - 1))
            longest = max(longest, run)
        out[detector_id] = {"sustained": longest >= RUN_BINS, "longest_min": longest * minutes,
                            "mean_kmh": round(sum(diffs) / len(diffs), 1) if diffs else None,
                            "worst_kmh": round(min(diffs), 1) if diffs else None,
                            "onset": onset}
    return out


def no_traffic(day: dict, ref: dict, slots: list[dt.datetime], ref_shift: dt.timedelta,
               minutes: int) -> dict[str, int]:
    """Detectors with NO_TRAFFIC_BINS+ slots of zero vehicles the control day did not have."""
    out = {}
    for detector_id in LEG:
        run = longest = 0
        for slot in slots:
            a, b = day.get((detector_id, slot)), ref.get((detector_id, slot - ref_shift))
            empty = (a is not None and a["flow_veh_h"] == 0
                     and a["lane_completeness_pct"] >= detectors.MIN_LANE_COMPLETENESS_PCT
                     and b is not None and b["flow_veh_h"] not in ("", 0))
            run = run + 1 if empty else 0
            longest = max(longest, run)
        if longest >= NO_TRAFFIC_BINS:
            out[detector_id] = longest * minutes
    return out


def evidence(incident: dict, corridor: list[dict], holiday_table: dict,
             minutes: int = 5) -> dict:
    """What the detectors saw of one incident, against two ordinary days."""
    start, end = window_for(incident)
    new_at, closed_at = _t(incident["new_at"]), _t(incident["closed_at"])
    days = control_days(incident, corridor, holiday_table)
    found = {"control_days": days,
             "holiday": holiday_table.get(new_at.date(), ""),
             "others_in_window": others_in(start, end, corridor, incident["incident_number"])}
    if len(days) < 2:
        return {**found, "credited": {}, "no_traffic": {}, "noise": [], "coverage_pct": None}

    a, b = (dt.timedelta(days=d) for d in days)
    day = _bins(start, end, minutes)
    ctl_a = _bins(start - a, end - a, minutes)
    ctl_b = _bins(start - b, end - b, minutes)
    slots = detectors.slot_starts(new_at - dt.timedelta(minutes=LOOK_BEFORE_MIN),
                                  closed_at + dt.timedelta(minutes=LOOK_AFTER_MIN), minutes)
    signal = compare(day, ctl_a, slots, dt.timedelta(0), a, minutes)
    noise = compare(ctl_b, ctl_a, slots, b, a, minutes)
    credited = {d: {**v, "leg": LEG[d]} for d, v in signal.items()
                if v["sustained"] and v["longest_min"] > noise[d]["longest_min"]}
    during = [day[k]["coverage_pct"] for k in day if new_at <= k[1] < closed_at]
    return {**found, "credited": credited,
            "no_traffic": no_traffic(day, ctl_a, slots, a, minutes),
            "noise": sorted(d for d in LEG if noise[d]["sustained"]),
            "coverage_pct": round(sum(during) / len(during)) if during else 0}


def strongest(row: dict) -> tuple[str, dict] | None:
    """The credited detector furthest below its ordinary day, on average."""
    credited = row.get("credited") or {}
    if not credited:
        return None
    return min(credited.items(), key=lambda kv: kv[1]["mean_kmh"])


def onset_vs_report_min(row: dict) -> int | None:
    """Minutes from the first credited slowdown to TD's NEW (negative: before it)."""
    onsets = [v["onset"] for v in (row.get("credited") or {}).values() if v.get("onset")]
    new_at = _t(row.get("new_at"))
    if not onsets or new_at is None:
        return None
    return round((min(onsets) - new_at).total_seconds() / 60)


def score(row: dict) -> float:
    """Rank candidates on how plainly the detectors show the incident. Visible on purpose.

    Up to 1 point each for: how far below an ordinary day the strongest
    detector ran (30 km/h = full), how long (45 min = full), how many detectors
    (3 = full), a closure seen as no traffic, and archive coverage. Minus 1
    when another corridor incident overlaps the window, minus 0.5 when the
    slowdown began over EARLY_ONSET_MIN before TD's report.
    """
    best = strongest(row)
    if best is None:
        return 0.0
    points = (min(-best[1]["mean_kmh"] / 30, 1.0) if best[1]["mean_kmh"] is not None else 0.0)
    points += min(max(v["longest_min"] for v in row["credited"].values()) / 45, 1.0)
    points += min(len(row["credited"]) / 3, 1.0)
    points += 1.0 if row.get("no_traffic") else 0.0
    points += (row.get("coverage_pct") or 0) / 100
    if row.get("others_in_window"):
        points -= 1.0
    onset = onset_vs_report_min(row)
    if onset is not None and onset < -EARLY_ONSET_MIN:
        points -= 0.5
    return round(max(points, 0.0), 2)


def shortlist(start: str, end: str, bin_minutes: int = 5, log=print) -> list[dict]:
    """Every usable corridor incident, with its evidence, best first."""
    first = dt.date.fromisoformat(start) - LOOKBACK
    holiday_table = holidays.load()
    holidays.require_years(holiday_table, first, dt.date.fromisoformat(end))
    # From LOOKBACK before `start`, so every control day is checked for
    # incidents; only incidents from `start` on are screened.
    all_incidents = incidents.load(first.isoformat(), end)
    corridor = [i for i in all_incidents if i["corridor_road"]]
    in_range = [i for i in all_incidents if (i.get("new_at") or "")[:10] >= start]
    usable = incidents.usable_corridor_incidents(in_range, MIN_DURATION_MIN)
    screened = [i for i in usable
                if i.get("detail_en") in KINDS and i["duration_min"] <= MAX_DURATION_MIN]
    log(f"{len(in_range)} incidents, {len(usable)} on the corridor with a clear "
        f"NEW and CLOSED at least {MIN_DURATION_MIN} min apart; {len(screened)} of them "
        f"{' or '.join(KINDS).lower()} of at most {MAX_DURATION_MIN} min, screened")
    usable = screened
    rows = []
    for n, incident in enumerate(usable, 1):
        row = {**incident, **evidence(incident, corridor, holiday_table, bin_minutes)}
        row["score"] = score(row)
        rows.append(row)
        log(f"  [{n}/{len(usable)}] {incident['incident_number']}  "
            f"{len(row['credited'])} detectors credited  score {row['score']}")
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows


def _cell(value, suffix: str = "") -> str:
    """A table cell: the value with its unit, or a dash -- never 'None'."""
    return "—" if value is None or value == "" else f"{value}{suffix}"


def _strongest_cell(row: dict) -> str:
    best = strongest(row)
    if best is None:
        return "none"
    d, v = best
    return f"{d} ({v['leg'].replace('_', ' ')}) {v['mean_kmh']} km/h, {v['longest_min']} min"


def _days_cell(row: dict) -> str:
    """The ordinary days an incident was compared with, e.g. "8 May, 24 Apr"."""
    new_at = _t(row.get("new_at"))
    if new_at is None or not row.get("control_days"):
        return "—"
    return ", ".join(f"{d.day} {d:%b}" for d in
                     (new_at.date() - dt.timedelta(days=n) for n in row["control_days"]))


def write_markdown(rows: list[dict], path: Path = OUT_PATH) -> Path:
    """data/candidates.md -- the evidence table the team picks demo incidents from."""
    lines = [
        "# Candidate demo incidents",
        "",
        f"Generated {dt.date.today().isoformat()} by `python -m src.loaders.fetch candidates`. "
        "Regenerate rather than edit; the reasoned pick is in `data/demo_shortlist.md`.",
        "",
        f"Screened: corridor incidents of type {', '.join(KINDS)}, with a clear NEW and CLOSED "
        f"{MIN_DURATION_MIN}-{MAX_DURATION_MIN} min apart, from all three STN files.",
        "",
        "Each incident is compared with two ordinary days: the same weekday and clock time "
        "1-6 weeks earlier that is not a public holiday and has no corridor incident in the "
        "window. A detector is "
        f"**credited** when it ran at least {SLOW_KMH} km/h below the first ordinary day for "
        f"{RUN_BINS * 5}+ minutes, longer than the two ordinary days ever differed that way. "
        "**No traffic** is a detector carrying no vehicles for 15+ minutes with every lane "
        "reporting: a closure seen directly.",
        "",
        "| # | Incident | When | Ordinary days | Where | TD's lane wording | Duration | Credited "
        "| Strongest (mean below ordinary, longest run) | No traffic | Onset vs report | Coverage "
        "| Other corridor incident | Score |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for n, r in enumerate(rows, 1):
        onset = onset_vs_report_min(r)
        lines.append(
            f"| {n} | `{r['incident_number']}` | {r['new_at'][:16].replace('T', ' ')}"
            f"{' (public holiday)' if r.get('holiday') else ''} "
            f"| {_days_cell(r)} "
            f"| {r['location_en']} ({r['direction_en'] or 'no direction'}); {r.get('detail_en', '')} "
            f"| {_cell(r.get('lane_wording'))} "
            f"| {r['duration_min']} min "
            f"| {len(r.get('credited') or {})} "
            f"| {_strongest_cell(r)} "
            f"| {', '.join(f'{d} {m} min' for d, m in (r.get('no_traffic') or {}).items()) or '—'} "
            f"| {_cell(onset, ' min')} "
            f"| {_cell(r.get('coverage_pct'), '%')} "
            f"| {', '.join(r.get('others_in_window') or []) or '—'} "
            f"| {r['score']} |")
    lines += [
        "",
        "## Reading the table",
        "",
        "- **Ordinary days** — the two days the incident was compared with. Public holidays "
        "(`data/hk_holidays.csv`) are never used. **(public holiday)** after the time means "
        "the incident itself fell on one, so it is compared with working days and may look "
        "milder than it was.",
        "- **Onset vs report** — the first credited slowdown against TD's NEW message; "
        "negative means before it. Queues usually build 5-25 minutes before the report; "
        f"more than {EARLY_ONSET_MIN} minutes before may be something else.",
        "- **Coverage** — mean share of each 5-minute bin the archive delivered during the "
        "incident (docs/02-data.md section 3).",
        "- **Other corridor incident** — another incident on the corridor overlaps the "
        "detector window, so part of the slowdown may be its doing.",
        "- **Score** — one point each for depth, duration, spread, a closure seen as no "
        "traffic, and coverage; minus one for an overlapping incident, minus a half for an "
        "early onset. It orders the table; it does not pick the demo.",
        "- An incident with fewer than two clean ordinary days is listed with no evidence "
        "rather than judged against a contaminated one.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path
