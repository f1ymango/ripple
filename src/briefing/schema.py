"""Existing result.json and briefing.json shapes, plus F's text-only model reply."""
from src.plans.schema import NAME, NONNEGATIVE, TEXT, array, obj

PERCENT = {"type": "number", "minimum": 0, "maximum": 100}
VALIDATION = obj({"geh_under_5_pct": PERCENT, "speed_mape_pct": NONNEGATIVE})
# Version 2 (13 Oct 2026, src/validation_targets.py): speed error over free-flow bins, congestion-state
# agreement and wrong-lane teleports other than at a lane shutting or in a jam. speed_mape_pct stays whole-run.
VALIDATION_V2 = obj({"geh_under_5_pct": PERCENT, "speed_mape_pct": NONNEGATIVE,
                     "speed_mape_free_flow_pct": NONNEGATIVE, "congestion_state_agreement_pct": PERCENT,
                     "wrong_lane_teleports_other": {"type": "integer", "minimum": 0}})
RESULT_SCHEMA = obj({
    "run_id": NAME, "plan_id": {"enum": ["P0", "P1", "P2"]}, "incident_id": NAME,
    "scenario": obj({"compliance": {"type": "number", "minimum": 0, "maximum": 1},
                     "clearance_min": {"type": "number", "exclusiveMinimum": 0},
                     "seed": {"type": "integer"}}),
    "metrics": obj({
        "total_vehicle_hours_delay": NONNEGATIVE,
        "delay_vs_do_nothing_pct": {"type": "number"},
        "max_queue_m": {"type": "object", "additionalProperties": NONNEGATIVE},
        "corridor_tt_p95_min": NONNEGATIVE, "emergency_tt_min": NONNEGATIVE,
        "co2_kg": NONNEGATIVE,
        "residential_delay_share_pct": {"type": "number", "minimum": 0, "maximum": 100},
        "vehicles_completed": {"type": "integer", "minimum": 0},
    }),
    "validation": {"anyOf": [VALIDATION, VALIDATION_V2, obj({}), {"type": "null"}]},
})
RESULT_SCHEMA["required"].remove("validation")

PUBLIC_MESSAGE = obj({"audience": NAME, "text_en": NAME, "text_zh": NAME})
DRAFT_SCHEMA = obj({
    "operator_briefing_en": NAME, "operator_briefing_zh": NAME,
    "vms_messages": array(obj({"sign_id": NAME, "text_en": NAME, "text_zh": NAME})),
    "public_messages": array(PUBLIC_MESSAGE),
    "uncertainty_note_en": NAME,
})
BRIEFING_SCHEMA = obj({
    "run_id": NAME, "recommended_plan_id": {"enum": ["P0", "P1", "P2"]},
    "operator_briefing_en": NAME, "operator_briefing_zh": NAME,
    "vms_messages": array(obj({"sign_id": NAME, "text_en": NAME, "text_zh": NAME,
                               "chars_en": {"type": "integer", "minimum": 0}})),
    "public_messages": array(PUBLIC_MESSAGE),
    "uncertainty_note_en": NAME,
    "sources": array(NAME, minItems=3, uniqueItems=True),
})
