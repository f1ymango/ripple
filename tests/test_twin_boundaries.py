"""Geometry and route-construction regressions; all graphs are mock fixtures."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from src.twin.boundary_routes import build_chain, combine_paths, external_branch
from src.twin.route_crossings import crosses_detector
from src.twin import fit_demand

FIXTURE = Path(__file__).parent / "fixtures" / "mock_boundary_graph.json"


class MockEdge:
    def __init__(self, eid):
        self.eid, self.incoming, self.outgoing = eid, {}, {}

    def getID(self):
        return self.eid

    def getIncoming(self):
        return self.incoming

    def getOutgoing(self):
        return self.outgoing


class MockConnection:
    def getFromLane(self):
        return self

    def getToLane(self):
        return self

    def allows(self, vehicle_class):
        return vehicle_class == "passenger"


@pytest.fixture
def graph():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    edges = {eid: MockEdge(eid) for pair in data["connections"] for eid in pair}
    for source, dest in data["connections"]:
        edges[source].outgoing[edges[dest]] = [MockConnection()]
        edges[dest].incoming[edges[source]] = [MockConnection()]
    return data, edges


@pytest.mark.parametrize("position,depart,arrival,expected", [
    (10, "20", "max", False), (50, "20", "80", True),
    (80, "20", "80", False), (76, "20", "80", False),
    (75, "20", "80", False), (74, "20", "80", True),
    (95, "0", "max", False), (94, "0", "max", True),
    (50, "50", "max", False), (50, "-80", "-10", True),
    (2, "base", "max", False),
])
def test_same_edge_front_must_enter_and_rear_must_clear(graph, position, depart, arrival, expected):
    data, _ = graph
    assert crosses_detector(["a"], "a", position, data["lengths"], depart, arrival) is expected


def test_intermediate_edge_and_invalid_positions(graph):
    data, _ = graph
    assert crosses_detector(["a", "b", "c"], "b", 99, data["lengths"], "90", "10")
    assert not crosses_detector(["a", "c"], "b", 50, data["lengths"])
    with pytest.raises(ValueError, match="endpoint position"):
        crosses_detector(["a"], "a", 50, data["lengths"], "free")
    with pytest.raises(ValueError, match="Repeated-edge"):
        crosses_detector(["a", "b", "a"], "a", 50, data["lengths"])


def test_existing_entry_exit_connections_and_cycle_rejection(graph):
    data, edges = graph
    spine = [edges[e] for e in data["spine"]]
    entry = external_branch(edges["join"], set(data["spine"]), True, set())
    assert [e.getID() for e in entry] == ["side", "join"]
    assert external_branch(edges["bypass"], set(data["spine"]), True, set()) == []
    assert external_branch(edges["cycle1"], set(data["spine"]), True, set()) == []
    paths = combine_paths(spine, [(0, [edges["up"]]), (1, entry)],
                          [(1, [edges["exit"]]), (2, [edges["down"]])])
    assert ("side", "join", "b", "exit") in paths
    assert ("up", "a", "b", "c", "down") in paths
    assert len(paths) == 4
    assert combine_paths(spine, [(0, [edges["side"]])], [(2, [edges["down"]])]) == []


def test_net_flow_evidence_selects_real_branches(graph):
    data, edges = graph

    class MockNet:
        def getEdge(self, eid):
            return edges[eid]

        def getShortestPath(self, source, dest, **kwargs):
            ordered = [edges[e] for e in data["spine"]]
            return ordered[ordered.index(source):ordered.index(dest) + 1], 1

    paths, audit = build_chain(MockNet(), data["chain"], data["mapping"])
    assert ("side", "join", "b", "exit") in paths
    assert audit["unresolved_net_changes"] == []
    data["chain"]["steps"][0]["margin_veh_h"] = 200
    paths, _ = build_chain(MockNet(), data["chain"], data["mapping"])
    assert not any("side" in path for path in paths)


def test_fitter_preserves_positions_and_conserves_emitted_demand(tmp_path, monkeypatch):
    data = json.loads((FIXTURE.parent / "mock_position_demand.json").read_text(encoding="utf-8"))
    candidate = tmp_path / "mock_candidates.rou.xml"
    candidate.write_text(data["candidate_xml"], encoding="utf-8")
    additional = tmp_path / "mock_loops.xml"
    additional.with_suffix(".csv").write_text(data["mapping_csv"], encoding="utf-8")
    observations = tmp_path / "mock_observations.json"
    observations.write_text(json.dumps(data["observations"]), encoding="utf-8")
    output = tmp_path / "mock_fitted.rou.xml"
    config = tmp_path / "mock_config.json"
    config.write_text(json.dumps({"candidate_routes": str(candidate), "routes": str(output),
                                 "detector_additional": str(additional), "network": "mock_network",
                                 "begin": 0, "end": 7200, "calibration_seconds": 3600}), encoding="utf-8")

    class MockNet:
        def getEdges(self):
            edge = MockEdge("a")
            edge.getLength = lambda: 100
            return [edge]

    monkeypatch.setattr("sumolib.net.readNet", lambda _: MockNet())
    monkeypatch.setattr(sys, "argv", ["fit_demand", "--config", str(config),
                                     "--detectors", str(observations), "--no-closure"])
    fit_demand.main()
    flow = ET.parse(output).getroot().find("flow")
    assert flow.get("departPos") == "20" and flow.get("arrivalPos") == "80"
    assert flow.get("number") == "240"
    summary = json.loads((tmp_path / "fit-summary.json").read_text(encoding="utf-8"))
    assert summary["route_weights"][0]["crossings"] == ["D2"]
    assert summary["vehicles_generated"] == 240
    assert summary["vehicles_removed_by_origin_suspension_including_rounding"] == 0
