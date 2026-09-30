"""Read saved E results, require comparable runs, and rank by total delay."""
from pathlib import Path

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


def select(plans, artifacts):
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
    if (not validation or validation["geh_under_5_pct"] < 85
            or validation["speed_mape_pct"] > 15):
        raise ValueError("Baseline has not met the documented validation targets")
    if baseline["metrics"]["delay_vs_do_nothing_pct"] != 0:
        raise ValueError("P0 delay versus itself must be zero")
    winner = min(runs.values(), key=lambda r: (r["metrics"]["total_vehicle_hours_delay"], r["plan_id"]))
    return by_plan[winner["plan_id"]], winner, baseline, sorted(sources)
