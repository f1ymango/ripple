"""Run one validated plan through the twin and save its contracted result.

    python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-first --plan P0 \\
        --scenario sim/scenarios/evaluator_IN-26-03365.json --compliance 0.5 --clearance 67

Writes results/runs/<run_id>.json, its .provenance.json sidecar, and a run
report in results/evaluator/ with the run's health, the scenario's assumptions
and how each metric was measured. Nothing is written if the run does not finish.
"""
import argparse
import shutil

from src.briefing.schema import RESULT_SCHEMA
from src.evaluation_provenance import capture_inputs, sidecar_path, write_result
from src.evaluator import metrics, scenario as scenarios, simulate
from src.generation import load_json, save_json, validate
from src.plans.validator import validate_plan
from src.twin.common import ROOT, resolve

CODE = ["src/evaluator/scenario.py", "src/evaluator/simulate.py", "src/evaluator/metrics.py",
        "src/evaluator/run.py", "src/twin/evaluate.py"]


def simulation_files(scenario_path, scenario):
    """Every file that decides the simulated numbers: inputs, the scenario itself and E's code."""
    files = {name: resolve(path) for name, path in scenario["inputs"].items()}
    files["scenario"] = resolve(scenario_path)
    files.update({f"code:{path}": ROOT / path for path in CODE})
    missing = [str(path) for path in files.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Simulation inputs not found: {missing}")
    return files


def load_plan(plans_dir, plan_id, scenario):
    """The saved plan, only if it is exactly what the constraint validator returns for its saved inputs."""
    plans_dir = resolve(plans_dir)
    plan = load_json(plans_dir / f"{plan_id}.json")
    generation_inputs = load_json(plans_dir / "generation-inputs.json")
    incident = generation_inputs["incident"]
    if incident["incident_id"] != scenario["incident_id"] or plan["plan_id"] != plan_id:
        raise ValueError("Plan, generation inputs and scenario must describe the same incident and plan")
    if validate_plan(plan, generation_inputs["policy_context"], incident) != plan:
        raise ValueError("The saved plan is not the constraint validator's output for its saved inputs")
    return plan, generation_inputs


def evaluate(plans_dir, plan_id, scenario_path, compliance, clearance_min,
             results_dir="results", work_root="sim/work/evaluator"):
    scenario = scenarios.load(resolve(scenario_path))
    plan, generation_inputs = load_plan(plans_dir, plan_id, scenario)
    if plan_id != "P0":
        raise NotImplementedError(
            "E can only run P0 so far. Diversions and signal changes are not modelled yet, "
            "so a P1 or P2 run would be the do-nothing case under another name")
    run_id = scenarios.run_id(scenario, plan_id, compliance, clearance_min)
    result_path = resolve(results_dir) / "runs" / f"{run_id}.json"
    report_path = resolve(results_dir) / "evaluator" / f"{run_id}.report.json"
    if any(path.exists() for path in (result_path, sidecar_path(result_path), report_path)):
        raise ValueError(f"{run_id} already has a result; results are never overwritten")
    files = simulation_files(scenario_path, scenario)
    captured = capture_inputs(plan, generation_inputs, files)        # before the simulator starts

    work = resolve(work_root) / run_id
    if work.exists():
        shutil.rmtree(work)                                           # scratch from an unfinished attempt
    health = simulate.run(scenario, {name: files[name] for name in scenario["inputs"]},
                          work, clearance_min)
    if not health["complete"]:
        raise RuntimeError(f"Run stopped at {health['final_time_seconds']} s of "
                           f"{scenario['run']['end_seconds']}; no result written. Output kept in {work}")

    net = metrics.read_net(files["network"])
    values, detail = metrics.compute(scenario, files, work, net)
    evaluation = metrics.score_against_detectors(work, files["observations"],
                                                 scenario["run"]["warmup_seconds"])
    result = {
        "run_id": run_id, "plan_id": plan_id, "incident_id": scenario["incident_id"],
        "scenario": {"compliance": compliance, "clearance_min": clearance_min, "seed": scenario["seed"]},
        "metrics": {"total_vehicle_hours_delay": values["total_vehicle_hours_delay"],
                    "delay_vs_do_nothing_pct": 0,
                    **{k: v for k, v in values.items() if k != "total_vehicle_hours_delay"}},
        "validation": metrics.validation(evaluation),
    }
    validate(result, RESULT_SCHEMA)
    targets_met = (result["validation"]["geh_under_5_pct"] >= 85
                   and result["validation"]["speed_mape_pct"] <= 15)
    report = {
        "run_id": run_id,
        "status": scenario["status"],
        "validation_targets_met": targets_met,
        "validation_targets": "GEH < 5 for at least 85% of count bins and speed MAPE at most 15% (03-architecture.md §4)",
        "validation_by_phase": metrics.by_phase(evaluation, scenario, clearance_min),
        "validation_bins": {"count": evaluation["count_bin_n"], "speed": evaluation["speed_bin_n"],
                            "unmatched_count": evaluation["unmatched_count_intervals"],
                            "missing_detectors": evaluation["missing_detector_ids"]},
        "run_health": health,
        "measurement_detail": detail,
        "metric_definitions": metrics.DEFINITIONS,
        "assumptions": scenario["assumptions"],
        "plan_effects_modelled": "none: P0 applies no operator action; compliance has no effect on this run",
        "simulation_inputs": {name: str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
                              for name, path in sorted(files.items())},
    }
    write_result(result_path, result, captured)
    save_json(report_path, report)
    return result, report, result_path


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plans", required=True, help="Folder D wrote: P0.json ... and generation-inputs.json")
    parser.add_argument("--plan", required=True, choices=["P0", "P1", "P2"])
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--compliance", type=float, required=True, help="Share of advised drivers who divert, 0 to 1")
    parser.add_argument("--clearance", type=float, required=True, help="Minutes from closure onset to reopening")
    args = parser.parse_args()
    result, report, path = evaluate(args.plans, args.plan, args.scenario, args.compliance, args.clearance)
    health, check = report["run_health"], result["validation"]
    print(f"{result['run_id']}: {health['vehicles_inserted']} of {health['vehicles_loaded']} vehicles entered, "
          f"{health['vehicles_waiting_to_enter_at_end']} still waiting, {health['teleports']['total']} teleports")
    print(f"GEH<5 {check['geh_under_5_pct']}%, speed MAPE {check['speed_mape_pct']}% -> validation targets "
          f"{'met' if report['validation_targets_met'] else 'NOT met; do not rank plans against this run'}")
    print(f"-> {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


if __name__ == "__main__":
    main()
