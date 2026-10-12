"""Run a plan set through the twin at several compliance levels: P0 first, then P1 and P2 against it.

    python -m src.evaluator.batch --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal \\
        --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --clearance 66 \\
        --results-dir results/evaluator-rehearsal

The default compliance levels are 0.3, 0.5 and 0.7 (03-architecture.md §4).
Results are never overwritten. A run that already has a result is kept only
if that result binds these plans, their inputs and today's simulation inputs;
otherwise the batch stops. P0 takes no action, so its three results differ
only in name; each plan is compared with the P0 of its own compliance level.
"""
import argparse

from src.evaluator import scenario as scenarios
from src.evaluator.run import evaluate, kept_result
from src.twin.common import resolve

PLANS = ("P0", "P1", "P2")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plans", required=True)
    parser.add_argument("--plan-set", required=True, help="Short name of the plans folder for the run_id")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--clearance", type=float, required=True)
    parser.add_argument("--compliance", type=float, nargs="+", default=[0.3, 0.5, 0.7])
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()
    scenario = scenarios.load(resolve(args.scenario))
    for compliance in args.compliance:
        for plan_id in PLANS:
            run_id = scenarios.run_id(scenario, plan_id, compliance, args.clearance, args.plan_set)
            path = resolve(args.results_dir) / "runs" / f"{run_id}.json"
            if path.exists():
                kept_result(args.plans, plan_id, args.scenario, scenario, path,
                            plan_set=args.plan_set, compliance=compliance, clearance_min=args.clearance)
                print(f"{run_id}: kept, it already has a result from these plans and inputs")
                continue
            result, report, _ = evaluate(args.plans, args.plan_set, plan_id, args.scenario, compliance,
                                         args.clearance, results_dir=args.results_dir)
            metrics = result["metrics"]
            print(f"{run_id}: delay {metrics['total_vehicle_hours_delay']} vehicle-hours "
                  f"({metrics['delay_vs_do_nothing_pct']:+}% against doing nothing), "
                  f"validation targets {'met' if report['validation_targets_met'] else 'NOT met'}")


if __name__ == "__main__":
    main()
