"""The backup network: the corridor's four chains, built only from data in the repo.

A link runs from one detector to the next. Every number it needs comes from a
file, and nothing is taken from the morning the network is tested on:

  length       the OSM path between the two detectors, from Simulation's map
               audit (results/twin/osm-network-audit.json)
  lanes        what TD's feed reports at the two detectors, the fewer of the
               two; OSM's count where the feed has none (AID01105, AID01220,
               TDSSPWR20002)
  speed        the ordinary mornings' speed at the detector the link ends at, or
               at the one before it where that detector has no data: until
               something goes wrong, traffic moves as on an ordinary morning
  joins, exits the flow change between neighbouring detectors that report,
               averaged over the ordinary mornings, halfway along the link into
               the downstream one (only the net change is visible)
  capacity     LANE_CAPACITY_VEH_H per lane. Queues come from the incident; an
               ordinary morning's slowdowns are already in the speed.

Each chain starts with a short approach (APPROACH_M) ending at its first
detector, so that detector reads its own speed like every other one.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from src.fallback.ctm import Corridor, Link
from src.loaders.corridor import (CHAIN_EASTBOUND, CHAIN_WESTBOUND, CHAIN_WESTERN_EASTBOUND,
                                  CHAIN_WESTERN_WESTBOUND)
from src.loaders.flow_balance import hourly_flows

AUDIT = Path("results/twin/osm-network-audit.json")
LANE_CAPACITY_VEH_H = 1800   # stated assumption: one lane of uninterrupted road
APPROACH_M = 200.0           # the stretch before each chain's first detector
CHAINS = {"main_eastbound": CHAIN_EASTBOUND, "main_westbound": CHAIN_WESTBOUND,
          "western_eastbound": CHAIN_WESTERN_EASTBOUND, "western_westbound": CHAIN_WESTERN_WESTBOUND}


@dataclass
class Ordinary:
    """One detector over the same hour of each ordinary morning."""
    flows: list[float]           # vehicles per hour
    speeds: list[float]          # km/h, averaged over the vehicles counted


def audit(path: Path = AUDIT) -> tuple[dict[tuple[str, str], float], dict[str, int]]:
    """Path lengths between neighbouring detectors, and each detector's lanes."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    lengths = {(p["from"], p["to"]): p["path_m"] for p in doc["paths"]}
    lanes = {d["detector_id"]: d["td_lanes"] or d["sumo_lanes"] for d in doc["detectors"]}
    return lengths, lanes


def hourly_speeds(rows: list[dict]) -> dict[str, float]:
    """Per detector: the average speed of the vehicles counted, over valid lane readings."""
    weighted: dict[str, float] = {}
    vehicles: dict[str, float] = {}
    for r in rows:
        if r["valid"] and r["volume"] and r["speed_kmh"] is not None:
            d = r["detector_id"]
            weighted[d] = weighted.get(d, 0.0) + r["speed_kmh"] * r["volume"]
            vehicles[d] = vehicles.get(d, 0.0) + r["volume"]
    return {d: weighted[d] / vehicles[d] for d in weighted}


def ordinary(rows_per_day: list[list[dict]]) -> dict[str, Ordinary]:
    """Each detector's hourly flow and speed on every ordinary morning (detectors seen on all)."""
    per_day = [(hourly_flows(rows), hourly_speeds(rows)) for rows in rows_per_day]
    seen = set.intersection(*(set(f) & set(s) for f, s in per_day))
    return {d: Ordinary([f[d]["veh_h"] for f, _ in per_day], [s[d] for _, s in per_day]) for d in seen}


def build(typical: dict[str, Ordinary]) -> tuple[dict[str, Corridor], list[dict]]:
    """The four chains, and one row per link saying what went into it."""
    lengths, lanes = audit()
    corridors, table = {}, []
    for name, chain in CHAINS.items():
        def speed(*candidates):
            return next(mean(typical[d].speeds) for d in candidates if d in typical)
        first = chain[0]
        links = [Link(f"approach->{first}", APPROACH_M, lanes[first], speed(first),
                      lanes[first] * LANE_CAPACITY_VEH_H, ends_at=first)]
        for up, down in zip(chain, chain[1:]):
            width = min(lanes[up], lanes[down])
            links.append(Link(f"{up}->{down}", lengths[(up, down)], width, speed(down, up),
                              width * LANE_CAPACITY_VEH_H, ends_at=down))
        _joins_and_exits(chain, links, typical)
        corridors[name] = Corridor(f"approach to {first}", links)
        table += [{"chain": name, "link": l.id, "length_m": round(l.length_m), "lanes": l.lanes,
                   "speed_kmh": round(l.free_speed_kmh, 1), "capacity_veh_h": round(l.capacity_veh_h),
                   "join_veh_h": round(l.join_veh_h), "exit_share": round(l.exit_share, 3)} for l in links]
    return corridors, table


def _joins_and_exits(chain: list[str], links: list[Link], typical: dict[str, Ordinary]) -> None:
    """Net change between neighbouring reporting detectors, on the link into the downstream one.

    links[0] is the approach, so the link ending at chain[i] is links[i].
    """
    reporting = [d for d in chain if d in typical]
    for up, down in zip(reporting, reporting[1:]):
        change = mean(typical[down].flows) - mean(typical[up].flows)
        link = links[chain.index(down)]
        if change > 0:
            link.join_veh_h = change
        elif change < 0:
            link.exit_share = -change / mean(typical[up].flows)
