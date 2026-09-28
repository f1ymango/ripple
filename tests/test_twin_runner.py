"""A staged closure restores lanes and reports whole-run SUMO counters."""
import json
import sys
from types import SimpleNamespace

from src.twin import run_scenario


def test_staged_closure_and_cumulative_statistics(tmp_path, monkeypatch):
    config = tmp_path / "scenario.json"
    config.write_text(json.dumps({
        "network": str(tmp_path / "network.net.xml"),
        "routes": str(tmp_path / "routes.rou.xml"),
        "detector_additional": str(tmp_path / "loops.add.xml"),
        "output_dir": str(tmp_path / "results"),
        "begin": 0, "end": 5, "step_length": 1,
        "max_depart_delay": 60,
        "incident": {"start": 1, "duration_seconds": 3, "edge_id": "E1", "phases": [
            {"offset_seconds": 0, "lane_indices": [0]},
            {"offset_seconds": 2, "lane_indices": "all"},
        ]},
    }), encoding="utf-8")

    class Edge:
        def getLanes(self):
            return [object(), object()]

    class Net:
        def getEdge(self, edge_id):
            assert edge_id == "E1"
            return Edge()

    monkeypatch.setattr("sumolib.net.readNet", lambda _: Net())
    monkeypatch.setattr(run_scenario, "require_command", lambda _: "sumo")
    clock = SimpleNamespace(time=0)
    changes = []
    state = {}

    def set_disallowed(lane, classes):
        changes.append((clock.time, "disallow", lane, bool(classes)))
        state[lane] = list(classes)

    fake_lane = SimpleNamespace(
        getAllowed=lambda _: [], getDisallowed=lambda lane: state.get(lane, []),
        setAllowed=lambda lane, allowed: changes.append((clock.time, "restore", lane, allowed)),
        setDisallowed=set_disallowed,
    )
    fake_simulation = SimpleNamespace(
        getTime=lambda: clock.time,
        getMinExpectedNumber=lambda: 0,
        getPendingVehicles=lambda: ["waiting-a", "waiting-b"],
        getArrivedNumber=lambda: 1,
    )
    command = []

    def start(cmd, **_):
        command.extend(cmd)

    def close():
        path = command[command.index("--statistic-output") + 1]
        with open(path, "w", encoding="utf-8") as stream:
            stream.write('<statistics><vehicles loaded="10" inserted="7" waiting="2"/>'
                         '<teleports total="3" jam="1" yield="0" wrongLane="2"/>'
                         '</statistics>')

    fake_traci = SimpleNamespace(
        start=start, close=close, lane=fake_lane, simulation=fake_simulation,
        simulationStep=lambda: setattr(clock, "time", clock.time + 1),
    )
    monkeypatch.setitem(sys.modules, "traci", fake_traci)
    monkeypatch.setattr(sys, "argv", ["run_scenario", "--config", str(config)])
    run_scenario.main()

    summary = json.loads((tmp_path / "results" / "baseline.run-summary.json").read_text())
    assert summary["steps"] == 5 and summary["scenario_complete"]
    assert summary["vehicles_loaded"] == 10 and summary["vehicles_departed"] == 7
    assert summary["pending_departures"] == 2 and summary["vehicles_arrived"] == 5
    assert summary["teleports_total"] == 3
    assert summary["estimated_dropped_after_departure_delay"] == 1
    assert (1, "disallow", "E1_0", True) in changes
    assert (3, "disallow", "E1_1", True) in changes
    assert (4, "restore", "E1_0", []) in changes
    assert (4, "restore", "E1_1", []) in changes
