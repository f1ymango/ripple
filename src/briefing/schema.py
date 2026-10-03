"""Existing result.json and briefing.json shapes, plus F's text-only model reply."""
from src.plans.schema import NAME, NONNEGATIVE, TEXT, array, obj

VALIDATION = obj({"geh_under_5_pct": {"type": "number", "minimum": 0, "maximum": 100},
                  "speed_mape_pct": NONNEGATIVE})
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
    "validation": {"anyOf": [VALIDATION, obj({}), {"type": "null"}]},
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
