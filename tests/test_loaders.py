"""Tests for the data layer (component A). No network, no LLM.

Fixtures are real archived files, trimmed to the corridor:
  detector_snapshot_20260921-0830.xml  -- archived 08:30, holds 08:21 data
  stn_snapshot_*.xml                   -- three Special Traffic News snapshots
"""
import datetime as dt
import io
from pathlib import Path

import pytest

from src.loaders import candidates, detectors, incidents, lanes, live
from src.loaders.corridor import CORRIDOR_ROAD_NAMES, DETECTOR_IDS, LEG, on_corridor

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


def test_screening_catches_every_shared_corridor_road_name():
    """The loaders' fragments must never miss a road the shared list names."""
    missed = [n for n in CORRIDOR_ROAD_NAMES if n.isascii() and on_corridor(n) is None]
    assert missed == []


def test_chinese_road_names_are_tds_own_not_ours():
    """Rule 4: every Chinese name is copied from TD's detector list, never typed from memory."""
    import csv
    with open("data/detectors.csv", encoding="utf-8", newline="") as f:
        td_names = " ".join(row["road_tc"] for row in csv.DictReader(f))
    assert [n for n in CORRIDOR_ROAD_NAMES if not n.isascii() and n not in td_names] == []


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


def test_wider_bins_multiply_the_samples_behind_a_count():
    """The archive keeps <50% of minutes, so widening a bin is the cheapest way
    to make a count precise: same data, more of it behind each number."""
    base = dt.datetime(2026, 9, 21, 8, 0, tzinfo=HK)
    rows = [{"timestamp": base + dt.timedelta(minutes=m), "detector_id": "AID01107",
             "direction": "", "lane": "Fast Lane", "speed_kmh": 40.0, "volume": 10.0,
             "occupancy_pct": 10.0, "speed_sd": 0, "period_s": 30.0, "valid": True}
            for m in (0, 4, 7, 12)]

    five = detectors.bin_window(rows, 5)
    fifteen = detectors.bin_window(rows, 15)

    assert len(five) == 3 and len(fifteen) == 1
    assert max(b["periods_observed"] for b in five) == 2
    assert fifteen[0]["periods_observed"] == 4          # every sample in one bin
    assert fifteen[0]["bin_minutes"] == 15
    assert fifteen[0]["coverage_pct"] == 13             # 4 x 30s of 900s
    # The rate is the same either way -- only the precision changed.
    assert fifteen[0]["flow_veh_h"] == 1200


def test_bin_width_must_divide_an_hour():
    with pytest.raises(ValueError, match="divisor of 60"):
        detectors.bin_window([], 7)


def test_bins_report_a_flow_rate_not_a_partial_sum():
    """Archive coverage is ~47% of minutes, so a five-minute bin holds one or two
    sampled periods. Summing raw volume would understate flow by about half."""
    base = dt.datetime(2026, 9, 21, 8, 0, tzinfo=HK)
    rows = [
        {"timestamp": base, "detector_id": "AID01107", "direction": "North East",
         "lane": "Fast Lane", "speed_kmh": 20.0, "volume": 10.0,
         "occupancy_pct": 20.0, "speed_sd": 0.0, "period_s": 30.0, "valid": True},
        {"timestamp": base, "detector_id": "AID01107", "direction": "North East",
         "lane": "Slow Lane", "speed_kmh": 60.0, "volume": 0.0,
         "occupancy_pct": 2.0, "speed_sd": 0.0, "period_s": 30.0, "valid": True},
    ]
    binned = detectors.bin_5min(rows)
    assert len(binned) == 1
    b = binned[0]
    assert b["periods_observed"] == 1                 # one 30-second period
    assert b["coverage_pct"] == 10                    # 30s of the 300s bin
    assert b["flow_veh_h"] == 1200                    # 10 vehicles in 30s
    assert b["count_bin"] == 100                      # what a full bin implies
    assert b["speed_kmh"] == 20.0                     # volume-weighted, not 40.0


def test_offline_lanes_are_counted_not_treated_as_zero_traffic():
    base = dt.datetime(2026, 9, 21, 8, 0, tzinfo=HK)
    rows = [
        {"timestamp": base, "detector_id": "AID01107", "direction": "", "lane": "Fast Lane",
         "speed_kmh": 30.0, "volume": 5.0, "occupancy_pct": 10.0, "speed_sd": 0, "period_s": 30.0, "valid": True},
        {"timestamp": base, "detector_id": "AID01107", "direction": "", "lane": "Slow Lane",
         "speed_kmh": None, "volume": None, "occupancy_pct": None, "speed_sd": 0, "period_s": 30.0, "valid": False},
    ]
    b = detectors.bin_5min(rows)[0]
    assert b["lanes_valid"] == 1 and b["lanes_offline"] == 1
    # The slow lane never reported, so the detector's total is unknown -- not
    # the fast lane's 600 veh/h passed off as the whole road. (This test used to
    # assert 600, which pinned review item 1 as correct behaviour.)
    assert b["flow_veh_h"] == "" and b["count_bin"] == ""
    assert b["lane_completeness_pct"] == 50


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
            "speed_kmh": speed, "flow_veh_h": 1200, "count_bin": 100,
            "occupancy_pct": 10, "volume_observed": 10,
            "periods_observed": max(coverage_pct // 10, 0),
            "coverage_pct": coverage_pct, "lane_completeness_pct": 100,
            "lanes_valid": 2, "lanes_offline": 0}


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
    """Pins what the feed actually sends: the order the XML lists lanes in.

    That is NOT carriageway order. The adopted convention (docs/02-data.md
    section 1) is Fast, Middle Lane 2, Middle Lane 1, Slow, offside to nearside,
    so nothing may infer a lane's position from its place in the file. Lanes are
    matched by name; only [E]'s SUMO lane mapping needs positions.

    If TD ever changes these strings or their order, this fails and the open
    question has to be revisited before anything is simulated.
    """
    rows = detectors.parse_snapshot(detector_xml, keep={"AID01217"})
    first_period = min(r["timestamp"] for r in rows)
    lanes = [r["lane"] for r in rows if r["timestamp"] == first_period]
    assert lanes == ["Fast Lane", "Middle Lane 1", "Middle Lane 2", "Slow Lane"]


# --- candidate screening --------------------------------------------------

def _incident(number, new_at, closed_at, duration):
    return {"incident_number": number, "new_at": new_at, "closed_at": closed_at,
            "duration_min": duration, "location_en": "Aberdeen Tunnel",
            "direction_en": "Causeway Bay", "corridor_road": "aberdeen tunnel",
            "left_censored": False, "right_censored": False}


def test_candidate_window_covers_the_pre_incident_hour_and_recovery():
    start, end = candidates.window_for(
        _incident("IN-1", "2026-09-18T18:00:00+08:00", "2026-09-18T19:00:00+08:00", 60))
    assert start.strftime("%H:%M") == "16:30"     # 90 min before NEW
    assert end.strftime("%H:%M") == "20:00"       # 60 min after CLOSED


def test_candidate_window_is_none_when_times_are_censored():
    assert candidates.window_for(_incident("IN-2", "", "", None)) is None


# --- live poller ----------------------------------------------------------

def test_live_filename_comes_from_the_data_not_the_wall_clock(detector_xml):
    """Two polls of an unrefreshed feed must land on the same name, or the
    poller would store duplicates every 30 seconds instead of one per minute."""
    assert live._stamp("detectors", detector_xml) == "20260921-082100"
    assert live._stamp("detectors", detector_xml) == live._stamp("detectors", detector_xml)


def test_live_stn_is_named_by_poll_time_not_by_its_newest_announcement():
    """The newest announcement moves BACKWARD when a CLOSED message disappears,
    so naming by it dropped exactly that snapshot (review item 10). This test
    used to assert the announcement-based name."""
    xml = (FIXTURES / "stn_snapshot_20260918-1828.xml").read_bytes()
    polled = dt.datetime(2026, 9, 23, 12, 0, 5, tzinfo=HK)
    assert live._stamp("stn", xml, polled) == "20260923-120005"


# --- lane identity --------------------------------------------------------

def _lane_readings(speed, volume, occupancy, n=80):
    base = dt.datetime(2026, 9, 21, 8, 0, tzinfo=HK)
    return [{"timestamp": base + dt.timedelta(seconds=30 * i), "detector_id": "AID01217",
             "direction": "", "lane": "x", "speed_kmh": speed, "volume": volume,
             "occupancy_pct": occupancy, "speed_sd": 0, "period_s": 30.0, "valid": True}
            for i in range(n)]


def test_length_index_is_occupancy_per_vehicle_times_speed():
    s = lanes.lane_stats(_lane_readings(speed=80.0, volume=4.0, occupancy=3.0))
    assert s["occ_per_vehicle"] == 0.75          # 3.0 / 4.0
    assert s["length_index"] == 60.0             # 0.75 * 80
    assert s["reliable"] is True


def test_a_near_empty_lane_is_marked_unreliable_not_compared():
    """The Slow Lane at 0.4 vehicles a period produces ratios that are pure noise.
    Flagging it is what stops it being read as 'short vehicles'."""
    s = lanes.lane_stats(_lane_readings(speed=73.0, volume=0.4, occupancy=0.3))
    assert s["reliable"] is False


def test_too_few_periods_refuses_to_conclude():
    summary = {"Middle Lane 1": lanes.lane_stats(_lane_readings(80.0, 4.0, 3.0, n=20)),
               "Middle Lane 2": lanes.lane_stats(_lane_readings(75.0, 4.5, 5.6, n=20))}
    assert "cache more data" in lanes.verdict(summary)["conclusion"]


def test_heavier_middle_lane_2_is_recorded_as_disagreeing_but_never_overrides():
    summary = {"Middle Lane 1": lanes.lane_stats(_lane_readings(80.0, 4.0, 3.0)),
               "Middle Lane 2": lanes.lane_stats(_lane_readings(75.0, 4.5, 5.6))}
    result = lanes.verdict(summary)
    assert result["readings_suggest"] == lanes.FILE_ORDER
    assert result["agrees_with_convention"] is False
    assert "convention, which stands" in result["conclusion"]


def test_heavier_middle_lane_1_agrees_with_the_adopted_convention():
    summary = {"Middle Lane 1": lanes.lane_stats(_lane_readings(75.0, 4.5, 5.6)),
               "Middle Lane 2": lanes.lane_stats(_lane_readings(80.0, 4.0, 3.0))}
    result = lanes.verdict(summary)
    assert result["readings_suggest"] == lanes.ADOPTED_ORDER
    assert result["agrees_with_convention"] is True


def test_indistinguishable_middle_lanes_mean_the_ordering_does_not_matter():
    summary = {"Middle Lane 1": lanes.lane_stats(_lane_readings(78.0, 4.0, 3.0)),
               "Middle Lane 2": lanes.lane_stats(_lane_readings(78.0, 4.1, 3.05))}
    result = lanes.verdict(summary)
    assert result["readings_suggest"] is None
    assert "either convention is safe" in result["conclusion"]


def test_two_lane_detector_has_nothing_to_decide():
    summary = {"Fast Lane": lanes.lane_stats(_lane_readings(83.0, 6.0, 4.0)),
               "Slow Lane": lanes.lane_stats(_lane_readings(86.0, 5.0, 3.0))}
    assert "not a 4-lane detector" in lanes.verdict(summary)["conclusion"]


def test_report_presents_evidence_without_overriding_the_spec(tmp_path):
    summary = {"Middle Lane 1": lanes.lane_stats(_lane_readings(80.0, 4.0, 3.0)),
               "Middle Lane 2": lanes.lane_stats(_lane_readings(75.0, 4.5, 5.6))}
    text = lanes.report("AID01217", summary, lanes.verdict(summary),
                        tmp_path / "lane_identity.md")
    assert "evidence from readings, not a statement from the Transport" in text
    assert "adopted convention stands" in text     # the tool never overrides it
    assert " → ".join(lanes.ADOPTED_ORDER) in text


def _bands(m1_index_first, m2_index_first, flip_last=False):
    """Five bands of synthetic readings; optionally make the last band disagree."""
    out = {}
    for i, band in enumerate(lanes.TIME_BANDS):
        m1, m2 = (m2_index_first, m1_index_first) if (flip_last and i == 4) \
            else (m1_index_first, m2_index_first)
        out[band] = {"Middle Lane 1": lanes.lane_stats(_lane_readings(80.0, 4.0, m1)),
                     "Middle Lane 2": lanes.lane_stats(_lane_readings(80.0, 4.0, m2))}
    return out


def test_a_consistent_result_across_every_band_is_reported_as_such():
    summary = {"Middle Lane 1": lanes.lane_stats(_lane_readings(80.0, 4.0, 3.0)),
               "Middle Lane 2": lanes.lane_stats(_lane_readings(75.0, 4.5, 5.6))}
    result = lanes.verdict(summary, _bands(3.0, 5.6))
    assert result["bands_agreeing"] == "5/5"
    assert result["readings_suggest"] == lanes.FILE_ORDER


def test_a_result_that_only_holds_some_of_the_day_refuses_to_conclude():
    """If the heavier lane changes with the hour, the difference is about when we
    looked, not about the lane -- so the tool must withdraw the verdict."""
    summary = {"Middle Lane 1": lanes.lane_stats(_lane_readings(80.0, 4.0, 3.0)),
               "Middle Lane 2": lanes.lane_stats(_lane_readings(75.0, 4.5, 5.6))}
    result = lanes.verdict(summary, _bands(3.0, 5.6, flip_last=True))
    assert result["bands_agreeing"] == "4/5"
    assert result["readings_suggest"] is None
    assert "unresolved" in result["conclusion"]


def test_band_splitting_keeps_readings_in_the_right_hour():
    base = dt.datetime(2026, 9, 21, tzinfo=HK)
    readings = []
    for hour in (2, 8, 12, 18, 22):
        readings += [{**r, "timestamp": base + dt.timedelta(hours=hour, seconds=30 * i)}
                     for i, r in enumerate(_lane_readings(80.0, 4.0, 3.0, n=2))]
    bands = lanes.by_time_band({"Middle Lane 1": readings})
    assert sorted(bands) == sorted(lanes.TIME_BANDS)
    assert all(b["Middle Lane 1"]["periods"] == 2 for b in bands.values())


# --- review fixes (PR #2 review, 23 Sep) ---------------------------------

def _periods(n, lanes, start=dt.datetime(2026, 9, 21, 8, 0, tzinfo=HK)):
    """n consecutive 30-second periods; `lanes` maps lane name -> valid flag."""
    return [{"timestamp": start + dt.timedelta(seconds=30 * i), "detector_id": "AID01107",
             "direction": "", "lane": lane, "speed_kmh": 50.0 if ok else None,
             "volume": 10.0 if ok else None, "occupancy_pct": 10.0 if ok else None,
             "speed_sd": 0, "period_s": 30.0, "valid": ok}
            for i in range(n) for lane, ok in lanes.items()]


def test_review_1_offline_lane_no_longer_halves_the_count():
    both = detectors.bin_window(_periods(10, {"Fast Lane": True, "Slow Lane": True}))[0]
    slow_down = detectors.bin_window(_periods(10, {"Fast Lane": True, "Slow Lane": False}))[0]
    assert both["count_bin"] == 200 and both["lane_completeness_pct"] == 100
    # Before the fix: count 100, coverage 100, and it passed the calibration filter.
    assert slow_down["count_bin"] == ""
    assert slow_down["lane_completeness_pct"] == 50
    assert detectors.usable_for_calibration([slow_down]) == []


def test_review_1_a_lane_that_flickers_is_rated_on_its_own_valid_seconds():
    rows = _periods(10, {"Fast Lane": True, "Slow Lane": True})
    for r in rows:                        # slow lane offline for the first 5 periods
        if r["lane"] == "Slow Lane" and r["timestamp"].second + 60 * r["timestamp"].minute < 150:
            r.update(valid=False, volume=None, speed_kmh=None, occupancy_pct=None)
    b = detectors.bin_window(rows)[0]
    # 10 veh per 30 s in each lane, whichever periods it reported: still 200.
    assert b["count_bin"] == 200
    assert b["lane_completeness_pct"] == 75


def test_review_2_detector_outage_is_not_an_archive_gap():
    b = detectors.bin_window(_periods(10, {"Fast Lane": False, "Slow Lane": False}))[0]
    assert b["periods_observed"] == 10 and b["coverage_pct"] == 100   # archive delivered
    assert b["lane_completeness_pct"] == 0                             # sensors did not
    assert b["count_bin"] == ""
    assert detectors.usable_for_calibration([b]) == []


@pytest.mark.parametrize("width", [0, -5, 7])
def test_review_4_bin_width_must_be_a_positive_divisor_of_60(width):
    with pytest.raises(ValueError, match="positive divisor of 60"):
        detectors.bin_window(_periods(10, {"Fast Lane": True}), width)


def test_extra_fifteen_minute_request_returns_fifteen_minutes(monkeypatch):
    stamps = [f"08:{m:02d}:{s:02d}" for m in range(15, 31) for s in (0, 30)][:-1]  # to 08:30:00
    def snap(hms):
        ends = (dt.datetime.strptime(hms, "%H:%M:%S") + dt.timedelta(seconds=30)).strftime("%H:%M:%S")
        return (f"<raw_speed_volume_list><date>2026-09-21</date><periods><period>"
                f"<period_from>{hms}</period_from><period_to>{ends}</period_to><detectors><detector>"
                f"<detector_id>AID01107</detector_id><direction>East</direction><lanes><lane>"
                f"<lane_id>Fast Lane</lane_id><speed>50</speed><occupancy>10</occupancy>"
                f"<volume>10</volume><s.d.>0</s.d.><valid>Y</valid></lane></lanes></detector>"
                f"</detectors></period></periods></raw_speed_volume_list>").encode()
    monkeypatch.setattr(detectors, "window_timestamps", lambda a, b: stamps)
    monkeypatch.setattr(detectors.archive, "iter_snapshots",
                        lambda feed, ts: ((t, snap(t)) for t in ts))
    rows = detectors.load_window(dt.datetime(2026, 9, 21, 8, 15, tzinfo=HK),
                                 dt.datetime(2026, 9, 21, 8, 30, tzinfo=HK))
    starts = sorted({b["bin_start"][11:16] for b in detectors.bin_window(rows)})
    assert starts == ["08:15", "08:20", "08:25"]   # was also 08:30, at 10% coverage


def test_review_13_candidates_table_never_prints_none(tmp_path):
    row = {**_incident("IN-13", "2026-09-18T17:00:00+08:00", "2026-09-18T18:00:00+08:00", 40),
           "retrievable_pct": 50, "score": 1.0, "bins": 0, "mean_coverage_pct": 0,
           "usable_pct": 0, "lanes_valid_pct": 0, "speed_drop_kmh": None, "drop_detector": None}
    line = [l for l in candidates.write_markdown([row], tmp_path / "c.md")
            .read_text(encoding="utf-8").splitlines() if "IN-13" in l][0]
    assert "None" not in line and "—%" not in line


# --- review fixes, round 2 (items 3, 6-12, 15, and B) ---------------------

import gzip
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.loaders import archive, common, fetch as fetch_cli

DETECTOR_OK = (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes()
HTML_PAGE = b"<html><body>Service temporarily unavailable</body></html>"


@pytest.fixture
def stub(tmp_path, monkeypatch):
    """A real HTTP server standing in for the archive, with the real retry
    policy minus the backoff wait. `stub.respond(path) -> (status, body)`."""
    class Stub:
        hits: list = []
        respond = staticmethod(lambda path: (200, DETECTOR_OK))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            Stub.hits.append(time.monotonic())
            status, body = Stub.respond(self.path)
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setattr(archive, "ARCHIVE_API", f"http://127.0.0.1:{server.server_address[1]}")
    monkeypatch.setattr(archive, "CACHE_ROOT", tmp_path / "raw")
    monkeypatch.setattr(archive, "RETRY", archive.RETRY.new(backoff_factor=0))
    monkeypatch.setattr(archive, "REQUEST_PAUSE_S", 0.05)
    archive._local.__dict__.pop("session", None)
    yield Stub
    server.shutdown()
    archive._local.__dict__.pop("session", None)


def test_review_3_period_length_comes_from_the_file():
    def snap(frm, to, volume):
        return (f"<raw_speed_volume_list><date>2026-09-21</date><periods><period>"
                f"<period_from>{frm}</period_from><period_to>{to}</period_to><detectors>"
                f"<detector><detector_id>AID01107</detector_id><direction>East</direction>"
                f"<lanes><lane><lane_id>Fast Lane</lane_id><speed>50</speed><occupancy>10"
                f"</occupancy><volume>{volume}</volume><s.d.>0</s.d.><valid>Y</valid></lane>"
                f"</lanes></detector></detectors></period></periods></raw_speed_volume_list>").encode()
    sixty = detectors.parse_snapshot(snap("08:00:00", "08:01:00", 10))
    assert sixty[0]["period_s"] == 60
    assert detectors.bin_window(sixty)[0]["flow_veh_h"] == 600        # was 1200
    midnight = detectors.parse_snapshot(snap("23:59:30", "00:00:00", 10))
    assert midnight[0]["period_s"] == 30                               # wraps, not -86370
    assert detectors.parse_snapshot(snap("08:00:00", "garbled", 10)) == []   # untimed: skipped


def test_review_6_persistent_503_is_an_archive_error_not_a_crash(stub):
    stub.respond = staticmethod(lambda path: (503, b"busy"))
    with pytest.raises(archive.ArchiveUnavailable):
        archive.fetch("detectors", "20990101-0000")
    assert len(stub.hits) == 5                                    # 1 try + 4 retries
    assert not archive.missing_marker("detectors", "20990101-0000").exists()  # retry later
    counts = archive.prefetch("detectors", ["20990101-0001"], workers=1, log=io.StringIO())
    assert counts["failed"] == 1                                  # counted, run continues


def test_review_6_network_failure_is_an_archive_error(monkeypatch, tmp_path):
    monkeypatch.setattr(archive, "ARCHIVE_API", "http://127.0.0.1:9")   # nothing listens
    monkeypatch.setattr(archive, "CACHE_ROOT", tmp_path)
    monkeypatch.setattr(archive, "RETRY", archive.RETRY.new(backoff_factor=0))
    archive._local.__dict__.pop("session", None)
    with pytest.raises(archive.ArchiveUnavailable):
        archive.fetch("detectors", "20990101-0000")
    with pytest.raises(archive.ArchiveUnavailable):
        archive.list_versions("detectors", "2099-01-01", "2099-01-01")
    archive._local.__dict__.pop("session", None)


def test_review_7_an_error_page_served_as_200_is_never_cached(stub):
    stub.respond = staticmethod(lambda path: (200, HTML_PAGE))
    with pytest.raises(archive.ArchiveUnavailable):
        archive.fetch("detectors", "20990101-0000")
    assert archive.read_cached("detectors", "20990101-0000") is None


def test_review_7_an_error_page_cached_before_the_fix_is_dropped_and_refetched(stub):
    path = archive.cache_path("detectors", "20990101-0000")
    path.parent.mkdir(parents=True)
    with gzip.open(path, "wb") as f:
        f.write(HTML_PAGE)
    assert archive.read_cached("detectors", "20990101-0000") is None and not path.exists()
    assert archive.fetch("detectors", "20990101-0000") == DETECTOR_OK   # refetched cleanly


def test_review_7_snapshot_without_periods_has_no_readings():
    xml = b"<raw_speed_volume_list><date>2026-09-21</date></raw_speed_volume_list>"
    assert detectors.parse_snapshot(xml) == []


def test_review_8_a_404_is_recorded_and_never_requested_again(stub):
    stub.respond = staticmethod(lambda path: (404, b"not found"))
    stamps = ["20990101-0100", "20990101-0101", "20990101-0102"]
    first = archive.prefetch("detectors", stamps, workers=1, log=io.StringIO())
    assert first["missing"] == 3 and len(stub.hits) == 3
    gaps = [b - a for a, b in zip(stub.hits, stub.hits[1:])]
    assert min(gaps) >= archive.REQUEST_PAUSE_S                   # polite on 404s too
    second = archive.prefetch("detectors", stamps, workers=1, log=io.StringIO())
    assert second["known_missing"] == 3 and len(stub.hits) == 3   # no new requests
    with pytest.raises(archive.NotArchived):
        archive.fetch("detectors", stamps[0])                     # answered from the marker


def test_review_9_corridor_is_found_in_any_message_not_just_the_first():
    def msg(i, status, when, location, content=""):
        return {"first_seen": "20260918-1700", "last_seen": "20260918-1800",
                "stn": {"ID": str(i), "INCIDENT_NUMBER": "IN-9", "INCIDENT_STATUS_EN": status,
                        "ANNOUNCEMENT_DATE": when, "LOCATION_EN": location, "CONTENT_EN": content}}
    built = incidents.build_incidents({
        "1": msg(1, "NEW", "2026-09-18T17:00:00", "Southern District", "Traffic accident."),
        "2": msg(2, "UPDATED", "2026-09-18T17:10:00", "Aberdeen Tunnel"),
        "3": msg(3, "CLOSED", "2026-09-18T17:40:00", "Aberdeen Tunnel")})
    assert built[0]["corridor_road"] == "aberdeen tunnel"
    assert incidents.usable_corridor_incidents(built) == built


class _FakeResponse:
    def __init__(self, body):
        self.content = body

    def raise_for_status(self):
        pass


def _feed(*announced):
    msgs = "".join(f"<message><ANNOUNCEMENT_DATE>{a}</ANNOUNCEMENT_DATE></message>"
                   for a in announced)
    return f"<list>{msgs}</list>".encode()


@pytest.fixture
def live_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "LIVE_ROOT", tmp_path / "live")
    monkeypatch.setattr(live, "_last_hash", {})
    return tmp_path / "live"


def _poll(monkeypatch, body, second):
    monkeypatch.setattr(live.http, "get", lambda url, timeout: _FakeResponse(body))
    return live.poll_once("stn", dt.datetime(2026, 9, 23, 3, 0, second, tzinfo=HK))


def test_review_10_an_empty_stn_feed_is_stored_once_not_every_poll(monkeypatch, live_dir):
    stored = [_poll(monkeypatch, b"<list></list>", s)[1] for s in (0, 30, 59)]
    assert stored == [True, False, False]
    assert len(list((live_dir / "stn").glob("*.xml.gz"))) == 1   # was one per poll


def test_review_10_a_disappearing_closed_message_is_recorded(monkeypatch, live_dir):
    assert _poll(monkeypatch, _feed("2026-09-23T10:00:00"), 0)[1]
    assert _poll(monkeypatch, _feed("2026-09-23T10:00:00", "2026-09-23T10:30:00"), 30)[1]
    # The CLOSED message vanishes; the newest announcement goes back to 10:00.
    assert _poll(monkeypatch, _feed("2026-09-23T10:00:00"), 59)[1]      # was dropped
    assert len(list((live_dir / "stn").glob("*.xml.gz"))) == 3


def test_review_10_a_restart_does_not_duplicate_the_last_body(monkeypatch, live_dir):
    assert _poll(monkeypatch, _feed("2026-09-23T10:00:00"), 0)[1]
    live._last_hash.clear()                                       # simulate a restart
    assert _poll(monkeypatch, _feed("2026-09-23T10:00:00"), 30)[1] is False


def test_review_10_a_non_xml_live_body_is_refused(monkeypatch, live_dir):
    monkeypatch.setattr(live.http, "get", lambda url, timeout: _FakeResponse(HTML_PAGE))
    with pytest.raises(ValueError):
        live.poll_once("stn")
    assert not (live_dir / "stn").exists()


def test_review_11_first_and_last_seen_span_every_message():
    def rec(i, when, first, last):
        return {"first_seen": first, "last_seen": last,
                "stn": {"ID": str(i), "INCIDENT_NUMBER": "IN-11", "INCIDENT_STATUS_EN": "UPDATED",
                        "ANNOUNCEMENT_DATE": when, "LOCATION_EN": "Aberdeen Tunnel"}}
    row = incidents.build_incidents({
        "1": rec(1, "2026-09-18T17:00:00", "20260918-1700", "20260918-1930"),
        "2": rec(2, "2026-09-18T17:15:00", "20260918-1715", "20260918-1720")})[0]
    assert row["last_seen"] == "20260918-1930"                    # was 1720
    assert row["first_seen"] == "20260918-1700"


@pytest.mark.parametrize("writer", [detectors.write_csv, incidents.write_csv, common.write_csv])
def test_review_12_writing_nothing_says_so_instead_of_index_error(writer, tmp_path):
    with pytest.raises(ValueError, match="no rows to write"):
        writer([], tmp_path / "empty.csv")


def test_review_12_incidents_command_handles_an_empty_window(monkeypatch, capsys):
    monkeypatch.setattr(fetch_cli.incidents, "load", lambda a, b: [])
    fetch_cli.cmd_incidents(type("Args", (), {"start": "2026-09-18", "end": "2026-09-18"}))
    assert "no incidents" in capsys.readouterr().out


def test_review_15_one_definition_of_each_shared_thing():
    assert detectors.HK is incidents.HK is live.HK is fetch_cli.HK is common.HK
    assert candidates.MIN_DURATION_MIN == incidents.MIN_DURATION_MIN == common.MIN_DURATION_MIN
    assert not hasattr(live, "LIVE_URLS")                          # URLs from archive.FEEDS
    assert set(live.LIVE_FEEDS) <= set(archive.FEEDS)


def test_extra_b_censored_incident_has_no_duration_only_an_observed_span():
    row = incidents.build_incidents({"1": {
        "first_seen": "20260918-1817", "last_seen": "20260918-1830",
        "stn": {"ID": "1", "INCIDENT_NUMBER": "IN-B", "INCIDENT_STATUS_EN": "UPDATED",
                "ANNOUNCEMENT_DATE": "2026-09-18T18:17:00", "LOCATION_EN": "Pok Fu Lam Road"}}})[0]
    assert row["duration_min"] == ""                              # was 0
    assert row["new_at"] == "" and row["closed_at"] == ""         # not a guessed start
    assert row["observed_span_min"] == 0 and row["first_announced_at"].startswith("2026-09-18T18:17")
