"""Detector placement creates the output directory SUMO needs for E1 files."""
import json
import sys

from src.twin import place_detectors


def test_loop_output_directory_exists_before_sumo_runs(tmp_path, monkeypatch):
    class Lane:
        def getIndex(self):
            return 0

        def getID(self):
            return "E1_0"

    class Edge:
        def getLength(self):
            return 10

        def getLanes(self):
            return [Lane()]

        def getID(self):
            return "E1"

    class Net:
        def getEdge(self, edge_id):
            assert edge_id == "E1"
            return Edge()

    monkeypatch.setattr("sumolib.net.readNet", lambda _: Net())
    outputs = tmp_path / "nested" / "results"
    config = tmp_path / "scenario.json"
    config.write_text(json.dumps({
        "network": str(tmp_path / "network.net.xml"),
        "detector_additional": str(tmp_path / "loops.add.xml"),
        "output_dir": str(outputs),
        "osm_output": str(tmp_path / "absent.osm.xml"),
    }), encoding="utf-8")
    handover = tmp_path / "detectors.json"
    handover.write_text(json.dumps({
        "interval_seconds": 300,
        "detectors": [{"id": "MOCK", "edge_id": "E1", "position_m": 5}],
    }), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["place_detectors", "--config", str(config),
                                     "--detectors", str(handover)])
    place_detectors.main()
    assert outputs.is_dir()
    assert (tmp_path / "loops.add.xml").exists()
