"""Rank a plan set's plans over a grid of seeds and assumptions, calling a tie where the runs cannot tell (E).

    python -m src.evaluator.ranking --grid sim/scenarios/rankings/IN-26-03365_lead-draft-20261013-b.json
    -> results/rankings/<plan set>.json

A cell is one scenario at one compliance and clearance: the P0, P1 and P2
results of a plan set with their run reports. A cell counts only if its P0
meets the validation targets (src/validation_targets.py) and none of its three
runs had a wrong-lane teleport other than at a lane shutting or in a jam
(src/evaluator/metrics.py, wrong_lane_teleports). Cells that do not
count are listed; if more than MAX_LEFT_OUT of them do not count, no order is
stated.

For each pair of plans A and B, each counting cell gives the difference in
total delay, A minus B, as a % of that cell's P0 delay: the same seed and
assumptions for both plans, so most of the cell's own noise cancels. "A before
B" if the 95% confidence interval of the mean difference lies wholly below
zero, "B before A" if wholly above, and a tie otherwise. F recommends a plan
only if it comes before both others (src/briefing/results.py).

The team set this rule on 13 October 2026, after 4 of the 33 cells of the
first grid had been seen and before the other 29 were run.

With --check the tool prints where the grid stands and writes nothing. Without
it, every cell must have its three results, all made by the same E code; the
ranking is written once and never overwritten.
"""
import argparse
import math
from itertools import combinations
from statistics import mean, stdev

from src import validation_targets as targets
from src.evaluation_provenance import verify_result
from src.evaluator import scenario as scenarios
from src.evaluator.run import complete_result_report, load_plan
from src.generation import load_json, save_json, validate
from src.plans.schema import NAME, array, obj
from src.twin.common import resolve

PLANS = ("P0", "P1", "P2")
OUT_DIR = "results/rankings"
MAX_LEFT_OUT = 0.10       # share of cells that may not count before no order is stated
# Two-sided 95% Student t value by degrees of freedom; between two rows the smaller df is used, which is wider.
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
       12: 2.179, 15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980}
GRID_SCHEMA = obj({
    "incident_id": NAME, "plans": NAME, "plan_set": NAME,
    "why": NAME,                                             # what the cells vary and where each choice comes from
    "cells": array(obj({"name": NAME, "scenario": NAME,
                        "compliance": {"type": "number", "minimum": 0, "maximum": 1},
                        "clearance_min": {"type": "number", "exclusiveMinimum": 0},
                        "results_dir": NAME}), minItems=2),
})
RULE = ("A cell counts if its P0 meets the validation targets and none of its runs had a wrong-lane teleport other "
        "than at a lane shutting or in a jam; no order is stated if more than 10% of cells do not count. 'A before B' if the "
        "95% confidence interval of the mean of (A delay - B delay) / P0 delay over the counting cells lies wholly "
        "below zero; a tie if it contains zero. Validation targets: " + targets.DESCRIPTION)


def load_grid(path):
    grid = load_json(resolve(path))
    validate(grid, GRID_SCHEMA)
    names = [c["name"] for c in grid["cells"]]
    settings = [(c["scenario"], c["compliance"], c["clearance_min"]) for c in grid["cells"]]
    if len(set(names)) != len(names) or len(set(settings)) != len(settings):
        raise ValueError("Each cell of the grid needs its own name and its own scenario, compliance and clearance")
    return grid


def read_cell(cell, grid):
    """(the cell's runs, delays and checks, the E code hashes its runs were made with)."""
    scenario = scenarios.load(resolve(cell["scenario"]))
    if scenario["incident_id"] != grid["incident_id"]:
        raise ValueError(f"{cell['name']}: the scenario is for another incident")
    settings = {"compliance": cell["compliance"], "clearance_min": cell["clearance_min"], "seed": scenario["seed"]}
    out = {"name": cell["name"], "scenario": cell["scenario"], **settings, "run_ids": {},
           "total_vehicle_hours_delay": {}, "wrong_lane_teleports_other": {}}
    shared = None
    for plan_id in PLANS:
        run_id = scenarios.run_id(scenario, plan_id, cell["compliance"], cell["clearance_min"], grid["plan_set"])
        path = resolve(cell["results_dir"]) / "runs" / f"{run_id}.json"
        report_path = resolve(cell["results_dir"]) / "evaluator" / f"{run_id}.report.json"
        if not (path.is_file() and report_path.is_file()):
            raise FileNotFoundError(f"{cell['name']}: {run_id} has no result yet")
        result, report = complete_result_report(path, report_path, run_id, plan_id, scenario, settings)
        plan, generation_inputs = load_plan(grid["plans"], plan_id, scenario)
        inputs = verify_result(path, result, plan, generation_inputs)
        if shared is not None and inputs != shared:
            raise ValueError(f"{cell['name']}: its runs were made from different simulation inputs")
        shared = inputs
        if "wrong_lane_teleports" not in report:
            raise ValueError(f"{run_id}: its report has no wrong-lane teleport check; run it again with today's E")
        out["run_ids"][plan_id] = run_id
        out["total_vehicle_hours_delay"][plan_id] = result["metrics"]["total_vehicle_hours_delay"]
        out["wrong_lane_teleports_other"][plan_id] = report["wrong_lane_teleports"]["other"]
        if plan_id == "P0":
            out["baseline_validation"] = result["validation"]
    met, reason = targets.check(out["baseline_validation"])
    teleported = [pid for pid, found in out["wrong_lane_teleports_other"].items() if found]
    out["counts"] = met and not teleported
    out["why_not"] = reason or (f"wrong-lane teleport other than at a lane shutting or in a jam in {', '.join(teleported)}"
                                if teleported else "")
    return out, {name: digest for name, digest in shared.items() if name.startswith("code:")}


def t95(df):
    return T95[max(row for row in T95 if row <= df)]


def compare(cells, a, b):
    """A against B over the counting cells: mean difference in % of P0 delay, its 95% interval, the plan before."""
    used = [c["total_vehicle_hours_delay"] for c in cells if c["counts"]]
    out = {"a": a, "b": b, "cells": len(used), "cells_a_lower": sum(d[a] < d[b] for d in used),
           "cells_b_lower": sum(d[b] < d[a] for d in used), "before": None}
    left_out = len(cells) - len(used)
    if left_out > MAX_LEFT_OUT * len(cells) or len(used) < 2:
        return {**out, "verdict": f"not stated: {left_out} of {len(cells)} cells do not count"}
    diffs = [100 * (d[a] - d[b]) / d["P0"] for d in used]
    centre, half = mean(diffs), t95(len(diffs) - 1) * stdev(diffs) / math.sqrt(len(diffs))
    low, high = centre - half, centre + half
    before = a if high < 0 else b if low > 0 else None
    return {**out, "mean_difference_pct": round(centre, 2), "interval_pct": [round(low, 2), round(high, 2)],
            "before": before,
            "verdict": f"{before} before {b if before == a else a}" if before else f"{a} and {b} tie"}


def orders(cells):
    """(every pair's comparison, the plan before both others or None)."""
    pairs = [compare(cells, a, b) for a, b in combinations(PLANS, 2)]
    first = next((x for x in PLANS if all(p["before"] == x for p in pairs if x in (p["a"], p["b"]))), None)
    return pairs, first


def rank(grid_path):
    """(the ranking or None until every cell has its results, the cells still without results, the cells read)."""
    grid = load_grid(grid_path)
    cells, pending, code = [], [], None
    for cell in grid["cells"]:
        try:
            read, hashes = read_cell(cell, grid)
        except FileNotFoundError as exc:
            pending.append(str(exc))
            continue
        if code is not None and hashes != code:
            raise ValueError(f"{cell['name']}: made by other E code than the cells before it; rerun the grid")
        code = hashes
        cells.append(read)
    if pending:
        return None, pending, cells
    pairs, first = orders(cells)
    ranking = {"incident_id": grid["incident_id"], "plan_set": grid["plan_set"], "plans": grid["plans"],
               "grid": str(grid_path), "why": grid["why"], "rule": RULE, "e_code_sha256": code, "cells": cells,
               "cells_not_counting": [f"{c['name']}: {c['why_not']}" for c in cells if not c["counts"]],
               "pairs": pairs, "verdicts": [p["verdict"] for p in pairs], "first": first}
    return ranking, [], cells


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--grid", required=True, help="Grid file: plans, plan set and cells")
    parser.add_argument("--check", action="store_true", help="Print where the grid stands; write nothing")
    parser.add_argument("--name", help="Ranking file name in results/rankings/, default the plan set; e.g. <plan set>-confirm")
    args = parser.parse_args()
    ranking, pending, cells = rank(args.grid)
    for c in cells:
        delays = c["total_vehicle_hours_delay"]
        print(f"{c['name']:<22} " + "  ".join(f"{p} {delays[p]:>7}" for p in PLANS)
              + ("" if c["counts"] else f"  does not count: {c['why_not']}"))
    if pending:
        print(f"{len(pending)} of {len(pending) + len(cells)} cells still without results, e.g. {pending[0]}")
        if not args.check:
            raise SystemExit("Nothing written: every cell needs its results first")
        return
    for p in ranking["pairs"]:
        print(f"{p['a']} - {p['b']}: mean {p.get('mean_difference_pct')}% of P0 delay, 95% interval "
              f"{p.get('interval_pct')}; {p['a']} lower in {p['cells_a_lower']}, {p['b']} in {p['cells_b_lower']} "
              f"of {p['cells']} counting cells -> {p['verdict']}")
    print(f"Before both others: {ranking['first'] or 'no plan'}")
    if args.check:
        return
    out = resolve(OUT_DIR) / f"{args.name or ranking['plan_set']}.json"
    if out.exists():
        raise SystemExit(f"{out} already exists; rankings are never overwritten")
    save_json(out, ranking)
    print(f"-> {OUT_DIR}/{out.name}")


if __name__ == "__main__":
    main()
