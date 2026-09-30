"""Where traffic joins and leaves the corridor between detectors (week 2, for the twin).

The twin's routes start and end at detector locations (src/twin/make_routes.py),
so traffic that really joins from a side road between two detectors has to be
inserted at the next detector instead. This measures, for each pair of
neighbouring detectors on each chain, how the hourly flow changes between
them: a rise means traffic joins in between, a fall means it leaves. Only the
net is visible (+600 could be 800 joining and 200 leaving), so it is measured
on the incident morning and at the same clock time on ordinary days: a real
junction shows up every time.

    python -m src.loaders.fetch flow-balance --start 2026-05-15T07:55 \\
        --end 2026-05-15T08:55 --ordinary-day 2026-05-08 2026-04-24
    -> results/data/flow-balance_20260515-0755_0855.md and .json
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

from src.loaders import detectors
from src.loaders.corridor import (CHAIN_EASTBOUND, CHAIN_WESTBOUND, CHAIN_WESTERN_EASTBOUND,
                                  CHAIN_WESTERN_WESTBOUND, OUT_PATH as DETECTORS_CSV)

OUT_DIR = Path("results/data")
CHAINS = {"Main road, eastbound (Aberdeen to Wan Chai)": CHAIN_EASTBOUND,
          "Main road, westbound (Wan Chai to Aberdeen)": CHAIN_WESTBOUND,
          "Western alternative, eastbound": CHAIN_WESTERN_EASTBOUND,
          "Western alternative, westbound": CHAIN_WESTERN_WESTBOUND}


def hourly_flows(rows: list[dict]) -> dict[str, dict]:
    """Per detector: vehicles per hour over the seconds each lane was observed, with a margin.

    Each lane's rate is its counted vehicles over its own valid seconds, as in
    detectors.bin_window. A detector with a lane that never reported valid is
    left out: its total is unknown, not smaller. The margin is the 95% range
    from sampling alone if vehicles arrive at random (Poisson); platoons from
    traffic lights make the real spread somewhat wider.
    """
    vol, secs, lanes = defaultdict(float), defaultdict(float), defaultdict(set)
    for r in rows:
        lanes[r["detector_id"]].add(r["lane"])
        if r["valid"] and r["volume"] is not None:
            vol[(r["detector_id"], r["lane"])] += r["volume"]
            secs[(r["detector_id"], r["lane"])] += r["period_s"]
    out = {}
    for d, names in lanes.items():
        keys = [(d, lane) for lane in names]
        if not all(secs[k] for k in keys):
            continue
        flow = sum(vol[k] / secs[k] * 3600 for k in keys)
        variance = sum(vol[k] * (3600 / secs[k]) ** 2 for k in keys)
        out[d] = {"veh_h": round(flow), "margin_veh_h": round(1.96 * math.sqrt(variance)),
                  "observed_min": round(max(secs[k] for k in keys) / 60)}
    return out


def change(flows: dict[str, dict], up: str, down: str) -> dict | None:
    """The flow change from `up` to `down` with its margin, or None if either is unknown."""
    if up not in flows or down not in flows:
        return None
    return {"change_veh_h": flows[down]["veh_h"] - flows[up]["veh_h"],
            "margin_veh_h": round(math.hypot(flows[up]["margin_veh_h"],
                                             flows[down]["margin_veh_h"]))}


def clear(changes: list[dict | None]) -> bool:
    """A junction every day: each change beyond its own margin, all the same way."""
    return (all(c is not None and abs(c["change_veh_h"]) > c["margin_veh_h"] for c in changes)
            and len({c["change_veh_h"] > 0 for c in changes}) == 1)


def steps(chain: list[str], flows: dict[str, dict]) -> list[dict]:
    """Neighbouring detectors that both have a flow, and the change between them.

    A detector with no flow is stepped over and named in `skipped`: the change
    then covers a longer stretch, so it says less about where the junction is.
    """
    known = [d for d in chain if d in flows]
    return [{"from": up, "to": down, "skipped": chain[chain.index(up) + 1:chain.index(down)],
             **change(flows, up, down)} for up, down in zip(known, known[1:])]


def build(start: dt.datetime, end: dt.datetime, ordinary_days: list[dt.date]) -> dict:
    """The incident window, then the same clock times on each ordinary day."""
    days = {}
    for day in [start.date()] + list(ordinary_days):
        shift = dt.datetime.combine(day, start.timetz()) - start
        lines: list[str] = []
        rows = detectors.load_window(start + shift, end + shift, log=lines.append)
        days[day.isoformat()] = {"archive": lines[-1] if lines else "", "flows": hourly_flows(rows)}
    first = start.date().isoformat()
    chains = {}
    for name, chain in CHAINS.items():
        ref = steps(chain, days[first]["flows"])
        for s in ref:        # the same stretch on the other days, where both ends reported
            s["other_days"] = {day: change(d["flows"], s["from"], s["to"])
                               for day, d in days.items() if day != first}
            s["clear_every_day"] = clear([s] + list(s["other_days"].values()))
        chains[name] = {"detectors": chain, "steps": ref}
    return {"start": start.isoformat(), "end": end.isoformat(), "days": days, "chains": chains}


def _places() -> dict[str, str]:
    """Detector id -> where it is, without the direction TD appends."""
    with DETECTORS_CSV.open(encoding="utf-8", newline="") as f:
        return {r["detector_id"]: r["road_en"].rsplit(" - ", 1)[0] for r in csv.DictReader(f)}


def _num(value) -> str:
    return "—" if value is None else f"{value:,}"


def _change_cell(c: dict | None) -> str:
    return "—" if c is None else f"{c['change_veh_h']:+,} ± {c['margin_veh_h']}"


def _md(doc: dict, command: str) -> str:
    days = list(doc["days"])
    first, others = days[0], days[1:]
    places = _places()
    window = f"{doc['start'][11:16]}-{doc['end'][11:16]}"
    out = [f"# Where traffic joins and leaves the corridor, {window}", "",
           f"Generated by `{command}`. Regenerate rather than edit.", "",
           "Hourly flow at each detector, and the change between neighbouring detectors: a rise "
           "means traffic joins in between, a fall means it leaves. Only the net is visible. "
           "The margin is the 95% range from sampling alone; *clear every day* means the change "
           "is larger than its margin on every day, and goes the same way.", ""]
    for name, chain in doc["chains"].items():
        out += [f"## {name}", "",
                "| Detector | Where | " + " | ".join(f"{d} veh/h" for d in days) + " |",
                "|---|---|" + "---|" * len(days)]
        for d in chain["detectors"]:
            cells = [_num(doc["days"][day]["flows"].get(d, {}).get("veh_h")) for day in days]
            out.append(f"| {d} | {places.get(d, '')} | " + " | ".join(cells) + " |")
        out += ["", "| Between | " + " | ".join(f"Change {d}, veh/h" for d in days)
                + " | Clear every day |", "|---|" + "---|" * len(days) + "---|"]
        for s in chain["steps"]:
            gap = f" (past {', '.join(s['skipped'])}, no data)" if s["skipped"] else ""
            out.append(f"| {s['from']} → {s['to']}{gap} | {_change_cell(s)} | "
                       + " | ".join(_change_cell(s["other_days"][d]) for d in others)
                       + f" | {'yes' if s['clear_every_day'] else 'no'} |")
        out.append("")
    out += ["Archive: " + "; ".join(f"{d}: {v['archive']}" for d, v in doc["days"].items()), ""]
    return "\n".join(out)


def write(doc: dict, command: str, out_dir: Path = OUT_DIR) -> tuple[Path, Path]:
    start, end = dt.datetime.fromisoformat(doc["start"]), dt.datetime.fromisoformat(doc["end"])
    stem = out_dir / f"flow-balance_{start:%Y%m%d-%H%M}_{end:%H%M}"
    out_dir.mkdir(parents=True, exist_ok=True)
    md, js = stem.with_suffix(".md"), stem.with_suffix(".json")
    md.write_text(_md(doc, command), encoding="utf-8", newline="\n")
    js.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return md, js
