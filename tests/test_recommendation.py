"""Operator recommendations must trace to comparable simulator outputs."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.console import recommendation

FIXTURES = Path(__file__).parent / "fixtures" / "mock_recommendation"


def _inputs():
    objects, errors = recommendation.read_objects(FIXTURES)
    assert not errors
    plans = [item for item in objects if "diversions" in item]
    runs = [item for item in objects if "metrics" in item]
    return runs, plans


def _assess(runs, plans, key=(0.5, 60.0, 42)):
    return recommendation.assess(
        runs, plans, "MOCK-INCIDENT", key,
        result_paths={r["run_id"]: FIXTURES / f"mock_{r['plan_id'].lower()}_result.json"
                      for r in runs},
        generation_inputs=json.loads((FIXTURES / "mock_generation-inputs.json").read_text(encoding="utf-8")),
        results_dir=FIXTURES)


def _copy_inputs(tmp_path):
    results_dir, plans_dir = tmp_path / "results", tmp_path / "plans"
    results_dir.mkdir()
    plans_dir.mkdir()
    for path in FIXTURES.glob("mock_p*.json"):
        shutil.copy(path, (results_dir if "_result" in path.name else plans_dir) / path.name)
    shutil.copy(FIXTURES / "mock_generation-inputs.json", plans_dir / "generation-inputs.json")
    return results_dir, plans_dir


def test_recommendation_uses_complete_matching_runs_and_lowest_simulator_delay():
    runs, plans = _inputs()
    key = (0.5, 60.0, 42)
    assert recommendation.scenarios_for(runs, "MOCK-INCIDENT") == [key]
    selected, reason = _assess(runs, plans, key)
    assert reason == ""
    assert selected["winner"]["plan_id"] == "P2"
    assert selected["baseline"]["run_id"] == "mock_P0_c50_t60"


def test_recommendation_withheld_when_baseline_is_not_validated():
    runs, plans = _inputs()
    runs[0]["validation"]["geh_under_5_pct"] = 66.5
    selected, reason = _assess(runs, plans)
    assert selected is None
    assert "below" in reason


def test_recommendation_rejects_missing_plan_and_mismatched_scenario():
    runs, plans = _inputs()
    selected, reason = _assess(runs, [p for p in plans if p["plan_id"] != "P2"])
    assert selected is None and "P2 plan.json" in reason
    runs[-1]["scenario"]["seed"] = 99
    assert recommendation.scenarios_for(runs, "MOCK-INCIDENT") == []


def test_recommendation_rejects_duplicate_run_instead_of_picking_one():
    runs, plans = _inputs()
    selected, reason = _assess(runs + [runs[1]], plans)
    assert selected is None and "More than one P1" in reason


def test_recommendation_requires_the_plan_constraint_record():
    runs, plans = _inputs()
    plans[1]["constraints_checked"] = []
    selected, reason = _assess(runs, plans)
    assert selected is None and "constraint validation" in reason


def test_console_shows_recommendation_from_result_files(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    from src.console import app

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shutil.copy(Path(__file__).resolve().parents[1] / "data" / "detectors.csv",
                data_dir / "detectors.csv")
    results_dir, plans_dir = _copy_inputs(tmp_path)
    monkeypatch.setenv("RIPPLE_DATA_DIR", str(data_dir))
    monkeypatch.setenv("RIPPLE_RESULTS_DIR", str(results_dir))
    monkeypatch.setenv("RIPPLE_PLANS_DIR", str(plans_dir))
    monkeypatch.setattr(app, "DETECTORS_CSV", data_dir / "detectors.csv")
    monkeypatch.setattr(app, "SPEED_GLOB", str(data_dir / "detector_5min_*.csv"))
    monkeypatch.setattr(app, "INCIDENT_GLOB", str(data_dir / "incidents_*.csv"))
    monkeypatch.setattr(app, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(app, "PLANS_DIR", plans_dir)

    at = AppTest.from_file(str(Path(app.__file__))).run()
    assert not at.exception
    assert any("Coordinated split (P2)" in success.value for success in at.success)
