"""Week 2 data checks: bins each calibration threshold leaves, and lanes reading by reading."""
import datetime as dt

from src.loaders import bin_survival, common, flow_balance, free_flow, lane_evidence

HK = common.HK
T0 = dt.datetime(2026, 5, 15, 8, 0, tzinfo=HK)
SPLIT = T0 + dt.timedelta(minutes=10)


def _bin(detector, minute, coverage=40, lanes=100, count=50, speed=60.0, periods=4):
    return {"bin_start": (T0 + dt.timedelta(minutes=minute)).isoformat(), "detector_id": detector,
            "coverage_pct": coverage, "lane_completeness_pct": lanes, "count_bin": count,
            "speed_kmh": speed, "periods_observed": periods}


def _grid():
    """AID01101: every slot usable at 40%, except one at 20%. AID01102: missing from the feed."""
    rows = [_bin("AID01101", m) for m in (0, 5, 10)] + [_bin("AID01101", 15, coverage=20, speed=58.0)]
    rows += [_bin("AID01102", m, coverage=0, lanes=0, count="", speed="", periods=0)
             for m in (0, 5, 10, 15)]
    return rows


# ---------------------------------------------------------------- bin survival

def test_each_threshold_counts_bins_before_and_from_the_split():
    got = bin_survival.survey(_grid(), SPLIT)
    default = got["thresholds"][0]
    assert (default["min_coverage_pct"], default["min_lane_completeness_pct"]) == (40, 90)
    assert (default["before"], default["after"], default["all"]) == (2, 1, 3)
    at_20 = next(t for t in got["thresholds"] if t["min_coverage_pct"] == 20
                 and t["min_lane_completeness_pct"] == 90)
    assert at_20["all"] == 4                            # the 20% bin joins
    assert got["slots"] == {"before": 4, "after": 4, "all": 8}


def test_a_detector_missing_from_every_snapshot_is_named_not_blamed_on_the_archive():
    assert bin_survival.absent_detectors(_grid()) == ["AID01102"]


def test_the_bias_check_skips_empty_slots_and_refuses_tiny_groups(tmp_path):
    got = bin_survival.survey(_grid(), SPLIT)
    at_40 = got["bias"]["all_cov40"]
    assert at_40["low_coverage_bins"] == 1                # the 20% bin; empty slots left out
    md, js = bin_survival.write({"start": T0.isoformat(),
                                 "end": (T0 + dt.timedelta(minutes=20)).isoformat(), **got},
                                "cmd", tmp_path)
    text = md.read_text(encoding="utf-8")
    assert "too few bins below 40% to compare" in text and "None" not in text
    assert "AID01102" in text and js.exists()


# ---------------------------------------------------------------- lane by lane

def _reading(second, fast, slow, valid=True):
    t = T0 + dt.timedelta(seconds=second)
    return [{"timestamp": t, "detector_id": "AID01104", "lane": "Fast Lane", "volume": fast,
             "speed_kmh": 50.0 if fast else None, "occupancy_pct": 5.0, "valid": True},
            {"timestamp": t, "detector_id": "AID01104", "lane": "Slow Lane", "volume": slow,
             "speed_kmh": 50.0 if slow else None, "occupancy_pct": 0.0, "valid": valid}]


def test_a_lane_is_empty_only_while_another_lane_is_moving():
    fast_only = {"Fast Lane": {"volume": 3}, "Slow Lane": {"volume": 0}}
    both_empty = {"Fast Lane": {"volume": 0}, "Slow Lane": {"volume": 0}}
    assert lane_evidence.empty_while_moving(fast_only) == ["Slow Lane"]
    assert lane_evidence.empty_while_moving(both_empty) == []          # a closure, not one lane


def test_readings_with_an_offline_lane_are_left_out():
    rows = _reading(0, 3, 0) + _reading(30, 3, 0, valid=False)
    assert [t for t, _ in lane_evidence.by_reading(rows, "AID01104")] == [T0]


def test_the_longest_run_and_its_span_are_reported():
    rows = (_reading(0, 3, 1) + _reading(30, 3, 0) + _reading(60, 2, 0) + _reading(90, 4, 0)
            + _reading(120, 0, 0) + _reading(150, 3, 0))
    got = lane_evidence.summary(lane_evidence.by_reading(rows, "AID01104"))
    slow = got["Slow Lane"]
    assert slow["empty_while_moving"] == 4 and slow["longest_run"] == 3
    assert slow["longest_run_span"] == [(T0 + dt.timedelta(seconds=30)).isoformat(),
                                        (T0 + dt.timedelta(seconds=90)).isoformat()]
    assert list(got) == ["Fast Lane", "Slow Lane"] and got["Fast Lane"]["share_pct"] == 94


def test_ordinary_days_are_read_at_the_same_clock_time(monkeypatch):
    asked = []
    monkeypatch.setattr(lane_evidence.detectors, "load_window",
                        lambda a, b, ids, log: asked.append((a, b)) or [])
    lane_evidence.build("AID01104", T0, T0 + dt.timedelta(minutes=40), [dt.date(2026, 5, 8)])
    week = dt.timedelta(days=7)
    assert sorted(asked) == [(T0 - week, T0 + dt.timedelta(minutes=40) - week),
                             (T0, T0 + dt.timedelta(minutes=40))]


# ---------------------------------------------------------------- flow balance


def _lane(detector, lane, second, volume, valid=True, speed=60.0, occupancy=5.0, period=30.0):
    return {"timestamp": T0 + dt.timedelta(seconds=second), "detector_id": detector, "lane": lane,
            "volume": volume, "valid": valid, "speed_kmh": speed if volume else None,
            "occupancy_pct": occupancy, "period_s": period}


def test_hourly_flow_is_each_lanes_rate_summed_with_a_poisson_margin():
    rows = [_lane("A", "Fast Lane", 0, 5), _lane("A", "Fast Lane", 30, 7), _lane("A", "Slow Lane", 0, 3)]
    got = flow_balance.hourly_flows(rows)["A"]
    assert got["veh_h"] == 720 + 360                  # 12 in 60 s, plus 3 in 30 s
    assert got["margin_veh_h"] == 576                 # 1.96 * sqrt(12 * 60**2 + 3 * 120**2)
    assert got["observed_min"] == 1


def test_a_detector_with_a_lane_never_valid_has_no_flow():
    rows = [_lane("A", "Fast Lane", 0, 5), _lane("A", "Slow Lane", 0, 3, valid=False)]
    assert flow_balance.hourly_flows(rows) == {}


def test_a_missing_detector_is_stepped_over_and_named():
    flows = {"A": {"veh_h": 1000, "margin_veh_h": 30}, "C": {"veh_h": 1600, "margin_veh_h": 40}}
    assert flow_balance.steps(["A", "B", "C"], flows) == [
        {"from": "A", "to": "C", "skipped": ["B"], "change_veh_h": 600, "margin_veh_h": 50}]


def test_a_junction_is_clear_only_if_every_day_agrees_beyond_its_margin():
    def c(v, m=100):
        return {"change_veh_h": v, "margin_veh_h": m}
    assert flow_balance.clear([c(600), c(500), c(700)]) is True
    assert flow_balance.clear([c(342), c(9), c(360)]) is False      # one day within its margin
    assert flow_balance.clear([c(600), c(-500)]) is False           # opposite ways
    assert flow_balance.clear([c(600), None]) is False              # a day with no data


# ---------------------------------------------------------------- free-flow speeds

def test_only_light_valid_readings_with_a_vehicle_count():
    rows = [_lane("A", "Fast Lane", 0, 4, speed=72.0), _lane("A", "Fast Lane", 30, 4, occupancy=25.0),
            _lane("A", "Fast Lane", 60, 0), _lane("A", "Fast Lane", 90, 4, valid=False)]
    assert free_flow.light_readings(rows) == {"A": [(72.0, 4)]}


def test_percentiles_weight_each_reading_by_its_vehicles():
    pairs = [(50.0, 1), (70.0, 3)]
    assert free_flow.percentile(pairs, 50) == 70.0 and free_flow.percentile(pairs, 20) == 50.0


def test_too_few_readings_is_not_reported_as_a_speed():
    got = free_flow.summary([(70.0, 2)] * (free_flow.MIN_READINGS - 1))
    assert got["enough"] is False and "median_kmh" not in got
    got = free_flow.summary([(70.0, 2)] * free_flow.MIN_READINGS)
    assert got["enough"] is True and got["median_kmh"] == 70.0 and got["above_cap_pct"] == 100
