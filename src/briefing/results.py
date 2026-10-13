"""Read saved E results, require comparable runs, and rank by total delay.

A baseline with a version 2 validation block (src/validation_targets.py) also
needs the plan set's ranking, results/rankings/<plan set>.json from
src/evaluator/ranking.py: the lowest-delay plan here is recommended only if the
ranking puts it before both other plans over its grid of seeds and assumptions.
"""
from pathlib import Path

from src import validation_targets as targets
from src.briefing.schema import RESULT_SCHEMA
from src.generation import load_json, validate
from src.plans.schema import PLAN_SCHEMA
from src.plans.validator import CHECKS


def load_results(paths, root=Path("results/runs")):
    root = Path(root).resolve()
    artifacts = []
    for name in paths:
        path = Path(name).resolve()
        try:
            relative = path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Briefing inputs must be saved under results/runs/") from exc
        artifacts.append(("results/runs/" + relative.as_posix(), load_json(path)))
    return artifacts


def plan_set_of(run_id):
    """The plan set a run_id names last: ..._<scenario label>_<plan set>."""
    return run_id.rsplit("_", 1)[-1]


def load_ranking(run_id, root=Path("results/rankings")):
    """The saved ranking of the run's plan set, or None if there is none."""
    path = Path(root) / f"{plan_set_of(run_id)}.json"
    return load_json(path) if path.is_file() else None


def check_ranking(ranking, runs, winner):
    """Refuse a winner the plan set's ranking over its grid does not back, for exactly these runs."""
    if ranking is None:
        raise ValueError("No ranking for this plan set in results/rankings/; run src.evaluator.ranking")
    baseline = runs["P0"]
    if ranking.get("plan_set") != plan_set_of(baseline["run_id"]) or ranking.get("incident_id") != baseline["incident_id"]:
        raise ValueError("The ranking is for another plan set or incident")
    ids = {pid: r["run_id"] for pid, r in runs.items()}
    cell = next((c for c in ranking.get("cells", []) if c.get("run_ids") == ids), None)
    if cell is None:
        raise ValueError("These runs are not a cell of the plan set's ranking")
    if cell.get("total_vehicle_hours_delay") != {pid: r["metrics"]["total_vehicle_hours_delay"] for pid, r in runs.items()}:
        raise ValueError("The ranking's delays differ from these results")
    first = ranking.get("first")
    if first is None:
        raise ValueError("The plan set's ranking puts no plan before both others (" + "; ".join(ranking.get(
            "verdicts", [])) + "); no plan can be recommended")
    if first != winner["plan_id"]:
        raise ValueError("The ranking and these runs disagree on the lowest-delay plan")


def select(plans, artifacts, ranking=None):
    for plan in plans:
        validate(plan, PLAN_SCHEMA)
        if plan["constraints_checked"] != CHECKS:
            raise ValueError("Briefing requires plans passed through the constraint validator")
    by_plan = {p["plan_id"]: p for p in plans}
    if len(plans) != 3 or set(by_plan) != {"P0", "P1", "P2"}:
        raise ValueError("Comparison requires P0, P1 and P2")
    runs, sources, run_ids = {}, [], set()
    for source, result in artifacts:
        validate(result, RESULT_SCHEMA)
        pid = result["plan_id"]
        if pid in runs or source in sources or result["run_id"] in run_ids:
            raise ValueError("Duplicate plan result, run ID or source")
        if pid != "P0" and result.get("validation"):
            raise ValueError("Validation is populated only for baseline P0")
        runs[pid] = result
        sources.append(source)
        run_ids.add(result["run_id"])
    if set(runs) != set(by_plan):
        raise ValueError("A saved result is required for every candidate plan")
    baseline = runs["P0"]
    if any(r["incident_id"] != baseline["incident_id"] or r["scenario"] != baseline["scenario"]
           for r in runs.values()):
        raise ValueError("Compared runs must share incident, compliance, clearance and seed")
    validation = baseline.get("validation")
    met, reason = targets.check(validation)
    if not met:
        raise ValueError(f"Baseline has not met the documented validation targets: {reason}")
    if baseline["metrics"]["delay_vs_do_nothing_pct"] != 0:
        raise ValueError("P0 delay versus itself must be zero")
    winner = min(runs.values(), key=lambda r: (r["metrics"]["total_vehicle_hours_delay"], r["plan_id"]))
    if targets.is_version_2(validation):
        check_ranking(ranking, runs, winner)
    return by_plan[winner["plan_id"]], winner, baseline, sorted(sources)
