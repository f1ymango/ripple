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
    monkeypatch.setattr(app, "INCIDENT_GLOB", str(tmp_path / "incidents_*.csv"))
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


def test_bin_slider_ticks_show_clock_time_not_the_raw_timestamp():
    assert app.label_bin("2026-09-21T08:20:00+08:00") == "08:20"


def test_an_unparseable_bin_start_is_shown_as_it_came():
    # Better a tick that looks odd than one that quietly invents a time.
    assert app.label_bin("not-a-timestamp") == "not-a-timestamp"


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


# --- what a silent loop means --------------------------------------------
#
# The fixture these use is a real archived snapshot from the demo incident
# (IN-26-03365, Fri 15 May, 09:09:30), trimmed to the corridor detectors the
# same way the 21 Sep fixture was. Nothing in it is edited: AID01104's loops
# report that period and count nobody -- the closure -- while AID01103 is
# crawling at 8 km/h in the queue behind it, and three detectors are absent
# because the archive served nothing for them.

MAY_FIXTURE = FIXTURES / "detector_snapshot_20260515-0916.xml"


def _may_bins(dir_: Path, name: str = "detector_5min_20260515-0905_0910_b5.csv") -> Path:
    rows = detectors.bin_window(
        detectors.parse_snapshot(MAY_FIXTURE.read_bytes()), 5)
    return common.write_csv(rows, dir_ / name)


def test_a_loop_reporting_no_vehicle_is_not_a_missing_reading(tmp_path):
    frame = app.load_bins(str(_may_bins(tmp_path)))
    states = frame.set_index("detector_id")["state"]
    assert states["AID01104"] == "no_vehicles"   # reported, counted nobody
    assert states["AID01103"] == "speed"         # 8 km/h in the queue
    assert app.state_colour("no_vehicles", None) != app.GREY


def test_no_vehicles_is_off_the_speed_ramp_entirely(tmp_path):
    # Otherwise an empty road reads as a speed we never measured.
    empty = app.state_colour("no_vehicles", None)
    ramp = [app.speed_to_colour(s) for s in range(0, 121, 5)]
    assert empty not in ramp


def test_a_detector_the_archive_never_served_is_unknown(tmp_path):
    frame = app.load_bins(str(_may_bins(tmp_path)))
    served = set(frame["detector_id"])
    corridor = set(pd.read_csv(REAL_DETECTORS_CSV)["detector_id"])
    assert corridor - served, "fixture should be missing some detectors"
    assert app.state_colour("unknown", None) == app.GREY


def test_the_label_says_which_kind_of_silence_it_is():
    assert app.state_label("speed", 42.0) == "42 km/h"
    assert app.state_label("no_vehicles", None) == "no vehicle crossed"
    assert app.state_label("unknown", None) == "no reading"


def test_vehicles_without_a_speed_are_unknown_not_an_empty_road():
    # A loop can count vehicles and still time none of them. That is a gap in
    # what we know, not an empty road.
    frame = pd.DataFrame({"speed_kmh": [""], "volume_observed": [7],
                          "periods_observed": [3]})
    assert list(app.bin_state(frame)) == ["unknown"]


def test_bin_state_survives_a_file_without_the_volume_columns():
    frame = pd.DataFrame({"speed_kmh": [31.0, ""]})
    assert list(app.bin_state(frame)) == ["speed", "unknown"]


def test_a_bin_showing_only_an_empty_road_is_still_worth_drawing():
    frame = pd.DataFrame({
        "bin_start": ["2026-05-15T09:05:00+08:00", "2026-05-15T09:10:00+08:00"],
        "speed_kmh": ["", ""], "volume_observed": [0, 4], "periods_observed": [2, 0],
    })
    frame["state"] = app.bin_state(frame)
    # The first bin is a closed road; the second is an archive gap.
    assert app.showable_bins(frame) == ["2026-05-15T09:05:00+08:00"]


def test_evidence_says_how_thin_the_reading_is():
    assert app.evidence_label(1, 40) == "1 vehicle · 40% of the minutes"
    assert app.evidence_label(19, 20) == "19 vehicles · 20% of the minutes"
    assert app.evidence_label(None, None) == ""


# --- playback -------------------------------------------------------------

def test_playback_stops_at_the_end_rather_than_looping():
    assert app.next_index(0, 3) == 1
    assert app.next_index(2, 3) is None
    assert app.next_index(0, 1) is None


def test_the_transport_controls_appear_with_a_window(data_dir):
    _snapshot(data_dir, "detector_5min_20260921-0800_0900_b5.csv")
    at = _run()
    assert not at.exception
    assert {b.label for b in at.button} == {"◀", "▶", "▶|", "|◀"}


def test_pressing_play_on_a_one_bin_window_does_not_hang(data_dir):
    # There is nowhere to advance to, so playback has to switch itself off
    # instead of sleeping and rerunning forever.
    _snapshot(data_dir, "detector_5min_20260921-0800_0900_b5.csv")
    at = _run()
    play = next(b for b in at.button if b.label == "▶")
    at = play.click().run()
    assert not at.exception
    assert at.session_state["playing"] is False
    # And the control says so: it must not still offer to pause a stopped run.
    assert any(b.label == "▶" for b in at.button)


@pytest.mark.parametrize("stop_button", [0, 1, 2, 3])
def test_stopping_playback_immediately_restores_the_play_button(stop_button):
    from streamlit.testing.v1 import AppTest

    # Render only the controls, so autoplay cannot add a rerun that hides a
    # stale button label. Use the real fixture's timestamp, without a timer.
    bins = sorted({row["bin_start"] for row in _binned(5)})
    at = AppTest.from_string(
        "from src.console import app\n"
        f"app.playback_index({bins!r}, 5)\n"
    ).run()
    at = at.button[1].click().run()
    assert not at.exception
    assert at.session_state["playing"] is True
    assert at.button[1].label == "⏸"

    at = at.button[stop_button].click().run()
    assert not at.exception
    assert at.session_state["playing"] is False
    assert at.button[1].label == "▶"


def test_step_buttons_follow_the_time_selected_by_scrubbing():
    from streamlit.testing.v1 import AppTest

    # These timestamps all come from the real archive fixtures. Only the
    # transport controls are under test; no traffic reading is manufactured.
    may = detectors.bin_window(detectors.parse_snapshot(MAY_FIXTURE.read_bytes()), 5)
    bins = sorted({row["bin_start"] for row in may + _binned(5) + _binned(1)})
    assert len(bins) >= 3
    at = AppTest.from_string(
        "from src.console import app\n"
        f"app.playback_index({bins!r}, None)\n"
    ).run()
    at = at.select_slider[0].set_value(bins[1]).run()
    assert at.session_state["bin_index"] == 1

    at = at.button[2].click().run()
    assert not at.exception
    assert at.session_state["bin_index"] == 2
    assert at.select_slider[0].value == bins[2]

    at = at.select_slider[0].set_value(bins[1]).run()
    at = at.button[0].click().run()
    assert not at.exception
    assert at.session_state["bin_index"] == 0
    assert at.select_slider[0].value == bins[0]


# --- the timeline strip ---------------------------------------------------

def test_the_timeline_tracks_the_slowest_detector_not_the_mean(tmp_path):
    # The corridor mean barely moves when one link closes: averaged over 28
    # detectors in both directions, the 15 May queue is a 2 km/h dip. The
    # slowest detector is the series that shows it.
    frame = app.load_bins(str(_may_bins(tmp_path)))
    timeline = app.corridor_timeline(frame)
    assert len(timeline) == 1
    row = timeline.iloc[0]
    assert row["slowest_kmh"] == 8.0 and row["slowest_id"] == "AID01103"
    assert row["no_vehicles"] == 1
    assert row["slowest_kmh"] < frame["speed_kmh"].mean()


def test_a_bin_with_no_speed_at_all_leaves_a_hole_not_a_zero():
    frame = pd.DataFrame({
        "bin_start": ["2026-05-15T09:05:00+08:00"],
        "speed_kmh": [float("nan")], "state": ["no_vehicles"],
    })
    assert pd.isna(app.corridor_timeline(frame).iloc[0]["slowest_kmh"])


def test_no_incident_table_means_no_times_on_the_chart(data_dir):
    assert app.load_incident_markers("2026-05-15T07:55:00+08:00",
                                     "2026-05-15T10:35:00+08:00").empty


def test_incident_markers_are_tds_own_times(data_dir):
    # The real row the loader wrote for the demo incident:
    #   python -m src.loaders.fetch incidents --start 2026-05-15 --end 2026-05-15
    table = pd.DataFrame([{
        "incident_number": "IN-26-03365", "corridor_road": "aberdeen tunnel",
        "new_at": "2026-05-15T09:01:00+08:00",
        "closed_at": "2026-05-15T10:02:00+08:00",
    }, {
        "incident_number": "IN-26-03370", "corridor_road": "aberdeen tunnel",
        "new_at": "2026-05-15T12:40:00+08:00", "closed_at": "",
    }])
    table.to_csv(data_dir / "incidents_2026-05-15_2026-05-15.csv", index=False)

    markers = app.load_incident_markers("2026-05-15T07:55:00+08:00",
                                        "2026-05-15T10:35:00+08:00")
    assert list(markers["label"]) == ["IN-26-03365 reported", "IN-26-03365 cleared"]
    # The afternoon incident is outside the replay window and stays off it.
    assert "IN-26-03370" not in " ".join(markers["label"])


def test_the_chart_is_skipped_rather_than_guessed_when_times_will_not_parse():
    timeline = pd.DataFrame([{"bin_start": "not-a-timestamp", "slowest_kmh": 20.0,
                              "slowest_id": "AID01101", "reporting": 1,
                              "no_vehicles": 0}])
    assert app.timeline_chart(timeline, "not-a-timestamp",
                              pd.DataFrame(columns=["bin_start", "label"])) is None
