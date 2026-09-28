"""Demand fit regressions using a minimal route and detector hand-over."""
import csv
import json
import sys
import xml.etree.ElementTree as ET

import pytest

from src.twin import fit_demand


def test_missing_calibration_counts_do_not_become_zero_flow_targets(tmp_path, monkeypatch):
    candidate = tmp_path / "candidates.rou.xml"
    candidate.write_text(
        '<routes><vehicle id="candidate"><route edges="E1"/></vehicle></routes>',
        encoding="utf-8",
    )
    additional = tmp_path / "loops.add.xml"
    with additional.with_suffix(".csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["detector_id", "edge_id"])
        writer.writerows([("observed", "E1"), ("missing", "E1")])

    observations = tmp_path / "detectors.json"
    observations.write_text(json.dumps({
        "interval_seconds": 300,
        "detectors": [
            {"id": "observed", "observations": [{"count": 10}] + [{"count": None}] * 11},
            {"id": "missing", "observations": [{"count": None}] * 12},
        ],
    }), encoding="utf-8")
    output = tmp_path / "fitted.rou.xml"
    config = tmp_path / "scenario.json"
    scenario = {
        "candidate_routes": str(candidate), "network": str(tmp_path / "network.net.xml"),
        "detector_additional": str(additional), "routes": str(output),
        "begin": 0, "end": 7200, "calibration_seconds": 3600,
        "observation_start_sim_seconds": 900, "incident": {"start": 4500},
    }
    config.write_text(json.dumps(scenario), encoding="utf-8")

    class Net:
        def getEdges(self):
            return [type("Edge", (), {"getID": lambda self: "E1"})()]

    monkeypatch.setattr("sumolib.net.readNet", lambda _: Net())
    monkeypatch.setattr(sys, "argv", ["fit_demand", "--config", str(config),
                                     "--detectors", str(observations), "--iterations", "2"])
    fit_demand.main()
    summary = json.loads((tmp_path / "fit-summary.json").read_text(encoding="utf-8"))
    assert summary["target_counts"] == {"observed": 120.0}
    assert summary["predicted_counts"] == {"observed": 120.0}
    assert summary["detectors_without_calibration_counts"] == ["missing"]
    flow = ET.parse(output).getroot().find("flow")
    assert flow.get("number") == "240"
    assert flow.get("departLane") == "best"
    assert flow.get("departPos") == "0"

    scenario["incident"]["start"] = 4200
    config.write_text(json.dumps(scenario), encoding="utf-8")
    with pytest.raises(ValueError, match="overlaps the configured incident"):
        fit_demand.main()
