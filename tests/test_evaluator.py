"""E: lane mapping, closure timing, metrics read from simulator output, and the provenance-bound result.

No SUMO needed: the simulator is replaced by mock output files written here.
"""
import json
import shutil
import sys
import types
from pathlib import Path

import pytest

from src.briefing.schema import RESULT_SCHEMA
from src.evaluation_provenance import sidecar_path, verify_result
from src.evaluator import metrics, od_demand, run, scenario as scenarios, simulate
from src.generation import load_json, validate

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


def write_mock_output(work):
    work = Path(work)
    (work / "tripinfo.xml").write_text("<tripinfos>" + "".join(
        f'<tripinfo id="{i}" depart="{d}" departDelay="{w}" arrival="{a}" duration="{t}" timeLoss="{loss}">'
        f'<emissions CO2_abs="{co2}"/></tripinfo>' for i, d, w, a, t, loss, co2 in TRIPS) + "</tripinfos>")
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


def mock_run(complete=True):
    def fake(scenario, files, work, clearance_min, on_step=None):
        simulate.prepare(scenario, files, work)
        write_mock_output(work)
        return {"complete": complete, "final_time_seconds": 900 if complete else 450,
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
        return run.evaluate(plans, plan_id, scenario, 0.5, 5.0,
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
    assert scenarios.run_id(scenario, "P0", 0.5, 5.0) == "mock_P0_c50_t5_mock-closure"


def test_scenario_must_resolve_unspecified_lanes(tmp_path):
    scenario = load_json(MOCK / "mock_scenario.json")
    scenario["closure"]["phases"][0]["lanes"] = ["unspecified"]
    path = tmp_path / "mock_unspecified.json"
    path.write_text(json.dumps(scenario))
    with pytest.raises(ValueError, match="unspecified"):
        scenarios.load(path)


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
    simulate.prepare(scenario, files, tmp_path / "work")
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


def test_validation_rounding_never_turns_a_miss_into_a_pass():
    assert metrics.validation({"geh_under_5_percent": 84.999, "speed_mape_percent": 15.001}) == {
        "geh_under_5_pct": 84.99, "speed_mape_pct": 15.01}


def test_expected_demand_over_the_closed_edge_by_exit():
    totals = od_demand.expected_by_exit(MOCK / "mock_routes.rou.xml", "closed", 300, 600)
    assert totals == {"out": pytest.approx(3.0), "side_out": pytest.approx(3.0)}


# --- the provenance-bound result -------------------------------------------------------

def test_p0_result_meets_the_contract_and_its_sidecar_verifies(evaluate, plans, tmp_path):
    result, report, path = evaluate()
    validate(result, RESULT_SCHEMA)
    assert path == tmp_path / "results" / "runs" / "mock_P0_c50_t5_mock-closure.json"
    assert load_json(path) == result
    assert result["scenario"] == {"compliance": 0.5, "clearance_min": 5.0, "seed": 42}
    assert result["metrics"]["delay_vs_do_nothing_pct"] == 0
    assert result["validation"] == {"geh_under_5_pct": 100.0, "speed_mape_pct": 0.0}
    files = verify_result(path, result, load_json(plans / "P0.json"), load_json(plans / "generation-inputs.json"))
    assert {"network", "routes", "detector_loops", "observations", "scenario",
            "code:src/evaluator/metrics.py", "code:src/twin/evaluate.py"} <= set(files)
    assert report["validation_targets_met"] is True
    assert report["assumptions"] and report["metric_definitions"]["max_queue_m"]
    assert (tmp_path / "results" / "evaluator" / "mock_P0_c50_t5_mock-closure.report.json").is_file()


def test_results_are_never_overwritten(evaluate):
    evaluate()
    with pytest.raises(ValueError, match="never overwritten"):
        evaluate()


def test_unfinished_run_writes_no_result(evaluate, tmp_path, monkeypatch):
    monkeypatch.setattr(simulate, "run", mock_run(complete=False))
    with pytest.raises(RuntimeError, match="no result written"):
        evaluate()
    assert not (tmp_path / "results").exists()


def test_plans_with_actions_are_refused_until_they_are_modelled(evaluate, tmp_path):
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
