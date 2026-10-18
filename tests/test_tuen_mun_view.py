"""End-to-end check of the two-case console using frozen Tuen Mun evidence."""
from __future__ import annotations

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "console" / "app.py"
OBSERVATIONS = ROOT / "sim" / "tuen-mun" / "observations_20260415.json"


def _detector_layer(at: AppTest) -> tuple[dict, list[dict]]:
    charts = at.get("deck_gl_json_chart")
    assert len(charts) == 1
    map_json = json.loads(charts[0].proto.json)
    layers = [layer for layer in map_json["layers"]
              if layer["@@type"] == "ScatterplotLayer"]
    assert len(layers) == 1
    return map_json, layers[0]["data"]


def _page_text(at: AppTest) -> str:
    groups = (at.title, at.subheader, at.markdown, at.caption,
              at.info, at.warning, at.success, at.error)
    return "\n".join(str(item.value) for group in groups for item in group)


def test_case_selector_tuen_mun_map_playback_and_frozen_plan(monkeypatch, tmp_path):
    # The Aberdeen default can show a saved briefing. Keep any view audit from
    # this UI test outside the repository while exercising the real app path.
    monkeypatch.setenv("RIPPLE_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    source = json.loads(OBSERVATIONS.read_text(encoding="utf-8"))
    real_detectors = {row["id"]: row for row in source["detectors"]}
    assert len(real_detectors) == 27

    at = AppTest.from_file(str(APP)).run(timeout=90)
    assert not at.exception
    case = next(box for box in at.selectbox if box.label == "Incident case")
    assert case.value.startswith("Aberdeen")
    tuen_mun = next(option for option in case.options
                    if option.startswith("Tuen Mun · IN-26-02615"))
    at = case.select(tuen_mun).run(timeout=90)
    assert not at.exception and not at.error
    assert [title.value for title in at.title] == ["Ripple — Tuen Mun Road"]

    map_json, points = _detector_layer(at)
    assert {point["detector_id"] for point in points} == set(real_detectors)
    for point in points:
        real = real_detectors[point["detector_id"]]
        assert point["latitude"] == real["lat"]
        assert point["longitude"] == real["lon"]
    assert "Aberdeen" not in json.dumps(map_json)
    assert "Aberdeen" not in _page_text(at)

    # Null observed counts cannot imply that no vehicle crossed. The first
    # recorded bin contains unknown readings and must label those as unknown.
    unknown = [point for point in points if point["state"] == "unknown"]
    assert unknown
    assert all(point["speed_label"] == "no reading" for point in unknown)
    assert all(point["speed_label"] != "no vehicle crossed" for point in points)

    text = _page_text(at)
    assert "27 westbound TD detectors" in text
    assert "P2 · advise 11%" in text
    assert "Castle Peak Road" in text
    assert "simulated candidate outcomes, not measured road savings" in text
    assert any(metric.label == "Targeted advice vs no advice" and metric.value == "−4.3%"
               for metric in at.metric)

    slider = at.select_slider[0]
    assert slider.label == "5-minute bin"
    assert len(slider.options) > 1
    first_bin, next_bin = sorted({observation["time"]
                                  for detector in source["detectors"]
                                  for observation in detector["observations"]})[:2]
    assert slider.value == first_bin
    first_speeds = {point["detector_id"]: point["speed_label"] for point in points}
    at = slider.set_value(slider.options[1]).run(timeout=90)
    assert not at.exception and not at.error
    assert at.select_slider[0].value == next_bin
    assert at.session_state.bin_index == 1
    assert "17:05 HKT" in _page_text(at)
    _, later_points = _detector_layer(at)
    later_speeds = {point["detector_id"]: point["speed_label"]
                    for point in later_points}
    assert later_speeds != first_speeds
    assert "Aberdeen" not in _page_text(at)
