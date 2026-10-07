"""Run one validated plan through the twin and save its contracted result.

    python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-rehearsal --plan P0 \\
        --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --compliance 0.5 --clearance 66

Writes results/runs/<run_id>.json, its .provenance.json sidecar, and a run
report in results/evaluator/ with the run's health, the scenario's assumptions
and how each metric was measured. Nothing is written if the run does not finish.

Run P0 first. P1 and P2 are compared with the P0 result of the same scenario,
compliance and clearance, and are refused if it is missing or was made from
different simulation inputs.
"""
import argparse
import shutil

from src.briefing.schema import RESULT_SCHEMA
from src.evaluation_provenance import capture_inputs, sidecar_path, write_result
from src.evaluator import metrics, scenario as scenarios, simulate
from src.evaluator.actions import PlanActions, has_actions
from src.evaluator.behaviour import DriversLeave
from src.generation import load_json, save_json, validate
from src.plans.validator import validate_plan
from src.twin.common import ROOT, resolve

CODE = ["src/evaluator/scenario.py", "src/evaluator/simulate.py", "src/evaluator/behaviour.py",
        "src/evaluator/actions.py", "src/evaluator/metrics.py", "src/evaluator/run.py", "src/twin/evaluate.py"]
TARGETS = "GEH < 5 for at least 85% of count bins and speed MAPE at most 15% (03-architecture.md §4)"


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


def do_nothing_baseline(results_dir, scenario, compliance, clearance_min, captured):
    """The P0 result and report a plan is compared with: same scenario, compliance, clearance and inputs."""
    run_id = scenarios.run_id(scenario, "P0", compliance, clearance_min)
    path = resolve(results_dir) / "runs" / f"{run_id}.json"
    if not path.is_file():
        raise ValueError(f"Run P0 first: {run_id} has no result to compare this plan with")
    if load_json(sidecar_path(path))["simulation_inputs"] != captured["simulation_inputs"]:
        raise ValueError(f"{run_id} was made from different simulation inputs; run P0 again before this plan")
    return load_json(path), load_json(resolve(results_dir) / "evaluator" / f"{run_id}.report.json")


def evaluate(plans_dir, plan_id, scenario_path, compliance, clearance_min,
             results_dir="results", work_root="sim/work/evaluator"):
    scenario = scenarios.load(resolve(scenario_path))
    plan, generation_inputs = load_plan(plans_dir, plan_id, scenario)
    actions = (PlanActions(plan, generation_inputs["policy_context"], scenario, compliance, clearance_min)
               if has_actions(plan) else None)
    leaving = DriversLeave(scenario, actions) if "drivers_leave" in scenario else None
    controllers = [c for c in (actions, leaving) if c]      # advice first: a driver who follows it does not leave
    run_id = scenarios.run_id(scenario, plan_id, compliance, clearance_min)
    result_path = resolve(results_dir) / "runs" / f"{run_id}.json"
    report_path = resolve(results_dir) / "evaluator" / f"{run_id}.report.json"
    if any(path.exists() for path in (result_path, sidecar_path(result_path), report_path)):
        raise ValueError(f"{run_id} already has a result; results are never overwritten")
    files = simulation_files(scenario_path, scenario)
    captured = capture_inputs(plan, generation_inputs, files)        # before the simulator starts
    baseline = (None if plan_id == "P0" else
                do_nothing_baseline(results_dir, scenario, compliance, clearance_min, captured))

    work = resolve(work_root) / run_id
    if work.exists():
        shutil.rmtree(work)                                           # scratch from an unfinished attempt
    health = simulate.run(scenario, {name: files[name] for name in scenario["inputs"]},
                          work, clearance_min, controllers)
    if not health["complete"]:
        raise RuntimeError(f"Run stopped at {health['final_time_seconds']} s of "
                           f"{scenario['run']['end_seconds']}; no result written. Output kept in {work}")
    if leaving:
        leaving.save(work)

    net = metrics.read_net(files["network"])
    values, detail = metrics.compute(scenario, files, work, net)
    delay = values.pop("total_vehicle_hours_delay")
    if baseline:
        before = baseline[0]["metrics"]["total_vehicle_hours_delay"]
        change = round(100 * (delay - before) / before, 1) if before else 0
    result = {
        "run_id": run_id, "plan_id": plan_id, "incident_id": scenario["incident_id"],
        "scenario": {"compliance": compliance, "clearance_min": clearance_min, "seed": scenario["seed"]},
        "metrics": {"total_vehicle_hours_delay": delay,
                    "delay_vs_do_nothing_pct": change if baseline else 0, **values},
        "validation": {},                                             # only P0 is compared with the real morning
    }
    report = {"run_id": run_id, "status": scenario["status"], "validation_targets": TARGETS}
    if baseline:
        report.update(validation_targets_met=baseline[1]["validation_targets_met"],
                      compared_with={"run_id": baseline[0]["run_id"], "validation": baseline[0]["validation"]})
    else:
        evaluation = metrics.score_against_detectors(work, files["observations"],
                                                     scenario["run"]["warmup_seconds"])
        result["validation"] = metrics.validation(evaluation)
        report.update(
            validation_targets_met=(result["validation"]["geh_under_5_pct"] >= 85
                                    and result["validation"]["speed_mape_pct"] <= 15),
            validation_by_phase=metrics.by_phase(evaluation, scenario, clearance_min),
            validation_bins={"count": evaluation["count_bin_n"], "speed": evaluation["speed_bin_n"],
                             "unmatched_count": evaluation["unmatched_count_intervals"],
                             "missing_detectors": evaluation["missing_detector_ids"]})
        if "speed_assessment_detectors" in scenario:
            report["speed_error_by_source"] = metrics.speed_error_by_source(
                evaluation, set(scenario["speed_assessment_detectors"]))
    validate(result, RESULT_SCHEMA)
    report.update({
        "run_health": health,
        "measurement_detail": detail,
        "metric_definitions": metrics.DEFINITIONS,
        "assumptions": scenario["assumptions"],
        "plan_effects_modelled": (actions.report() if actions else
                                  "none: this plan applies no operator action; compliance has no effect on this run"),
        "driver_rerouting": ("drivers reroute by themselves while every lane is closed"
                             if health.get("drivers_rerouted_during_seconds") else "none: every vehicle keeps its route"),
        "drivers_leaving": leaving.report() if leaving else "none: no driver leaves the corridor",
        "simulation_inputs": {name: str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
                              for name, path in sorted(files.items())},
    })
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
    parser.add_argument("--results-dir", default="results",
                        help="Use another folder for a diagnostic that must not sit beside the baseline in results/runs/")
    args = parser.parse_args()
    result, report, path = evaluate(args.plans, args.plan, args.scenario, args.compliance, args.clearance,
                                    results_dir=args.results_dir)
    health, measured = report["run_health"], result["metrics"]
    check = result["validation"] or report["compared_with"]["validation"]
    print(f"{result['run_id']}: {health['vehicles_inserted']} of {health['vehicles_loaded']} vehicles entered, "
          f"{health['vehicles_waiting_to_enter_at_end']} still waiting, {health['teleports']['total']} teleports")
    print(f"delay {measured['total_vehicle_hours_delay']} vehicle-hours ({measured['delay_vs_do_nothing_pct']:+}% "
          f"against doing nothing), queue {measured['max_queue_m']} m")
    print(f"{'This run' if result['validation'] else 'Its P0'}: GEH<5 {check['geh_under_5_pct']}%, speed MAPE "
          f"{check['speed_mape_pct']}% -> validation targets "
          f"{'met' if report['validation_targets_met'] else 'NOT met; do not rank plans against this run'}")
    print(f"-> {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


if __name__ == "__main__":
    main()
