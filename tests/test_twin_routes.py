"""Corridor route candidates must follow the registry's travel directions."""
import csv
import json
import sys
import xml.etree.ElementTree as ET

from src.twin import make_routes
from src.loaders.corridor import CHAIN_WESTERN_EASTBOUND, CHAIN_WESTERN_WESTBOUND


def test_western_candidate_trips_stay_on_ordered_carriageways(tmp_path, monkeypatch):
    east = CHAIN_WESTERN_EASTBOUND
    west = CHAIN_WESTERN_WESTBOUND
    handover = tmp_path / "detectors.json"
    handover.write_text(json.dumps({"detectors": [{"id": did} for did in east + west]}),
                        encoding="utf-8")
    additional = tmp_path / "loops.add.xml"
    with additional.with_suffix(".csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["detector_id", "edge_id"])
        writer.writerows((did, f"E_{did}") for did in east + west)
    output = tmp_path / "candidates.rou.xml"
    config = tmp_path / "scenario.json"
    config.write_text(json.dumps({"network": str(tmp_path / "network.net.xml"),
                                  "detector_additional": str(additional),
                                  "candidate_routes": str(output)}), encoding="utf-8")

    class Edge:
        def __init__(self, edge_id):
            self.edge_id = edge_id

        def getID(self):
            return self.edge_id

    class Net:
        def getEdge(self, edge_id):
            return Edge(edge_id)

        def getShortestPath(self, source, destination, **_):
            return [source, destination], 1

    monkeypatch.setattr("sumolib.net.readNet", lambda _: Net())
    monkeypatch.setattr(sys, "argv", ["make_routes", "--config", str(config),
                                     "--detectors", str(handover)])
    make_routes.main()
    actual = {tuple(vehicle.find("route").get("edges").split())
              for vehicle in ET.parse(output).getroot().findall("vehicle")}
    expected = {(f"E_{sequence[i]}", f"E_{sequence[j]}")
                for sequence in (east, west)
                for i in range(len(sequence)) for j in range(i + 1, len(sequence))}
    assert actual == expected
    assert len(actual) == 12
