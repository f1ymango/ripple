"""Write P0, P1 and P2 for E without calling a model, so that E can be run before D's model has.

    python -m src.evaluator.rehearsal_plans \\
        --incident data/generated-plans/IN-26-03365-p0-only/generation-inputs.json \\
        --context data/plan-context/IN-26-03365_first-report-v2.json \\
        --out-dir data/generated-plans/IN-26-03365-rehearsal

These are stand-ins, built from the reviewed context alone and passed through
D's own checks (src/plans/generator.py validate_plans):

  P0  no action;
  P1  what D's prompt defines: the context's one detour, advised to every od
      group with share 1, no signal change;
  P2  the same detour advised to `--p2-share` of each od group, and every
      junction the context offers given its full green extension.

They say nothing about what D's model would propose. When D generates its own
set, evaluate that instead: a result is bound to one exact plan file.
"""
import argparse

from src.generation import load_json, save_json
from src.plans.generator import validate_plans
from src.plans.run import read_incident
from src.twin.common import resolve


def rehearsal_plans(incident, context, p2_share):
    vias = {route["via"] for route in context["routes"]}
    if len(vias) != 1:
        raise ValueError("The rehearsal set needs a context with exactly one detour")
    via = vias.pop()

    def plan(plan_id, label, rationale, share, signals):
        return {"plan_id": plan_id, "label": label, "rationale": rationale,
                "diversions": [{"od_group": od, "via": via, "share": share}
                               for od in sorted(context["od_demand_vehicles"])] if share else [],
                "signals": signals, "vms": [], "pt_nudge": {"mode": "", "intent": ""},
                "priority_corridor": context["priority_corridor"], "constraints_checked": []}
    signals = [{"junction_id": junction, "green_extend_s": limit}
               for junction, limit in sorted(context["signals"].items()) if limit]
    return validate_plans({"plans": [
        plan("P0", "Do nothing", "No operator action: the counterfactual every other plan is compared with.", 0, []),
        plan("P1", f"Advise everyone to use {via}",
             "Rehearsal stand-in: the one detour advised to every od group, with no signal change.", 1, []),
        plan("P2", f"Advise part of the traffic to use {via} and lengthen its green",
             "Rehearsal stand-in: the detour advised to part of each od group, and the junctions on it "
             "given their full green extension.", p2_share, signals),
    ]}, context, incident)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--incident", required=True,
                        help="Reader JSONL (with --message-id), an incident file, or a saved generation-inputs.json")
    parser.add_argument("--message-id")
    parser.add_argument("--context", required=True)
    parser.add_argument("--p2-share", type=float, default=0.5)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out = resolve(args.out_dir)
    if out.exists():
        raise ValueError("Use a new output directory to preserve earlier handoffs")
    incident = read_incident(resolve(args.incident), args.message_id)
    incident = incident.get("incident", incident)           # a saved generation-inputs.json holds it under this key
    context = load_json(resolve(args.context))
    for plan in rehearsal_plans(incident, context, args.p2_share):
        save_json(out / f"{plan['plan_id']}.json", plan)
    save_json(out / "generation-inputs.json", {"incident": incident, "policy_context": context})
    print(f"P0, P1, P2 and generation-inputs.json written to {out}; no model called, nothing simulated.")


if __name__ == "__main__":
    main()
