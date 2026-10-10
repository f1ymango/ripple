"""E's scenario file: the simulator inputs, the closure E assumes, and how each metric is measured.

The file is one of the hashed simulation inputs, so the assumptions travel with
every result. Nothing here is read from an LLM.

Four blocks are optional. A scenario without them runs exactly as before:

  closure.scene   speeds E sets around the crash: the closed edge and the lanes
                  leading to it. With it, a lane closed while another stays
                  open is closed to traffic (drivers move over beforehand)
                  instead of being set to zero speed.
  vehicles        the mean vehicle length, which sets how much road a queue takes.
  drivers_leave   drivers who see the queue ahead of an exit take that exit.
  plan_actions    where a plan's od groups, routes and junctions are in this
                  network. Without it E can only run P0.
"""
import hashlib
import re
from datetime import datetime

from src.generation import load_json, validate
from src.plans.schema import NAME, array, obj

SECONDS = {"type": "number", "minimum": 0}
POSITIVE = {"type": "number", "exclusiveMinimum": 0}
SHARE = {"type": "number", "minimum": 0, "maximum": 1}
EDGES = array(NAME, minItems=1, uniqueItems=True)
LANES = array(NAME, minItems=1, uniqueItems=True)


def optional(schema, *names):
    """`schema` with these properties allowed to be absent."""
    schema["required"] = [name for name in schema["required"] if name not in names]
    return schema


def named(items):
    return {"type": "object", "additionalProperties": items}


SCENE = optional(obj({
    "approach_edges": EDGES,                 # the lanes leading to the closed edge, where traffic passes the scene
    "open_kmh": POSITIVE,                    # the closed edge and the approach when nothing is closed
    "passing_kmh": POSITIVE,                 # the open lanes of the closed edge while another lane is closed
    "crawl_kmh": POSITIVE,                   # the approach while every lane is closed
    "move_over_at_edges": EDGES,             # where drivers learn a lane ahead is closed; default reroute_at_edges
    "reopening": obj({"lanes": LANES, "minutes": POSITIVE, "approach_kmh": POSITIVE}),
}), "move_over_at_edges", "reopening")
DRIVERS_LEAVE = optional(obj({
    "share": SHARE,                          # of the drivers who see the queue at an exit
    "queue_kmh": POSITIVE,                   # traffic ahead slower than this is a queue
    "route_crosses": NAME,                   # only drivers heading for this edge
    "exits": array(obj({"decide_on": EDGES, "exit_edge": NAME, "look_ahead": EDGES,
                        "nearside_lanes": {"type": "integer", "minimum": 1}}), minItems=1),
    "entry": obj({"edge": NAME, "after_waiting_seconds": POSITIVE}),
    "extra_minutes_outside": {"type": "number", "minimum": 0},
}), "entry")
PLAN_ACTIONS = obj({
    "od_groups": named(obj({"via_edge": NAME, "to_edge": NAME})),
    "routes": named(obj({"replace": EDGES, "with": EDGES})),
    "signals": named(obj({"tls_id": NAME, "green_phases": array({"type": "integer", "minimum": 0}, minItems=1)})),
})
SCENARIO_SCHEMA = obj({
    "incident_id": NAME,
    "run_prefix": NAME,                      # date and corridor, e.g. 2026-05-15_ABD
    "run_label": NAME,                       # names the closure assumption in the run_id
    "status": NAME,
    "sumo_version": NAME,
    "seed": {"type": "integer"},
    "inputs": optional(obj({"network": NAME, "routes": NAME, "detector_loops": NAME, "observations": NAME,
                            "speed_signs": NAME}), "speed_signs"),
    "run": obj({"begin": {"type": "string", "format": "date-time"},
                "end_seconds": {"type": "integer", "exclusiveMinimum": 0},
                "warmup_seconds": {"type": "integer", "minimum": 0},
                "wall_timeout_seconds": {"type": "integer", "exclusiveMinimum": 0}}),
    "closure": optional(obj({"edge_id": NAME, "lanes_total": {"type": "integer", "minimum": 1},
                             "onset_seconds": SECONDS,
                             "phases": array(obj({"offset_seconds": SECONDS, "lanes": LANES}), minItems=1),
                             "reroute_at_edges": EDGES,          # see reroute_window
                             "detour": obj({"replace": EDGES, "with": EDGES}),   # the road round it; default SUMO's choice
                             "scene": SCENE}), "reroute_at_edges", "detour", "scene"),
    "vehicles": obj({"type": NAME, "length_m": POSITIVE}),
    "drivers_leave": DRIVERS_LEAVE,
    "plan_actions": PLAN_ACTIONS,
    "speed_assessment_detectors": array(NAME, minItems=1, uniqueItems=True),   # where the model makes the speed itself
    "assumptions": array(obj({"choice": NAME, "status": NAME, "source": NAME}), minItems=1),
    "metrics": obj({
        "queue_paths": {"type": "object", "minProperties": 1, "additionalProperties": EDGES},
        "corridor": obj({"from_edge": NAME, "to_edge": NAME, "via_edge": NAME}),
        "emergency_route_edges": EDGES,
        "residential_edge_types": array(NAME, minItems=1, uniqueItems=True),
    }),
})
optional(SCENARIO_SCHEMA, "vehicles", "drivers_leave", "plan_actions", "speed_assessment_detectors")
LABEL = re.compile(r"[a-z0-9][a-z0-9-]*")      # no underscore: it separates the parts of a run_id
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
    if not LABEL.fullmatch(scenario["run_label"]):
        raise ValueError("run_label is lower-case letters, digits and hyphens")
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
    scene = closure.get("scene")
    if scene:
        if "reroute_at_edges" not in closure:
            raise ValueError("A scene needs closure.reroute_at_edges: where drivers move over or turn off")
    if "detour" in closure and ("reroute_at_edges" not in closure
                                or closure["detour"]["replace"][0] != closure["edge_id"]):
        raise ValueError("closure.detour needs reroute_at_edges and must replace the closed edge onwards")
        if "reopening" in scene:
            still = lane_indices(scene["reopening"]["lanes"], closure["lanes_total"])
            if len(still) == closure["lanes_total"]:
                raise ValueError("At reopening at least one lane must open")
    return scenario


def draw(seed, *parts):
    """A number in [0, 1) fixed by the run's seed and these words: the same driver decides the same way in every run."""
    text = ":".join(map(str, (seed,) + parts)).encode("utf-8")
    return int(hashlib.sha256(text).hexdigest()[:13], 16) / 16 ** 13


def closure_steps(scenario, clearance_min):
    """[(simulation second, lane indices closed from then on)], ending with the reopening ([])."""
    closure = scenario["closure"]
    reopen = reopen_second(scenario, clearance_min)
    if reopen >= scenario["run"]["end_seconds"]:            # the last second simulated is end_seconds - 1
        raise ValueError("The closure must reopen within the run; a longer clearance needs a longer run")
    steps = [(closure["onset_seconds"] + phase["offset_seconds"],
              lane_indices(phase["lanes"], closure["lanes_total"]))
             for phase in closure["phases"]
             if closure["onset_seconds"] + phase["offset_seconds"] < reopen]    # a phase due at reopening never starts
    reopening = closure.get("scene", {}).get("reopening")
    if not reopening:
        return steps + [(reopen, [])]
    last = reopen + round(reopening["minutes"] * 60)       # the road reopens in two stages
    if last >= scenario["run"]["end_seconds"]:
        raise ValueError("Every lane must reopen within the run")
    return steps + [(reopen, lane_indices(reopening["lanes"], closure["lanes_total"])), (last, [])]


def reopen_second(scenario, clearance_min):
    """When the first lane reopens: the clearance, counted from the closure onset."""
    return scenario["closure"]["onset_seconds"] + round(clearance_min * 60)


def reroute_window(scenario, clearance_min):
    """(from, until) in simulation seconds while every lane is closed, if the scenario reroutes drivers.

    With the whole edge shut nobody can get through, so a driver entering one of
    `reroute_at_edges` takes another road: `closure.detour` if the scenario names
    one, otherwise the one SUMO picks. Drivers do not reroute while a lane is
    still open.
    """
    closure = scenario["closure"]
    if "reroute_at_edges" not in closure:
        return None
    steps = closure_steps(scenario, clearance_min)
    shut = [second for second, lanes in steps if len(lanes) == closure["lanes_total"]]
    return (shut[0], reopen_second(scenario, clearance_min)) if shut else None


def lane_closures(scenario, clearance_min):
    """[(from, until, lane indices)] while some lanes are closed and others open. Empty without a scene.

    With a scene these lanes are closed to traffic, so drivers move over before
    them. Without one they are set to zero speed, as src/twin/run_scenario.py does.
    """
    closure = scenario["closure"]
    if "scene" not in closure:
        return []
    steps = closure_steps(scenario, clearance_min)
    return [(second, until, lanes) for (second, lanes), (until, _) in zip(steps, steps[1:])
            if 0 < len(lanes) < closure["lanes_total"]]


def scene_speeds(scenario, clearance_min, now):
    """(km/h on the closed edge, km/h on the approach) that E sets at simulation second `now`.

    Some lanes closed: the open lanes pass at `passing_kmh`. Every lane
    closed: nobody new gets onto the edge (they are turned off at
    `reroute_at_edges`), the few already on it leave at the same speed, and
    the approach crawls past the scene. Some lanes still closed after the first
    one reopens: the edge runs freely and the approach at the reopening speed.
    """
    closure, scene = scenario["closure"], scenario["closure"]["scene"]
    steps = closure_steps(scenario, clearance_min)
    closed = ([lanes for second, lanes in steps if second <= now] or [[]])[-1]
    if len(closed) == closure["lanes_total"]:
        return scene["passing_kmh"], scene["crawl_kmh"]
    if closed and now < reopen_second(scenario, clearance_min):
        return scene["passing_kmh"], scene["open_kmh"]
    if closed:
        return scene["open_kmh"], scene["reopening"]["approach_kmh"]
    return scene["open_kmh"], scene["open_kmh"]


def run_id(scenario, plan_id, compliance, clearance_min, plan_set):
    """date_corridor_plan_c<compliance %>_t<clearance min>_<scenario label>_<plan set>.

    e.g. 2026-05-15_ABD_P1_c50_t66_replay_rehearsal. The plan set names the
    folder of plans the run evaluates, so that two plan sets never share a run_id.
    """
    if not isinstance(plan_set, str) or not LABEL.fullmatch(plan_set):
        raise ValueError(f"A plan set is named in lower-case letters, digits and hyphens, not {plan_set!r}")
    percent, minutes = f"{compliance * 100:g}", f"{clearance_min:g}"
    if abs(float(percent) - compliance * 100) > 1e-9 or abs(float(minutes) - clearance_min) > 1e-9:
        raise ValueError(f"A run_id cannot tell compliance {compliance!r} or clearance {clearance_min!r} "
                         "from nearby values; use fewer decimals")
    return f"{scenario['run_prefix']}_{plan_id}_c{percent}_t{minutes}_{scenario['run_label']}_{plan_set}"
