"""The twin's hand-over from Data: what each number is, and what never leaks in from the replay day."""
import datetime as dt

import pytest

from src.loaders import twin_inputs
from src.loaders.common import HK
from src.twin import run_flow_balance

DAY, ORDINARY = dt.date(2026, 5, 15), [dt.date(2026, 5, 8), dt.date(2026, 4, 24)]
FIRST, NEXT = twin_inputs.CHAINS["main_eastbound"][:2]


def _readings(day, detector, start, end, flow, speed):
    """One 30-second single-lane reading a minute from `start` to `end`, at `flow` veh/h and `speed` km/h."""
    t, stop, rows = dt.datetime.combine(day, start, HK), dt.datetime.combine(day, end, HK), []
    while t < stop:
        rows.append({"timestamp": t, "detector_id": detector, "direction": "", "lane": "Slow Lane",
                     "speed_kmh": speed, "volume": flow * 30 / 3600, "occupancy_pct": 10.0, "speed_sd": None,
                     "valid": True, "period_s": 30})
        t += dt.timedelta(minutes=1)
    return rows


OTHER_FIRSTS = [chain[0] for name, chain in twin_inputs.CHAINS.items() if name != "main_eastbound"]


def _load(per_day):
    """A loader over made-up days: {day: [(detector, flow, speed)]} all morning; the other chains run steadily."""
    def load(start, end):
        rows = []
        for detector, flow, speed in per_day[start.date()] + [(d, 600, 50.0) for d in OTHER_FIRSTS]:
            rows += _readings(start.date(), detector, start.time(), end.time(), flow, speed)
        return sorted(rows, key=lambda r: r["timestamp"])
    return load


def test_a_quarter_hour_queued_one_day_and_free_the_next_gets_the_travel_time_speed():
    days = [_readings(d, "X", dt.time(8, 0), dt.time(8, 15), 1200, speed)
            for d, speed in zip(ORDINARY, (20.0, 60.0))]
    profile = twin_inputs.speed_profiles(days)
    assert profile == {"X": {"08:00": 30.0}}              # 2 / (1/20 + 1/60), not the plain mean of 40


def test_speeds_are_kept_per_quarter_of_an_hour():
    rows = (_readings(DAY, "X", dt.time(8, 0), dt.time(8, 15), 1200, 60.0)
            + _readings(DAY, "X", dt.time(8, 15), dt.time(8, 30), 1200, 20.0))
    assert twin_inputs.speed_profiles([rows]) == {"X": {"08:00": 60.0, "08:15": 20.0}}


def test_refresh_scales_a_quarter_by_the_one_before_it_and_stops_at_the_limit():
    ordinary = {"X": {"08:00": 60.0, "08:15": 50.0, "08:30": 40.0, "08:45": 40.0}}
    own = {"X": {"08:00": 30.0, "08:15": 50.0, "08:30": 10.0}}
    out, ratios = twin_inputs.refreshed(ordinary, own, until="08:30")
    assert out["X"] == {"08:00": 60.0, "08:15": 25.0, "08:30": 40.0, "08:45": 40.0}
    assert ratios["X"] == {"08:15": 0.5, "08:30": 1.0}    # 08:45 is after the limit: the ordinary speed


def test_refresh_never_moves_a_speed_beyond_the_clip():
    out, ratios = twin_inputs.refreshed({"X": {"08:00": 60.0, "08:15": 60.0}}, {"X": {"08:00": 6.0}}, until="08:15")
    assert ratios["X"]["08:15"] == twin_inputs.REFRESH_CLIP[0] and out["X"]["08:15"] == 24.0


def test_flow_changes_are_joins_in_vehicles_and_exits_as_a_share():
    third = twin_inputs.CHAINS["main_eastbound"][2]
    rows = [(_readings(d, FIRST, dt.time(7, 55), dt.time(8, 55), 1000, 60.0)
             + _readings(d, NEXT, dt.time(7, 55), dt.time(8, 55), 1300, 60.0)
             + _readings(d, third, dt.time(7, 55), dt.time(8, 55), 1040, 60.0)) for d in ORDINARY]
    pairs, flow = twin_inputs.flow_changes(rows)
    assert flow[FIRST] == 1000 and flow[NEXT] == 1300
    assert pairs[0] == {"chain": "main_eastbound", "up": FIRST, "down": NEXT, "up_veh_h": 1000, "down_veh_h": 1300,
                        "join_veh_h": 300.0, "exit_share": 0.0}
    assert pairs[1]["join_veh_h"] == 0.0 and pairs[1]["exit_share"] == pytest.approx(0.2)


def test_a_detector_missing_on_one_ordinary_day_is_stepped_over():
    rows = [_readings(ORDINARY[0], FIRST, dt.time(7, 55), dt.time(8, 55), 1000, 60.0)
            + _readings(ORDINARY[0], NEXT, dt.time(7, 55), dt.time(8, 55), 1300, 60.0),
            _readings(ORDINARY[1], FIRST, dt.time(7, 55), dt.time(8, 55), 1000, 60.0)]
    pairs, flow = twin_inputs.flow_changes(rows)
    assert NEXT not in flow and pairs == []


def test_only_the_first_detectors_take_anything_from_the_replay_day():
    per_day = {DAY: [(FIRST, 1500, 30.0), (NEXT, 9999, 5.0)],
               ORDINARY[0]: [(FIRST, 1000, 60.0), (NEXT, 1200, 50.0)],
               ORDINARY[1]: [(FIRST, 1000, 60.0), (NEXT, 1200, 50.0)]}
    doc = twin_inputs.build(DAY, ORDINARY, load=_load(per_day), window=(dt.time(7, 30), dt.time(9, 30)))
    assert doc["demand_setting_detectors"][0] == FIRST
    entry = doc["entries"]["main_eastbound"]
    assert entry["veh_h"][:6] == [1500.0] * 6 and entry["from"][:6] == ["replay morning"] * 6     # to 09:00
    assert entry["veh_h"][6:] == [1000.0, 1000.0] and entry["from"][6:] == ["ordinary mornings"] * 2
    assert doc["pairs"][0]["join_veh_h"] == 200.0                      # 1,200 - 1,000: the ordinary days'
    assert set(doc["speed_profile_kmh"][NEXT].values()) == {50.0}      # not the replay day's 5 km/h
    assert doc["speeds"] == "ordinary mornings only" and doc["speed_refresh_ratios"] is None


def test_refresh_is_labelled_and_uses_the_replay_days_own_earlier_readings():
    per_day = {DAY: [(FIRST, 1500, 30.0)], ORDINARY[0]: [(FIRST, 1000, 60.0)], ORDINARY[1]: [(FIRST, 1000, 60.0)]}
    doc = twin_inputs.build(DAY, ORDINARY, refresh=True, load=_load(per_day),
                            window=(dt.time(7, 30), dt.time(9, 30)), refresh_until=dt.time(8, 45))
    speeds = doc["speed_profile_kmh"][FIRST]
    assert speeds["07:30"] == 60.0 and speeds["07:45"] == 30.0 and speeds["08:45"] == 30.0
    assert speeds["09:00"] == 60.0                                      # past the limit
    assert "refreshed" in doc["speeds"] and doc["speed_refresh_ratios"][FIRST]["08:00"] == 0.5


def test_the_window_must_start_on_a_quarter_and_hold_the_scored_hour():
    with pytest.raises(ValueError, match="quarter"):
        twin_inputs.build(DAY, ORDINARY, load=lambda s, e: [], window=(dt.time(7, 25), dt.time(9, 0)))
    with pytest.raises(ValueError, match="inside the window"):
        twin_inputs.build(DAY, ORDINARY, load=lambda s, e: [], window=(dt.time(8, 0), dt.time(9, 0)))


def test_the_score_is_split_between_demand_setting_and_assessment_detectors():
    evaluation = {"count_bins": [{"detector_id": "A", "within_5": True, "observed": 100, "simulated": 98},
                                 {"detector_id": "B", "within_5": False, "observed": 100, "simulated": 40},
                                 {"detector_id": "B", "within_5": True, "observed": 100, "simulated": 95}],
                  "speed_bins": [{"detector_id": "A", "absolute_percentage_error": 5.0},
                                 {"detector_id": "B", "absolute_percentage_error": 20.0},
                                 {"detector_id": "B", "absolute_percentage_error": 30.0}]}
    score = run_flow_balance.split_score(evaluation, {"A"})
    assert score["demand_setting_detectors"] == {"geh_under_5_percent": 100.0, "count_bins": 1,
                                                 "speed_mape_percent": 5.0, "speed_bins": 1}
    assert score["assessment_detectors"] == {"geh_under_5_percent": 50.0, "count_bins": 2,
                                             "speed_mape_percent": 25.0, "speed_bins": 2}
    assert score["all_detectors"]["count_bins"] == 3
    table = run_flow_balance.per_detector(evaluation)
    assert table["B"] == {"count_bins": 2, "geh_under_5": 1, "observed_total": 200, "simulated_total": 135,
                          "speed_bins": 2, "speed_mape_percent": 25.0}


def test_a_first_detector_with_no_count_at_all_stops_the_build():
    per_day = {d: [(NEXT, 1000, 60.0)] for d in [DAY] + ORDINARY}
    with pytest.raises(ValueError, match=f"{FIRST}: no usable count"):
        twin_inputs.build(DAY, ORDINARY, load=_load(per_day), window=(dt.time(7, 30), dt.time(9, 30)))
