"""Generate bilingual drafts; substitute metric tokens from E using code."""
from copy import deepcopy
from pathlib import Path
import re

from src.briefing.results import load_results, select
from src.briefing.schema import BRIEFING_SCHEMA, DRAFT_SCHEMA
from src.generation import generate_checked, validate

HERE = Path(__file__).parent
TOKEN = re.compile(r"\{\{([a-z_][a-z_0-9]*)\}\}")


def evidence_tokens(result, baseline):
    metrics, scenario = result["metrics"], result["scenario"]
    values = {
        "plan_id": result["plan_id"],
        "delay_hours": metrics["total_vehicle_hours_delay"],
        "delay_vs_do_nothing_pct": metrics["delay_vs_do_nothing_pct"],
        "travel_time_p95_min": metrics["corridor_tt_p95_min"],
        "emergency_tt_min": metrics["emergency_tt_min"],
        "co2_kg": metrics["co2_kg"],
        "residential_delay_share_pct": metrics["residential_delay_share_pct"],
        "vehicles_completed": metrics["vehicles_completed"],
        "compliance_pct": scenario["compliance"] * 100,
        "clearance_min": scenario["clearance_min"],
        **baseline["validation"],
    }
    return {name: format(value, ".12g") if isinstance(value, (int, float)) else value
            for name, value in values.items()}


def render_text(text, tokens):
    def replace(match):
        name = match.group(1)
        if name not in tokens:
            raise ValueError(f"Unknown evidence token: {name}")
        return tokens[name]
    residue = TOKEN.sub("", text)
    if any(c.isnumeric() for c in residue) or "{" in residue or "}" in residue:
        raise ValueError("Use evidence tokens for numbers; no literal numeric claims")
    return TOKEN.sub(replace, text)


def check_vms(text):
    lines = re.split(r"\r?\n|//", text)
    if len(lines) > 3 or any(not line.strip() or len(line.strip()) > 60 for line in lines):
        raise ValueError("VMS allows at most three nonempty lines of at most 60 characters")


def assemble(draft, plan, result, baseline, sources):
    validate(draft, DRAFT_SCHEMA)
    tokens = evidence_tokens(result, baseline)
    signs = [v["sign_id"] for v in draft["vms_messages"]]
    if len(signs) != len(set(signs)) or set(signs) != {v["sign_id"] for v in plan["vms"]}:
        raise ValueError("Briefing VMS signs must match the selected plan")
    for name in ("operator_briefing_en", "operator_briefing_zh"):
        sentences = [s for s in re.split(r"[.!?。！？]+", draft[name]) if s.strip()]
        if not 3 <= len(sentences) <= 5:
            raise ValueError("Each operator briefing must contain three to five sentences")
    uncertainty = draft["uncertainty_note_en"]
    if not all("{{" + token + "}}" in uncertainty for token in ("compliance_pct", "clearance_min")):
        raise ValueError("Uncertainty note must state supplied compliance and clearance assumptions")
    output = deepcopy(draft)
    for name in ("operator_briefing_en", "operator_briefing_zh", "uncertainty_note_en"):
        output[name] = render_text(output[name], tokens)
    for message in output["vms_messages"] + output["public_messages"]:
        for name in ("text_en", "text_zh"):
            message[name] = render_text(message[name], tokens)
    for message in output["public_messages"]:
        message["audience"] = render_text(message["audience"], tokens)
    for message in output["vms_messages"]:
        check_vms(message["text_en"])
        check_vms(message["text_zh"])
        message["chars_en"] = len(message["text_en"])
    output.update(run_id=result["run_id"], recommended_plan_id=plan["plan_id"], sources=sources)
    validate(output, BRIEFING_SCHEMA)
    return output


def write_briefing(plans, result_paths, model="qwen3:8b", *, incident_id,
                   results_root=Path("results/runs")):
    plan, result, baseline, sources = select(plans, load_results(result_paths, results_root))
    if result["incident_id"] != incident_id:
        raise ValueError("Saved results belong to a different incident from the plan input")
    return generate_checked(
        component="briefing", prompt=HERE / "prompts" / "system.md",
        payload={"selected_plan": plan, "selected_result": result, "baseline_result": baseline,
                 "evidence_tokens": evidence_tokens(result, baseline)},
        schema=DRAFT_SCHEMA,
        check=lambda draft: assemble(draft, plan, result, baseline, sources),
        model=model, temperature=0.0)
