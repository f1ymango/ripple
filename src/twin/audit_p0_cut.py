"""Audit the observed flyover cut against generated routes and real OSM connections.

This reports a structural mismatch; it does not fit incident-window demand or
choose a driver diversion fraction.
"""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import sumolib


FLYOVER = "44419212"
FORK = "1198059120"
SURFACE = "1198059138"
DOWNSTREAM = "1198101443"
DETECTORS = ("AID01103", "AID01104", "AID01106", "AID01107")
WINDOW = ("09:45", "10:00")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def eligible_counts(evaluation, detector):
    return [row for row in evaluation["count_bins"]
            if row["detector_id"] == detector and WINDOW[0] <= row["time"][11:16] < WINDOW[1]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("network", "routes", "build", "evaluation", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    net = sumolib.net.readNet(str(args.network))
    path, length = net.getShortestPath(net.getEdge(SURFACE), net.getEdge(DOWNSTREAM),
                                       vClass="passenger")
    if not path or FLYOVER in {edge.getID() for edge in path}:
        raise ValueError("No passenger-car surface path around the flyover")
    lateral_entries = []
    for previous, current in zip(path, path[1:]):
        for incoming in current.getFromNode().getIncoming():
            if (incoming.getID() != previous.getID() and incoming.allows("passenger")
                    and current in incoming.getOutgoing()):
                lateral_entries.append({"onto": current.getID(), "from": incoming.getID(),
                                        "road_name": incoming.getName()})
    roots = ET.parse(args.routes).getroot()
    route_groups = {"flyover": [], "surface_ends_at_fork": [],
                    "surface_reaches_downstream": []}
    for flow in roots.findall("flow"):
        route = flow.find("route")
        edges = route.get("edges").split() if route is not None else []
        if FORK not in edges:
            continue
        if FLYOVER in edges:
            route_groups["flyover"].append(flow.get("id"))
        if SURFACE in edges:
            key = ("surface_reaches_downstream" if DOWNSTREAM in edges
                   else "surface_ends_at_fork")
            route_groups[key].append(flow.get("id"))
    build = json.loads(args.build.read_text(encoding="utf-8"))
    plan = build["plan"]["main_eastbound"]
    evaluation = json.loads(args.evaluation.read_text(encoding="utf-8"))
    readings = {}
    for detector in DETECTORS:
        rows = eligible_counts(evaluation, detector)
        readings[detector] = {"bins": len(rows),
                              "observed": sum(row["observed"] for row in rows),
                              "simulated": sum(row["simulated"] for row in rows)}
    joins = [origin for origin in plan["origins"]
             if origin.get("pair") == "AID01104->AID01106"
             and origin["start"] > plan["edges"].index(FLYOVER)]
    report = {
        "purpose": "Locate P0's route-topology mismatch without using incident readings to set demand",
        "observation_window_hkt": ["2026-05-15T09:45:00+08:00",
                                   "2026-05-15T10:00:00+08:00"],
        "eligible_detector_counts": readings,
        "fork": FORK,
        "flyover": FLYOVER,
        "surface_exit": SURFACE,
        "downstream_tunnel_entrance": DOWNSTREAM,
        "passenger_surface_path": [edge.getID() for edge in path],
        "passenger_surface_path_length_m": length,
        "other_passenger_entries_to_surface_path": lateral_entries,
        "generated_fork_flow_groups": {
            name: {"count": len(ids), "flow_ids": ids} for name, ids in route_groups.items()},
        "ordinary_day_downstream_joins": joins,
        "ordinary_day_downstream_join_veh_h": sum(item["veh_h"] for item in joins),
        "limitations": [
            "A drivable path does not establish how many incident drivers used it.",
            "The route file has stochastic flows; counts here are flow definitions, not vehicles.",
            "AID01106 physical cross-section remains provisional in the source audit.",
            "The observed downstream count must not also be used as a validation target if it sets diversion demand.",
        ],
        "source_sha256": {name: digest(getattr(args, name)) for name in
                          ("network", "routes", "build", "evaluation")},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
