"""Replay a morning on the backup network and score it the way the twin is scored.

    python -m src.fallback.run --day 2026-05-15 --ordinary-day 2026-05-08 2026-04-24
    -> results/fallback/replay_20260515.md and .json

What goes in:
  * the network (network.py), built from the ordinary mornings only;
  * traffic arriving at each chain's first detector in 15-minute steps: the
    replay morning's own counts until 09:00, then the ordinary mornings'
    average, because once the queue reaches a first detector it counts the
    queue, not the traffic trying to get in;
  * the incident as the detectors saw it (Data's choice from the lane evidence,
    for the README's open decision on unspecified lanes): the slow lane blocked
    from 08:54, letting through only what the fast lane carried past it; all
    lanes from 09:00; re-opened 10:02, TD's re-opening message.

What comes out is scored as src/twin/evaluate.py scores SUMO: GEH < 5 on every
5-minute count the loader marks usable (40% coverage, 90% of lanes valid), and
the mean absolute percentage error of speed, over the pre-incident hour
07:55-08:55. Each chain's first detector is reported apart: the model is fed
its counts, so they cannot count as a match. Next to the speed error stands
the ordinary mornings' own error: predict every 5-minute speed with the
ordinary mornings' average at that detector. A network built from those
mornings cannot beat it without knowing something about the day they do not.

The incident is then followed detector by detector up to the blockage: when
the queue reached each one, when it cleared, and the flow while all lanes
were closed. Nobody turns off in this network yet (diversion routes come in
week 3), so every vehicle waits for the road to re-open.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
from statistics import mean

from src.fallback import network
from src.fallback.ctm import Closure, Result
from src.loaders import detectors
from src.loaders.common import HK

OUT_DIR = Path("results/fallback")
LANE_EVIDENCE = Path("results/data/lane-evidence_AID01104_20260515-0840_0920.json")
WARM_UP_MIN = 30
SCORED = (dt.time(7, 55), dt.time(8, 55))          # the pre-incident hour, as for SUMO
REPLAY_END = dt.time(10, 35)
INCIDENT_LINK, INCIDENT_AT = "AID01103->AID01104", 0.9   # just before AID01104: its loops saw an empty road
SLOW_LANE, ALL_LANES, REOPENED = dt.time(8, 54), dt.time(9, 0), dt.time(10, 2)
DEMAND_SWITCH = dt.time(9, 0)                      # from here the first detectors may sit in the queue
SLOW_KMH = 30                                      # below it, a detector is in the queue


def _at(day: dt.date, t: dt.time) -> dt.datetime:
    return dt.datetime.combine(day, t, HK)


def _within(rows: list[dict], start: dt.datetime, end: dt.datetime, ids=None) -> list[dict]:
    return [r for r in rows if start <= r["timestamp"] < end and (ids is None or r["detector_id"] in ids)]


def slow_lane_capacity(path: Path = LANE_EVIDENCE) -> float:
    """What got past the blocked slow lane: fast-lane vehicles per hour while the slow lane was empty."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    readings = [r for r in doc["incident"]["readings"] if "Slow Lane" in r["empty_while_moving"]
                and SLOW_LANE.isoformat() <= r["time"][11:19] < ALL_LANES.isoformat()]
    vehicles = sum(r["lanes"]["Fast Lane"]["volume"] for r in readings)
    return vehicles / (30 * len(readings)) * 3600          # each reading covers 30 seconds


def entry_demand(entry: str, rows: dict[dt.date, list[dict]], day: dt.date, start: dt.datetime,
                 end: dt.datetime) -> tuple[list[float], list[str]]:
    """Vehicles per hour arriving at `entry` for each 15 minutes from `start`, and where each came from."""
    def flows(d: dt.date) -> list[float | None]:
        s, e = (dt.datetime.combine(d, x.timetz()) for x in (start, end))
        grid = detectors.bin_window(_within(rows[d], s, e, {entry}), 15, start=s, end=e,
                                    detector_ids=[entry])
        return [None if b["flow_veh_h"] == "" else float(b["flow_veh_h"]) for b in grid]
    own = flows(day)
    others = [flows(d) for d in rows if d != day]
    switch = (_at(day, DEMAND_SWITCH) - start).total_seconds() // 900
    out: list[float | None] = []
    source = []
    for i, value in enumerate(own):
        typical = [o[i] for o in others if o[i] is not None]
        if i < switch and value is not None:
            out.append(value); source.append("replay morning")
        elif typical:
            out.append(mean(typical)); source.append("ordinary mornings")
        else:
            out.append(None); source.append("gap: nearest step")
    for i, value in enumerate(out):                       # a gap takes its nearest neighbour
        if value is None:
            out[i] = out[min((j for j, v in enumerate(out) if v is not None), key=lambda j: abs(j - i))]
    return out, source


def observed(rows: list[dict], day: dt.date) -> dict[tuple[str, str], dict]:
    """The detectors' 5-minute counts (usable ones only) and speeds from 07:55 to the end of the replay."""
    s, e = _at(day, SCORED[0]), _at(day, REPLAY_END)
    series = detectors.calibration_series(detectors.bin_window(_within(rows, s, e), 5, start=s, end=e))
    return {(b["detector_id"], b["bin_start"][11:16]): b for b in series}


def _pct(errors: list[float]) -> float | None:
    return round(100 * mean(errors), 1) if errors else None


def geh(m: float, c: float) -> float:
    return math.sqrt(2 * (m - c) ** 2 / (m + c)) if m + c > 0 else 0.0


def score(results: dict[str, Result], obs: dict, entries: set[str], start: dt.datetime,
          typical: dict[str, network.Ordinary]) -> dict:
    """GEH and speed error over the scored hour, per detector and overall.

    `ordinary` errors put the ordinary mornings' average speed at each detector
    against the same observed bins as the model.
    """
    first = int((_at(start.date(), SCORED[0]) - start).total_seconds() // 300)
    last = int((_at(start.date(), SCORED[1]) - start).total_seconds() // 300)
    per, errors, ordinary = {}, {}, {}
    for r in results.values():
        for d, counts in r.counts.items():
            gehs, errs, ordinary_errs, obs_total, model_total = [], [], [], 0.0, 0.0
            for b in range(first, last):
                o = obs.get((d, (start + dt.timedelta(minutes=5 * b)).strftime("%H:%M")))
                if o is None:
                    continue
                if o["count_bin"] != "":
                    gehs.append(geh(counts[b], float(o["count_bin"])))
                    obs_total += float(o["count_bin"])
                    model_total += counts[b]
                if o["speed_kmh"] != "" and float(o["speed_kmh"]) > 0 and r.speeds[d][b] is not None:
                    seen = float(o["speed_kmh"])
                    errs.append(abs(r.speeds[d][b] - seen) / seen)
                    if d in typical:
                        ordinary_errs.append(abs(mean(typical[d].speeds) - seen) / seen)
            if gehs or errs:
                errors[d], ordinary[d] = errs, ordinary_errs
                per[d] = {"first_of_chain": d in entries, "count_bins": len(gehs),
                          "geh_under_5": sum(g < 5 for g in gehs), "observed_total": round(obs_total),
                          "model_total": round(model_total), "speed_bins": len(errs),
                          "speed_mape_pct": _pct(errs), "ordinary_speed_error_pct": _pct(ordinary_errs)}

    def overall(ids):
        bins = sum(per[d]["count_bins"] for d in ids)
        errs = [e for d in ids for e in errors[d]]
        return {"geh_under_5_pct": round(100 * sum(per[d]["geh_under_5"] for d in ids) / bins, 1) if bins else None,
                "count_bins": bins, "speed_mape_pct": _pct(errs), "speed_bins": len(errs),
                "ordinary_speed_mape_pct": _pct([e for d in ids for e in ordinary[d]])}
    return {"inside_the_chains": overall([d for d in per if not per[d]["first_of_chain"]]),
            "all_detectors": overall(list(per)), "per_detector": per}


def incident_upstream(result: Result, obs: dict, chain: list[str], start: dt.datetime) -> list[dict]:
    """From the chain's first detector to the one past the blockage, observed against modelled.

    When the queue reached each detector (the first 5-minute bin from the
    incident on below SLOW_KMH), when it cleared (the first bin from the
    re-opening on back at or above it), and the mean flow while all lanes were
    closed, over the bins whose counts are usable.
    """
    def bin_of(clock: dt.time) -> int:
        return int((_at(start.date(), clock) - start).total_seconds() // 300)

    def clock(b: int) -> str:
        return (start + dt.timedelta(minutes=5 * b)).strftime("%H:%M")
    bins = len(result.speeds[chain[0]])
    onset, reopened = bin_of(SLOW_LANE), bin_of(REOPENED)
    closed = range(bin_of(ALL_LANES), reopened)

    def queue(speeds: list[float | None]) -> tuple[str | None, str | None]:
        slow = next((b for b in range(onset, bins) if speeds[b] is not None and speeds[b] < SLOW_KMH), None)
        if slow is None:
            return None, None
        clear = next((b for b in range(max(slow, reopened), bins)
                      if speeds[b] is not None and speeds[b] >= SLOW_KMH), None)
        return clock(slow), None if clear is None else clock(clear)

    out = []
    for d in chain[:chain.index(INCIDENT_LINK.split("->")[1]) + 1]:
        seen = [obs.get((d, clock(b))) for b in range(bins)]
        speeds = [float(o["speed_kmh"]) if o is not None and o["speed_kmh"] != "" else None for o in seen]
        usable = [b for b in closed if seen[b] is not None and seen[b]["flow_veh_h"] != ""]
        flow = [float(seen[b]["flow_veh_h"]) for b in usable]
        model_flow = [result.counts[d][b] * 3600 / result.bin_s for b in usable]
        (obs_slow, obs_clear), (model_slow, model_clear) = queue(speeds), queue(result.speeds[d])
        out.append({"detector": d,
                    "queue_reached": {"observed": obs_slow, "model": model_slow},
                    "cleared": {"observed": obs_clear, "model": model_clear},
                    "flow_while_closed_veh_h": {"observed": round(mean(flow)) if flow else None,
                                                "model": round(mean(model_flow)) if model_flow else None,
                                                "bins": len(usable)}})
    return out


def replay(day: dt.date, ordinary_days: list[dt.date]) -> dict:
    start = _at(day, SCORED[0]) - dt.timedelta(minutes=WARM_UP_MIN)
    end = _at(day, REPLAY_END)
    demand_start = start.replace(minute=start.minute - start.minute % 15)
    rows = {d: detectors.load_window(dt.datetime.combine(d, demand_start.timetz()), _at(d, REPLAY_END),
                                     log=lambda line: None) for d in [day] + list(ordinary_days)}
    typical = network.ordinary([_within(rows[d], _at(d, SCORED[0]), _at(d, SCORED[1]))
                                for d in ordinary_days])
    corridors, links = network.build(typical)
    slow_cap = slow_lane_capacity()
    t = lambda clock: (_at(day, clock) - start).total_seconds()
    closures = [Closure(INCIDENT_LINK, t(SLOW_LANE), t(ALL_LANES), slow_cap, INCIDENT_AT),
                Closure(INCIDENT_LINK, t(ALL_LANES), t(REOPENED), 0.0, INCIDENT_AT)]
    obs = observed(rows[day], day)
    results, demand_notes = {}, {}
    offset = (start - demand_start).total_seconds()
    for name, corridor in corridors.items():
        entry = network.CHAINS[name][0]
        steps, source = entry_demand(entry, rows, day, demand_start, end)
        demand = lambda s, steps=steps: steps[min(int((s + offset) // 900), len(steps) - 1)]
        results[name] = corridor.run(demand, (end - start).total_seconds(),
                                     closures=closures if name == "main_eastbound" else [])
        demand_notes[entry] = {"veh_h": [round(v) for v in steps], "from": source}
    entries = {chain[0] for chain in network.CHAINS.values()}
    return {
        "day": day.isoformat(), "ordinary_days": [d.isoformat() for d in ordinary_days],
        "model_start": start.isoformat(), "scored": [SCORED[0].isoformat("minutes"), SCORED[1].isoformat("minutes")],
        "incident": {"link": INCIDENT_LINK, "at": INCIDENT_AT,
                     "slow_lane_from": SLOW_LANE.isoformat("minutes"), "slow_lane_capacity_veh_h": round(slow_cap),
                     "all_lanes_from": ALL_LANES.isoformat("minutes"), "reopened": REOPENED.isoformat("minutes")},
        "links": links, "entry_demand_15min_from": demand_start.isoformat(), "entry_demand": demand_notes,
        "score": score(results, obs, entries, start, typical),
        "incident_eastbound": incident_upstream(results["main_eastbound"], obs, network.CHAINS["main_eastbound"],
                                                start),
        "runs": {name: {"entered": round(r.entered), "left": round(r.left),
                        "waiting_at_end": round(r.waiting_at_end), "in_corridor_at_end": round(r.in_corridor_at_end),
                        "unaccounted": round(r.entered - r.left - r.waiting_at_end - r.in_corridor_at_end, 6),
                        "delay_vehicle_hours": round(r.delay_vehicle_hours, 1),
                        "longest_queue_m": round(r.longest_queue_m),
                        "max_queue_m": {k: round(v) for k, v in r.max_queue_m.items() if v > 0},
                        "counts_5min": {d: [round(c, 1) for c in v] for d, v in r.counts.items()},
                        "speeds_5min": {d: [None if s is None else round(s, 1) for s in v]
                                        for d, v in r.speeds.items()}}
                 for name, r in results.items()},
    }


def _share(x: float) -> str:
    return f"{x:.0%}" if x else ""


def _md(doc: dict, command: str) -> str:
    s = doc["score"]
    demand = doc["entry_demand"]
    lines = [f"# Backup network replay, {doc['day']}", "",
             f"Generated by `{command}`. Regenerate rather than edit.", "",
             f"Built from the ordinary mornings {', '.join(doc['ordinary_days'])}. Traffic arrives at each "
             f"chain's first detector ({', '.join(demand)}) in 15-minute steps: the replay morning's own "
             f"counts until {DEMAND_SWITCH.isoformat('minutes')}, then the ordinary mornings' average. "
             f"Scored over {doc['scored'][0]}-{doc['scored'][1]} as SUMO is scored.", "",
             "| Scored on | GEH < 5 | Count bins | Speed error (MAPE) | Ordinary mornings' own error | Speed bins |",
             "|---|---|---|---|---|---|"]
    for key, label in (("inside_the_chains", "Detectors inside the chains"), ("all_detectors", "All detectors")):
        x = s[key]
        lines.append(f"| {label} | {x['geh_under_5_pct']}% | {x['count_bins']} | {x['speed_mape_pct']}% "
                     f"| {x['ordinary_speed_mape_pct']}% | {x['speed_bins']} |")
    lines += ["", "Targets: GEH < 5 for at least 85% of counts; speed error about 15% or less on 5-minute bins "
              "(docs/03-architecture.md section 4). The ordinary mornings' own error is what predicting every "
              "5-minute speed with the ordinary mornings' average at that detector scores; a network built from "
              "those mornings cannot beat it without knowing something about the day that they do not. "
              "Each chain's first detector is fed its own counts, so only the detectors inside the chains test "
              "the network.", "", "## Per detector", "",
              "| Detector | First of its chain | Count bins | GEH < 5 | Observed | Model | Speed error "
              "| Ordinary mornings' own error |",
              "|---|---|---|---|---|---|---|---|"]
    for d, r in s["per_detector"].items():
        err = "—" if r["speed_mape_pct"] is None else f"{r['speed_mape_pct']}%"
        own = "—" if r["ordinary_speed_error_pct"] is None else f"{r['ordinary_speed_error_pct']}%"
        lines.append(f"| {d} | {'yes' if r['first_of_chain'] else ''} | {r['count_bins']} | {r['geh_under_5']} "
                     f"| {r['observed_total']} | {r['model_total']} | {err} | {own} |")
    inc = doc["incident"]
    lines += ["", "## The incident, eastbound", "",
              f"Slow lane blocked from {inc['slow_lane_from']} (passing {inc['slow_lane_capacity_veh_h']} veh/h, "
              f"what the fast lane carried past it), all lanes from {inc['all_lanes_from']}, re-opened "
              f"{inc['reopened']}, on {inc['link']}, {inc['at']:.0%} of the way along.", "",
              "| Detector | Queue reached it: observed | Model | Cleared: observed | Model "
              "| Flow while all lanes closed, veh/h: observed | Model |",
              "|---|---|---|---|---|---|---|"]
    for x in doc["incident_eastbound"]:
        q, c, f = x["queue_reached"], x["cleared"], x["flow_while_closed_veh_h"]
        lines.append(f"| {x['detector']} | {q['observed'] or '—'} | {q['model'] or '—'} | {c['observed'] or '—'} "
                     f"| {c['model'] or '—'} | {_or_dash(f['observed'])} | {_or_dash(f['model'])} |")
    lines += ["", f"Queue reached it: the first 5-minute bin below {SLOW_KMH} km/h, from the bin holding "
              f"{inc['slow_lane_from']} on. Cleared: the first bin back at {SLOW_KMH} km/h or more, from the bin "
              f"holding {inc['reopened']} on; '—' if not by the end of the replay. Flow while closed: "
              f"{inc['all_lanes_from']}-{inc['reopened']}, over the bins whose counts are usable.", "",
              "Nobody turns off in this network yet: every vehicle that reaches the queue waits for the road to "
              "re-open. Where the observed flow while closed is higher than the model's, traffic kept moving past "
              "that detector and left the corridor before the blockage. Diversion routes come in week 3; until "
              "then this replay overstates the queue behind the incident and how long it takes to clear."]
    lines += ["", "## Runs", "", "| Chain | Entered | Left | Waiting to enter at the end | Delay (vehicle-hours) "
              "| Longest queue, m |", "|---|---|---|---|---|---|"]
    for name, r in doc["runs"].items():
        lines.append(f"| {name} | {r['entered']} | {r['left']} | {r['waiting_at_end']} "
                     f"| {r['delay_vehicle_hours']} | {r['longest_queue_m'] or '—'} |")
    lines += ["", "Waiting to enter: queued beyond the chain's start, where the network ends. Delay: time spent "
              "beyond driving the chain at the links' speeds, waiting to enter included."]
    lines += ["", "## Links", "", "| Link | Length m | Lanes | Speed km/h | Capacity veh/h | Joins veh/h | Leaves |",
              "|---|---|---|---|---|---|---|"]
    lines += [f"| {l['link']} | {l['length_m']} | {l['lanes']} | {l['speed_kmh']} | {l['capacity_veh_h']} "
              f"| {l['join_veh_h'] or ''} | {_share(l['exit_share'])} |" for l in doc["links"]]
    return "\n".join(lines) + "\n"


def _or_dash(x) -> str:
    return "—" if x is None else str(x)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--day", required=True, help="YYYY-MM-DD, the morning to replay")
    ap.add_argument("--ordinary-day", nargs="+", required=True, dest="ordinary_day",
                    help="YYYY-MM-DD, the ordinary mornings the network is built from")
    args = ap.parse_args()
    day = dt.date.fromisoformat(args.day)
    doc = replay(day, [dt.date.fromisoformat(d) for d in args.ordinary_day])
    command = f"python -m src.fallback.run --day {args.day} --ordinary-day {' '.join(args.ordinary_day)}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md, js = OUT_DIR / f"replay_{day:%Y%m%d}.md", OUT_DIR / f"replay_{day:%Y%m%d}.json"
    md.write_text(_md(doc, command), encoding="utf-8", newline="\n")
    js.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")
    for key, label in (("inside_the_chains", "inside the chains"), ("all_detectors", "all detectors")):
        x = doc["score"][key]
        print(f"{label + ':':19s} GEH<5 {x['geh_under_5_pct']}% of {x['count_bins']} bins, speed error "
              f"{x['speed_mape_pct']}% (ordinary mornings' own error {x['ordinary_speed_mape_pct']}%)")
    print(f"-> {md}, {js}")


if __name__ == "__main__":
    main()
