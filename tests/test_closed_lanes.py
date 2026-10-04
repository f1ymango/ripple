"""The closed-lane rule: what counts as a blocked lane, a full closure, and not enough to say."""
import datetime as dt

from src.loaders import closed_lanes
from src.loaders.common import HK

T0 = dt.datetime(2026, 5, 15, 8, 50, tzinfo=HK)


def _readings(volumes):
    """[(fast, slow), ...] -> lane readings 30 seconds apart, as lane_evidence.by_reading returns them."""
    return [(T0 + dt.timedelta(seconds=30 * i),
             {lane: {"volume": v, "speed_kmh": 50.0 if v else None, "occupancy_pct": 5.0, "period_s": 30.0}
              for lane, v in zip(("Fast Lane", "Slow Lane"), pair)})
            for i, pair in enumerate(volumes)]


ORDINARY = closed_lanes.ordinary_traffic([_readings([(6, 4)] * 20)])     # slow lane carries 40%


def test_ordinary_traffic_gives_each_lane_its_share():
    assert ORDINARY["share"] == {"Fast Lane": 0.6, "Slow Lane": 0.4}
    assert ORDINARY["vehicles_per_reading"] == 10 and ORDINARY["readings"] == 20


def test_a_lane_empty_while_the_other_moves_is_blocked():
    doc = closed_lanes.resolve(_readings([(6, 4), (5, 3), (4, 0), (5, 0), (6, 0), (4, 0), (5, 5)]), ORDINARY)
    assert doc["decision"] == "lanes"
    (phase,) = doc["phases"]
    assert phase["lanes_closed"] == ["Slow Lane"] and phase["readings"] == 4
    assert phase["from"] == (T0 + dt.timedelta(seconds=60)).isoformat()
    assert phase["last_open"] == (T0 + dt.timedelta(seconds=30)).isoformat()      # the onset lies between
    assert phase["next_reading"] == (T0 + dt.timedelta(seconds=180)).isoformat()
    assert phase["vehicles_in_other_lanes"] == 19 and phase["passing_veh_h"] == 570   # 19 in 2 minutes
    assert phase["chance"] == 0.6 ** 19
    assert doc["summary"]["lanes_closed_first"] == ["Slow Lane"] and doc["summary"]["passing_veh_h"] == 570


def test_a_quiet_road_decides_nothing():
    # three readings in a row, but only three vehicles passed: 0.6^3 is about 1 in 5
    doc = closed_lanes.resolve(_readings([(2, 1), (1, 0), (1, 0), (1, 0), (2, 1)]), ORDINARY)
    assert doc["decision"] == "insufficient_evidence" and doc["phases"] == []
    assert "chance" in doc["rejected"][0]["why"]
    assert doc["summary"]["lanes_closed_first"] is None


def test_two_readings_in_a_row_are_too_few_however_busy():
    doc = closed_lanes.resolve(_readings([(6, 4), (20, 0), (20, 0), (6, 4)]), ORDINARY)
    assert doc["decision"] == "insufficient_evidence"
    assert "fewer than 3" in doc["rejected"][0]["why"]


def test_a_lane_then_every_lane():
    doc = closed_lanes.resolve(_readings([(6, 4), (5, 0), (6, 0), (5, 0), (4, 0), (0, 0), (0, 0), (0, 0), (5, 4)]),
                               ORDINARY)
    assert doc["decision"] == "lanes"
    assert [x["lanes_closed"] for x in doc["phases"]] == [["Slow Lane"], "all"]
    s = doc["summary"]
    assert s["all_lanes_from"] == (T0 + dt.timedelta(seconds=150)).isoformat()
    assert s["last_closed_reading"] == (T0 + dt.timedelta(seconds=210)).isoformat()
    assert s["flowing_again_by"] == (T0 + dt.timedelta(seconds=240)).isoformat()


def test_every_lane_empty_from_the_start_is_a_full_closure():
    doc = closed_lanes.resolve(_readings([(0, 0)] * 4 + [(5, 4)]), ORDINARY)
    assert doc["decision"] == "all_lanes" and doc["phases"][0]["lanes_closed"] == "all"
    assert doc["phases"][0]["last_open"] is None                      # the window began closed


def test_an_empty_road_at_night_is_not_a_closure():
    night = closed_lanes.ordinary_traffic([_readings([(1, 0), (0, 0), (0, 1), (0, 0)] * 5)])   # 0.5 per reading
    doc = closed_lanes.resolve(_readings([(1, 0), (0, 0), (0, 0), (0, 0), (0, 1)]), night)
    assert doc["decision"] == "insufficient_evidence"                 # exp(-1.5) is about 1 in 4


def test_without_ordinary_days_nothing_is_decided():
    doc = closed_lanes.resolve(_readings([(6, 0)] * 6 + [(0, 0)] * 6), closed_lanes.ordinary_traffic([]))
    assert doc["decision"] == "insufficient_evidence"
    assert {x["why"] for x in doc["rejected"]} == {"no ordinary-day readings for this lane",
                                                   "no ordinary-day readings"}


def test_the_report_names_the_decision_and_the_phases():
    doc = closed_lanes.resolve(_readings([(6, 4), (5, 0), (6, 0), (5, 0), (4, 0), (5, 4)]), ORDINARY)
    full = {"detector_id": "AID01104", "start": T0.isoformat(), "end": (T0 + dt.timedelta(minutes=3)).isoformat(),
            "ordinary_days": ["2026-05-08"], "archive": "", "readings": 6, **doc}
    text = closed_lanes._md(full, "the command")
    assert "**Decision: lanes**" in text and "Closed first: **Slow Lane**, from 08:50:30" in text
