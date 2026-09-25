"""The data layer's hand-over to the twin (A -> C): full slot grids, the
calibration series, and sim/scenarios/detectors.json -- checked against the
twin's own evaluate.py, which lines observations up by position."""
import datetime as dt
import json
import sys
import xml.etree.ElementTree as ET

import pytest

from src.loaders import common, detectors, twin_export
from src.twin import evaluate

HK = common.HK
T0 = dt.datetime(2026, 5, 15, 8, 0, tzinfo=HK)


def reading(at, detector="AID01107", lane="Fast Lane", valid=True, volume=10.0, speed=50.0):
    return {"timestamp": at, "detector_id": detector, "direction": "", "lane": lane,
            "speed_kmh": speed if valid else None, "volume": volume if valid else None,
            "occupancy_pct": 10.0 if valid else None, "speed_sd": 0, "valid": valid,
            "period_s": 30.0}


def minutes_of(detector, first_min, n_periods, **kw):
    return [reading(T0 + dt.timedelta(minutes=first_min, seconds=30 * i), detector, **kw)
            for i in range(n_periods)]


# ---------------------------------------------------------------- the full slot grid

def test_a_full_grid_has_every_slot_of_every_detector_in_order():
    rows = minutes_of("AID01107", 0, 6)                          # 08:00-08:03 only
    grid = detectors.bin_window(rows, 5, start=T0, end=T0 + dt.timedelta(minutes=30),
                                detector_ids=["AID01107", "AID01217"])
    assert len(grid) == 6 * 2
    assert [(b["bin_start"][11:16], b["detector_id"]) for b in grid[:4]] == [
        ("08:00", "AID01107"), ("08:00", "AID01217"), ("08:05", "AID01107"), ("08:05", "AID01217")]
    empty = [b for b in grid if b["periods_observed"] == 0]
    assert len(empty) == 11
    assert all(b["speed_kmh"] == "" and b["count_bin"] == "" and b["coverage_pct"] == 0
               for b in empty)
    report = detectors.coverage_report(grid)
    assert report["empty_bins"] == 11                             # was always 0
    assert report["bins_below_lane_completeness"] == 0            # a gap is not a sensor outage


def test_the_grid_changes_nothing_about_the_bins_that_had_readings():
    rows = minutes_of("AID01107", 0, 10) + minutes_of("AID01107", 12, 4)
    plain = detectors.bin_window(rows, 5)
    grid = detectors.bin_window(rows, 5, start=T0, end=T0 + dt.timedelta(minutes=20),
                                detector_ids=["AID01107"])
    assert [b for b in grid if b["periods_observed"]] == plain
    assert [b["bin_start"][11:16] for b in grid] == ["08:00", "08:05", "08:10", "08:15"]


def test_a_detector_with_no_reading_at_all_still_gets_every_slot():
    grid = detectors.bin_window([], 5, start=T0, end=T0 + dt.timedelta(hours=1))
    assert len(grid) == 12 * len(detectors.DETECTOR_IDS)
    assert {b["detector_id"] for b in grid} == set(detectors.DETECTOR_IDS)


def test_a_start_between_slot_boundaries_starts_at_its_slot():
    starts = detectors.slot_starts(T0.replace(minute=3), T0.replace(minute=12))
    assert [s.strftime("%H:%M") for s in starts] == ["08:00", "08:05", "08:10"]


def test_readings_outside_the_grid_are_not_emitted():
    rows = minutes_of("AID01107", 40, 2)
    grid = detectors.bin_window(rows, 5, start=T0, end=T0 + dt.timedelta(minutes=10),
                                detector_ids=["AID01107"])
    assert [b["periods_observed"] for b in grid] == [0, 0]


@pytest.mark.parametrize("kwargs", [{"start": T0}, {"end": T0},
                                    {"start": T0, "end": T0 + dt.timedelta(minutes=5),
                                     "per_lane": True}])
def test_half_a_grid_or_a_per_lane_grid_is_refused(kwargs):
    with pytest.raises(ValueError):
        detectors.bin_window([], 5, **kwargs)


# ---------------------------------------------------------------- calibration series

def test_the_calibration_series_keeps_every_row_and_blanks_unusable_counts():
    rows = (minutes_of("AID01107", 0, 10)                       # full: 100% coverage
            + minutes_of("AID01107", 5, 2)                      # 1 min of 5: 20%
            + minutes_of("AID01107", 10, 10, valid=False))      # all lanes offline
    grid = detectors.bin_window(rows, 5, start=T0, end=T0 + dt.timedelta(minutes=20),
                                detector_ids=["AID01107"])
    series = detectors.calibration_series(grid)
    assert len(series) == len(grid) == 4
    assert [b["calibration_ok"] for b in series] == [True, False, False, False]
    assert series[0]["count_bin"] == grid[0]["count_bin"] != ""
    assert series[1]["count_bin"] == "" and series[1]["speed_kmh"] == 50.0   # speed survives
    assert len(detectors.usable_for_calibration(grid)) == 1     # the filter is unchanged


# ---------------------------------------------------------------- detectors.json for the twin

def _doc(rows, minutes=30, ids=("AID01104", "AID01107"), **kw):
    return twin_export.build(T0, T0 + dt.timedelta(minutes=minutes), rows=rows,
                             detector_ids=list(ids), **kw)


def test_one_observation_per_slot_starting_at_simulation_time_zero():
    doc = _doc(minutes_of("AID01107", 0, 10) + minutes_of("AID01107", 20, 10))
    assert doc["interval_seconds"] == 300 and doc["source"]["simulation_time_0"] == T0.isoformat()
    for d in doc["detectors"]:
        times = [dt.datetime.fromisoformat(o["time"]) for o in d["observations"]]
        assert times[0] == T0 and len(times) == 6
        assert all(b - a == dt.timedelta(minutes=5) for a, b in zip(times, times[1:]))
    quiet = next(d for d in doc["detectors"] if d["id"] == "AID01104")
    assert all(o["count"] is None and o["speed_kmh"] is None for o in quiet["observations"])
    busy = next(d for d in doc["detectors"] if d["id"] == "AID01107")
    assert [o["count"] is not None for o in busy["observations"]] == [True, False, False, False, True, False]


def test_no_vehicles_is_a_zero_count_and_no_speed_not_a_gap():
    """IN-26-03365: AID01104 carried nothing 09:15-09:55 while all lanes were shut."""
    doc = _doc(minutes_of("AID01107", 0, 10, volume=0.0, speed=None), minutes=5, ids=["AID01107"])
    only = doc["detectors"][0]["observations"][0]
    assert only["count"] == 0 and only["speed_kmh"] is None


def test_the_document_has_every_field_of_the_twins_template():
    template = json.load(open("sim/scenarios/detectors.example.json", encoding="utf-8"))
    doc = _doc(minutes_of("AID01107", 0, 10), minutes=5, ids=["AID01107"])
    assert set(template) <= set(doc)
    assert set(template["detectors"][0]) <= set(doc["detectors"][0])
    assert set(template["detectors"][0]["observations"][0]) <= set(doc["detectors"][0]["observations"][0])
    json.dumps(doc)                                              # serialisable as is


def test_a_hand_filled_edge_mapping_survives_a_rewrite(tmp_path):
    out = tmp_path / "detectors.json"
    first = _doc([], minutes=5)
    first["detectors"][0]["edge_id"], first["detectors"][0]["position_m"] = "E12", 40.5
    twin_export.write(first, out)
    again = _doc([], minutes=5, keep_from=out)
    assert (again["detectors"][0]["edge_id"], again["detectors"][0]["position_m"]) == ("E12", 40.5)
    assert again["detectors"][1]["edge_id"] is None


@pytest.mark.parametrize("start,end,why", [
    (T0.replace(tzinfo=None), T0.replace(tzinfo=None, minute=30), "timezone"),
    (T0, T0, "not after"),
    (T0.replace(minute=3), T0.replace(minute=30), "boundary"),
    (T0, T0.replace(minute=31), "boundary"),
])
def test_bad_windows_are_refused_with_a_reason(start, end, why):
    with pytest.raises(ValueError, match=why):
        twin_export.build(start, end, rows=[])


def test_missing_detector_positions_or_an_unknown_detector_are_refused(monkeypatch, tmp_path):
    with pytest.raises(RuntimeError, match="no position"):
        _doc([], minutes=5, ids=["AID99999"])
    monkeypatch.setattr(twin_export, "DETECTORS_CSV", tmp_path / "nope.csv")
    with pytest.raises(RuntimeError, match="fetch corridor"):
        _doc([], minutes=5)


# ---------------------------------------------------------------- through the twin's evaluate.py

def _sumo_e1(folder, doc, drop_slot=None):
    """E1 output a perfect simulation would write for `doc`, one file per detector."""
    step = doc["interval_seconds"]
    for d in doc["detectors"]:
        root = ET.Element("detector")
        obs = [o for i, o in enumerate(d["observations"]) if i != drop_slot]
        for i, o in enumerate(obs):
            ET.SubElement(root, "interval", begin=f"{i * step:.2f}", end=f"{(i + 1) * step:.2f}",
                          id=d["id"], nVehContrib=str(o["count"] or 0),
                          meanSpeed=str((o["speed_kmh"] or 0) / 3.6))
        ET.ElementTree(root).write(folder / f"e1_{d['id']}.xml")


def _evaluate(tmp_path, monkeypatch, doc, drop_slot=None):
    sim = tmp_path / f"sim{drop_slot}"
    sim.mkdir()
    _sumo_e1(sim, doc, drop_slot)
    obs, out = tmp_path / "detectors.json", tmp_path / f"result{drop_slot}.json"
    twin_export.write(doc, obs)
    monkeypatch.setattr(sys, "argv", ["evaluate", "--observations", str(obs),
                                      "--sim", str(sim), "--out", str(out)])
    evaluate.main()
    return json.loads(out.read_text(encoding="utf-8"))


def test_the_twins_evaluator_lines_our_slots_up_with_its_intervals(tmp_path, monkeypatch):
    rows = [r for m in range(0, 30, 5)
            for r in minutes_of("AID01107", m, 10, volume=float(5 + m))]
    doc = _doc(rows, ids=["AID01107"])
    perfect = _evaluate(tmp_path, monkeypatch, doc)
    assert perfect["count_bin_n"] == twin_export.summary(doc)["with_both"] == 6
    assert all(r["geh"] == 0 for r in perfect["count_bins"])
    # One missing slot -- what a gappy bin list did -- shifts everything after it.
    shifted = _evaluate(tmp_path, monkeypatch, doc, drop_slot=2)
    assert any(r["geh"] > 0 for r in shifted["count_bins"])


def test_the_command_line_refuses_a_bad_window_with_a_message_not_a_traceback(monkeypatch, capsys):
    from src.loaders import fetch
    monkeypatch.setattr(sys, "argv", ["fetch", "twin-detectors", "--start", "2026-05-15T07:53",
                                      "--end", "2026-05-15T10:35"])
    with pytest.raises(SystemExit, match="not on a 5-minute boundary"):
        fetch.main()
