"""Modelled demand over the closed edge, by exit, for the plan context's od_demand_vehicles.

    python -m src.evaluator.od_demand --scenario sim/scenarios/evaluator_IN-26-03365.json \\
        --start 2026-05-15T09:01:00+08:00 --until 2026-05-15T10:02:00+08:00

Counts vehicles the demand file schedules to enter the network inside the
window on a route that crosses the scenario's closed edge. These are expected
values of the generated demand, not observed counts.
"""
import argparse
import re
import xml.etree.ElementTree as ET
from datetime import datetime

from src.evaluator import scenario as scenarios
from src.twin.common import resolve


def expected_by_exit(routes_path, via_edge, start_s, end_s):
    """{last edge of the route: expected vehicles scheduled in [start_s, end_s)}."""
    totals = {}
    for flow in ET.parse(routes_path).getroot().iter("flow"):
        edges = flow.find("route").get("edges").split()
        if via_edge not in edges:
            continue
        begin, end = float(flow.get("begin")), float(flow.get("end"))
        if flow.get("number") is not None:
            vehicles = float(flow.get("number"))
        else:                                   # period="exp(rate)": Poisson arrivals at `rate` per second
            vehicles = float(re.fullmatch(r"exp\((.+)\)", flow.get("period")).group(1)) * (end - begin)
        overlap = max(0.0, min(end, end_s) - max(begin, start_s))
        totals[edges[-1]] = totals.get(edges[-1], 0.0) + vehicles * overlap / (end - begin)
    return totals


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--until", required=True)
    args = parser.parse_args()
    scenario = scenarios.load(resolve(args.scenario))
    begin = datetime.fromisoformat(scenario["run"]["begin"])
    window = [(datetime.fromisoformat(t) - begin).total_seconds() for t in (args.start, args.until)]
    totals = expected_by_exit(resolve(scenario["inputs"]["routes"]), scenario["closure"]["edge_id"], *window)
    for exit_edge, vehicles in sorted(totals.items()):
        print(f"exit edge {exit_edge}: {vehicles:.1f} vehicles")


if __name__ == "__main__":
    main()
