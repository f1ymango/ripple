"""Which lane closed first? One detector's lanes, reading by reading (week 2).

TD's first message for IN-26-03365 says only "part of the lanes", so the
Evaluator has to choose which lane the replay closes, and say so
(docs/03-architecture.md section 3). The detectors measure every lane on its
own, every 30 seconds. This lists those readings for one detector, and counts
the readings in which a lane carried no vehicle while another lane still did --
on the incident day and at the same clock time on ordinary days, because a
quiet lane empties now and then on any day.

    python -m src.loaders.fetch lane-evidence --detector AID01104 \\
        --start 2026-05-15T08:40 --end 2026-05-15T09:20 --ordinary-day 2026-05-08
    -> results/data/lane-evidence_AID01104_20260515-0840_0920.md and .json
"""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

from src.loaders import detectors

OUT_DIR = Path("results/data")
# Offside to nearside, the team's lane convention (docs/02-data.md).
LANE_ORDER = ["Fast Lane", "Middle Lane 2", "Middle Lane", "Middle Lane 1", "Slow Lane"]


def by_reading(rows: list[dict], detector_id: str) -> list[tuple[dt.datetime, dict]]:
    """[(time, {lane: row})], keeping only readings where every lane reported valid."""
    readings: dict[dt.datetime, dict] = defaultdict(dict)
    lanes, invalid = set(), set()
    for r in rows:
        if r["detector_id"] != detector_id:
            continue
        lanes.add(r["lane"])
        if r["valid"]:
            readings[r["timestamp"]][r["lane"]] = r
        else:
            invalid.add(r["timestamp"])
    return [(t, got) for t, got in sorted(readings.items())
            if set(got) == lanes and t not in invalid]


def ordered_lanes(readings: list[tuple[dt.datetime, dict]]) -> list[str]:
    seen = {lane for _, got in readings for lane in got}
    known = [lane for lane in LANE_ORDER if lane in seen]
    return known + sorted(seen - set(known))


def empty_while_moving(got: dict) -> list[str]:
    """Lanes that carried no vehicle in this reading while another lane carried one."""
    if not any((r["volume"] or 0) > 0 for r in got.values()):
        return []
    return [lane for lane, r in got.items() if r["volume"] == 0]


def summary(readings: list[tuple[dt.datetime, dict]]) -> dict[str, dict]:
    """Per lane: vehicles, share, and how often and how long it sat empty while others moved."""
    lanes = ordered_lanes(readings)
    total = sum(r["volume"] or 0 for _, got in readings for r in got.values())
    out = {}
    for lane in lanes:
        vehicles = sum(got[lane]["volume"] or 0 for _, got in readings)
        flagged, run, best, best_span, run_start = 0, 0, 0, None, None
        for t, got in readings:
            if lane not in empty_while_moving(got):
                run = 0
                continue
            flagged += 1
            if run == 0:
                run_start = t
            run += 1
            if run > best:
                best, best_span = run, (run_start, t)
        out[lane] = {"readings": len(readings), "vehicles": round(vehicles),
                     "share_pct": round(vehicles / total * 100) if total else None,
                     "empty_while_moving": flagged, "longest_run": best,
                     "longest_run_span": [t.isoformat() for t in best_span] if best_span else []}
    return out


def _day(start: dt.datetime, end: dt.datetime, detector_id: str) -> dict:
    lines: list[str] = []
    rows = detectors.load_window(start, end, [detector_id], log=lines.append)
    readings = by_reading(rows, detector_id)
    return {"start": start.isoformat(), "end": end.isoformat(),
            "archive": lines[-1] if lines else "",
            "readings": [{"time": t.isoformat(),
                          "lanes": {lane: {"volume": r["volume"], "speed_kmh": r["speed_kmh"],
                                           "occupancy_pct": r["occupancy_pct"]}
                                    for lane, r in got.items()},
                          "empty_while_moving": empty_while_moving(got)}
                         for t, got in readings],
            "summary": summary(readings)}


def build(detector_id: str, start: dt.datetime, end: dt.datetime,
          ordinary_days: list[dt.date]) -> dict:
    """The incident window, then the same clock times on each ordinary day."""
    ordinary = []
    for day in ordinary_days:
        shift = dt.datetime.combine(day, start.timetz()) - start
        ordinary.append(_day(start + shift, end + shift, detector_id))
    return {"detector_id": detector_id, "incident": _day(start, end, detector_id),
            "ordinary": ordinary}


def _num(value) -> str:
    return "—" if value is None else f"{value:g}"


def _md(doc: dict, command: str) -> str:
    inc = doc["incident"]
    lanes = list(inc["summary"])
    when = f"{inc['start'][:10]} {inc['start'][11:16]}-{inc['end'][11:16]}"
    out = [f"# Lane by lane at {doc['detector_id']}, {when}", "",
           f"Generated by `{command}`. Regenerate rather than edit.", "",
           "Every 30-second reading the archive kept in which all lanes reported valid. "
           "*Empty while another moved*: the lane carried no vehicle in that reading while "
           "another lane carried at least one. Occupancy is as the loader reports it.", "",
           "## Per lane, incident day against ordinary days", "",
           "| Day | Lane | Readings | Vehicles | Share | Empty while another moved "
           "| Longest run in a row |", "|---|---|---|---|---|---|---|"]
    for day in [inc] + doc["ordinary"]:
        for lane, s in day["summary"].items():
            span = s["longest_run_span"]
            run = (f"{s['longest_run']} ({span[0][11:19]}-{span[1][11:19]})" if span else "0")
            out.append(f"| {day['start'][:10]} | {lane} | {s['readings']} | {s['vehicles']} "
                       f"| {_num(s['share_pct'])}% | {s['empty_while_moving']} | {run} |")
    out += ["", "Archive: " + "; ".join(f"{d['start'][:10]}: {d['archive']}"
                                        for d in [inc] + doc["ordinary"]),
            "", f"## Every reading on {inc['start'][:10]}", "",
            "| Time | " + " | ".join(f"{lane}: vehicles, km/h, occupancy %" for lane in lanes)
            + " | Empty while another moved |",
            "|---|" + "---|" * len(lanes) + "---|"]
    for r in inc["readings"]:
        cells = [f"{_num(r['lanes'][lane]['volume'])}, {_num(r['lanes'][lane]['speed_kmh'])}, "
                 f"{_num(r['lanes'][lane]['occupancy_pct'])}" for lane in lanes]
        out.append(f"| {r['time'][11:19]} | " + " | ".join(cells)
                   + f" | {', '.join(r['empty_while_moving']) or '—'} |")
    return "\n".join(out) + "\n"


def write(doc: dict, command: str, out_dir: Path = OUT_DIR) -> tuple[Path, Path]:
    start = dt.datetime.fromisoformat(doc["incident"]["start"])
    end = dt.datetime.fromisoformat(doc["incident"]["end"])
    stem = out_dir / f"lane-evidence_{doc['detector_id']}_{start:%Y%m%d-%H%M}_{end:%H%M}"
    out_dir.mkdir(parents=True, exist_ok=True)
    md, js = stem.with_suffix(".md"), stem.with_suffix(".json")
    md.write_text(_md(doc, command), encoding="utf-8", newline="\n")
    js.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return md, js
