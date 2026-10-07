"""E's scenario file: the simulator inputs, the closure E assumes, and how each metric is measured.

The file is one of the hashed simulation inputs, so the assumptions travel with
every result. Nothing here is read from an LLM.
"""
from datetime import datetime

from src.generation import load_json, validate
from src.plans.schema import NAME, array, obj

SECONDS = {"type": "number", "minimum": 0}
EDGES = array(NAME, minItems=1, uniqueItems=True)
SCENARIO_SCHEMA = obj({
    "incident_id": NAME,
    "run_prefix": NAME,                      # date and corridor, e.g. 2026-05-15_ABD
    "run_label": NAME,                       # names the closure assumption in the run_id
    "status": NAME,
    "sumo_version": NAME,
    "seed": {"type": "integer"},
    "inputs": obj({"network": NAME, "routes": NAME, "detector_loops": NAME, "observations": NAME}),
    "run": obj({"begin": {"type": "string", "format": "date-time"},
                "end_seconds": {"type": "integer", "exclusiveMinimum": 0},
                "warmup_seconds": {"type": "integer", "minimum": 0},
                "wall_timeout_seconds": {"type": "integer", "exclusiveMinimum": 0}}),
    "closure": obj({"edge_id": NAME, "lanes_total": {"type": "integer", "minimum": 1},
                    "onset_seconds": SECONDS,
                    "phases": array(obj({"offset_seconds": SECONDS,
                                         "lanes": array(NAME, minItems=1, uniqueItems=True)}),
                                    minItems=1)}),
    "assumptions": array(obj({"choice": NAME, "status": NAME, "source": NAME}), minItems=1),
    "metrics": obj({
        "queue_paths": {"type": "object", "minProperties": 1, "additionalProperties": EDGES},
        "corridor": obj({"from_edge": NAME, "to_edge": NAME, "via_edge": NAME}),
        "emergency_route_edges": EDGES,
        "residential_edge_types": array(NAME, minItems=1, uniqueItems=True),
    }),
})
STEP_SECONDS = 1        # every twin run so far uses a one-second step
BIN_SECONDS = 300       # detector observations and edge statistics are five-minute bins


def lane_indices(lanes, lanes_total):
    """Lane names to SUMO lane indices: the one place this conversion happens.

    03-architecture.md §3: offside to nearside is fast, middle2, middle1, slow.
    In our left-hand network SUMO counts from the nearside, so slow is index 0.
    """
    if lanes == ["all"]:
        return list(range(lanes_total))
    index = {"slow": 0, "fast": lanes_total - 1}
    if lanes_total >= 3:
        index["middle1"] = 1
    if lanes_total == 4:
        index["middle2"] = 2
    if any(lane not in index for lane in lanes) or (lanes_total == 1 and len(lanes) > 1):
        raise ValueError(
            f"Cannot close lanes {lanes} on a {lanes_total}-lane edge. 'unspecified' must be "
            "resolved to named lanes in the scenario file, with the reason stated in its assumptions")
    return sorted(index[lane] for lane in lanes)


def load(path):
    scenario = load_json(path)
    validate(scenario, SCENARIO_SCHEMA)
    run, closure = scenario["run"], scenario["closure"]
    if datetime.fromisoformat(run["begin"]).utcoffset() is None:
        raise ValueError("run.begin needs a time zone")
    if run["warmup_seconds"] % BIN_SECONDS or run["end_seconds"] % BIN_SECONDS:
        raise ValueError("Warm-up and end must fall on five-minute bin edges")
    if not run["warmup_seconds"] <= closure["onset_seconds"] < run["end_seconds"]:
        raise ValueError("The closure must start after the warm-up and before the run ends")
    offsets = [phase["offset_seconds"] for phase in closure["phases"]]
    if offsets[0] != 0 or offsets != sorted(set(offsets)):
        raise ValueError("Closure phases must start at offset 0 and be strictly increasing")
    for phase in closure["phases"]:
        lane_indices(phase["lanes"], closure["lanes_total"])
    return scenario


def closure_steps(scenario, clearance_min):
    """[(simulation second, lane indices closed from then on)], ending with the reopening ([])."""
    closure = scenario["closure"]
    reopen = closure["onset_seconds"] + round(clearance_min * 60)
    if reopen > scenario["run"]["end_seconds"]:
        raise ValueError("The closure must reopen within the run; a longer clearance needs a longer run")
    steps = [(closure["onset_seconds"] + phase["offset_seconds"],
              lane_indices(phase["lanes"], closure["lanes_total"]))
             for phase in closure["phases"]
             if phase["offset_seconds"] < clearance_min * 60]
    return steps + [(reopen, [])]


def run_id(scenario, plan_id, compliance, clearance_min):
    return (f"{scenario['run_prefix']}_{plan_id}_c{compliance * 100:g}_t{clearance_min:g}"
            f"_{scenario['run_label']}")
