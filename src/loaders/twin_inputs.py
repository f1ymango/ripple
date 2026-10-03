"""What a replay needs from the detectors to run one morning: demand and speeds (Data -> twin).

The SUMO twin and the backup network are both driven by the same three things,
and only the first comes from the morning being replayed:

  entries   traffic arriving at each chain's first detector, in 15-minute
            steps: the replay morning's own counts until `own_until`, then the
            ordinary mornings' average (after an incident a first detector may
            be counting a queue, not the traffic trying to get in);
  changes   between two neighbouring reporting detectors, the ordinary
            mornings' average change in flow over the scored hour: traffic
            joining (vehicles per hour) or leaving (a share of what passes the
            upstream detector). Only the net change is visible;
  speeds    per detector and quarter of an hour, the ordinary mornings' speed:
            the vehicle-weighted harmonic mean of their 5-minute speeds, which
            is the speed that gives the right travel time when some mornings
            crawl and others flow.

So every detector inside a chain is predicted without that morning's own
readings, and the first detectors are the only ones that set demand.

`--refresh` is a different claim and is labelled as one in the file: each
quarter-hour's speed is scaled by how the replay morning itself ran in the
quarter before (its own speed over the ordinary speed in that quarter), up to
`refresh_until`. That is what a live twin would do, 15 minutes ahead; it is not
a calibration from ordinary mornings, because every detector's own earlier
readings go in.

    python -m src.loaders.fetch twin-inputs --day 2026-05-15 \\
        --ordinary-day 2026-05-08 2026-04-24 2026-04-17 2026-04-10
    -> sim/scenarios/twin-inputs_20260515.json

The times default to the 15 May demo (readings 07:15-10:35, flow changes over
07:55-08:55, own counts until 09:00, refresh until 08:45). Another incident or
another time of day gives its own with --start, --end, --scored-from,
--scored-to, --own-until and --refresh-until.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from statistics import mean

from src.loaders import detectors
from src.loaders.common import HK
from src.loaders.corridor import (CHAIN_EASTBOUND, CHAIN_WESTBOUND, CHAIN_WESTERN_EASTBOUND,
                                  CHAIN_WESTERN_WESTBOUND)
from src.loaders.flow_balance import hourly_flows

OUT_DIR = Path("sim/scenarios")
CHAINS = {"main_eastbound": CHAIN_EASTBOUND, "main_westbound": CHAIN_WESTBOUND,
          "western_eastbound": CHAIN_WESTERN_EASTBOUND, "western_westbound": CHAIN_WESTERN_WESTBOUND}
WINDOW = (dt.time(7, 15), dt.time(10, 35))       # the readings loaded for every day
SCORED = (dt.time(7, 55), dt.time(8, 55))        # the hour the flow changes are taken over
OWN_UNTIL = dt.time(9, 0)                        # entries switch to the ordinary days here
REFRESH_UNTIL = dt.time(8, 45)                   # the last quarter refreshed: nothing from 08:54 on goes in
STEP_MIN = 15
REFRESH_CLIP = (0.4, 2.5)


def _at(day: dt.date, clock: dt.time) -> dt.datetime:
    return dt.datetime.combine(day, clock, HK)


def _within(rows: list[dict], start: dt.datetime, end: dt.datetime) -> list[dict]:
    return [r for r in rows if start <= r["timestamp"] < end]


def speed_profiles(rows_per_day: list[list[dict]], minutes: int = STEP_MIN) -> dict[str, dict[str, float]]:
    """{detector: {"HH:MM": km/h}} per `minutes` of clock time, pooled over the mornings given.

    The harmonic mean of the 5-minute speeds, weighted by the vehicles seen in
    each: distance over time, so a quarter-hour that was queued on one morning
    and free on another gets the speed a vehicle would average across both.
    """
    seen: dict[str, dict[str, list[float]]] = {}
    for rows in rows_per_day:
        for b in detectors.bin_window(rows, 5):
            if b["speed_kmh"] == "" or float(b["speed_kmh"]) <= 0:
                continue
            t = dt.datetime.fromisoformat(b["bin_start"])
            key = f"{t.hour:02d}:{t.minute - t.minute % minutes:02d}"
            acc = seen.setdefault(b["detector_id"], {}).setdefault(key, [0.0, 0.0])
            weight = b["volume_observed"] or 1
            acc[0] += weight
            acc[1] += weight / float(b["speed_kmh"])
    return {d: {k: round(w / inv, 2) for k, (w, inv) in sorted(slots.items())} for d, slots in seen.items()}


def refreshed(profiles: dict, own: dict, until: str, clip: tuple[float, float] = REFRESH_CLIP) -> tuple[dict, dict]:
    """The profiles with each slot scaled by the replay morning's own previous slot; and the ratios used.

    ratio = own speed in the slot before / ordinary speed in that slot, kept
    within `clip`. Slots after `until`, and slots with no own reading before
    them, keep the ordinary speed.
    """
    out, ratios = {}, {}
    for det, prof in profiles.items():
        keys = sorted(prof)
        out[det], ratios[det] = dict(prof), {}
        for prev, key in zip(keys, keys[1:]):
            if key > until or prev not in own.get(det, {}):
                continue
            r = min(max(own[det][prev] / prof[prev], clip[0]), clip[1])
            out[det][key], ratios[det][key] = round(prof[key] * r, 2), round(r, 3)
    return out, ratios


def flow_changes(rows_per_day: list[list[dict]]) -> tuple[list[dict], dict[str, float]]:
    """Per chain, the change between neighbouring detectors that report on every morning given.

    Returns the changes and each such detector's average flow (vehicles per hour).
    """
    per_day = [hourly_flows(rows) for rows in rows_per_day]
    flow = {d: mean(f[d]["veh_h"] for f in per_day) for d in set.intersection(*(set(f) for f in per_day))}
    pairs = []
    for name, chain in CHAINS.items():
        reporting = [d for d in chain if d in flow]
        for up, down in zip(reporting, reporting[1:]):
            diff = flow[down] - flow[up]
            pairs.append({"chain": name, "up": up, "down": down,
                          "up_veh_h": round(flow[up]), "down_veh_h": round(flow[down]),
                          "join_veh_h": round(diff, 1) if diff > 0 else 0.0,
                          "exit_share": round(-diff / flow[up], 4) if diff < 0 else 0.0})
    return pairs, {d: round(v) for d, v in sorted(flow.items())}


def entry_demand(entry: str, rows: dict[dt.date, list[dict]], day: dt.date, start: dt.datetime,
                 end: dt.datetime, own_until: dt.time = OWN_UNTIL) -> tuple[list[float], list[str]]:
    """Vehicles per hour arriving at `entry` for each 15 minutes from `start`, and where each came from."""
    def flows(d: dt.date) -> list[float | None]:
        s, e = (dt.datetime.combine(d, x.timetz()) for x in (start, end))
        grid = detectors.bin_window([r for r in _within(rows[d], s, e) if r["detector_id"] == entry],
                                    STEP_MIN, start=s, end=e, detector_ids=[entry])
        return [None if b["flow_veh_h"] == "" else float(b["flow_veh_h"]) for b in grid]
    own = flows(day)
    others = [flows(d) for d in rows if d != day]
    switch = (_at(day, own_until) - start).total_seconds() // (STEP_MIN * 60)
    out: list[float | None] = []
    source = []
    for i, value in enumerate(own):
        typical = [o[i] for o in others if o[i] is not None]
        if i < switch and value is not None:
            out.append(value)
            source.append("replay morning")
        elif typical:
            out.append(mean(typical))
            source.append("ordinary mornings")
        else:
            out.append(None)
            source.append("gap: nearest step")
    if all(value is None for value in out):
        raise ValueError(f"{entry}: no usable count between {start:%H:%M} and {end:%H:%M} on any of the days given")
    for i, value in enumerate(out):                       # a gap takes its nearest neighbour
        if value is None:
            out[i] = out[min((j for j, v in enumerate(out) if v is not None), key=lambda j: abs(j - i))]
    return [round(v, 1) for v in out], source


def build(day: dt.date, ordinary_days: list[dt.date], refresh: bool = False, load=None,
          window: tuple[dt.time, dt.time] = WINDOW, scored: tuple[dt.time, dt.time] = SCORED,
          own_until: dt.time = OWN_UNTIL, refresh_until: dt.time = REFRESH_UNTIL) -> dict:
    """The hand-over for one day. `load(start, end)` returns lane readings (the archive cache by default).

    `window` must start on a quarter of an hour: the demand steps and the speed
    slots are counted from it.
    """
    if window[0].minute % STEP_MIN or window[0].second:
        raise ValueError(f"the window must start on a quarter of an hour, got {window[0]}")
    if not window[0] <= scored[0] < scored[1] <= window[1]:
        raise ValueError("the scored hour must lie inside the window")
    load = load or (lambda s, e: detectors.load_window(s, e, log=lambda line: None))
    rows = {d: load(_at(d, window[0]), _at(d, window[1])) for d in [day] + list(ordinary_days)}
    ordinary = [rows[d] for d in ordinary_days]
    pairs, flow = flow_changes([_within(rows[d], _at(d, scored[0]), _at(d, scored[1])) for d in ordinary_days])
    profiles, ratios = speed_profiles(ordinary), None
    if refresh:
        profiles, ratios = refreshed(profiles, speed_profiles([rows[day]]), refresh_until.isoformat("minutes"))
    entries = {}
    for name, chain in CHAINS.items():
        steps, source = entry_demand(chain[0], rows, day, _at(day, window[0]), _at(day, window[1]), own_until)
        entries[name] = {"detector": chain[0], "veh_h": steps, "from": source}
    return {"day": day.isoformat(), "ordinary_days": [d.isoformat() for d in ordinary_days],
            "demand_steps_from": _at(day, window[0]).isoformat(), "demand_step_s": STEP_MIN * 60,
            "flow_changes_over": [t.isoformat("minutes") for t in scored],
            "entries": entries, "pairs": pairs, "ordinary_flow_veh_h": flow,
            "speed_profile_minutes": STEP_MIN, "speed_profile_kmh": profiles,
            "speeds": ("ordinary mornings, refreshed from the replay morning's own previous quarter-hour "
                       f"until {refresh_until.isoformat('minutes')}" if refresh else "ordinary mornings only"),
            "speed_refresh_ratios": ratios,
            "demand_setting_detectors": [chain[0] for chain in CHAINS.values()]}


def write(doc: dict, path: Path | None = None) -> Path:
    path = path or OUT_DIR / (f"twin-inputs_{doc['day'].replace('-', '')}"
                              f"{'_refreshed' if doc['speed_refresh_ratios'] is not None else ''}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    return path
