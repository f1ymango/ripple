"""Executable forms of plan.json and D's local, caller-supplied policy context."""


def obj(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def array(items, **limits):
    return {"type": "array", "items": items, **limits}


TEXT = {"type": "string"}
NAME = {"type": "string", "minLength": 1}
NONNEGATIVE = {"type": "number", "minimum": 0}
PRIORITY = obj({"od": NAME, "keep_clear": array(NAME, minItems=1, uniqueItems=True)})
PLAN_SCHEMA = obj({
    "plan_id": {"enum": ["P0", "P1", "P2"]},
    "label": NAME,
    "rationale": NAME,
    "diversions": array(obj({"od_group": NAME, "via": NAME,
                            "share": {"type": "number", "exclusiveMinimum": 0, "maximum": 1}})),
    "signals": array(obj({"junction_id": NAME,
                         "green_extend_s": {"type": "integer", "minimum": 0}})),
    "vms": array(obj({"sign_id": NAME, "intent": NAME})),
    "pt_nudge": obj({"mode": TEXT, "intent": TEXT}),
    "priority_corridor": PRIORITY,
    "constraints_checked": array(NAME, uniqueItems=True),
})
PLANS_SCHEMA = obj({"plans": array(PLAN_SCHEMA, minItems=3, maxItems=3)})
CONTEXT_SCHEMA = obj({
    "incident_id": NAME,
    "reviewed": {"const": True},
    "sources": array(NAME, minItems=1, uniqueItems=True),
    "active_from": {"type": "string", "format": "date-time"},
    "active_until": {"type": "string", "format": "date-time"},
    "od_demand_vehicles": {"type": "object", "minProperties": 1,
                           "additionalProperties": NONNEGATIVE},
    "routes": array(obj({
        "od_group": NAME, "via": NAME, "roads": array(NAME, minItems=1, uniqueItems=True),
        "residential": {"type": "boolean"}, "school": {"type": "boolean"},
    }), minItems=1),
    "blocked_roads": array(NAME, uniqueItems=True),
    "signals": {"type": "object", "additionalProperties": {"type": "integer", "minimum": 0}},
    "sign_ids": array(NAME, uniqueItems=True),
    "pt_modes": array(NAME, uniqueItems=True),
    "priority_corridor": PRIORITY,
})
