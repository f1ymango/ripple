"""Slow-traffic counts, the congested-merge trade-off, and the observation rule that follows (component A)."""
import gzip

import pytest

from src.loaders import archive, count_bias, merge_tradeoff, twin_export


def clock(seconds):
    return f"09:{seconds // 60:02d}:{seconds % 60:02d}"


def period(minute, second, up, down):
    """A 30-s period from 09:<minute> + `second` s; `up`, `down`: (volume, speed) for UP and DOWN, one lane each."""
    start = minute * 60 + second

    def detector(name, volume, speed):
        return (f"<detector><detector_id>{name}</detector_id><direction>East</direction><lanes><lane>"
                f"<lane_id>Fast Lane</lane_id><speed>{speed}</speed><occupancy>5</occupancy>"
                f"<volume>{volume}</volume><s.d.>0</s.d.><valid>Y</valid></lane></lanes></detector>")
    return (f"<period><period_from>{clock(start)}</period_from><period_to>{clock(start + 30)}</period_to>"
            f"<detectors>{detector('UP', *up)}{detector('DOWN', *down)}</detectors></period>")


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "CACHE_ROOT", tmp_path)
    (tmp_path / "detectors").mkdir()

    def write(day, stamp, periods):
        body = f"<raw_speed_volume_list><date>{day}</date><periods>{''.join(periods)}</periods></raw_speed_volume_list>"
        (tmp_path / "detectors" / f"{day.replace('-', '')}-{stamp}.xml.gz").write_bytes(gzip.compress(body.encode()))
    return write


def test_slow_bins_show_the_upstream_detector_counting_fewer(cache):
    # 09:00-09:05: fast traffic, both count 10 a period; 09:05-09:10: slow at UP, which counts 5 of DOWN's 10
    fast = [period(0, s, (10, 60), (10, 60)) for s in (0, 30, 60, 90)]
    slow = [period(5, s, (5, 8), (10, 50)) for s in (0, 30, 60, 90)]
    cache("2026-05-08", "0910", fast + slow)
    cache("2026-05-15", "0910", [period(0, s, (1, 60), (10, 60)) for s in (0, 30, 60)])   # left out below
    result = count_bias.compare("UP", "DOWN", exclude_days=("20260515",))
    bands = {row["band_kmh"]: row for row in result["bands"]}
    assert bands["0-10"]["up_over_down"] == 0.5 and bands["0-10"]["bins"] == 1
    assert bands["50+"]["up_over_down"] == 1.0 and bands["50+"]["bins"] == 1
    assert result["days_read"] == ["20260508"]


def test_a_period_with_an_invalid_lane_is_not_compared(cache):
    bad = period(0, 0, (10, 60), (10, 60)).replace("<valid>Y</valid></lane></lanes></detector></detectors>",
                                                   "<valid>N</valid></lane></lanes></detector></detectors>")
    cache("2026-05-08", "0910", [bad] + [period(0, s, (10, 60), (10, 60)) for s in (30, 60, 90)])
    assert len(count_bias.matched_periods("UP", "DOWN", ["20260508"])) == 3


def test_the_congested_merge_slope_is_the_join_lost_per_main_line_vehicle(monkeypatch):
    rows = [{"start": f"2026-05-0{d}T08:00:00+08:00", "main_veh_h": main, "after_veh_h": main + 1600 - 0.5 * main,
             "main_kmh": 70, "after_kmh": 40} for d, main in enumerate((900, 1200, 1500, 1800), start=1)]
    rows.append({"start": "2026-05-06T08:00:00+08:00", "main_veh_h": 1000, "after_veh_h": 2000,
                 "main_kmh": 70, "after_kmh": 20})              # merged road too slow to count: left out
    monkeypatch.setattr(merge_tradeoff, "quarter_hours", lambda main, after, days: rows)
    monkeypatch.setattr(merge_tradeoff, "cached_days", lambda: ["20260501"])
    result = merge_tradeoff.compare("M", "A")
    assert result["states"]["congested"]["slope_join_per_main_vehicle"] == -0.5
    assert result["states"]["congested"]["quarter_hours"] == 4


def test_counts_measured_in_slow_traffic_are_withheld_and_speeds_kept():
    doc = {"source": {"count_rule": "coverage"}, "detectors": [{"id": "X", "observations": [
        {"time": "t0", "count": 50, "speed_kmh": 12.0}, {"time": "t1", "count": 80, "speed_kmh": 45.0},
        {"time": "t2", "count": 0, "speed_kmh": None}, {"time": "t3", "count": None, "speed_kmh": 5.0}]}]}
    out = twin_export.withhold_slow_counts(doc, 30)
    obs = out["detectors"][0]["observations"]
    assert [o["count"] for o in obs] == [None, 80, 0, None]
    assert [o["speed_kmh"] for o in obs] == [12.0, 45.0, None, 5.0]
    assert out["source"]["counts_withheld_as_slow"] == 1 and "30 km/h" in out["source"]["count_rule"]
    assert doc["detectors"][0]["observations"][0]["count"] == 50                 # the input is not changed
