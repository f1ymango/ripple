"""Tests for the twin (component C) that need no SUMO install.

They pin the layout: paths resolve from the repo root, generated files stay
under the git-ignored sim/work/, and the scripts call each other as modules.
Detector files here are made up inline and named mock-*.
"""
import json
import subprocess

from src.twin import common, evaluate, run_sensitivity

EXAMPLE = "sim/scenarios/scenario.example.json"


def test_relative_paths_resolve_from_the_repo_root():
    assert common.resolve(EXAMPLE).exists()
    assert common.resolve("src/twin/common.py") == common.ROOT / "src" / "twin" / "common.py"


def test_example_config_follows_the_repo_layout():
    cfg = common.load_json(common.resolve(EXAMPLE))
    # Reviewed, committed files, where docs/03-architecture.md section 2 puts them.
    assert cfg["network"] == "sim/aberdeen.net.xml"
    assert cfg["detector_additional"] == "sim/detectors.add.xml"
    # Everything regenerated lives under the git-ignored sim/work/.
    for key in ("routes", "output_dir", "osm_output"):
        assert cfg[key].startswith("sim/work/"), key


def test_evaluate_compares_simulated_loops_with_observations(tmp_path, monkeypatch):
    (tmp_path / "e1_mock-det.xml").write_text(
        '<detector><interval begin="0.00" end="300.00" nVehContrib="10" meanSpeed="10.00"/></detector>',
        encoding="utf-8")
    observations = tmp_path / "mock_detectors.json"
    observations.write_text(json.dumps({"interval_seconds": 300, "detectors": [
        {"id": "mock-det", "observations": [{"time": "mock", "count": 12, "speed_kmh": 36.0}]}]}),
        encoding="utf-8")
    out = tmp_path / "validation.json"
    monkeypatch.setattr("sys.argv", ["evaluate", "--observations", str(observations),
                                     "--sim", str(tmp_path), "--out", str(out)])
    evaluate.main()

    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["count_bin_n"] == 1 and result["geh_under_5_percent"] == 100
    assert result["speed_mape_percent"] == 0  # 10 m/s is exactly 36 km/h


def test_sensitivity_grid_runs_the_scenario_module_from_the_repo_root(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: calls.append((cmd, kw)))
    monkeypatch.setattr("sys.argv", ["run_sensitivity", "--config", EXAMPLE,
                                     "--plan-routes", "sim/work/routes/mock_plan.rou.xml"])
    run_sensitivity.main()

    assert len(calls) == 9  # 3 compliance levels x 3 clearance times
    cmd, kw = calls[0]
    assert cmd[1:3] == ["-m", "src.twin.run_scenario"] and kw["cwd"] == common.ROOT
