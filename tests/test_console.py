"""Console (component G) — the colour ramp, the labels, and the grey fallbacks.

The snapshot CSVs the console reads are not committed (the data layer writes
them into data/ on demand), so the tests here build one from the real detector
snapshot in tests/fixtures/ and write it to tmp_path. Nothing is invented: the
rows are the fixture's own readings, binned by the real loader. Where a test
needs blank speeds it blanks the column deliberately — that is the condition
under test, and is exactly what the loader emits when no vehicle crossed the
loop (docs/02-data.md section 7).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from src.console import app
from src.loaders import common, detectors

FIXTURES = Path(__file__).parent / "fixtures"
REAL_DETECTORS_CSV = Path(__file__).resolve().parents[1] / "data" / "detectors.csv"


def _binned(bin_minutes: int) -> list[dict]:
    """Real fixture readings, binned at the requested width by the real loader."""
    rows = detectors.parse_snapshot(
        (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes())
    return detectors.bin_window(rows, bin_minutes)


def _snapshot(dir_: Path, name: str, bin_minutes: int = 5,
              blank_speeds: bool = False) -> Path:
    rows = _binned(bin_minutes)
    if blank_speeds:
        rows = [{**r, "speed_kmh": ""} for r in rows]
    return common.write_csv(rows, dir_ / name)


@pytest.fixture
def data_dir(tmp_path, monkeypatch) -> Path:
    """A stand-in data/ directory the console reads instead of the real one."""
    shutil.copy(REAL_DETECTORS_CSV, tmp_path / "detectors.csv")
    monkeypatch.setenv("RIPPLE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(app, "DATA_DIR", tmp_path)
    monkeypatch.setattr(app, "DETECTORS_CSV", tmp_path / "detectors.csv")
    monkeypatch.setattr(app, "SPEED_GLOB", str(tmp_path / "detector_5min_*.csv"))
    return tmp_path


def _run(script_timeout: int = 60):
    from streamlit.testing.v1 import AppTest

    root = Path(__file__).resolve().parents[1]
    return AppTest.from_file(str(root / "src" / "console" / "app.py")).run(
        timeout=script_timeout)


# --- colour ramp ----------------------------------------------------------

def test_unknown_speed_is_grey_never_a_colour():
    assert app.speed_to_colour(None) == app.GREY
    assert app.speed_to_colour(float("nan")) == app.GREY
    assert app.speed_to_colour(pd.NA) == app.GREY


def test_free_flow_is_green_and_a_stop_is_red():
    stopped = app.speed_to_colour(0.0)
    free = app.speed_to_colour(app.FREE_FLOW_KMH)
    assert stopped[0] == 255 and stopped[1] == 0
    assert free[0] == 0 and free[1] == 180


def test_ramp_is_clamped_at_both_ends():
    assert app.speed_to_colour(app.FREE_FLOW_KMH * 2) == \
        app.speed_to_colour(app.FREE_FLOW_KMH)
    assert app.speed_to_colour(-10.0) == app.speed_to_colour(0.0)


def test_slower_is_redder_and_never_grey():
    ramp = [app.speed_to_colour(s) for s in (10.0, 30.0, 50.0)]
    assert [c[0] for c in ramp] == sorted([c[0] for c in ramp], reverse=True)
    assert app.GREY not in ramp


# --- bin width ------------------------------------------------------------

@pytest.mark.parametrize("width", [5, 15])
def test_bin_width_comes_from_the_csv_column(tmp_path, width):
    path = _snapshot(tmp_path, f"detector_5min_w_b{width}.csv", bin_minutes=width)
    assert app.bin_minutes(app.load_speeds(str(path))) == width


def test_bin_width_is_unknown_rather_than_guessed():
    assert app.bin_minutes(pd.DataFrame({"bin_start": ["x"]})) is None
    assert app.bin_minutes(pd.DataFrame({"bin_minutes": [5, 15]})) is None


def test_slider_is_labelled_with_the_real_width_not_the_filename(data_dir):
    # The loader names a 15-minute export detector_5min_..._b15.csv: the stem
    # says 5, the column says 15, and the label has to follow the column.
    _snapshot(data_dir, "detector_5min_20260921-0800_0900_b15.csv", bin_minutes=15)
    at = _run()
    assert not at.exception
    assert at.select_slider[0].label == "15-minute bin"


# --- snapshot dropdown ----------------------------------------------------

def test_filtered_exports_are_labelled_and_listed_after_full_windows(data_dir):
    full = _snapshot(data_dir, "detector_5min_20260921-0800_0900_b5.csv")
    filtered = _snapshot(data_dir, "detector_5min_20260921-0800_0900_b5_cov40.csv")
    assert app.find_speed_files() == [str(full), str(filtered)]
    assert "filtered: coverage ≥ 40%" in app.label_speed_file(str(filtered))
    assert "filtered" not in app.label_speed_file(str(full))


def test_any_coverage_threshold_is_recognised_not_just_40():
    name = "data/detector_5min_20260921-0800_0900_b5_cov25.csv"
    assert app.coverage_threshold(name) == 25
    assert "filtered: coverage ≥ 25%" in app.label_speed_file(name)
    assert app.coverage_threshold(name.replace("_cov25", "")) is None


def test_label_separates_snapshots_that_differ_only_by_bin_width():
    five = app.label_speed_file("detector_5min_20260921-0800_0900_b5.csv")
    fifteen = app.label_speed_file("detector_5min_20260921-0800_0900_b15.csv")
    assert five != fifteen
    assert "21/09 08:00–09:00" in five and "5 min" in five and "15 min" in fifteen


# --- grey fallbacks -------------------------------------------------------

def test_blank_speeds_are_dropped_rather_than_read_as_zero(tmp_path):
    path = _snapshot(tmp_path, "detector_5min_quiet_b5.csv", blank_speeds=True)
    assert app.load_speeds(str(path)).empty


def test_snapshot_with_no_usable_speed_greys_the_map_instead_of_crashing(data_dir):
    # Regression: bins was empty, so bins[-1] raised IndexError before the page
    # rendered. A quiet night window is a real reading, not a fault.
    _snapshot(data_dir, "detector_5min_20260922-0200_0300_b5.csv", blank_speeds=True)
    at = _run()
    assert not at.exception
    assert not at.select_slider
    said = " ".join(m.value for m in at.info)
    assert "detector_5min_20260922-0200_0300_b5.csv" in said


def test_no_snapshot_at_all_still_draws_the_corridor(data_dir):
    at = _run()
    assert not at.exception
    assert not at.select_slider
    assert "No speed snapshot found" in " ".join(m.value for m in at.info)


def test_a_usable_snapshot_still_colours_the_map(data_dir):
    _snapshot(data_dir, "detector_5min_20260921-0800_0900_b5.csv")
    at = _run()
    assert not at.exception
    assert at.select_slider[0].label == "5-minute bin"
    assert not at.info
