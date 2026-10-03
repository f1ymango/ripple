"""Draft the required P0/P1/P2 set through the logged model adapter."""
from pathlib import Path

from src.generation import generate_checked, load_json, validate
from src.plans.schema import PLANS_SCHEMA
from src.plans.validator import key, validate_context, validate_plan
from src.reader.reader import check_lanes

HERE = Path(__file__).parent
INCIDENT_SCHEMA = load_json(HERE.parent / "reader" / "incident.schema.json")


def validate_plans(value, context, incident):
    validate(incident, INCIDENT_SCHEMA)
    check_lanes(incident["lanes_closed"])
    if not incident["in_scope"] or incident["status"] == "CLOSED":
        raise ValueError("Only an active in-scope incident can start plan generation")
    validate(value, PLANS_SCHEMA)
    plans = value["plans"]
    if {p["plan_id"] for p in plans} != {"P0", "P1", "P2"}:
        raise ValueError("Exactly one P0, P1 and P2 are required")
    checked = sorted((validate_plan(p, context, incident) for p in plans),
                     key=lambda p: p["plan_id"])
    # A new label or rationale is not a distinct intervention.
    actions = [{"diversions": sorted((d["od_group"], key(d["via"]), d["share"])
                                     for d in p["diversions"]),
                "signals": sorted(p["signals"], key=lambda s: s["junction_id"]),
                "pt_nudge": p["pt_nudge"]} for p in checked]
    if actions[2] in actions[:2]:
        raise ValueError("P2 must propose a distinct intervention")
    return checked


def generate(incident, context, model="qwen3:8b"):
    validate(incident, INCIDENT_SCHEMA)
    check_lanes(incident["lanes_closed"])
    if not incident["in_scope"] or incident["status"] == "CLOSED":
        raise ValueError("Only an active in-scope incident can start plan generation")
    validate_context(context, incident)
    return generate_checked(
        component="plans", prompt=HERE / "prompts" / "system.md",
        payload={"incident": incident, "policy_context": context}, schema=PLANS_SCHEMA,
        check=lambda value: validate_plans(value, context, incident),
        model=model, temperature=0.3)
