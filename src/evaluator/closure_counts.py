"""Traffic reaching the tunnel while the flyover is shut: each cell's P0 against the detectors (component E).

    python -m src.evaluator.closure_counts --grid sim/scenarios/rankings/IN-26-03365_lead-draft-20261013-b.json
    -> <results dir of the grid>/closure-counts.json

GEH < 5 on five-minute bins lets a large shortfall through at these volumes:
62 simulated against 89.5 counted scores 3.3. GEH is meant for hourly flows,
so this sums the counted and simulated vehicles over the bins wholly inside
the full closure, 09:05 to 09:55, and scores the hourly-equivalent flow at the
detectors after the flyover. It reads each P0's evaluation.json in its work
folder (sim/work/evaluator/<run_id>/), which exists wherever the run was made.

Reported, not a validation target: whether it should be one is open
(docs/evaluator-lead-plans-2026-10-13.md, section 5).
"""
import argparse
import json
import math

from src.evaluator import scenario as scenarios
from src.generation import load_json, save_json
from src.twin.common import resolve

DETECTORS = ("AID01106", "AID01107", "AID01108")   # after the flyover, toward the tunnel and Canal Road
WINDOW = ("09:05", "09:55")                         # bin starts wholly inside both lanes shut, 09:00:30 to 10:00
WORK = "sim/work/evaluator"


def geh(modelled, counted):
    return math.sqrt(2 * (modelled - counted) ** 2 / (modelled + counted)) if modelled + counted else 0.0


def cell_counts(evaluation):
    """Per detector: bins, counted and simulated vehicles, their ratio and the hourly-equivalent GEH."""
    out = {}
    for detector in DETECTORS:
        rows = [r for r in evaluation["count_bins"]
                if r["detector_id"] == detector and WINDOW[0] <= r["time"][11:16] <= WINDOW[1]]
        if not rows:
            continue
        counted, simulated = sum(r["observed"] for r in rows), sum(r["simulated"] for r in rows)
        hours = len(rows) * 5 / 60
        out[detector] = {"bins": len(rows), "counted": round(counted), "simulated": round(simulated),
                         "simulated_over_counted": round(simulated / counted, 2),
                         "geh_hourly_equivalent": round(geh(simulated / hours, counted / hours), 1),
                         "five_minute_bins_geh_under_5": sum(r["within_5"] for r in rows)}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--grid", required=True)
    args = parser.parse_args()
    grid = load_json(resolve(args.grid))
    cells, out_dir = [], None
    for cell in grid["cells"]:
        scenario = scenarios.load(resolve(cell["scenario"]))
        run_id = scenarios.run_id(scenario, "P0", cell["compliance"], cell["clearance_min"], grid["plan_set"])
        evaluation = load_json(resolve(WORK) / run_id / "evaluation.json")
        cells.append({"name": cell["name"], "run_id": run_id, "detectors": cell_counts(evaluation)})
        out_dir = resolve(cell["results_dir"])
    worst = {d: [c["detectors"][d]["simulated_over_counted"] for c in cells if d in c["detectors"]] for d in DETECTORS}
    for d, ratios in worst.items():
        print(f"{d}: simulated / counted {min(ratios)} to {max(ratios)} over {len(ratios)} baselines")
    save_json(out_dir / "closure-counts.json", {
        "grid": args.grid, "window_bin_starts": list(WINDOW), "detectors": list(DETECTORS),
        "why": __doc__.split("\n\n")[1].replace("\n", " "), "cells": cells})
    print(f"-> {(out_dir / 'closure-counts.json').relative_to(resolve('.'))}")


if __name__ == "__main__":
    main()
