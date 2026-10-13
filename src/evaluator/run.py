"""Run one validated plan through the twin and save its contracted result.

    python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal \\
        --plan P0 --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --compliance 0.5 --clearance 66 \\
        --results-dir results/evaluator-rehearsal

Writes <results-dir>/runs/<run_id>.json, its .provenance.json sidecar, and a
run report in <results-dir>/evaluator/ with the run's health, the scenario's
assumptions and how each metric was measured. Nothing is written if the run
does not finish. `--plan-set` names the plans folder in the run_id, so two plan
sets never share one.

Run P0 first. P1 and P2 are compared with the P0 result of the same scenario,
plan set, compliance and clearance, and are refused if it is missing or was
made from other plans or simulation inputs.
"""
import argparse
import math
import shutil

from jsonschema import ValidationError

from src.briefing.schema import RESULT_SCHEMA
from src import validation_targets as targets
from src.evaluation_provenance import capture_inputs, sidecar_path, verify_result, write_result
from src.evaluator import metrics, scenario as scenarios, simulate
from src.evaluator.actions import PlanActions, has_actions
from src.evaluator.behaviour import DriversLeave
from src.generation import load_json, save_json, validate
from src.plans.validator import validate_plan
from src.twin.common import ROOT, resolve

CODE = ["src/evaluator/scenario.py", "src/evaluator/simulate.py", "src/evaluator/behaviour.py",
        "src/evaluator/actions.py", "src/evaluator/metrics.py", "src/evaluator/run.py", "src/twin/evaluate.py",
        "src/validation_targets.py"]


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


def do_nothing_baseline(results_dir, scenario, plan_set, compliance, clearance_min, captured, p0_plan,
                        generation_inputs):
    """The P0 result and report a plan is compared with: same scenario, compliance, clearance and inputs.

    The P0 result must still match its sidecar, the P0 plan and the generation
    inputs this plan came with, as F will check when it compares them.
    """
    run_id = scenarios.run_id(scenario, "P0", compliance, clearance_min, plan_set)
    path = resolve(results_dir) / "runs" / f"{run_id}.json"
    report = resolve(results_dir) / "evaluator" / f"{run_id}.report.json"
    if not path.is_file():
        raise ValueError(f"Run P0 first: {run_id} has no result to compare this plan with")
    if not (sidecar_path(path).is_file() and report.is_file()):
        raise ValueError(f"{run_id} is missing its provenance sidecar or run report; "
                         "run P0 again in a new results folder")
    result, p0_report = complete_result_report(
        path, report, run_id, "P0", scenario,
        {"compliance": compliance, "clearance_min": clearance_min, "seed": scenario["seed"]})
    try:
        inputs = verify_result(path, result, p0_plan, generation_inputs)
    except ValueError as exc:
        raise ValueError(f"{run_id} does not match its sidecar, P0.json or generation-inputs.json in the plans "
                         f"folder ({exc}); run P0 again from these plans") from None
    if inputs != captured["simulation_inputs"]:
        raise ValueError(f"{run_id} was made from different simulation inputs; run P0 again before this plan")
    return result, p0_report


def complete_result_report(path, report_path, run_id, plan_id, scenario, expected_settings):
    """Authenticate the result identity and completed report before a run is reused."""
    try:
        result = load_json(path)
        validate(result, RESULT_SCHEMA)
    except (OSError, ValueError, ValidationError) as exc:
        raise ValueError(f"{path.name} is not a valid result ({exc})") from None
    if (result["run_id"] != run_id or result["plan_id"] != plan_id
            or result["incident_id"] != scenario["incident_id"]):
        raise ValueError(f"{path.name} does not describe the requested run, plan and incident")
    if result["scenario"] != expected_settings:
        raise ValueError(f"{path.name} has other compliance, clearance or seed settings")
    try:
        report = load_json(report_path)
    except (OSError, ValueError) as exc:
        raise ValueError(f"{run_id} has an unreadable run report ({exc})") from None
    if (not isinstance(report, dict) or report.get("run_id") != run_id
            or not isinstance(report.get("run_health"), dict)
            or report["run_health"].get("complete") is not True):
        raise ValueError(f"{run_id} has a mismatched or incomplete run report")
    return result, report


def kept_result(plans_dir, plan_id, scenario_path, scenario, path, *, plan_set, compliance, clearance_min):
    """Keep only a complete result/report pair for the requested run and current inputs."""
    check_run_settings(scenario, plan_set, compliance, clearance_min)
    run_id = scenarios.run_id(scenario, plan_id, compliance, clearance_min, plan_set)
    path = resolve(path)
    if path.name != f"{run_id}.json":
        raise ValueError(f"{path.name} is not the requested run {run_id}")
    report_path = path.parent.parent / "evaluator" / f"{run_id}.report.json"
    if not report_path.is_file():
        raise ValueError(f"{run_id} is missing its run report; do not keep an incomplete result")
    expected_settings = {"compliance": compliance, "clearance_min": clearance_min, "seed": scenario["seed"]}
    result, _ = complete_result_report(path, report_path, run_id, plan_id, scenario, expected_settings)
    plan, generation_inputs = load_plan(plans_dir, plan_id, scenario)
    captured = capture_inputs(plan, generation_inputs, simulation_files(scenario_path, scenario))
    try:
        inputs = verify_result(path, result, plan, generation_inputs)
    except (OSError, ValueError) as exc:
        raise ValueError(f"{path.name} was made from another plan or plan inputs ({exc}); "
                         "give this plan set its own --plan-set name") from None
    if inputs != captured["simulation_inputs"]:
        raise ValueError(f"{path.name} was made from other simulation inputs (scenario, input files or E's code); "
                         "run the set again in a new --results-dir")


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_run_settings(scenario, plan_set, compliance, clearance_min):
    """Refuse settings the result contract or the scenario cannot hold, before anything is simulated."""
    if not (number(compliance) and 0 <= compliance <= 1):
        raise ValueError(f"Compliance must be a share from 0 to 1, not {compliance!r}")
    if not (number(clearance_min) and clearance_min > 0):
        raise ValueError(f"Clearance must be a positive number of minutes, not {clearance_min!r}")
    scenarios.closure_steps(scenario, clearance_min)           # raises if the road would not reopen within the run
    scenarios.run_id(scenario, "P0", compliance, clearance_min, plan_set)   # raises if it would not tell runs apart


def evaluate(plans_dir, plan_set, plan_id, scenario_path, compliance, clearance_min,
             results_dir="results", work_root="sim/work/evaluator"):
    scenario = scenarios.load(resolve(scenario_path))
    check_run_settings(scenario, plan_set, compliance, clearance_min)
    plan, generation_inputs = load_plan(plans_dir, plan_id, scenario)
    actions = (PlanActions(plan, generation_inputs["policy_context"], scenario, compliance, clearance_min)
               if has_actions(plan) else None)
    leaving = DriversLeave(scenario, actions) if "drivers_leave" in scenario else None
    controllers = [c for c in (actions, leaving) if c]      # advice first: a driver who follows it does not leave
    run_id = scenarios.run_id(scenario, plan_id, compliance, clearance_min, plan_set)
    result_path = resolve(results_dir) / "runs" / f"{run_id}.json"
    report_path = resolve(results_dir) / "evaluator" / f"{run_id}.report.json"
    if any(path.exists() for path in (result_path, sidecar_path(result_path), report_path)):
        raise ValueError(f"{run_id} already has a result; results are never overwritten")
    files = simulation_files(scenario_path, scenario)
    captured = capture_inputs(plan, generation_inputs, files)        # before the simulator starts
    baseline = (None if plan_id == "P0" else
                do_nothing_baseline(results_dir, scenario, plan_set, compliance, clearance_min, captured,
                                    load_plan(plans_dir, "P0", scenario)[0], generation_inputs))

    root = resolve(work_root).resolve()
    work = root / run_id
    target = work.resolve()
    if target == root or not target.is_relative_to(root) or target != work:
        raise ValueError(f"Unsafe evaluator scratch path for {run_id}: {work}")
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
    at_lane_shut, other = metrics.wrong_lane_teleports((work / "sumo.log").read_text(encoding="utf-8"),
                                                       health["closure_steps"])
    report = {"run_id": run_id, "status": scenario["status"], "validation_targets": targets.DESCRIPTION,
              "wrong_lane_teleports": {"at_a_lane_shutting": at_lane_shut, "other": other}}
    if baseline:
        # A plan run is only as good as its P0, and fails on its own wrong-lane teleport too.
        report.update(validation_targets_met=baseline[1]["validation_targets_met"] and not other,
                      compared_with={"run_id": baseline[0]["run_id"], "validation": baseline[0]["validation"]})
    else:
        evaluation = metrics.score_against_detectors(work, files["observations"],
                                                     scenario["run"]["warmup_seconds"])
        result["validation"] = metrics.validation(evaluation, other)
        report.update(
            validation_targets_met=targets.met(result["validation"]),
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
    parser.add_argument("--plan-set", required=True,
                        help="Short name of that folder for the run_id, e.g. rehearsal; one name per plan set")
    parser.add_argument("--plan", required=True, choices=["P0", "P1", "P2"])
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--compliance", type=float, required=True, help="Share of advised drivers who divert, 0 to 1")
    parser.add_argument("--clearance", type=float, required=True, help="Minutes from closure onset to reopening")
    parser.add_argument("--results-dir", default="results",
                        help="Use another folder for a diagnostic that must not sit beside the baseline in results/runs/")
    args = parser.parse_args()
    result, report, path = evaluate(args.plans, args.plan_set, args.plan, args.scenario, args.compliance,
                                    args.clearance, results_dir=args.results_dir)
    health, measured = report["run_health"], result["metrics"]
    check = result["validation"] or report["compared_with"]["validation"]
    print(f"{result['run_id']}: {health['vehicles_inserted']} of {health['vehicles_loaded']} vehicles entered, "
          f"{health['vehicles_waiting_to_enter_at_end']} still waiting, {health['teleports']['total']} teleports")
    print(f"delay {measured['total_vehicle_hours_delay']} vehicle-hours ({measured['delay_vs_do_nothing_pct']:+}% "
          f"against doing nothing), queue {measured['max_queue_m']} m")
    other = report["wrong_lane_teleports"]["other"]
    print(f"{'This run' if result['validation'] else 'Its P0'}: GEH<5 {check['geh_under_5_pct']}%, free-flow speed "
          f"MAPE {check.get('speed_mape_free_flow_pct')}%, congestion state {check.get('congestion_state_agreement_pct')}"
          f"% (whole-run speed MAPE {check['speed_mape_pct']}%); "
          f"{len(other)} wrong-lane teleport(s) of this run not at a lane shutting -> validation targets "
          f"{'met' if report['validation_targets_met'] else 'NOT met; do not rank plans against this run'}")
    print(f"-> {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


if __name__ == "__main__":
    main()
