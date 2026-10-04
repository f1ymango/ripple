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

    # A reopening flow must not precede another route's time-zero flow.
    candidate.write_text(
        '<routes><vehicle id="a"><route edges="E1"/></vehicle>'
        '<vehicle id="b"><route edges="E2"/></vehicle></routes>', encoding="utf-8")
    monkeypatch.setattr(Net, "getEdges", lambda self: [
        type("Edge", (), {"getID": lambda self, value=value: value})()
        for value in ("E1", "E2")])
    with additional.with_suffix(".csv").open("a", encoding="utf-8") as stream:
        stream.write("second,E2\n")
    data = json.loads(observations.read_text(encoding="utf-8"))
    data["detectors"].append({"id": "second", "observations": [{"count": 10}] * 12})
    observations.write_text(json.dumps(data), encoding="utf-8")
    scenario["incident"].update(edge_id="E1", duration_seconds=600)
    config.write_text(json.dumps(scenario), encoding="utf-8")
    fit_demand.main()
    flows = ET.parse(output).getroot().findall("flow")
    assert [float(item.get("begin")) for item in flows] == [0, 0, 5100]
    assert sum(int(item.get("number")) for item in flows) == 460

    # The no-closure diagnostic conserves the full fitted rate through warm-up
    # and the horizon, even when the scenario describes a later incident.
    monkeypatch.setattr(sys, "argv", ["fit_demand", "--config", str(config),
                                     "--detectors", str(observations), "--no-closure"])
    fit_demand.main()
    flows = ET.parse(output).getroot().findall("flow")
    assert len(flows) == 2
    assert sum(int(item.get("number")) for item in flows) == 480
    assert all(item.get("begin") == "0.00" and item.get("end") == "7200.00" for item in flows)
    summary = json.loads((tmp_path / "fit-summary.json").read_text(encoding="utf-8"))
    assert summary["vehicles_removed_by_origin_suspension_including_rounding"] == 0
    assert summary["vehicles_generated"] == summary["vehicles_before_origin_suspension"]

    scenario["incident"]["start"] = 4200
    config.write_text(json.dumps(scenario), encoding="utf-8")
    with pytest.raises(ValueError, match="overlaps the configured incident"):
        fit_demand.main()
