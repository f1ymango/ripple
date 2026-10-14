"""E: lane mapping, closure timing, driver behaviour, plan actions, metrics and the provenance-bound result.

No SUMO needed: the simulator is replaced by mock output files and a stand-in for TraCI written here.
"""
import json
import shutil
import sys
import types
from pathlib import Path

import pytest

from src.briefing.schema import RESULT_SCHEMA, VALIDATION_V2
from src.evaluation_provenance import json_hash, sidecar_path, verify_result
from src.evaluator import metrics, od_demand, run, scenario as scenarios, simulate, speed_signs
from src.evaluator.actions import PlanActions
from src.evaluator.behaviour import LEFT_FILE, DriversLeave
from src.generation import load_json, save_json, validate

FIXTURES = Path(__file__).parent / "fixtures"
MOCK = FIXTURES / "mock_evaluator"
SCENARIO = "tests/fixtures/mock_evaluator/mock_scenario.json"

TRIPS = [  # id, depart, departDelay, arrival, duration, timeLoss, CO2 mg
    ("main.0", 100, 0, 200, 100, 5, 9e9),        # scheduled inside the warm-up: out of scope
    ("main.1", 310, 10, 400, 90, 30, 1e6),
    ("main.2", 400, 0, 700, 300, 240, 2e6),
    ("main.3", 500, 100, -1, 400, 350, 3e6),     # still driving at the end
    ("main.4", -1, 200, -1, 0, 0, 0),            # never entered
    ("side.0", 350, 0, 450, 100, 20, 0),         # crosses the closed edge but leaves the corridor
    ("other.0", 600, 0, 660, 60, 30, 6e5),
]
QUEUES = {310: {"closed_0": 50}, 500: {"closed_0": 195, "closed_1": 120, "in_0": 60},
          600: {"closed_0": 180, "in_0": 100}}     # 180 m does not reach `in`: its queue is separate
EDGES = {300: {"home": (100, 5, 40), "closed": (200, 2, 160)},      # sampledSeconds, speed, timeLoss
         600: {"home": (100, 3, 60), "closed": (100, 1, 100)}}


class MockEdge:
    def __init__(self, length, kind):
        self.length, self.kind = length, kind

    def getLength(self):
        return self.length

    def getType(self):
        return self.kind

    def getSpeed(self):
        return 10.0


class MockNet:
    edges = {"in": MockEdge(100, "highway.primary"), "closed": MockEdge(200, "highway.primary"),
             "home": MockEdge(300, "highway.residential"), "quiet": MockEdge(500, "highway.residential")}

    def getEdge(self, edge_id):
        return self.edges[edge_id]


def write_mock_output(work, trips=TRIPS):
    work = Path(work)
    (work / "tripinfo.xml").write_text("<tripinfos>" + "".join(
        f'<tripinfo id="{i}" depart="{d}" departDelay="{w}" arrival="{a}" duration="{t}" timeLoss="{loss}">'
        f'<emissions CO2_abs="{co2}"/></tripinfo>' for i, d, w, a, t, loss, co2 in trips) + "</tripinfos>")
    (work / "queues.xml").write_text("<queue-export>" + "".join(
        f'<data timestep="{t}"><lanes>' + "".join(
            f'<lane id="{lane}" queueing_length="{m}"/>' for lane, m in lanes.items()) + "</lanes></data>"
        for t, lanes in QUEUES.items()) + "</queue-export>")
    (work / "edges.xml").write_text("<meandata>" + "".join(
        f'<interval begin="{begin}" end="{begin + 300}">' + "".join(
            f'<edge id="{e}" sampledSeconds="{s}" speed="{v}" timeLoss="{loss}"/>'
            for e, (s, v, loss) in edges.items()) + "</interval>" for begin, edges in EDGES.items()) + "</meandata>")
    (work / "results" / "e1_MOCK01_0.xml").write_text(
        '<detector><interval begin="300" nVehContrib="10" speed="10"/>'
        '<interval begin="600" nVehContrib="0" speed="-1"/></detector>')


def wrong_lane_line(vehicle, lane, second):
    return (f"Warning: Teleporting vehicle '{vehicle}'; waited too long (wrong lane), lane='{lane}', "
            f"time={second:.2f}.\n")


def mock_run(complete=True, trips=TRIPS, log=""):
    def fake(scenario, files, work, clearance_min, controllers=()):
        simulate.prepare(scenario, files, work, clearance_min)
        write_mock_output(work, trips)
        (Path(work) / "sumo.log").write_text("Simulation version 1.27.1 started with time: 0.00.\n" + log)
        return {"complete": complete, "final_time_seconds": 900 if complete else 450,
                "closure_steps": [{"second": second, "lanes_closed": [f"closed_{i}" for i in lanes]}
                                  for second, lanes in scenarios.closure_steps(scenario, clearance_min)],
                "vehicles_loaded": 7, "vehicles_inserted": 6, "vehicles_waiting_to_enter_at_end": 1,
                "teleports": {"total": 0, "jam": 0, "yield": 0, "wrongLane": 0}}
    return fake


@pytest.fixture
def plans(tmp_path):
    folder = tmp_path / "plans"
    folder.mkdir()
    for plan_id in ("P0", "P1"):
        shutil.copy(FIXTURES / "mock_recommendation" / f"mock_{plan_id.lower()}.json", folder / f"{plan_id}.json")
    shutil.copy(FIXTURES / "mock_recommendation" / "mock_generation-inputs.json", folder / "generation-inputs.json")
    return folder


@pytest.fixture
def evaluate(tmp_path, plans, monkeypatch):
    monkeypatch.setattr(simulate, "run", mock_run())
    monkeypatch.setattr(metrics, "read_net", lambda path: MockNet())

    def call(plan_id="P0", scenario=SCENARIO):
        return run.evaluate(plans, "mock-plans", plan_id, scenario, 0.5, 5.0,
                            results_dir=tmp_path / "results", work_root=tmp_path / "work")
    return call


# --- scenario -------------------------------------------------------------

def test_lane_names_map_to_sumo_indices_from_the_nearside():
    assert scenarios.lane_indices(["slow"], 2) == [0]
    assert scenarios.lane_indices(["fast"], 2) == [1]
    assert scenarios.lane_indices(["fast", "middle1"], 3) == [1, 2]
    assert scenarios.lane_indices(["middle2", "slow"], 4) == [0, 2]
    assert scenarios.lane_indices(["all"], 3) == [0, 1, 2]


@pytest.mark.parametrize("lanes,total", [(["unspecified"], 2), (["middle1"], 2), (["middle2"], 3),
                                         (["hard_shoulder"], 3), (["all", "slow"], 2)])
def test_unresolved_or_impossible_lanes_are_refused(lanes, total):
    with pytest.raises(ValueError, match="unspecified"):
        scenarios.lane_indices(lanes, total)


def test_closure_steps_follow_the_clearance():
    scenario = scenarios.load(SCENARIO)
    assert scenarios.closure_steps(scenario, 5) == [(300, [0]), (420, [0, 1]), (600, [])]
    assert scenarios.closure_steps(scenario, 1.5) == [(300, [0]), (390, [])]   # reopens before phase two
    with pytest.raises(ValueError, match="within the run"):
        scenarios.closure_steps(scenario, 11)
    assert scenarios.run_id(scenario, "P0", 0.5, 5.0, "mock-plans") == "mock_P0_c50_t5_mock-closure_mock-plans"


def test_drivers_reroute_only_while_every_lane_is_closed(tmp_path):
    scenario = scenarios.load(SCENARIO)
    assert scenarios.reroute_window(scenario, 5) is None           # this scenario keeps every route
    scenario["closure"]["reroute_at_edges"] = ["in"]
    assert scenarios.reroute_window(scenario, 5) == (420, 600)     # phase two shuts both lanes
    assert scenarios.reroute_window(scenario, 1.5) is None         # reopened before both lanes shut
    files = {name: Path(path) for name, path in scenario["inputs"].items()}
    extras = simulate.prepare(scenario, files, tmp_path / "work", 5)
    assert extras[-1].read_text() == (
        '<additional><rerouter id="closure" edges="in"><interval begin="420" end="600">'
        '<closingReroute id="closed"/></interval></rerouter></additional>\n')


def test_scenario_must_resolve_unspecified_lanes(tmp_path):
    scenario = load_json(MOCK / "mock_scenario.json")
    scenario["closure"]["phases"][0]["lanes"] = ["unspecified"]
    path = tmp_path / "mock_unspecified.json"
    path.write_text(json.dumps(scenario))
    with pytest.raises(ValueError, match="unspecified"):
        scenarios.load(path)


@pytest.mark.parametrize("prefix", ["../outside", "..\\outside", "/outside", "C:\\outside",
                                     ".", "..", "a/b", "a\\b"])
def test_run_prefix_cannot_escape_the_scratch_folder(tmp_path, prefix):
    scenario = load_json(MOCK / "mock_scenario.json")
    scenario["run_prefix"] = prefix
    path = tmp_path / "mock_bad_prefix.json"
    path.write_text(json.dumps(scenario))
    with pytest.raises(ValueError, match="run_prefix"):
        scenarios.load(path)


@pytest.mark.parametrize("prefix", ["mock", "2026-05-15_ABD"])
def test_run_prefix_keeps_existing_safe_names(tmp_path, prefix):
    scenario = load_json(MOCK / "mock_scenario.json")
    scenario["run_prefix"] = prefix
    path = tmp_path / "mock_safe_prefix.json"
    path.write_text(json.dumps(scenario))
    assert scenarios.load(path)["run_prefix"] == prefix


def test_redirected_scratch_path_is_refused_before_cleanup(evaluate, tmp_path, monkeypatch):
    root = tmp_path / "work"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    sentinel = outside / "keep.txt"
    sentinel.write_text("do not remove")
    redirected = root / "mock_P0_c50_t5_mock-closure_mock-plans"
    try:
        redirected.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"This platform does not permit a directory symlink: {exc}")
    monkeypatch.setattr(run.shutil, "rmtree", lambda path: pytest.fail("scratch cleanup must not run"))
    monkeypatch.setattr(simulate, "run", lambda *args, **kwargs: pytest.fail("simulation must not run"))
    with pytest.raises(ValueError, match="Unsafe evaluator scratch path"):
        evaluate()
    assert sentinel.read_text() == "do not remove"
    assert not (tmp_path / "results").exists()


# --- simulate: closure timing against a stand-in for TraCI ---------------------

class MockTraci:
    def __init__(self, on_step=lambda now: None):
        self.now, self.calls, self.on_step = 0.0, [], on_step
        self.simulation = types.SimpleNamespace(getTime=lambda: self.now)
        self.lane = types.SimpleNamespace(
            getMaxSpeed=lambda lane: 13.89,
            setMaxSpeed=lambda lane, speed: self.calls.append((self.now, lane, speed)))

    def start(self, command, label, stdout=None):
        Path(command[command.index("--statistic-output") + 1]).write_text(
            '<statistics><vehicles loaded="7" inserted="6" running="1" waiting="1"/>'
            '<teleports total="0" jam="0" yield="0" wrongLane="0"/></statistics>')

    def getVersion(self):
        return 21, "SUMO mock"

    def simulationStep(self):
        self.on_step(self.now)
        self.now += 1

    def close(self):
        pass


@pytest.fixture
def twin(tmp_path, monkeypatch):
    scenario = scenarios.load(SCENARIO)
    files = {}
    for name, path in scenario["inputs"].items():
        files[name] = shutil.copy(Path(path), tmp_path / Path(path).name)
    monkeypatch.setattr(simulate, "require_command", lambda name: name)

    def start(fake, clearance=5):
        monkeypatch.setitem(sys.modules, "traci", fake)
        return simulate.run(scenario, files, tmp_path / "work", clearance)
    return start, files


def test_lanes_close_in_phases_and_reopen_at_clearance(twin):
    start, _ = twin
    fake = MockTraci()
    health = start(fake)
    assert sorted(fake.calls) == [(300, "closed_0", 0.0), (420, "closed_1", 0.0),
                                  (600, "closed_0", 13.89), (600, "closed_1", 13.89)]
    assert health["complete"] and health["final_time_seconds"] == 900
    assert health["vehicles_waiting_to_enter_at_end"] == 1


def test_run_that_hits_the_wall_clock_limit_is_incomplete(twin, monkeypatch):
    start, _ = twin
    ticks = iter([0.0] + [1e6] * 10)
    monkeypatch.setattr(simulate.time, "monotonic", lambda: next(ticks))
    assert start(MockTraci())["complete"] is False


def test_run_is_void_if_an_input_changes_underneath_it(twin):
    start, files = twin
    fake = MockTraci(on_step=lambda now: now == 10 and Path(files["routes"]).write_text("<routes/>"))
    with pytest.raises(RuntimeError, match="changed during the run"):
        start(fake)


# --- metrics --------------------------------------------------------------------

@pytest.fixture
def output(tmp_path):
    scenario = scenarios.load(SCENARIO)
    files = {name: Path(path) for name, path in scenario["inputs"].items()}
    simulate.prepare(scenario, files, tmp_path / "work", 5)
    write_mock_output(tmp_path / "work")
    return scenario, files, tmp_path / "work"


def test_metrics_count_unfinished_and_waiting_vehicles(output):
    scenario, files, work = output
    values, detail = metrics.compute(scenario, files, work, MockNet())
    assert detail["vehicles_in_scope"] == 6                       # main.0 left inside the warm-up
    assert detail["vehicles_in_scope_still_driving"] == 1
    assert detail["vehicles_in_scope_never_entered"] == 1
    assert values["vehicles_completed"] == 4
    assert values["total_vehicle_hours_delay"] == round((670 + 310) / 3600, 1)
    assert values["co2_kg"] == 7                                  # 6.6 kg; main.0's 9,000 kg is out of scope
    assert detail["corridor_vehicles"] == 3 and detail["corridor_vehicles_still_driving"] == 1
    assert values["corridor_tt_p95_min"] == round(400 / 60, 1)    # the vehicle still driving is the slowest


def test_queue_follows_spillback_upstream_only_while_edges_are_full(output):
    scenario, files, work = output
    values, detail = metrics.compute(scenario, files, work, MockNet())
    assert values["max_queue_m"] == {"MOCK01": 255}               # 195 m fills `closed`, plus 60 m on `in`
    assert detail["queue_path_m"] == {"MOCK01": 300} and detail["queue_share_of_path_pct"] == {"MOCK01": 85.0}


def test_edge_metrics_use_only_simulated_traffic(output):
    scenario, files, work = output
    values, detail = metrics.compute(scenario, files, work, MockNet())
    assert values["residential_delay_share_pct"] == round(100 * 100 / 360, 1)
    assert values["emergency_tt_min"] == round((300 / 4 + 500 / 10) / 60, 1)   # `quiet` at its speed limit
    assert detail["emergency_route_edges_with_traffic"] == 1


def speed_bin(observed, simulated):
    return {"observed_kmh": observed, "simulated_kmh": simulated,
            "absolute_percentage_error": 100 * abs(simulated - observed) / observed}


def test_validation_rounding_never_turns_a_miss_into_a_pass():
    evaluation = {"geh_under_5_percent": 84.999, "speed_mape_percent": 15.001,
                  "speed_bins": [speed_bin(100, 115.001)] + [speed_bin(50, 50)] * 5 + [speed_bin(10, 40)]}
    assert metrics.validation(evaluation, []) == {
        "geh_under_5_pct": 84.99, "speed_mape_pct": 15.01, "speed_mape_free_flow_pct": 2.51,
        "congestion_state_agreement_pct": 85.71, "wrong_lane_teleports_other": 0}


def test_free_flow_speed_error_leaves_out_bins_measured_under_30_kmh():
    evaluation = {"geh_under_5_percent": 90, "speed_mape_percent": 50,
                  "speed_bins": [speed_bin(80, 72), speed_bin(5, 30), speed_bin(29.9, 10)]}
    block = metrics.validation(evaluation, ["v lane 900"])
    assert block["speed_mape_free_flow_pct"] == 10.0                     # only the 80 km/h bin
    assert block["congestion_state_agreement_pct"] == 66.66              # 5 km/h measured, 30 simulated: disagree
    assert block["wrong_lane_teleports_other"] == 1
    validate(block, VALIDATION_V2)


def test_a_wrong_lane_teleport_counts_against_the_model_unless_at_a_lane_shutting_or_in_a_jam():
    steps = [{"second": 300, "lanes_closed": ["a_0"]}, {"second": 420, "lanes_closed": ["a_0", "a_1"]},
             {"second": 600, "lanes_closed": []}]
    near = {"b": {"b", ":j", "c"}, "c": {"c", ":k"}, "d": {"d"}}.__getitem__        # b leads through junction j to c
    log = (wrong_lane_line("x.1", "b_1", 604) + wrong_lane_line("x.2", "b_1", 781)      # waits from 304 and 481
           + wrong_lane_line("x.3", "d_0", 1500))
    assert metrics.wrong_lane_teleports(log, steps, near) == (["x.1 b_1 604"], [], ["x.2 b_1 781", "x.3 d_0 1500"])
    assert metrics.wrong_lane_teleports(wrong_lane_line("x.5", "b_1", 720), steps, near) == (["x.5 b_1 720"], [], [])
    assert metrics.wrong_lane_teleports(wrong_lane_line("x.6", "b_1", 900), steps, near)[2] == ["x.6 b_1 900"]  # reopening


def jam_line(lane, second):
    return f"Warning: Teleporting vehicle 'j.1'; waited too long (jam), lane='{lane}', time={second:.2f}.\n"


@pytest.mark.parametrize("jam, in_jam", [
    (jam_line("c_0", 1300), True),           # the next edge jammed during the wait (1200 to 1500)
    (jam_line("c_1", 900), True),            # ... or in the 300 s before it began
    (jam_line(":j_0_1", 1450), True),        # the junction b ends at
    (jam_line("b_2", 1499), True),           # its own edge
    (jam_line("c_0", 899), False),           # too early
    (jam_line("c_0", 1501), False),          # after it was lifted off
    (jam_line("e_0", 1300), False),          # elsewhere
])
def test_a_wrong_lane_teleport_inside_a_jam_on_its_edge_or_the_next_is_part_of_the_jam(jam, in_jam):
    near = {"b": {"b", ":j", "c"}}.get
    at_shut, jammed, other = metrics.wrong_lane_teleports(jam + wrong_lane_line("x.1", "b_1", 1500), [], near)
    assert (jammed, other) == ((["x.1 b_1 1500"], []) if in_jam else ([], ["x.1 b_1 1500"]))


def test_expected_demand_over_the_closed_edge_by_exit():
    totals = od_demand.expected_by_exit(MOCK / "mock_routes.rou.xml", "closed", 300, 600)
    assert totals == {"out": pytest.approx(3.0), "side_out": pytest.approx(3.0)}


# --- the provenance-bound result -------------------------------------------------------

def test_p0_result_meets_the_contract_and_its_sidecar_verifies(evaluate, plans, tmp_path):
    result, report, path = evaluate()
    validate(result, RESULT_SCHEMA)
    assert path == tmp_path / "results" / "runs" / "mock_P0_c50_t5_mock-closure_mock-plans.json"
    assert load_json(path) == result
    assert result["scenario"] == {"compliance": 0.5, "clearance_min": 5.0, "seed": 42}
    assert result["metrics"]["delay_vs_do_nothing_pct"] == 0
    assert result["validation"] == {"geh_under_5_pct": 100.0, "speed_mape_pct": 0.0, "speed_mape_free_flow_pct": 0.0,
                                    "congestion_state_agreement_pct": 100.0, "wrong_lane_teleports_other": 0}
    assert report["validation_targets_met"] and report["wrong_lane_teleports"] == {
        "at_a_lane_shutting": [], "in_a_jam": [], "other": []}
    files = verify_result(path, result, load_json(plans / "P0.json"), load_json(plans / "generation-inputs.json"))
    assert {"network", "routes", "detector_loops", "observations", "scenario",
            "code:src/evaluator/metrics.py", "code:src/twin/evaluate.py"} <= set(files)
    assert report["validation_targets_met"] is True
    assert report["assumptions"] and report["metric_definitions"]["max_queue_m"]
    assert (tmp_path / "results" / "evaluator" / "mock_P0_c50_t5_mock-closure_mock-plans.report.json").is_file()


def test_results_are_never_overwritten(evaluate):
    evaluate()
    with pytest.raises(ValueError, match="never overwritten"):
        evaluate()


def test_unfinished_run_writes_no_result(evaluate, tmp_path, monkeypatch):
    monkeypatch.setattr(simulate, "run", mock_run(complete=False))
    with pytest.raises(RuntimeError, match="no result written"):
        evaluate()
    assert not (tmp_path / "results").exists()


def test_plan_with_actions_is_refused_on_a_scenario_that_cannot_place_them(evaluate, tmp_path):
    with pytest.raises(NotImplementedError, match="only run P0"):
        evaluate("P1")
    assert not (tmp_path / "results").exists() and not (tmp_path / "work").exists()


def test_edited_plan_is_refused(evaluate, plans):
    plan = load_json(plans / "P0.json")
    plan["constraints_checked"] = plan["constraints_checked"][:-1]
    (plans / "P0.json").write_text(json.dumps(plan))
    with pytest.raises(ValueError, match="constraint validator"):
        evaluate()


def test_scenario_for_another_incident_is_refused(evaluate, tmp_path):
    scenario = load_json(MOCK / "mock_scenario.json")
    scenario["incident_id"] = "MOCK-OTHER"
    path = tmp_path / "mock_other.json"
    path.write_text(json.dumps(scenario))
    with pytest.raises(ValueError, match="same incident"):
        evaluate(scenario=path)


def test_sidecar_binds_the_exact_result(evaluate, plans):
    result, _, path = evaluate()
    changed = {**result, "metrics": {**result["metrics"], "co2_kg": 1}}
    with pytest.raises(ValueError, match="provenance"):
        verify_result(path, changed, load_json(plans / "P0.json"), load_json(plans / "generation-inputs.json"))
    assert sidecar_path(path).is_file()


def test_do_nothing_plan_is_the_validators_p0():
    from src.evaluator.do_nothing_plan import do_nothing
    inputs = load_json(FIXTURES / "mock_recommendation" / "mock_generation-inputs.json")
    plan = do_nothing(inputs["incident"], inputs["policy_context"])
    expected = load_json(FIXTURES / "mock_recommendation" / "mock_p0.json")
    assert {k: v for k, v in plan.items() if k not in ("label", "rationale")} == \
        {k: v for k, v in expected.items() if k not in ("label", "rationale")}


# --- a scenario with a scene, drivers who leave, and plan actions -----------------------

SCENE = {"approach_edges": ["in"], "open_kmh": 72, "passing_kmh": 3.6, "crawl_kmh": 7.2,
         "reopening": {"lanes": ["slow"], "minutes": 2, "approach_kmh": 18}}
LEAVE = {"share": 1.0, "queue_kmh": 15, "route_crosses": "closed",
         "exits": [{"decide_on": ["far", "in"], "exit_edge": "off", "look_ahead": ["closed"], "nearside_lanes": 1}],
         "entry": {"edge": "far", "after_waiting_seconds": 60}, "extra_minutes_outside": 20}
PLACES = {"od_groups": {"Mock origin->Mock destination": {"via_edge": "closed", "to_edge": "out"}},
          "routes": {"Mock Detour": {"replace": ["closed"], "with": ["under1", "under2"]}},
          "signals": {"MOCK-J": {"tls_id": "tls", "green_phases": [0]}}}


def full_scenario(tmp_path, **changes):
    """The mock scenario with every optional block, starting two minutes before the mock plans' action window."""
    scenario = load_json(MOCK / "mock_scenario.json")
    scenario["run"]["begin"] = "2026-05-15T08:59:00+08:00"       # the mock context acts from 09:01, second 120
    scenario["closure"].update(reroute_at_edges=["in"], scene=SCENE)
    scenario.update(drivers_leave=LEAVE, plan_actions=PLACES, vehicles={"type": "car", "length_m": 6.5},
                    speed_assessment_detectors=["MOCK01"])
    scenario.update(changes)
    path = tmp_path / "mock_full.json"
    path.write_text(json.dumps(scenario))
    return scenarios.load(path), path


def test_a_scene_reopens_in_two_stages_and_sets_the_speeds_around_the_crash(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    assert scenarios.closure_steps(scenario, 5) == [(300, [0]), (420, [0, 1]), (600, [0]), (720, [])]
    assert scenarios.reroute_window(scenario, 5) == (420, 600)            # turned off only while every lane is closed
    assert scenarios.lane_closures(scenario, 5) == [(300, 420, [0]), (600, 720, [0])]
    speeds = [scenarios.scene_speeds(scenario, 5, second) for second in (0, 300, 420, 600, 720)]
    assert speeds == [(72, 72), (3.6, 72), (3.6, 7.2), (72, 18), (72, 72)]   # (closed edge, approach) in km/h
    with pytest.raises(ValueError, match="within the run"):
        scenarios.closure_steps(scenario, 9)                              # the second stage would end after the run


def test_a_scene_needs_somewhere_for_drivers_to_turn_off(tmp_path):
    scenario = load_json(MOCK / "mock_scenario.json")
    scenario["closure"]["scene"] = SCENE
    path = tmp_path / "mock_scene_only.json"
    path.write_text(json.dumps(scenario))
    with pytest.raises(ValueError, match="reroute_at_edges"):
        scenarios.load(path)


@pytest.mark.parametrize("lanes", [["all"], ["slow", "fast"]])
def test_reopening_must_open_at_least_one_lane(tmp_path, lanes):
    scenario = load_json(MOCK / "mock_scenario.json")
    scene = json.loads(json.dumps(SCENE))
    scene["reopening"]["lanes"] = lanes
    scenario["closure"].update(reroute_at_edges=["in"], scene=scene)
    path = tmp_path / "mock_closed_reopening.json"
    path.write_text(json.dumps(scenario))
    with pytest.raises(ValueError, match="At reopening at least one lane must open"):
        scenarios.load(path)


def test_draws_are_fixed_by_seed_and_words():
    assert scenarios.draw(42, "f1.0", "advice") == scenarios.draw(42, "f1.0", "advice")
    assert scenarios.draw(42, "f1.0", "advice") != scenarios.draw(43, "f1.0", "advice")
    draws = [scenarios.draw(42, f"f1.{i}", "advice") for i in range(2000)]
    assert all(0 <= d < 1 for d in draws) and 0.45 < sum(draws) / len(draws) < 0.55


def test_with_a_scene_part_closed_lanes_are_closed_to_traffic_and_signs_are_loaded(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    files = {name: Path(path) for name, path in scenario["inputs"].items()}
    files["speed_signs"] = MOCK / "mock_loops.add.xml"                    # any file: prepare only passes it on
    extras = simulate.prepare(scenario, files, tmp_path / "work", 5)
    assert extras[2] == files["speed_signs"]
    assert extras[-1].read_text() == (
        '<additional><rerouter id="closure" edges="in"><interval begin="420" end="600">'
        '<closingReroute id="closed"/></interval></rerouter>'
        '<rerouter id="lanes" edges="in"><interval begin="300" end="420">'
        '<closingLaneReroute id="closed_0" disallow="all"/></interval><interval begin="600" end="720">'
        '<closingLaneReroute id="closed_0" disallow="all"/></interval></rerouter></additional>\n')


class Road:
    """A stand-in for TraCI with vehicles on edges: enough for the closure, the drivers and a plan's actions."""

    class TraCIException(Exception):
        pass

    def __init__(self):
        self.on, self.speed, self.routes, self.lane_index, self.index = {}, {}, {}, {}, {}
        self.pending, self.departed, self.removed, self.lane_speeds = [], [], [], {}
        self.program, self.logics = "0", {"0": types.SimpleNamespace(programID="0", type=0, phases=[
            types.SimpleNamespace(duration=24, state="G"), types.SimpleNamespace(duration=6, state="y")])}
        self.edge = types.SimpleNamespace(
            getLastStepVehicleIDs=lambda edge: list(self.on.get(edge, [])),
            getLastStepVehicleNumber=lambda edge: len(self.on.get(edge, [])),
            getLastStepMeanSpeed=lambda edge: self.speed.get(edge, 20.0), getLaneNumber=lambda edge: 2)
        self.vehicle = types.SimpleNamespace(
            getRoute=lambda v: tuple(self.routes[v]), getRouteIndex=lambda v: self.index.get(v, 0),
            getLaneIndex=lambda v: self.lane_index.get(v, 0), setRoute=self.set_route,
            getIDList=lambda: sorted(v for vehicles in self.on.values() for v in vehicles),
            remove=self.removed.append)
        self.simulation = types.SimpleNamespace(getPendingVehicles=lambda: list(self.pending),
                                                getDepartedIDList=lambda: list(self.departed))
        self.lane = types.SimpleNamespace(setMaxSpeed=self.lane_speeds.__setitem__)
        self.trafficlight = types.SimpleNamespace(
            getProgram=lambda tls: self.program, getAllProgramLogics=lambda tls: list(self.logics.values()),
            setProgramLogic=lambda tls, logic: self.logics.__setitem__(logic.programID, logic),
            setProgram=lambda tls, program: setattr(self, "program", program),
            Phase=lambda duration, state: types.SimpleNamespace(duration=duration, state=state),
            Logic=lambda program, kind, index, phases: types.SimpleNamespace(programID=program, type=kind, phases=phases))

    def set_route(self, vehicle, route):
        if route[0] != self.routes[vehicle][self.index.get(vehicle, 0)]:
            raise self.TraCIException("a new route must start where the vehicle is")
        self.routes[vehicle], self.index[vehicle] = list(route), 0

    def put(self, vehicle, edge, route, lane=0):
        self.on.setdefault(edge, []).append(vehicle)
        self.routes[vehicle], self.lane_index[vehicle], self.index[vehicle] = list(route), lane, route.index(edge)


THROUGH = ["far", "in", "closed", "out"]


def test_closure_with_a_scene_sets_each_lane_only_when_its_speed_changes(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    road, closure = Road(), simulate.Closure(scenario, 5)
    for now in (0, 1, 300, 420, 421, 600, 720):
        closure.step(road, now)
        if now == 0:
            assert road.lane_speeds == {"closed_0": 20.0, "closed_1": 20.0, "in_0": 20.0, "in_1": 20.0}
            road.lane_speeds.clear()
        elif now in (1, 421):
            assert road.lane_speeds == {}                                 # nothing changed: nothing sent
        elif now == 420:
            assert road.lane_speeds == {"in_0": 2.0, "in_1": 2.0}         # the approach crawls; the edge already did
            road.lane_speeds.clear()
        else:
            road.lane_speeds.clear()


def test_a_driver_at_an_exit_leaves_only_when_the_traffic_ahead_is_queued(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    road, drivers = Road(), DriversLeave(scenario)
    road.put("a.0", "in", THROUGH)
    road.put("ahead.0", "closed", THROUGH)
    drivers.step(road, 10)
    assert road.routes["a.0"] == THROUGH and drivers.left == []           # traffic ahead is moving
    road.speed["closed"] = 1.0
    drivers.step(road, 11)
    assert road.routes["a.0"] == ["in", "off"]
    assert drivers.left == [{"id": "a.0", "how": "exit", "edge": "off", "second": 11}]


def test_only_nearside_drivers_heading_for_the_queue_leave(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    road, drivers = Road(), DriversLeave(scenario)
    road.speed["closed"] = 1.0
    road.put("ahead.0", "closed", THROUGH)
    road.put("offside.0", "in", THROUGH, lane=1)
    road.put("local.0", "in", ["far", "in", "home"])
    drivers.step(road, 10)
    assert drivers.left == []
    road.lane_index["offside.0"] = 0                                      # it has moved over since
    drivers.step(road, 11)
    assert [row["id"] for row in drivers.left] == ["offside.0"]
    assert road.routes["local.0"] == ["far", "in", "home"]


def test_share_decides_how_many_leave(tmp_path):
    scenario, _ = full_scenario(tmp_path, drivers_leave={**LEAVE, "share": 0.4})
    road, drivers = Road(), DriversLeave(scenario)
    road.speed["closed"] = 1.0
    road.put("ahead.0", "closed", THROUGH)
    for i in range(1000):
        road.put(f"f.{i}", "in", THROUGH)
    drivers.step(road, 10)
    assert 350 < len(drivers.left) < 450
    drivers.step(road, 11)                                                # nobody is asked twice at the same exit
    assert 350 < len(drivers.left) < 450


def test_a_driver_kept_out_by_the_queue_gives_up_after_waiting(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    road, drivers = Road(), DriversLeave(scenario)
    road.pending, road.routes = ["late.0", "ramp.0"], {"late.0": THROUGH, "ramp.0": ["ramp", "in", "closed", "out"]}
    drivers.step(road, 100)
    drivers.step(road, 159)
    assert road.removed == []                                             # under a minute
    drivers.step(road, 160)
    assert road.removed == ["late.0"]                                     # the rule is for the corridor's entry only
    assert drivers.left == [{"id": "late.0", "how": "entry", "edge": "far", "second": 160, "waited_seconds": 60}]
    drivers.save(tmp_path)
    assert load_json(tmp_path / LEFT_FILE) == drivers.left
    assert drivers.report()["vehicles_left_by_edge"] == {"far": 1}


@pytest.fixture
def mock_plans():
    folder = FIXTURES / "mock_recommendation"
    return ({plan: load_json(folder / f"mock_{plan.lower()}.json") for plan in ("P0", "P1", "P2")},
            load_json(folder / "mock_generation-inputs.json")["policy_context"])


def test_plan_actions_e_cannot_model_are_refused(tmp_path, mock_plans):
    plans, context = mock_plans
    scenario, _ = full_scenario(tmp_path)
    with pytest.raises(NotImplementedError, match="public transport"):
        PlanActions({**plans["P1"], "pt_nudge": {"mode": "MTR", "intent": "ride"}}, context, scenario, 0.5, 5)
    with pytest.raises(NotImplementedError, match="does not place 'Mock Alternative'"):
        PlanActions({**plans["P1"], "diversions": [{**plans["P1"]["diversions"][0], "via": "Mock Alternative"}]},
                    context, scenario, 0.5, 5)
    with pytest.raises(NotImplementedError, match="only run P0"):
        PlanActions(plans["P1"], context, scenarios.load(SCENARIO), 0.5, 5)


def test_advised_drivers_take_the_detour_and_go_back_when_the_road_reopens(tmp_path, mock_plans):
    plans, context = mock_plans
    scenario, _ = full_scenario(tmp_path)
    road, actions = Road(), PlanActions(plans["P1"], context, scenario, 1.0, 5)
    assert (actions.start, actions.end) == (120, 600)                     # from the report until the first lane reopens
    road.put("early.0", "far", THROUGH)
    road.put("past.0", "closed", THROUGH)
    road.put("local.0", "far", ["far", "in", "home"])
    actions.step(road, 119)
    assert road.routes["early.0"] == THROUGH                              # nothing before the report
    actions.step(road, 120)                                               # everyone on the road hears it at once
    assert road.routes["early.0"] == ["far", "in", "under1", "under2", "out"]
    assert road.routes["past.0"] == THROUGH and road.routes["local.0"] == ["far", "in", "home"]
    road.on["far"].append("next.0")
    road.routes["next.0"], road.departed = list(THROUGH), ["next.0"]
    actions.step(road, 121)                                               # later drivers hear it as they set off
    assert road.routes["next.0"] == ["far", "in", "under1", "under2", "out"]
    assert actions.follows("next.0", road.routes["next.0"], 121) and not actions.follows("next.0", THROUGH, 600)
    road.departed, road.index["early.0"] = [], 2                          # early.0 is on the detour by now
    actions.step(road, 600)
    assert road.routes["next.0"] == THROUGH and road.routes["early.0"][-3:] == ["under1", "under2", "out"]
    assert actions.report()["vehicles_that_took_the_advised_route"] == 2
    assert actions.report()["of_them_back_on_the_reopened_road"] == 1


def test_compliance_scales_how_many_follow_and_followers_do_not_leave(tmp_path, mock_plans):
    plans, context = mock_plans
    scenario, _ = full_scenario(tmp_path, drivers_leave={**LEAVE, "route_crosses": "in"})   # the detour crosses it too
    road, actions = Road(), PlanActions(plans["P1"], context, scenario, 0.3, 5)
    for i in range(1000):
        road.put(f"f.{i}", "in", THROUGH)
    road.put("ahead.0", "closed", THROUGH)
    road.speed["closed"] = 1.0
    drivers = DriversLeave(scenario, actions)                             # share 1: everyone who may leave does
    actions.step(road, 120)
    drivers.step(road, 120)
    assert 250 < len(actions.rerouted) < 350
    assert len(drivers.left) == 1000 - len(actions.rerouted)
    assert not {row["id"] for row in drivers.left} & actions.rerouted


def test_signal_green_is_extended_for_the_action_window_only(tmp_path, mock_plans):
    plans, context = mock_plans
    scenario, _ = full_scenario(tmp_path)
    plan = {**plans["P0"], "plan_id": "P2", "signals": [{"junction_id": "MOCK-J", "green_extend_s": 10}]}
    road, actions = Road(), PlanActions(plan, context, scenario, 0.5, 5)
    actions.step(road, 119)
    assert road.program == "0"
    actions.step(road, 120)
    assert road.program == "plan" and [p.duration for p in road.logics["plan"].phases] == [34, 6]
    actions.step(road, 600)
    assert road.program == "0" and [p.duration for p in road.logics["0"].phases] == [24, 6]


def test_vehicles_that_left_the_corridor_are_charged_and_not_counted_as_completed(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    files = {name: Path(path) for name, path in scenario["inputs"].items()}
    simulate.prepare(scenario, files, tmp_path / "work", 5)
    write_mock_output(tmp_path / "work")
    before, _ = metrics.compute(scenario, files, tmp_path / "work", MockNet())
    (tmp_path / "work" / LEFT_FILE).write_text(json.dumps([
        {"id": "main.2", "how": "exit", "edge": "off", "second": 500},
        {"id": "main.9", "how": "entry", "edge": "far", "second": 700, "waited_seconds": 90},
        {"id": "main.8", "how": "entry", "edge": "far", "second": 250, "waited_seconds": 60}]))   # scheduled in the warm-up
    after, detail = metrics.compute(scenario, files, tmp_path / "work", MockNet())
    assert detail["vehicles_in_scope_left_corridor"] == {"at_an_exit": 1, "kept_out_of_the_network": 1}
    assert detail["vehicles_in_scope"] == 7
    assert detail["delay_hours_assumed_outside_network"] == round(2 * 20 / 60 + 90 / 3600, 1)
    assert after["total_vehicle_hours_delay"] == round((670 + 310 + 2 * 1200 + 90) / 3600, 1)
    assert after["vehicles_completed"] == before["vehicles_completed"] - 1
    assert detail["corridor_vehicles"] == 2                               # main.2 left: its time is not a corridor time


# --- P1 and P2 against their P0 ----------------------------------------------------------

@pytest.fixture
def evaluate_plans(tmp_path, plans, monkeypatch):
    shutil.copy(FIXTURES / "mock_recommendation" / "mock_p2.json", plans / "P2.json")
    monkeypatch.setattr(metrics, "read_net", lambda path: MockNet())
    _, scenario_path = full_scenario(tmp_path)

    def call(plan_id, trips=TRIPS, scenario=scenario_path):
        monkeypatch.setattr(simulate, "run", mock_run(trips=trips))
        return run.evaluate(plans, "mock-plans", plan_id, scenario, 0.5, 5.0,
                            results_dir=tmp_path / "results", work_root=tmp_path / "work")
    return call


def test_a_plan_is_compared_with_the_p0_of_the_same_scenario(evaluate_plans, plans):
    with pytest.raises(ValueError, match="Run P0 first"):
        evaluate_plans("P1")
    p0, p0_report, _ = evaluate_plans("P0")
    quicker = [(i, d, w, a, t, loss / 2, co2) for i, d, w, a, t, loss, co2 in TRIPS]
    p1, report, path = evaluate_plans("P1", trips=quicker)
    validate(p1, RESULT_SCHEMA)
    assert p1["validation"] == {}                                         # only P0 is compared with the real morning
    assert p1["metrics"]["total_vehicle_hours_delay"] == round((335 + 310) / 3600, 1)
    assert p1["metrics"]["delay_vs_do_nothing_pct"] == round(100 * (0.2 - 0.3) / 0.3, 1)
    assert report["compared_with"] == {"run_id": p0["run_id"], "validation": p0["validation"]}
    assert report["validation_targets_met"] is p0_report["validation_targets_met"]
    assert report["plan_effects_modelled"]["diversions"] == [
        {"od_group": "Mock origin->Mock destination", "probability_a_driver_follows": 0.5}]
    assert p0_report["speed_error_by_source"]["model_makes_the_speed"]["speed_bins"] == 1
    verify_result(path, p1, load_json(plans / "P1.json"), load_json(plans / "generation-inputs.json"))


def test_a_plan_is_refused_if_its_p0_was_made_from_other_inputs(evaluate_plans, tmp_path):
    evaluate_plans("P0")
    scenario = load_json(tmp_path / "mock_full.json")
    scenario["assumptions"][0]["choice"] = "Edited after P0 was run"
    (tmp_path / "mock_full.json").write_text(json.dumps(scenario))
    with pytest.raises(ValueError, match="different simulation inputs"):
        evaluate_plans("P1")


@pytest.mark.parametrize("missing", ["sidecar", "report"])
def test_a_plan_is_refused_if_its_p0_lost_its_sidecar_or_report(evaluate_plans, tmp_path, missing):
    _, _, path = evaluate_plans("P0")
    report = tmp_path / "results" / "evaluator" / f"{path.stem}.report.json"
    (sidecar_path(path) if missing == "sidecar" else report).unlink()
    with pytest.raises(ValueError, match="missing its provenance sidecar or run report"):
        evaluate_plans("P1")


@pytest.mark.parametrize("damage", ["wrong_id", "incomplete", "unreadable"])
def test_a_plan_is_refused_if_its_p0_report_is_not_complete_for_that_run(evaluate_plans, tmp_path, damage):
    _, _, path = evaluate_plans("P0")
    report_path = tmp_path / "results" / "evaluator" / f"{path.stem}.report.json"
    report = load_json(report_path)
    if damage == "wrong_id":
        report["run_id"] = "another-run"
    elif damage == "incomplete":
        report["run_health"]["complete"] = False
    if damage == "unreadable":
        report_path.write_text("not JSON")
    else:
        report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="run report"):
        evaluate_plans("P1")


def test_a_plan_is_refused_if_its_p0_result_has_another_identity(evaluate_plans):
    _, _, path = evaluate_plans("P0")
    result = load_json(path)
    result["plan_id"] = "P1"
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match="does not describe the requested run"):
        evaluate_plans("P1")


def test_a_plan_is_refused_if_its_p0_no_longer_matches_its_sidecar_or_plans(evaluate_plans, plans):
    _, _, path = evaluate_plans("P0")
    edited = load_json(path)
    edited["metrics"]["total_vehicle_hours_delay"] += 100                 # a hand-edited baseline
    path.write_text(json.dumps(edited))
    with pytest.raises(ValueError, match="does not match its sidecar"):
        evaluate_plans("P1")


# --- settings at and beyond the edges of the contract ------------------------------------

@pytest.mark.parametrize("compliance,clearance,plan_set", [
    (-0.1, 5.0, "p"), (1.1, 5.0, "p"), (float("nan"), 5.0, "p"), (float("inf"), 5.0, "p"), (True, 5.0, "p"),
    ("0.5", 5.0, "p"), (0.5, 0, "p"), (0.5, -5.0, "p"), (0.5, float("nan"), "p"), (0.5, float("inf"), "p"),
    (0.5, False, "p"),
    (0.5, 10.0, "p"), (0.5, 10.5, "p"),                # reopens as the run ends, or after it
    (0.1234567, 5.0, "p"), (0.5, 5.0000001, "p"),      # the run_id would not tell them from nearby values
    (0.5, 5.0, ""), (0.5, 5.0, "Lead_v1"), (0.5, 5.0, None),   # no plan set, or one that would split the run_id
])
def test_settings_the_contract_cannot_hold_are_refused_before_anything_runs(
        tmp_path, plans, monkeypatch, compliance, clearance, plan_set):
    monkeypatch.setattr(simulate, "run", lambda *args: pytest.fail("simulated a refused setting"))
    with pytest.raises(ValueError):
        run.evaluate(plans, plan_set, "P0", SCENARIO, compliance, clearance,
                     results_dir=tmp_path / "results", work_root=tmp_path / "work")
    assert not (tmp_path / "results").exists() and not (tmp_path / "work").exists()


@pytest.mark.parametrize("compliance,clearance", [(0, 5.0), (1, 5.0), (0.5, 9.5), (0.5, 0.5)])
def test_settings_at_the_edges_run_and_meet_the_contract(tmp_path, plans, monkeypatch, compliance, clearance):
    monkeypatch.setattr(simulate, "run", mock_run())
    monkeypatch.setattr(metrics, "read_net", lambda path: MockNet())
    result, _, _ = run.evaluate(plans, "mock-plans", "P0", SCENARIO, compliance, clearance,
                                results_dir=tmp_path / "results", work_root=tmp_path / "work")
    validate(result, RESULT_SCHEMA)
    assert result["scenario"] == {"compliance": compliance, "clearance_min": clearance, "seed": 42}


def test_run_ids_name_compliance_and_clearance_exactly():
    scenario = scenarios.load(SCENARIO)
    assert scenarios.run_id(scenario, "P1", 0.3, 66.0, "lead-v1") == "mock_P1_c30_t66_mock-closure_lead-v1"
    assert scenarios.run_id(scenario, "P1", 0.07, 66.5, "rehearsal") == "mock_P1_c7_t66.5_mock-closure_rehearsal"
    assert scenarios.run_id(scenario, "P1", 0.125, 0.5, "r2") == "mock_P1_c12.5_t0.5_mock-closure_r2"
    for compliance, clearance in ((0.5, 66.0000001), (0.1234567, 66.0), (0.5, 1 / 60)):
        with pytest.raises(ValueError, match="nearby values"):
            scenarios.run_id(scenario, "P1", compliance, clearance, "rehearsal")


def test_a_phase_due_when_the_road_reopens_never_starts(tmp_path):
    scenario = scenarios.load(SCENARIO)                                   # slow lane at 300, both lanes at 420
    assert scenarios.closure_steps(scenario, 1) == [(300, [0]), (360, [])]
    assert scenarios.closure_steps(scenario, 2.001) == [(300, [0]), (420, [])]   # 120.06 s rounds to 120
    assert scenarios.closure_steps(scenario, 2.01) == [(300, [0]), (420, [0, 1]), (421, [])]
    rerouted, _ = full_scenario(tmp_path)
    assert scenarios.reroute_window(rerouted, 2.001) is None              # never every lane: nobody turned off
    assert scenarios.lane_closures(rerouted, 2.001) == [(300, 420, [0]), (420, 540, [0])]


def test_a_plan_does_nothing_if_the_road_reopens_before_the_operator_can_act(tmp_path, mock_plans):
    plans, context = mock_plans
    scenario, _ = full_scenario(tmp_path)
    late = {**context, "active_from": "2026-05-15T09:10:00+08:00"}       # second 660; the road reopens at 600
    plan = {**plans["P1"], "signals": [{"junction_id": "MOCK-J", "green_extend_s": 10}]}
    road, actions = Road(), PlanActions(plan, late, scenario, 1.0, 5)
    road.put("early.0", "far", THROUGH)
    for now in (0, 120, 599, 600, 660, 661, 899):
        actions.step(road, now)
    assert road.routes["early.0"] == THROUGH and road.program == "0" and not actions.rerouted
    assert actions.report()["active_seconds"].startswith("none: the first lane reopens at second 600")


PLACES_TWO = {**PLACES, "routes": {**PLACES["routes"], "Mock Alternative": {"replace": ["closed"], "with": ["alt"]}}}


@pytest.mark.parametrize("compliance", [1.0, 0.5])
def test_two_routes_for_one_od_group_split_its_drivers_by_share(tmp_path, mock_plans, compliance):
    plans, context = mock_plans                                           # P2: Detour 0.5, Alternative 0.25
    scenario, _ = full_scenario(tmp_path, plan_actions=PLACES_TWO)
    road, actions = Road(), PlanActions(plans["P2"], context, scenario, compliance, 5)
    for i in range(4000):
        road.put(f"f.{i}", "far", THROUGH)
    actions.step(road, 120)
    took = [road.routes[f"f.{i}"][2] for i in range(4000)]
    assert abs(took.count("under1") / 4000 - 0.5 * compliance) < 0.03
    assert abs(took.count("alt") / 4000 - 0.25 * compliance) < 0.03
    assert took.count("closed") == 4000 - took.count("under1") - took.count("alt")
    assert all(actions.follows(f"f.{i}", road.routes[f"f.{i}"], 121) == (took[i] != "closed") for i in range(4000))


LONG_WAY = {**PLACES, "routes": {"Mock Detour": {"leaves_at": "in", "rejoin": "out", "with": ["west", "north"]}}}


def test_a_long_way_round_leaves_before_the_closed_road_and_rejoins_whatever_lies_between(tmp_path, mock_plans):
    plans, context = mock_plans
    scenario, _ = full_scenario(tmp_path, plan_actions=LONG_WAY)
    road, actions = Road(), PlanActions(plans["P1"], context, scenario, 1.0, 5)
    variant = ["far", "in", "closed", "side", "out"]                      # another route between leaving and rejoining
    road.put("a.0", "far", THROUGH)
    road.put("b.0", "far", variant)
    road.put("past.0", "in", THROUGH)                                     # already past where the route leaves
    actions.step(road, 120)
    assert road.routes["a.0"] == road.routes["b.0"] == ["far", "west", "north", "out"]
    assert road.routes["past.0"] == THROUGH and actions.rerouted == {"a.0", "b.0"}
    actions.step(road, 600)                                               # both still short of the long way
    assert road.routes["a.0"] == THROUGH and road.routes["b.0"] == variant
    assert actions.report()["of_them_back_on_the_reopened_road"] == 2


@pytest.mark.parametrize("route, message", [
    ({"replace": ["closed"], "rejoin": "out", "with": ["alt"]}, "either replace or rejoin"),
    ({"with": ["alt"]}, "either replace or rejoin"),
    ({"leaves_at": "in", "rejoin": "out", "with": ["west", "out"]}, "end before the rejoin edge")])
def test_a_plan_route_names_what_it_replaces_one_way_only(tmp_path, route, message):
    with pytest.raises(ValueError, match=message):
        full_scenario(tmp_path, plan_actions={**PLACES, "routes": {"Mock Detour": route}})


def test_routes_and_junctions_the_network_cannot_take_are_refused(tmp_path, mock_plans):
    plans, context = mock_plans
    starts_early = {**PLACES, "routes": {"Mock Detour": {"replace": ["in", "closed"], "with": ["under1"]}}}
    scenario, _ = full_scenario(tmp_path, plan_actions=starts_early)
    with pytest.raises(NotImplementedError, match="does not start on the road"):
        PlanActions(plans["P1"], context, scenario, 0.5, 5)
    one_light = {**PLACES, "signals": {"MOCK-J": {"tls_id": "tls", "green_phases": [0]},
                                       "MOCK-K": {"tls_id": "tls", "green_phases": [1]}}}
    scenario, _ = full_scenario(tmp_path, plan_actions=one_light)
    plan = {**plans["P0"], "plan_id": "P2", "signals": [{"junction_id": "MOCK-J", "green_extend_s": 10},
                                                         {"junction_id": "MOCK-K", "green_extend_s": 5}]}
    with pytest.raises(NotImplementedError, match="one traffic light"):
        PlanActions(plan, context, scenario, 0.5, 5)


def test_a_green_phase_the_light_does_not_have_stops_the_run(tmp_path, mock_plans):
    plans, context = mock_plans
    scenario, _ = full_scenario(tmp_path, plan_actions={**PLACES, "signals": {"MOCK-J": {"tls_id": "tls",
                                                                                         "green_phases": [2]}}})
    plan = {**plans["P0"], "plan_id": "P2", "signals": [{"junction_id": "MOCK-J", "green_extend_s": 10}]}
    actions = PlanActions(plan, context, scenario, 0.5, 5)
    with pytest.raises(ValueError, match="has 2 phases"):
        actions.step(Road(), 120)


def test_withdrawing_advice_leaves_drivers_whose_route_changed_or_who_have_gone(tmp_path, mock_plans):
    plans, context = mock_plans
    scenario, _ = full_scenario(tmp_path)
    road, actions = Road(), PlanActions(plans["P1"], context, scenario, 1.0, 5)
    for vehicle in ("changed.0", "gone.0", "short.0"):
        road.put(vehicle, "far", THROUGH)
    actions.step(road, 120)
    assert actions.rerouted == {"changed.0", "gone.0", "short.0"}
    road.routes["changed.0"] = ["far", "in", "elsewhere"]                 # SUMO rerouted it since
    road.on["far"].remove("gone.0")                                       # it has left the network
    actions.step(road, 600)
    assert road.routes["changed.0"] == ["far", "in", "elsewhere"] and road.routes["short.0"] == THROUGH
    assert actions.report()["of_them_back_on_the_reopened_road"] == 1


def keep_mock_result(plans, tmp_path, path, *, plan_id="P0", compliance=0.5, clearance_min=5.0):
    scenario_path = tmp_path / "mock_full.json"
    return run.kept_result(plans, plan_id, scenario_path, scenarios.load(scenario_path), path,
                           plan_set="mock-plans", compliance=compliance, clearance_min=clearance_min)


def test_a_batch_keeps_a_result_only_if_it_binds_these_plans_and_inputs(evaluate_plans, plans, tmp_path, monkeypatch):
    from src.evaluator import batch
    full_scenario(tmp_path, plan_actions=PLACES_TWO)
    monkeypatch.setattr(simulate, "run", mock_run())
    argv = ["batch", "--plans", str(plans), "--plan-set", "mock-plans", "--scenario", str(tmp_path / "mock_full.json"),
            "--clearance", "5", "--compliance", "0.5", "--results-dir", str(tmp_path / "results")]
    monkeypatch.setattr(sys, "argv", argv)
    batch.main()                                                          # P0, P1 and P2, through the mock run
    first = sorted(p.name for p in (tmp_path / "results" / "runs").iterdir())
    assert len(first) == 6 and all("_mock-closure_mock-plans" in name for name in first)
    batch.main()                                                          # the same plans again: all three kept
    assert sorted(p.name for p in (tmp_path / "results" / "runs").iterdir()) == first
    inputs = load_json(plans / "generation-inputs.json")
    inputs["policy_context"]["sources"].append("another plan set's source")
    (plans / "generation-inputs.json").write_text(json.dumps(inputs))      # another plan set, same --plan-set name
    with pytest.raises(ValueError, match="another plan or plan inputs"):
        batch.main()
    monkeypatch.setattr(sys, "argv", [*argv[:4], "lead-v1", *argv[5:]])
    batch.main()                                                          # its own name: its own three runs
    assert len(list((tmp_path / "results" / "runs").glob("*_lead-v1.json"))) == 3


def test_a_batch_will_not_keep_a_result_made_from_other_simulation_inputs(evaluate_plans, plans, tmp_path):
    _, _, path = evaluate_plans("P0")
    scenario_path = tmp_path / "mock_full.json"
    keep_mock_result(plans, tmp_path, path)
    edited = load_json(scenario_path)
    edited["assumptions"][0]["choice"] = "Edited after P0 was run"
    scenario_path.write_text(json.dumps(edited))
    with pytest.raises(ValueError, match="other simulation inputs"):
        keep_mock_result(plans, tmp_path, path)


def test_a_batch_will_not_keep_a_result_without_its_report(evaluate_plans, plans, tmp_path):
    _, _, path = evaluate_plans("P0")
    (tmp_path / "results" / "evaluator" / f"{path.stem}.report.json").unlink()
    with pytest.raises(ValueError, match="missing its run report"):
        keep_mock_result(plans, tmp_path, path)


@pytest.mark.parametrize("damage", ["wrong_id", "incomplete", "unreadable"])
def test_a_batch_will_not_keep_a_result_with_a_bad_report(evaluate_plans, plans, tmp_path, damage):
    _, _, path = evaluate_plans("P0")
    report_path = tmp_path / "results" / "evaluator" / f"{path.stem}.report.json"
    report = load_json(report_path)
    if damage == "wrong_id":
        report["run_id"] = "another-run"
    elif damage == "incomplete":
        report["run_health"]["complete"] = False
    else:
        report_path.write_text("not JSON")
    if damage != "unreadable":
        report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="run report"):
        keep_mock_result(plans, tmp_path, path)


def test_a_batch_will_not_keep_a_misfiled_result_pair(evaluate_plans, plans, tmp_path):
    _, report, c50 = evaluate_plans("P0")
    c30 = c50.with_name(c50.name.replace("_c50_", "_c30_"))
    shutil.copy(c50, c30)
    shutil.copy(sidecar_path(c50), sidecar_path(c30))
    c30_run_id = c30.stem
    report["run_id"] = c30_run_id
    (tmp_path / "results" / "evaluator" / f"{c30_run_id}.report.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="does not describe the requested run"):
        keep_mock_result(plans, tmp_path, c30, compliance=0.3)


@pytest.mark.parametrize("setting,wrong", [("compliance", 0.3), ("clearance_min", 6.0), ("seed", 43)])
def test_a_batch_will_not_keep_a_result_with_other_settings(evaluate_plans, plans, tmp_path, setting, wrong):
    _, _, path = evaluate_plans("P0")
    result = load_json(path)
    result["scenario"][setting] = wrong
    path.write_text(json.dumps(result))
    sidecar = load_json(sidecar_path(path))
    sidecar["result_sha256"] = json_hash(result)
    sidecar_path(path).write_text(json.dumps(sidecar))
    with pytest.raises(ValueError, match="other compliance, clearance or seed"):
        keep_mock_result(plans, tmp_path, path)


@pytest.mark.parametrize("field,wrong", [("run_id", "another-run"), ("plan_id", "P1"),
                                          ("incident_id", "OTHER-INCIDENT")])
def test_a_batch_will_not_keep_a_result_with_other_identity(evaluate_plans, plans, tmp_path, field, wrong):
    _, _, path = evaluate_plans("P0")
    result = load_json(path)
    result[field] = wrong
    path.write_text(json.dumps(result))
    sidecar = load_json(sidecar_path(path))
    sidecar[field] = wrong
    sidecar["result_sha256"] = json_hash(result)
    sidecar_path(path).write_text(json.dumps(sidecar))
    with pytest.raises(ValueError, match="does not describe the requested run"):
        keep_mock_result(plans, tmp_path, path)


def test_a_batch_will_not_keep_a_result_outside_the_result_schema(evaluate_plans, plans, tmp_path):
    _, _, path = evaluate_plans("P0")
    result = load_json(path)
    del result["metrics"]["co2_kg"]
    path.write_text(json.dumps(result))
    sidecar = load_json(sidecar_path(path))
    sidecar["result_sha256"] = json_hash(result)
    sidecar_path(path).write_text(json.dumps(sidecar))
    with pytest.raises(ValueError, match="not a valid result"):
        keep_mock_result(plans, tmp_path, path)


# --- 10 October: a named detour, and joins on the main line ---------------------------------

DETOUR = {"replace": ["closed"], "with": ["under1", "under2"]}


def test_with_a_named_detour_drivers_go_round_it_and_keep_their_own_route(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    scenario["closure"]["detour"] = DETOUR
    road, closure = Road(), simulate.Closure(scenario, 5)
    road.put("early.0", "in", THROUGH)
    road.put("local.0", "in", ["far", "in", "home"])
    closure.step(road, 300)                                               # one lane shut: nobody turns off
    assert road.routes["early.0"] == THROUGH
    closure.step(road, 420)                                               # every lane shut
    assert road.routes["early.0"] == ["in", "under1", "under2", "out"] and road.routes["local.0"] == ["far", "in", "home"]
    assert closure.sent_round == {"early.0"}
    assert "closingReroute" not in simulate.rerouters(scenario, 5)        # SUMO no longer picks the road
    assert "closingLaneReroute" in simulate.rerouters(scenario, 5)


def test_a_detour_must_start_at_the_closed_edge(tmp_path):
    with pytest.raises(ValueError, match="detour"):
        full_scenario(tmp_path, closure={**load_json(MOCK / "mock_scenario.json")["closure"],
                                         "reroute_at_edges": ["in"], "detour": {"replace": ["in"], "with": ["x"]}})


def test_a_join_can_be_moved_from_its_ramp_to_the_main_line():
    import xml.etree.ElementTree as ET
    from src.evaluator.main_line_join import join_on_main_line
    root = ET.fromstring('<routes><flow id="f1"><route edges="ramp merge main out"/></flow>'
                         '<flow id="f2"><route edges="a main out"/></flow></routes>')
    assert join_on_main_line(root, {"f1"}, "main") == {"f1": ["ramp", "merge"]}
    assert [f.find("route").get("edges") for f in root.iter("flow")] == ["main out", "a main out"]
    with pytest.raises(ValueError, match="does not pass"):
        join_on_main_line(root, {"f2"}, "elsewhere")
    with pytest.raises(ValueError, match="No flow"):
        join_on_main_line(root, {"f9"}, "main")


# --- E's output into F and G --------------------------------------------------------------

def time_lost(share):
    return [(i, d, w, a, t, loss * share, co2) for i, d, w, a, t, loss, co2 in TRIPS]


def ranking_grid(tmp_path, plans, evaluate_plans, second_cell_lost):
    """Two cells, the mock scenario and the same at seed 7, each run P0, P1, P2; the grid file's path."""
    _, first = full_scenario(tmp_path, plan_actions=PLACES_TWO)          # P2 also names Mock Alternative
    second = tmp_path / "mock_seed7.json"
    second.write_text(json.dumps({**load_json(first), "seed": 7, "run_label": "mock-seed7"}))
    paths = []
    for scenario, lost in ((first, {"P1": 0.75, "P2": 0}), (second, second_cell_lost)):
        paths.append([evaluate_plans("P0", scenario=scenario)[2]] + [
            evaluate_plans(pid, trips=time_lost(lost[pid]), scenario=scenario)[2] for pid in ("P1", "P2")])
    grid = tmp_path / "grid.json"
    grid.write_text(json.dumps({"incident_id": "MOCK-INCIDENT", "plans": str(plans), "plan_set": "mock-plans",
                                "why": "two seeds", "cells": [
        {"name": name, "scenario": str(path), "compliance": 0.5, "clearance_min": 5.0,
         "results_dir": str(tmp_path / "results")} for name, path in (("main", first), ("seed7", second))]}))
    return grid, paths[0]


def test_e_results_are_accepted_by_the_briefing_and_the_console(evaluate_plans, plans, tmp_path):
    from src.briefing.writer import prepare_comparison
    from src.console.recommendation import load_comparison, scenarios_for, read_objects
    from src.evaluator import ranking
    grid, paths = ranking_grid(tmp_path, plans, evaluate_plans, {"P1": 0.75, "P2": 0})
    runs_dir = tmp_path / "results" / "runs"
    results, errors = read_objects(runs_dir)
    assert not errors and scenarios_for(results, "MOCK-INCIDENT") == [(0.5, 5.0, 7), (0.5, 5.0, 42)]
    comparison, why = load_comparison(runs_dir, plans, "MOCK-INCIDENT", (0.5, 5.0, 42))
    assert comparison is None and "No ranking" in why                    # version 2 needs the every-cell ranking
    saved_ranking, pending, _ = ranking.rank(grid)
    assert not pending and saved_ranking["first"] == "P2" and not saved_ranking["cells_not_counting"]
    assert saved_ranking["verdicts"] == ["P1 before P0", "P2 before P0", "P2 before P1"]
    save_json(tmp_path / "results" / "rankings" / "mock-plans.json", saved_ranking)
    comparison, why = load_comparison(runs_dir, plans, "MOCK-INCIDENT", (0.5, 5.0, 42))
    assert why == "" and comparison["winner"]["plan_id"] == "P2" and comparison["ranking_cells"] == 2
    inputs = load_json(plans / "generation-inputs.json")
    saved = [load_json(plans / f"P{i}.json") for i in range(3)]
    plan, result, baseline, sources = prepare_comparison(saved, paths, generation_inputs=inputs,
                                                         results_root=runs_dir)
    assert plan["plan_id"] == result["plan_id"] == "P2" and baseline["plan_id"] == "P0"
    assert len(sources) == 6                                              # three results and their sidecars


def test_no_plan_is_recommended_unless_the_ranking_puts_it_before_both_others(evaluate_plans, plans, tmp_path):
    from src.console.recommendation import load_comparison
    from src.evaluator import ranking
    grid, _ = ranking_grid(tmp_path, plans, evaluate_plans, {"P1": 0.25, "P2": 0.5})   # P1 lower at seed 7
    saved_ranking, _, _ = ranking.rank(grid)
    assert saved_ranking["first"] is None and saved_ranking["verdicts"][2] == "P1 and P2 tie"
    save_json(tmp_path / "results" / "rankings" / "mock-plans.json", saved_ranking)
    comparison, why = load_comparison(tmp_path / "results" / "runs", plans, "MOCK-INCIDENT", (0.5, 5.0, 42))
    assert comparison is None and "puts no plan before both others (" in why


def test_a_cell_whose_runs_teleported_a_driver_out_of_a_wrong_lane_blocks_every_order(evaluate_plans, plans, tmp_path,
                                                                                         monkeypatch):
    from src.evaluator import ranking
    grid, _ = ranking_grid(tmp_path, plans, evaluate_plans, {"P1": 0.5, "P2": 0.25})
    report = next((tmp_path / "results" / "evaluator").glob("*P1*seed7*.report.json"))
    saved = load_json(report)
    saved["wrong_lane_teleports"]["other"] = ["v lane 900"]
    report.write_text(json.dumps(saved))
    saved_ranking, _, cells = ranking.rank(grid)
    assert [c["counts"] for c in cells] == [True, False] and "P1" in cells[1]["why_not"]
    assert saved_ranking["first"] is None                                # 1 of 2 cells does not count: over 10%
    assert all(v == "not stated: 1 of 2 cells do not count" for v in saved_ranking["verdicts"])


def test_a_cell_without_results_is_reported_and_nothing_is_ranked(evaluate_plans, plans, tmp_path):
    from src.evaluator import ranking
    grid, _ = ranking_grid(tmp_path, plans, evaluate_plans, {"P1": 0.5, "P2": 0.25})
    (tmp_path / "results" / "runs" / "mock_P2_c50_t5_mock-seed7_mock-plans.json").unlink()
    saved_ranking, pending, cells = ranking.rank(grid)
    assert saved_ranking is None and len(pending) == 1 and "seed7" in pending[0] and len(cells) == 1


# --- speed signs and the rehearsal plans -------------------------------------------------

def test_refreshed_signs_show_the_speed_measured_in_the_quarter_hour_before():
    observations = {"detectors": [{"id": "D1", "observations": [
        {"time": "2026-01-01T08:00:00+08:00", "count": 30, "speed_kmh": 30.0},
        {"time": "2026-01-01T08:05:00+08:00", "count": 10, "speed_kmh": 10.0},     # 40 vehicles, harmonic mean 20
        {"time": "2026-01-01T08:35:00+08:00", "count": None, "speed_kmh": None}]}]}
    own = speed_signs.own_profile(observations, 15)
    assert own == {"D1": {"08:00": pytest.approx(20.0)}}
    ordinary = {"07:45": 60.0, "08:00": 50.0, "08:15": 40.0, "08:30": 45.0}
    profile, ratios = speed_signs.refreshed(ordinary, own["D1"])
    assert profile == {"07:45": 60.0, "08:00": 50.0, "08:15": 20.0, "08:30": 45.0}   # no reading before 08:30: ordinary
    assert ratios == {"08:15": 0.5}


def test_held_signs_show_nothing_measured_after_the_hold():
    profile = {"08:30": 60.0, "08:45": 55.0, "09:00": 20.0, "09:15": 10.0}
    ratios = {"08:45": 0.9, "09:00": 0.4, "09:15": 0.2}
    assert speed_signs.held(profile, ratios, "09:00") == ({"08:30": 60.0, "08:45": 55.0, "09:00": 55.0, "09:15": 55.0},
                                                         {"08:45": 0.9})


def test_sign_file_keeps_ordinary_speeds_where_the_queue_must_form_by_itself():
    import datetime as dt
    import xml.etree.ElementTree as ET
    signs = ET.fromstring('<additional><variableSpeedSign id="vss_a" lanes="a_0"/>'
                          '<variableSpeedSign id="vss_b" lanes="b_0"/><variableSpeedSign id="vss_c" lanes="c_0"/></additional>')
    inputs = {"day": "2026-01-01", "ordinary_days": [], "speed_profile_minutes": 15,
              "speed_profile_kmh": {"D1": {"08:00": 50.0, "08:15": 40.0}, "D2": {"08:00": 72.0, "08:15": 72.0}}}
    observations = {"detectors": [{"id": d, "observations": [
        {"time": "2026-01-01T08:00:00+08:00", "count": 10, "speed_kmh": 18.0}]} for d in ("D1", "D2")]}
    out, report = speed_signs.build(signs, {"a": "D1", "b": "D2", "c": "D2"}, inputs, observations,
                                    ordinary_only={"D2"}, drop_edges={"c"},
                                    begin=dt.datetime.fromisoformat("2026-01-01T08:00:00+08:00"), end_seconds=1800)
    steps = {sign.get("id"): [(step.get("time"), step.get("speed")) for step in sign] for sign in out}
    assert steps == {"vss_a": [("0", "13.89"), ("900", "5.00")], "vss_b": [("0", "20.00"), ("900", "20.00")]}
    assert report["detectors"]["D1"]["kind"] == "refreshed" and report["detectors"]["D2"]["kind"] == "ordinary only"
    assert report["edges_left_unsigned"] == ["c"]


def test_every_source_a_plan_context_names_is_in_the_repository():
    root = Path(__file__).parent.parent
    for path in sorted((root / "data" / "plan-context").glob("*.json")):
        missing = [source for source in load_json(path)["sources"] if not (root / source).is_file()]
        assert not missing, f"{path.name} names sources that are not in the repository: {missing}"


def test_rehearsal_plans_pass_ds_checks_and_differ(mock_plans):
    from src.evaluator.rehearsal_plans import rehearsal_plans
    _, context = mock_plans
    inputs = load_json(FIXTURES / "mock_recommendation" / "mock_generation-inputs.json")
    context = {**context, "routes": context["routes"][:1]}                # one detour, as in the real context
    p0, p1, p2 = rehearsal_plans(inputs["incident"], context, 0.5)
    assert not p0["diversions"] and not p0["signals"]
    assert [d["share"] for d in p1["diversions"]] == [1] and not p1["signals"]
    assert [d["share"] for d in p2["diversions"]] == [0.5]
    assert p2["signals"] == [{"junction_id": "MOCK-J", "green_extend_s": 10}]
    with pytest.raises(ValueError, match="exactly one detour"):
        rehearsal_plans(inputs["incident"], {**context, "routes": mock_plans[1]["routes"][:2]}, 0.5)


def test_a_driver_stuck_at_the_end_of_a_lane_that_leads_nowhere_on_its_way_is_let_in(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    scenario["closure"]["scene"] = {**SCENE, "let_in_after_seconds": 60}
    road, closure = Road(), simulate.Closure(scenario, 5)
    # "in" has two lanes; only lane 0 leads to "out" (by "closed" lane 0); lane 1 leads to "closed" lane 1, which is shut
    road.put("stuck.0", "in", THROUGH, lane=1)
    road.put("behind.0", "in", THROUGH, lane=0)
    links = {"in_0": [("closed_0",)], "in_1": [("closed_1",)], "closed_0": [("out_0",)], "closed_1": [("out_1",)]}
    shut = {"closed_1"}
    waiting, speeds, changes, held, modes = {"stuck.0": 61.0, "behind.0": 0.0}, {"behind.0": 1.0}, [], [], []
    road.lane = types.SimpleNamespace(setMaxSpeed=road.lane_speeds.__setitem__, getLinks=lambda lane: links.get(lane, []),
                                      getLength=lambda lane: 100.0,
                                      getDisallowed=lambda lane: ["passenger"] if lane in shut else [],
                                      getAllowed=lambda lane: [])
    road.vehicle.getWaitingTime = waiting.__getitem__
    road.vehicle.getLanePosition = lambda v: 95.0
    road.vehicle.getSpeed = speeds.__getitem__
    road.vehicle.getNeighbors = lambda v, mode: [("behind.0", 4.0)] if mode == 0b001 else []
    road.vehicle.slowDown = lambda v, speed, duration: held.append(v)
    road.vehicle.setLaneChangeMode = lambda v, mode: modes.append(mode)
    road.vehicle.changeLane = lambda v, lane, duration: changes.append((v, lane))
    closure.step(road, 5)
    assert changes == [("stuck.0", 0)] and held == ["behind.0"] and modes == [simulate.LET_IN_MODE]
    assert closure.let_in_now == {"stuck.0"}
    changes.clear()
    waiting["stuck.0"] = 30.0                               # moving again, or not stuck long enough
    closure.step(road, 10)
    assert changes == []
    shut.clear()                                            # its own lane leads on again: nothing to do
    waiting["stuck.0"] = 90.0
    closure.step(road, 15)
    assert changes == []


def test_drivers_are_also_let_in_along_the_scenes_let_in_edges_once_each():
    closure = {"reroute_at_edges": ["far", "in"], "scene": {"approach_edges": ["in"], "let_in_edges": ["up", "far"]}}
    assert simulate.let_in_edges(closure) == ["in", "far", "up"]
    assert simulate.let_in_edges({"scene": {"approach_edges": ["in"]}}) == ["in"]


def test_without_the_let_in_rule_nobody_is_moved(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    road, closure = Road(), simulate.Closure(scenario, 5)
    road.put("stuck.0", "in", THROUGH, lane=1)
    closure.step(road, 5)                                   # Road has no getWaitingTime: it would fail if asked
    assert closure.let_in_now == set()


# --- 13 October: drivers already committed to the flyover, and a slow first reopening --------

def test_a_driver_already_in_a_lane_onto_the_closed_edge_goes_on_over_it(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    scenario["closure"]["detour"] = DETOUR
    scenario["closure"]["scene"] = {**SCENE, "committed_edges": ["in"]}
    road, closure = Road(), simulate.Closure(scenario, 5)
    road.put("committed.0", "in", THROUGH, lane=1)                        # lane 1 leads only onto "closed"
    road.put("free.0", "in", THROUGH, lane=0)                             # lane 0 also leads to the detour
    lane_of = lambda v: f"in_{road.lane_index[v]}"
    road.vehicle.getLaneID = lane_of
    road.lane = types.SimpleNamespace(setMaxSpeed=road.lane_speeds.__setitem__,
                                      getLinks=lambda lane: [("closed_0",), ("under1_0",)] if lane == "in_0"
                                      else [("closed_1",)])
    closure.step(road, 420)                                               # every lane shut
    assert road.routes["committed.0"] == THROUGH and closure.kept_on == {"committed.0"}
    assert road.routes["free.0"] == ["in", "under1", "under2", "out"] and closure.sent_round == {"free.0"}


def test_without_committed_edges_every_driver_is_sent_round(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    scenario["closure"]["detour"] = DETOUR
    road, closure = Road(), simulate.Closure(scenario, 5)
    road.put("committed.0", "in", THROUGH, lane=1)
    closure.step(road, 420)
    assert road.routes["committed.0"] == ["in", "under1", "under2", "out"] and closure.kept_on == set()


def test_a_reopening_stage_can_hold_the_open_lane_at_the_passing_speed(tmp_path):
    scenario, _ = full_scenario(tmp_path)
    scenario["closure"]["scene"] = {**SCENE, "reopening": {**SCENE["reopening"], "edge_kmh": 3.6}}
    assert scenarios.scene_speeds(scenario, 5, 600) == (3.6, 18)          # first lane back, at the passing speed
    assert scenarios.scene_speeds(scenario, 5, 720) == (72, 72)           # both lanes, full speed
    plain, _ = full_scenario(tmp_path)
    assert scenarios.scene_speeds(plain, 5, 600) == (72, 18)              # without edge_kmh: as before


def ranking_cell(p0, p1, p2, counts=True):
    return {"total_vehicle_hours_delay": {"P0": p0, "P1": p1, "P2": p2}, "counts": counts}


def test_a_plan_is_before_another_only_if_the_95_percent_interval_of_the_paired_difference_excludes_zero():
    from src.evaluator import ranking
    cells = [ranking_cell(100, 101, 97), ranking_cell(110, 109, 106.7), ranking_cell(90, 91, 86.4),
             ranking_cell(105, 104, 102.9), ranking_cell(95, 96, 93.1)]
    pairs, first = ranking.orders(cells)
    by = {(p["a"], p["b"]): p for p in pairs}
    assert by[("P0", "P1")]["verdict"] == "P0 and P1 tie"            # about -1, +1, -1, +1, -1 %: holds zero
    assert by[("P0", "P2")]["verdict"] == "P2 before P0" and by[("P0", "P2")]["interval_pct"][0] > 0
    assert by[("P0", "P2")]["mean_difference_pct"] == pytest.approx(2.8, abs=0.01)   # P0 - P2: 3, 3, 4, 2, 2 %
    assert by[("P1", "P2")]["verdict"] == "P2 before P1" and first == "P2"
    assert ranking.t95(4) == 2.776 and ranking.t95(13) == 2.179 and ranking.t95(500) == 1.980


def test_no_order_is_stated_when_more_than_a_tenth_of_the_cells_do_not_count():
    from src.evaluator import ranking
    good, bad = [ranking_cell(100, 90, 80)] * 9, ranking_cell(100, 120, 130, counts=False)
    assert ranking.orders(good + [bad])[1] == "P2"                   # 1 of 10 left out, and its delays are not used
    pairs, first = ranking.orders(good[:8] + [bad, bad])
    assert first is None and pairs[0]["verdict"] == "not stated: 2 of 10 cells do not count"


def test_closure_counts_score_the_hourly_flow_that_five_minute_geh_lets_through():
    from src.evaluator import closure_counts
    rows = [{"detector_id": "AID01106", "time": f"2026-05-15T09:{m:02d}:00+08:00", "observed": 90, "simulated": 62,
             "within_5": metrics_geh(62, 90) < 5} for m in range(5, 60, 5)]
    rows.append({"detector_id": "AID01106", "time": "2026-05-15T10:00:00+08:00", "observed": 90, "simulated": 0,
                 "within_5": False})                                     # outside the window: not counted
    out = closure_counts.cell_counts({"count_bins": rows})["AID01106"]
    assert out["bins"] == 11 and out["five_minute_bins_geh_under_5"] == 11      # every bin passes at five minutes
    assert out["simulated_over_counted"] == 0.69 and out["geh_hourly_equivalent"] > 10   # the hour fails


def metrics_geh(m, c):
    from src.evaluator.closure_counts import geh
    return geh(m, c)


def test_queue_onset_and_recovery_are_read_from_30_kmh_crossings():
    from src.evaluator import p0_checks
    speeds = {"08:25": 10, "08:30": 60, "09:05": 12, "09:30": 8, "10:00": 35, "10:05": 25, "10:10": 40, "10:15": 45,
              "10:30": 50}
    assert p0_checks.onset_and_recovery(speeds) == ("09:05", "10:10")    # 10:00 dips again at 10:05
    rows = [{"detector_id": d, "time": f"2026-05-15T{t}:00+08:00", "observed_kmh": v, "simulated_kmh": v - 30 * (t == "10:10")}
            for d in p0_checks.QUEUE_DETECTORS for t, v in speeds.items()]
    timing = p0_checks.queue_timing({"speed_bins": rows})
    assert timing["AID01103"]["minutes_late"] == [0, 5]                  # the model's queue lasts one bin longer
