"""Tests for the data layer (component A). No network, no LLM.

Fixtures are real archived files, trimmed to the corridor:
  detector_snapshot_20260921-0830.xml  -- archived 08:30, holds 08:21 data
  stn_snapshot_*.xml                   -- three Special Traffic News snapshots
"""
import datetime as dt
from pathlib import Path

import pytest

from src.loaders import detectors, incidents
from src.loaders.corridor import DETECTOR_IDS, LEG, on_corridor

FIXTURES = Path(__file__).parent / "fixtures"
HK = dt.timezone(dt.timedelta(hours=8))


@pytest.fixture
def detector_xml() -> bytes:
    return (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes()


# --- corridor -------------------------------------------------------------

def test_corridor_has_28_detectors_across_three_legs():
    assert len(DETECTOR_IDS) == 28
    assert len(set(DETECTOR_IDS)) == 28
    assert {LEG[d] for d in DETECTOR_IDS} == {
        "main_eastbound", "main_westbound", "western_alternative"}


def test_on_corridor_matches_location_and_free_text():
    assert on_corridor("Aberdeen Tunnel") == "aberdeen tunnel"
    assert on_corridor("", "the fast lane of Pok Fu Lam Road is closed") == "pok fu lam road"
    assert on_corridor("San Tin Highway", "near Fairview Park Roundabout") is None


# --- detectors ------------------------------------------------------------

def test_timestamp_comes_from_the_file_not_the_archive_name(detector_xml):
    """The file archived at 08:30 holds 08:21 data. Using the archive name would
    put every reading nine minutes late and quietly wreck the calibration."""
    rows = detectors.parse_snapshot(detector_xml)
    assert {r["timestamp"].strftime("%H:%M:%S") for r in rows} == {"08:21:00", "08:21:30"}


def test_lane_and_direction_are_text_not_codes(detector_xml):
    rows = detectors.parse_snapshot(detector_xml)
    assert {r["lane"] for r in rows} <= {
        "Fast Lane", "Middle Lane", "Middle Lane 1", "Middle Lane 2", "Slow Lane"}
    assert all(not r["direction"].isdigit() for r in rows)


def test_filter_keeps_only_requested_detectors(detector_xml):
    rows = detectors.parse_snapshot(detector_xml, keep={"AID01107"})
    assert rows and {r["detector_id"] for r in rows} == {"AID01107"}


def test_missing_values_are_none_never_zero():
    xml = b"""<raw_speed_volume_list><date>2026-09-21</date><periods><period>
      <period_from>08:00:00</period_from><period_to>08:00:30</period_to><detectors>
      <detector><detector_id>AID01107</detector_id><direction>North East</direction><lanes>
      <lane><lane_id>Fast Lane</lane_id><speed></speed><occupancy></occupancy>
      <volume></volume><s.d.></s.d.><valid>N</valid></lane>
      </lanes></detector></detectors></period></periods></raw_speed_volume_list>"""
    row = detectors.parse_snapshot(xml)[0]
    assert row["speed_kmh"] is None and row["volume"] is None
    assert row["valid"] is False


def test_bins_report_a_flow_rate_not_a_partial_sum():
    """Archive coverage is ~47% of minutes, so a five-minute bin holds one or two
    sampled periods. Summing raw volume would understate flow by about half."""
    base = dt.datetime(2026, 9, 21, 8, 0, tzinfo=HK)
    rows = [
        {"timestamp": base, "detector_id": "AID01107", "direction": "North East",
         "lane": "Fast Lane", "speed_kmh": 20.0, "volume": 10.0,
         "occupancy_pct": 20.0, "speed_sd": 0.0, "valid": True},
        {"timestamp": base, "detector_id": "AID01107", "direction": "North East",
         "lane": "Slow Lane", "speed_kmh": 60.0, "volume": 0.0,
         "occupancy_pct": 2.0, "speed_sd": 0.0, "valid": True},
    ]
    binned = detectors.bin_5min(rows)
    assert len(binned) == 1
    b = binned[0]
    assert b["periods_observed"] == 1                 # one 30-second period
    assert b["coverage_pct"] == 10                    # 30s of the 300s bin
    assert b["flow_veh_h"] == 1200                    # 10 vehicles in 30s
    assert b["count_5min"] == 100                     # what a full bin implies
    assert b["speed_kmh"] == 20.0                     # volume-weighted, not 40.0


def test_offline_lanes_are_counted_not_treated_as_zero_traffic():
    base = dt.datetime(2026, 9, 21, 8, 0, tzinfo=HK)
    rows = [
        {"timestamp": base, "detector_id": "AID01107", "direction": "", "lane": "Fast Lane",
         "speed_kmh": 30.0, "volume": 5.0, "occupancy_pct": 10.0, "speed_sd": 0, "valid": True},
        {"timestamp": base, "detector_id": "AID01107", "direction": "", "lane": "Slow Lane",
         "speed_kmh": None, "volume": None, "occupancy_pct": None, "speed_sd": 0, "valid": False},
    ]
    b = detectors.bin_5min(rows)[0]
    assert b["lanes_valid"] == 1 and b["lanes_offline"] == 1
    assert b["flow_veh_h"] == 600                     # from the valid lane alone


def test_real_snapshot_bins_cleanly(detector_xml):
    rows = detectors.parse_snapshot(detector_xml)
    binned = detectors.bin_5min(rows)
    assert len(binned) == len({r["detector_id"] for r in rows})
    assert all(b["coverage_pct"] <= 100 for b in binned)
    report = detectors.coverage_report(binned)
    assert report["bins"] == len(binned) and report["empty_bins"] == 0


# --- incidents ------------------------------------------------------------

def _messages(name: str) -> list[dict]:
    return incidents.parse_snapshot((FIXTURES / name).read_bytes())


def test_stn_fixture_has_the_fields_the_contract_needs():
    message = _messages("stn_snapshot_20260918-1828.xml")[0]
    for field in ("INCIDENT_NUMBER", "ANNOUNCEMENT_DATE", "INCIDENT_STATUS_EN",
                  "LOCATION_EN", "CONTENT_EN", "ID"):
        assert field in message
    # The two fields docs/02-data.md warns about really are empty here.
    assert message["DISTRICT_EN"] == "" and message["LATITUDE"] == ""


def test_timeline_uses_announcement_dates_for_start_and_clearance():
    def message(msg_id, status, when):
        return {"first_seen": "20260918-1800", "last_seen": "20260918-1900",
                "stn": {"ID": msg_id, "INCIDENT_NUMBER": "IN-26-06874",
                        "INCIDENT_STATUS_EN": status, "ANNOUNCEMENT_DATE": when,
                        "LOCATION_EN": "Pok Fu Lam Road", "CONTENT_EN": ""}}
    built = incidents.build_incidents({
        "1": message("1", "NEW", "2026-09-18T17:30:00"),
        "2": message("2", "UPDATED", "2026-09-18T18:00:00"),
        "3": message("3", "CLOSED", "2026-09-18T18:17:00"),
    })
    assert len(built) == 1
    row = built[0]
    assert row["duration_min"] == 47                  # 17:30 -> 18:17
    assert row["statuses"] == "NEW|UPDATED|CLOSED"
    assert not row["left_censored"] and not row["right_censored"]
    assert row["corridor_road"] == "pok fu lam road"
    assert row["new_at"].endswith("+08:00")           # Hong Kong time, always


def test_incident_without_a_closed_message_is_flagged_not_guessed():
    built = incidents.build_incidents({
        "1": {"first_seen": "20260918-1800", "last_seen": "20260918-1900",
              "stn": {"ID": "1", "INCIDENT_NUMBER": "IN-26-06999",
                      "INCIDENT_STATUS_EN": "NEW",
                      "ANNOUNCEMENT_DATE": "2026-09-18T17:30:00",
                      "LOCATION_EN": "Aberdeen Tunnel", "CONTENT_EN": ""}},
    })
    row = built[0]
    assert row["right_censored"] is True
    assert row["closed_at"] == ""
    assert incidents.usable_corridor_incidents(built) == []


def test_shortlist_excludes_short_and_censored_incidents():
    def incident(number, duration, left=False, right=False):
        return {"incident_number": number, "corridor_road": "aberdeen tunnel",
                "duration_min": duration, "left_censored": left, "right_censored": right}
    rows = [incident("A", 45), incident("B", 5), incident("C", 90, right=True)]
    assert [r["incident_number"] for r in incidents.usable_corridor_incidents(rows)] == ["A"]


# --- coverage warning -----------------------------------------------------

def _bin(detector_id: str, coverage_pct: int, speed: float | str = 50.0) -> dict:
    return {"bin_start": "2026-09-21T08:00:00+08:00", "detector_id": detector_id,
            "speed_kmh": speed, "flow_veh_h": 1200, "count_5min": 100,
            "occupancy_pct": 10, "volume_observed": 10,
            "periods_observed": max(coverage_pct // 10, 0),
            "coverage_pct": coverage_pct, "lanes_valid": 2, "lanes_offline": 0}


def test_calibration_filter_keeps_only_well_observed_bins():
    bins = [_bin("A", 10), _bin("B", 40), _bin("C", 80)]
    kept = detectors.usable_for_calibration(bins)
    assert [b["detector_id"] for b in kept] == ["B", "C"]      # 40 is inclusive


def test_threshold_can_be_relaxed_deliberately():
    bins = [_bin("A", 10), _bin("B", 40)]
    assert len(detectors.usable_for_calibration(bins, min_coverage_pct=10)) == 2


def test_report_always_carries_a_warning_naming_the_usable_count():
    report = detectors.coverage_report([_bin("A", 10), _bin("B", 60)])
    assert report["usable_for_calibration"] == 1
    assert report["usable_pct"] == 50
    assert "ESTIMATE" in report["warning"] and "40%" in report["warning"]


def test_empty_window_warns_rather_than_returning_a_bare_zero():
    report = detectors.coverage_report([])
    assert report["bins"] == 0 and "warning" in report


def test_bias_check_flags_a_speed_gap_between_coverage_groups():
    unbiased = detectors.coverage_bias_check([_bin("A", 10, 50.0), _bin("B", 80, 52.0)])
    assert unbiased["looks_unbiased"] is True

    biased = detectors.coverage_bias_check([_bin("A", 10, 20.0), _bin("B", 80, 60.0)])
    assert biased["mean_speed_gap_kmh"] == 40.0
    assert biased["looks_unbiased"] is False


def test_warning_block_is_hard_to_miss():
    block = detectors.format_warning(detectors.coverage_report([_bin("A", 10)]))
    assert "COVERAGE WARNING" in block and "docs/02-data.md" in block


def test_four_lane_detector_sends_the_expected_lane_names_in_file_order(detector_xml):
    """Pins what the feed actually sends, which is the part we are sure of.

    Whether this file order is also the lanes' order on the carriageway is an
    OPEN QUESTION -- the data-dictionary PDF numbers them Fast, Middle Lane 2,
    Middle Lane 1, Slow, and it is unclear whether that numbering is positional.
    See docs/02-data.md section 1. Nothing in the loaders depends on the answer
    because lanes are matched by name; only [E]'s SUMO lane mapping will.

    If TD ever changes these strings or their order, this fails and the open
    question has to be revisited before anything is simulated.
    """
    rows = detectors.parse_snapshot(detector_xml, keep={"AID01217"})
    first_period = min(r["timestamp"] for r in rows)
    lanes = [r["lane"] for r in rows if r["timestamp"] == first_period]
    assert lanes == ["Fast Lane", "Middle Lane 1", "Middle Lane 2", "Slow Lane"]
