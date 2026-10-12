"""Write P0 and generation-inputs.json for E without calling a model.

    python -m src.evaluator.do_nothing_plan --incident results/reader/2026-09-29T1608_qwen3-8b.jsonl \\
        --message-id 138270 --context data/plan-context/IN-26-03365_first-report.json \\
        --out-dir data/generated-plans/IN-26-03365-p0-only

P0 has no actions, so D's constraint validator fixes everything in it except
its label and rationale. This lets E produce a baseline before D's model has
run. When D generates P0/P1/P2 its own P0 replaces this one, and P0 must be
evaluated again: the provenance sidecar binds a result to one exact plan file.
"""
import argparse

from src.generation import load_json, save_json
from src.plans.generator import check_inputs
from src.plans.run import read_incident
from src.plans.validator import validate_plan
from src.twin.common import resolve


def do_nothing(incident, context):
    check_inputs(incident, context)
    return validate_plan({
        "plan_id": "P0", "label": "Do nothing",
        "rationale": "No operator action: the counterfactual every other plan is compared with.",
        "diversions": [], "signals": [], "vms": [], "pt_nudge": {"mode": "", "intent": ""},
        "priority_corridor": context["priority_corridor"], "constraints_checked": [],
    }, context, incident)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--incident", required=True)
    parser.add_argument("--message-id")
    parser.add_argument("--context", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out = resolve(args.out_dir)
    if out.exists():
        raise ValueError("Use a new output directory to preserve earlier handoffs")
    incident = read_incident(resolve(args.incident), args.message_id)
    context = load_json(resolve(args.context))
    plan = do_nothing(incident, context)
    save_json(out / "P0.json", plan)
    save_json(out / "generation-inputs.json", {"incident": incident, "policy_context": context})
    print(f"P0 and generation-inputs.json written to {out}; no model called, nothing simulated.")


if __name__ == "__main__":
    main()
