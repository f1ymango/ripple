"""Which lanes did an incident close, and from when? A rule, read off the lane readings.

TD's messages often say only "part of the lanes": the Incident Reader passes
that on as `lanes_closed: "unspecified"`, and neither replay may pick a lane
silently (docs/03-architecture.md section 3). The detectors measure every lane
on its own, every 30 seconds, so the detector just past the blockage shows
which lane stopped carrying traffic. This applies one fixed rule to those
readings (src/loaders/lane_evidence.py lists them) and returns a decision a
replay can read, or says that the readings do not decide it.

The rule, on the archived readings in which every lane reported valid:

  blocked lane   the lane carried no vehicle through MIN_RUN or more readings
                 in a row while another lane carried traffic, AND chance alone
                 would leave it empty that long less than once in CHANCE times:
                 with the lane's share of the traffic on the ordinary days at
                 the same clock time, a vehicle misses the lane with probability
                 (1 - share), so n vehicles all miss it with (1 - share)^n.
  all lanes      no lane carried a vehicle through MIN_RUN or more readings in a
                 row, where the ordinary days' traffic would leave a reading
                 empty less than once in CHANCE times (vehicles arriving at
                 random at the ordinary rate: exp(-vehicles expected)).
  otherwise      "insufficient_evidence". A quiet lane empties now and then on
                 any day, and the archive keeps under half the readings, so a
                 short or sparse run decides nothing. The replay must then be
                 told the lane by a person, or run each lane and report the
                 range; this module never guesses.

Each phase carries `from` (its first reading) and `last_open` (the reading
before it): the archive has gaps, so the true onset lies between the two.
`passing_veh_h` is what the open lanes carried past a blocked lane, the
capacity the backup network gives the blockage.

What it cannot do: say which detector to read (pick the first one downstream
of the reported place; upstream of a blockage every lane queues and no lane
empties), and map TD's lane names onto SUMO lane indices (Simulation's map).

    python -m src.loaders.fetch closed-lanes --detector AID01104 \\
        --start 2026-05-15T08:40 --end 2026-05-15T10:10 --ordinary-day 2026-05-08 2026-04-24
    -> results/data/closed-lanes_AID01104_20260515-0840_1010.md and .json
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

from src.loaders import detectors
from src.loaders.lane_evidence import by_reading, ordered_lanes

OUT_DIR = Path("results/data")
MIN_RUN = 3          # archived readings in a row; one or two is what an ordinary day shows
CHANCE = 1000        # "less than once in a thousand" before a run counts as a closure


def _volume(got: dict, lanes) -> float:
    return sum(got[lane]["volume"] or 0 for lane in lanes)


def ordinary_traffic(days: list[list[tuple[dt.datetime, dict]]]) -> dict:
    """Per lane: its share of the vehicles on the ordinary days; and vehicles per reading, all lanes."""
    readings = [got for day in days for _, got in day]
    lanes = sorted({lane for got in readings for lane in got})
    total = sum(_volume(got, got) for got in readings)
    if not readings or not total:
        return {"readings": len(readings), "share": {}, "vehicles_per_reading": None}
    return {"readings": len(readings),
            "share": {lane: sum(got.get(lane, {}).get("volume") or 0 for got in readings) / total
                      for lane in lanes},
            "vehicles_per_reading": total / len(readings)}


def _runs(flags: list[bool]) -> list[tuple[int, int]]:
    """(first, last) index of every run of True."""
    out, start = [], None
    for i, flag in enumerate(flags + [False]):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            out.append((start, i - 1))
            start = None
    return out


def _phase(readings, first: int, last: int, lanes_closed, chance: float, **extra) -> dict:
    return {"lanes_closed": lanes_closed,
            "from": readings[first][0].isoformat(),
            "last_open": readings[first - 1][0].isoformat() if first else None,
            "until": readings[last][0].isoformat(),
            "next_reading": readings[last + 1][0].isoformat() if last + 1 < len(readings) else None,
            "readings": last - first + 1, "chance": chance, **extra}


def resolve(readings: list[tuple[dt.datetime, dict]], ordinary: dict,
            min_run: int = MIN_RUN, chance: int = CHANCE) -> dict:
    """The decision for one detector's readings (lane_evidence.by_reading) against its ordinary days.

    `phases` are in time order: lanes found blocked while others moved, and
    stretches with every lane empty. `decision` is "lanes" when the first
    phase is a blocked lane, "all_lanes" when it is a full closure, and
    "insufficient_evidence" when no run passes the rule; `rejected` lists the
    runs that were long enough to look at and why they did not pass.
    """
    lanes = ordered_lanes(readings)
    share, rate = ordinary["share"], ordinary["vehicles_per_reading"]
    phases, rejected = [], []
    if len(lanes) > 1:
        for lane in lanes:
            others = [x for x in lanes if x != lane]
            flags = [got[lane]["volume"] == 0 and _volume(got, others) > 0 for _, got in readings]
            for first, last in _runs(flags):
                passed = sum(_volume(got, others) for _, got in readings[first:last + 1])
                seconds = sum(next(iter(got.values()))["period_s"] for _, got in readings[first:last + 1])
                if lane not in share:
                    p, why = None, "no ordinary-day readings for this lane"
                else:
                    p = (1 - share[lane]) ** passed
                    why = None if p < 1 / chance else f"chance {p:.2g} is not below 1 in {chance}"
                if last - first + 1 < min_run:
                    why = f"{last - first + 1} reading(s) in a row, fewer than {min_run}"
                row = _phase(readings, first, last, [lane], p, vehicles_in_other_lanes=round(passed),
                             passing_veh_h=round(passed / seconds * 3600) if seconds else None)
                (rejected.append({**row, "why": why}) if why else phases.append(row))
    flags = [_volume(got, got) == 0 for _, got in readings]
    for first, last in _runs(flags):
        n = last - first + 1
        if rate is None:
            p, why = None, "no ordinary-day readings"
        else:
            p = math.exp(-rate * n)
            why = None if p < 1 / chance else f"chance {p:.2g} is not below 1 in {chance}"
        if n < min_run:
            why = f"{n} reading(s) in a row, fewer than {min_run}"
        row = _phase(readings, first, last, "all", p)
        (rejected.append({**row, "why": why}) if why else phases.append(row))
    phases.sort(key=lambda x: x["from"])
    rejected.sort(key=lambda x: x["from"])
    decision = ("insufficient_evidence" if not phases
                else "all_lanes" if phases[0]["lanes_closed"] == "all" else "lanes")
    partial = [x for x in phases if x["lanes_closed"] != "all"]
    full = [x for x in phases if x["lanes_closed"] == "all"]
    summary = {"lanes_closed_first": phases[0]["lanes_closed"] if phases else None,
               "closed_from": phases[0]["from"] if phases else None,
               "last_open": phases[0]["last_open"] if phases else None,
               "passing_veh_h": partial[0]["passing_veh_h"] if partial and phases[0] is partial[0] else None,
               "all_lanes_from": full[0]["from"] if full else None,
               "last_closed_reading": max(x["until"] for x in phases) if phases else None,
               "flowing_again_by": max(phases, key=lambda x: x["until"])["next_reading"] if phases else None}
    return {"decision": decision, "summary": summary, "lanes": lanes, "phases": phases, "rejected": rejected,
            "rule": {"min_run_readings": min_run, "chance_one_in": chance},
            "ordinary": {"readings": ordinary["readings"],
                         "share_pct": {lane: round(100 * s, 1) for lane, s in share.items()},
                         "vehicles_per_reading": None if rate is None else round(rate, 2)}}


def build(detector_id: str, start: dt.datetime, end: dt.datetime,
          ordinary_days: list[dt.date]) -> dict:
    """Load the window and the same clock times on the ordinary days, and apply the rule."""
    def day(s: dt.datetime, e: dt.datetime) -> tuple[list, str]:
        lines: list[str] = []
        rows = detectors.load_window(s, e, [detector_id], log=lines.append)
        return by_reading(rows, detector_id), (lines[-1] if lines else "")
    readings, archive = day(start, end)
    others = []
    for d in ordinary_days:
        shift = dt.datetime.combine(d, start.timetz()) - start
        others.append(day(start + shift, end + shift)[0])
    doc = resolve(readings, ordinary_traffic(others))
    return {"detector_id": detector_id, "start": start.isoformat(), "end": end.isoformat(),
            "ordinary_days": [d.isoformat() for d in ordinary_days], "archive": archive,
            "readings": len(readings), **doc}


def _clock(text: str | None) -> str:
    return "—" if text is None else text[11:19]


def _chance(p: float | None) -> str:
    return "—" if p is None else "under 1 in a million" if p < 1e-6 else f"1 in {round(1 / p):,}"


def _summary_lines(s: dict) -> list[str]:
    if s["lanes_closed_first"] is None:
        return ["No phase passed the rule. Give the replay its lane by hand, or run each lane and report the range."]
    first = "all lanes" if s["lanes_closed_first"] == "all" else ", ".join(s["lanes_closed_first"])
    lines = [f"- Closed first: **{first}**, from {_clock(s['closed_from'])} "
             f"(the reading before it, still open: {_clock(s['last_open'])})."]
    if s["passing_veh_h"] is not None:
        lines.append(f"- Passing the blocked lane meanwhile: {s['passing_veh_h']} veh/h.")
    if s["all_lanes_from"] and s["lanes_closed_first"] != "all":
        lines.append(f"- All lanes empty from {_clock(s['all_lanes_from'])}.")
    lines.append(f"- Last closed reading {_clock(s['last_closed_reading'])}; the next reading, with the road "
                 f"carrying traffic again: {_clock(s['flowing_again_by'])}.")
    return lines


def _md(doc: dict, command: str) -> str:
    rule = doc["rule"]
    verdict = {"lanes": "a lane was blocked while others moved", "all_lanes": "all lanes closed",
               "insufficient_evidence": "the readings do not decide it: no lane is chosen"}[doc["decision"]]
    out = [f"# Closed lanes at {doc['detector_id']}, {doc['start'][:10]} "
           f"{doc['start'][11:16]}-{doc['end'][11:16]}", "",
           f"Generated by `{command}`. Regenerate rather than edit.", "",
           f"**Decision: {doc['decision']}** ({verdict}).", "",
           f"Rule: a lane is blocked if it carried no vehicle through {rule['min_run_readings']} or more "
           f"archived readings in a row while another lane carried traffic, and chance alone would do that "
           f"less than once in {rule['chance_one_in']:,} times given the lane's share of the traffic on the "
           f"ordinary days ({', '.join(doc['ordinary_days'])}). All lanes: every lane empty that long, where "
           f"the ordinary days' traffic would leave it empty less than once in {rule['chance_one_in']:,} times. "
           f"{doc['readings']} readings with every lane valid ({doc['archive']}); "
           f"{doc['ordinary']['readings']} on the ordinary days.", "",
           "## Summary for a replay", ""] + _summary_lines(doc["summary"]) + ["",
           "## Phases", "",
           "| Lanes closed | From (first reading) | Last reading before | Until (last reading) | Next reading "
           "| Readings | Vehicles in the other lanes | Chance | Passing, veh/h |", "|---|---|---|---|---|---|---|---|---|"]
    def row(x: dict) -> str:
        lanes = "all" if x["lanes_closed"] == "all" else ", ".join(x["lanes_closed"])
        return (f"| {lanes} | {_clock(x['from'])} | {_clock(x['last_open'])} | {_clock(x['until'])} "
                f"| {_clock(x['next_reading'])} | {x['readings']} | {x.get('vehicles_in_other_lanes', '—')} "
                f"| {_chance(x['chance'])} | {x.get('passing_veh_h', '—')} |")
    out += [row(x) for x in doc["phases"]] or ["| none | | | | | | | | |"]
    out += ["", "The archive keeps under half the readings: a phase began between *last reading before* and "
            "*from*, and ended between *until* and *next reading*. *Passing* is what the open lanes carried "
            "past the blocked one.", "", "## Ordinary days", "",
            "| Lane | Share of the vehicles |", "|---|---|"]
    out += [f"| {lane} | {pct}% |" for lane, pct in doc["ordinary"]["share_pct"].items()]
    out += ["", f"Vehicles per reading, all lanes: {doc['ordinary']['vehicles_per_reading']}."]
    if doc["rejected"]:
        out += ["", "## Runs that did not pass", "",
                "| Lanes | From | Until | Readings | Why not |", "|---|---|---|---|---|"]
        out += [f"| {'all' if x['lanes_closed'] == 'all' else ', '.join(x['lanes_closed'])} | {_clock(x['from'])} "
                f"| {_clock(x['until'])} | {x['readings']} | {x['why']} |" for x in doc["rejected"]]
    return "\n".join(out) + "\n"


def write(doc: dict, command: str, out_dir: Path = OUT_DIR) -> tuple[Path, Path]:
    start, end = dt.datetime.fromisoformat(doc["start"]), dt.datetime.fromisoformat(doc["end"])
    stem = out_dir / f"closed-lanes_{doc['detector_id']}_{start:%Y%m%d-%H%M}_{end:%H%M}"
    out_dir.mkdir(parents=True, exist_ok=True)
    md, js = stem.with_suffix(".md"), stem.with_suffix(".json")
    md.write_text(_md(doc, command), encoding="utf-8", newline="\n")
    js.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return md, js
