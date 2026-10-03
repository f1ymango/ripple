"""Flow-balance demand for SUMO, on a made-up road: where traffic joins, leaves and what speed each edge takes."""
import datetime as dt

import pytest

from src.loaders.common import HK
from src.twin import flow_balance_demand as fbd


class Lane:
    def __init__(self, edge, index):
        self.edge, self.index = edge, index

    def getID(self):
        return f"{self.edge.id}_{self.index}"

    def getIndex(self):
        return self.index


class Connection:
    def __init__(self, a, i, b, j):
        self.a, self.b = a.lanes[i], b.lanes[j]

    def getFromLane(self):
        return self.a

    def getToLane(self):
        return self.b

    def getViaLaneID(self):
        return f":{self.a.getID()}>{self.b.getID()}"


class Node:
    def __init__(self):
        self.incoming, self.outgoing = [], []

    def getIncoming(self):
        return self.incoming

    def getOutgoing(self):
        return self.outgoing


class Edge:
    def __init__(self, eid, start, end, length, lanes):
        self.id, self.start, self.end, self.length = eid, start, end, length
        self.lanes = [Lane(self, i) for i in range(lanes)]
        self.out = {}
        start.outgoing.append(self)
        end.incoming.append(self)

    getID = lambda self: self.id
    getLength = lambda self: self.length
    getLaneNumber = lambda self: len(self.lanes)
    getLanes = lambda self: self.lanes
    getFunction = lambda self: ""
    allows = lambda self, vclass: True
    getFromNode = lambda self: self.start
    getToNode = lambda self: self.end
    getOutgoing = lambda self: self.out


class Net:
    """feeder -> A [D1] -> B [D2] -> C [D3]; ramp R joins before B; exit X leaves after B."""

    def __init__(self):
        n = [Node() for _ in range(7)]
        spec = {"feeder": (0, 1, 200, 2), "A": (1, 2, 300, 2), "B": (2, 3, 300, 2), "C": (3, 4, 300, 2),
                "R": (5, 2, 150, 1), "X": (3, 6, 100, 1)}
        self.edges = {k: Edge(k, n[a], n[b], length, lanes) for k, (a, b, length, lanes) in spec.items()}
        for a, b, pairs in (("feeder", "A", [(0, 0), (1, 1)]), ("A", "B", [(0, 0), (1, 1)]),
                            ("B", "C", [(0, 0), (1, 1)]), ("R", "B", [(0, 0)]), ("B", "X", [(0, 0)])):
            self.edges[a].out[self.edges[b]] = [Connection(self.edges[a], i, self.edges[b], j) for i, j in pairs]

    def getEdge(self, eid):
        return self.edges[eid]


AUDIT = {"detectors": [{"detector_id": d, "edge_id": e, "position_m": 150.0} for d, e in (("D1", "A"), ("D2", "B"), ("D3", "C"))],
         "paths": [{"from": "D1", "to": "D2", "edges": ["A", "B"]}, {"from": "D2", "to": "D3", "edges": ["B", "C"]}]}
BEGIN = dt.datetime(2026, 5, 15, 7, 30, tzinfo=HK)


def _inputs(**changes):
    doc = {"day": "2026-05-15", "ordinary_days": ["2026-05-08"], "speeds": "ordinary mornings only",
           "demand_setting_detectors": ["D1"], "demand_steps_from": BEGIN.isoformat(), "demand_step_s": 900,
           "entries": {"toy": {"detector": "D1", "veh_h": [1200.0, 1200.0]}},
           "pairs": [{"chain": "toy", "up": "D1", "down": "D2", "up_veh_h": 1200, "down_veh_h": 1500,
                      "join_veh_h": 300.0, "exit_share": 0.0},
                     {"chain": "toy", "up": "D2", "down": "D3", "up_veh_h": 1500, "down_veh_h": 1125,
                      "join_veh_h": 0.0, "exit_share": 0.25}],
           "speed_profile_minutes": 15,
           "speed_profile_kmh": {d: {"07:30": v, "07:45": v / 2} for d, v in (("D1", 60.0), ("D2", 40.0), ("D3", 80.0))}}
    doc.update(changes)
    return doc


def _build(monkeypatch, inputs=None, **kw):
    monkeypatch.setattr(fbd, "CHAINS", {"toy": ["D1", "D2", "D3"]})
    return fbd.build(inputs or _inputs(), Net(), AUDIT, BEGIN, 1800, **kw)


def _per_hour(routes):
    """{route: vehicles per hour} over the half hour built."""
    out = {}
    for f in routes.findall("flow"):
        edges = f.find("route").get("edges")
        vehicles = float(f.get("number")) if f.get("number") else float(f.get("period")[4:-1]) * 900
        out[edges] = out.get(edges, 0) + vehicles * 2
    return out


def test_traffic_joins_by_the_ramp_and_leaves_by_the_exit_in_the_measured_shares(monkeypatch):
    routes, _, report = _build(monkeypatch)
    flows = _per_hour(routes)
    assert flows == pytest.approx({"A B C": 900, "A B X": 300, "R B C": 225, "R B X": 75}, abs=2)   # whole vehicles
    # past D1: 1,200; past D2: 1,500; past D3: 1,125 -- the three detector flows given
    assert flows["A B C"] + flows["A B X"] == 1200
    assert flows["A B C"] + flows["R B C"] == pytest.approx(1125, abs=2)
    assert report["notes"] == [] and report["vehicles_expected"] == 750


def test_entry_traffic_comes_in_on_the_first_edge_when_its_detector_is_far_enough_in(monkeypatch):
    _, _, report = _build(monkeypatch)
    assert report["plan"]["toy"]["origins"][0] == {"kind": "entry", "start": 0, "prefix": [], "weight": 1.0}


def test_entry_traffic_comes_in_on_the_road_before_when_the_detector_is_at_the_edge_start(monkeypatch):
    near = {**AUDIT, "detectors": [{**AUDIT["detectors"][0], "position_m": 5.0}] + AUDIT["detectors"][1:]}
    monkeypatch.setattr(fbd, "CHAINS", {"toy": ["D1", "D2", "D3"]})
    routes, additional, report = fbd.build(_inputs(), Net(), near, BEGIN, 1800)
    assert report["plan"]["toy"]["origins"][0]["prefix"] == ["feeder"]
    assert "feeder A B C" in _per_hour(routes)
    assert report["speed_detector_by_edge"]["feeder"] == "D1"            # the road before leads to D1


def test_a_change_with_no_ramp_to_carry_it_goes_on_the_main_line_and_is_reported(monkeypatch):
    pairs = [{"chain": "toy", "up": "D1", "down": "D2", "up_veh_h": 1200, "down_veh_h": 900,
              "join_veh_h": 0.0, "exit_share": 0.25},                    # no exit between D1 and D2
             {"chain": "toy", "up": "D2", "down": "D3", "up_veh_h": 900, "down_veh_h": 920,
              "join_veh_h": 20.0, "exit_share": 0.0}]                    # no ramp between D2 and D3, and small
    routes, _, report = _build(monkeypatch, _inputs(pairs=pairs))
    assert _per_hour(routes) == {"A": 300, "A B C": 900}
    assert "D1->D2: -25.0% leaves on the main line" in report["notes"][0]
    assert "D2->D3: +20 veh/h left out" in report["notes"][1]


def test_each_edge_takes_the_speed_of_the_detector_it_leads_to_by_quarter_hour(monkeypatch):
    _, additional, report = _build(monkeypatch)
    assert report["speed_detector_by_edge"] == {"A": "D1", "B": "D2", "C": "D3", "feeder": "D1"}
    signs = {v.get("id"): v for v in additional.findall("variableSpeedSign")}
    assert [(s.get("time"), s.get("speed")) for s in signs["vss_B"].findall("step")] == [("0", "11.11"), ("900", "5.56")]
    # the junction lanes out of A move at A's speed: traffic changes speed on the next edge
    assert signs["vss_A"].get("lanes") == "A_0 A_1 :A_0>B_0 :A_1>B_1"


def test_speeds_can_be_left_out(monkeypatch):
    _, additional, report = _build(monkeypatch, speeds=False)
    assert additional.findall("variableSpeedSign") == [] and report["speeds"] == "none"


def test_a_small_flow_is_given_random_arrivals_so_rounding_adds_no_bias(monkeypatch):
    routes, _, _ = _build(monkeypatch, _inputs(entries={"toy": {"detector": "D1", "veh_h": [20.0, 20.0]}}))
    small = [f for f in routes.findall("flow") if f.find("route").get("edges") == "A B X"]
    assert all(f.get("period", "").startswith("exp(") and f.get("number") is None for f in small)
