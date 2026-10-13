"""The checks an incident P0 must pass before any plan benefit is claimed, on every cell's P0 (component E).

    python -m src.evaluator.p0_checks --grid sim/scenarios/rankings/IN-26-03365_lead-draft-20261013-b.json
    -> <results dir of the grid>/p0-checks.json

Proposed by Data on 13 October (docs/incident-p0-verdict-2026-10-14.md) for
Simulation's review. They are reported, not enforced: F and the console still
use validation version 2 (src/validation_targets.py). Each check reads the P0's
result, run report and evaluation.json in its work folder.

  1. validation version 2 (the targets F and the console use)
  2. closure flow after the flyover: hourly-equivalent GEH < 5 at AID01106,
     AID01107 and AID01108 over the full closure (closure_counts.py)
  3. queue onset: the first bin under 30 km/h after 08:30 within 10 minutes of
     the detector's, at AID01101 to AID01103
  4. queue recovery: the first bin from 10:00 that stays at 30 km/h or more to
     10:30 within 10 minutes of the detector's, at AID01101 to AID01103
  5. vehicles still waiting to enter at the end: at most 1% of in-scope vehicles
  6. wrong-lane teleports: none other than at a lane shutting or in a jam
"""
import argparse
import json
from collections import defaultdict

from src import validation_targets as targets
from src.evaluator import closure_counts, scenario as scenarios
from src.generation import load_json, save_json
from src.twin.common import resolve

QUEUE_DETECTORS = ("AID01101", "AID01102", "AID01103")
TOLERANCE_MIN = 10
WAITING_MAX_PCT = 1.0


def minutes(clock):
    return int(clock[:2]) * 60 + int(clock[3:5])


def onset_and_recovery(speeds):
    """(first 'HH:MM' under 30 km/h from 08:30, first from 10:00 that stays at 30 km/h or more until 10:30)."""
    times = sorted(t for t in speeds if t >= "08:30")
    onset = next((t for t in times if speeds[t] < targets.CONGESTED_KMH), None)
    recovery = next((t for t in times if t >= "10:00" and all(
        speeds[u] >= targets.CONGESTED_KMH for u in times if t <= u <= "10:30")), None)
    return onset, recovery


def queue_timing(evaluation):
    """Per detector: measured and simulated onset and recovery, and the differences in minutes."""
    by = defaultdict(dict)
    for row in evaluation["speed_bins"]:
        by[row["detector_id"]][row["time"][11:16]] = row
    out = {}
    for detector in QUEUE_DETECTORS:
        measured = onset_and_recovery({t: r["observed_kmh"] for t, r in by[detector].items()})
        modelled = onset_and_recovery({t: r["simulated_kmh"] for t, r in by[detector].items()})
        out[detector] = {"measured": measured, "modelled": modelled, "minutes_late": [
            minutes(s) - minutes(m) if s and m else None for s, m in zip(modelled, measured)]}
    return out


def check_p0(result, report, evaluation):
    """Every check's value and whether it passes."""
    flows = closure_counts.cell_counts(evaluation)
    timing = queue_timing(evaluation)
    health, detail = report["run_health"], report["measurement_detail"]
    waiting_pct = 100 * health["vehicles_waiting_to_enter_at_end"] / detail["vehicles_in_scope"]
    def within(i):
        late = [timing[d]["minutes_late"][i] for d in QUEUE_DETECTORS]
        return all(x is not None and abs(x) <= TOLERANCE_MIN for x in late)
    return {
        "validation_version_2": {"passes": targets.met(result["validation"]), "value": result["validation"]},
        "closure_flow_after_flyover": {"passes": all(f["geh_hourly_equivalent"] < 5 for f in flows.values()),
                                       "value": flows},
        "queue_onset": {"passes": within(0), "value": {d: t["minutes_late"][0] for d, t in timing.items()}},
        "queue_recovery": {"passes": within(1), "value": {d: t["minutes_late"][1] for d, t in timing.items()}},
        "waiting_to_enter_at_end": {"passes": waiting_pct <= WAITING_MAX_PCT, "value": round(waiting_pct, 2),
                                    "entry_wait_share_of_delay_pct": round(
                                        100 * detail["delay_hours_waiting_to_enter"] / result["metrics"][
                                            "total_vehicle_hours_delay"], 1)},
        "wrong_lane_teleports": {"passes": not report["wrong_lane_teleports"]["other"],
                                 "value": report["wrong_lane_teleports"],
                                 "jam_teleports": health["teleports"]["jam"]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--grid", required=True)
    args = parser.parse_args()
    grid = load_json(resolve(args.grid))
    cells, out_dir = [], None
    for cell in grid["cells"]:
        scenario = scenarios.load(resolve(cell["scenario"]))
        run_id = scenarios.run_id(scenario, "P0", cell["compliance"], cell["clearance_min"], grid["plan_set"])
        out_dir = resolve(cell["results_dir"])
        checks = check_p0(load_json(out_dir / "runs" / f"{run_id}.json"),
                          load_json(out_dir / "evaluator" / f"{run_id}.report.json"),
                          load_json(resolve(closure_counts.WORK) / run_id / "evaluation.json"))
        cells.append({"name": cell["name"], "run_id": run_id, "checks": checks})
    names = list(cells[0]["checks"])
    summary = {name: sum(c["checks"][name]["passes"] for c in cells) for name in names}
    for name in names:
        print(f"{name:28} passes in {summary[name]:2d} of {len(cells)} baselines")
    save_json(out_dir / "p0-checks.json", {"grid": args.grid, "proposed_by": "Data, 13 October 2026",
                                          "enforced": False, "passes_per_check": summary, "cells": cells})
    print(f"-> {(out_dir / 'p0-checks.json').relative_to(resolve('.'))}")


if __name__ == "__main__":
    main()
