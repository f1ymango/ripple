"""The candidate screen: incident days against ordinary days, never the worst bin."""
import datetime as dt

import pytest

from src.loaders import candidates, common, incidents

HK = common.HK
NEW = dt.datetime(2026, 5, 15, 9, 0, tzinfo=HK)       # a Friday
CLOSED = NEW + dt.timedelta(hours=1)


def _incident(number="IN-X", new_at=NEW, closed_at=CLOSED, **kw):
    return {"incident_number": number, "new_at": new_at.isoformat() if new_at else "",
            "closed_at": closed_at.isoformat() if closed_at else "",
            "first_announced_at": new_at.isoformat() if new_at else "",
            "last_announced_at": closed_at.isoformat() if closed_at else "",
            "duration_min": 60, "location_en": "Wong Chuk Hang Road",
            "direction_en": "Aberdeen Tunnel", "detail_en": "Traffic Accident",
            "corridor_road": "wong chuk hang road", "lane_wording": "all lanes",
            "left_censored": False, "right_censored": False, **kw}


def _bin(speed, flow=600, completeness=100, coverage=60):
    return {"speed_kmh": speed, "flow_veh_h": flow, "lane_completeness_pct": completeness,
            "coverage_pct": coverage}


def _grid(speeds: dict, start: dt.datetime, minutes=210, default=70.0):
    """{detector: {slot offset in minutes: speed or a bin}} -> the dict _bins returns."""
    out = {}
    for d in candidates.LEG:
        for m in range(0, minutes, 5):
            value = speeds.get(d, {}).get(m, default)
            out[(d, start + dt.timedelta(minutes=m))] = value if isinstance(value, dict) else _bin(value)
    return out


def _patch_days(monkeypatch, incident_day: dict, control_a: dict | None = None,
                control_b: dict | None = None):
    """Serve synthetic grids: the incident day, then 1 and 2 weeks back."""
    start = NEW - dt.timedelta(minutes=candidates.BEFORE_MIN)
    days = {start: incident_day, start - dt.timedelta(weeks=1): control_a or {},
            start - dt.timedelta(weeks=2): control_b or {}}
    monkeypatch.setattr(candidates, "_bins", lambda a, b, minutes: _grid(days[a], a))


# ---------------------------------------------------------------- ordinary days

def test_control_days_skip_any_week_with_a_corridor_incident_of_any_kind():
    one_week = _incident("IN-OTHER", NEW - dt.timedelta(weeks=1), CLOSED - dt.timedelta(weeks=1),
                         detail_en="Road Works")
    assert candidates.control_days(_incident(), [one_week]) == [14, 21]


def test_an_incident_without_a_clearance_still_blocks_its_week():
    """Seen only as a NEW message: treated as running for 30 minutes."""
    open_ended = _incident("IN-OPEN", NEW - dt.timedelta(weeks=2, minutes=-10), None)
    assert candidates.control_days(_incident(), [open_ended]) == [7, 21]


def test_an_incident_is_not_its_own_contamination():
    me = _incident()
    assert candidates.others_in(*candidates.window_for(me), [me], skip="IN-X") == []


def test_fewer_than_two_clean_days_means_no_verdict(monkeypatch):
    busy = [_incident(f"IN-{w}", NEW - dt.timedelta(weeks=w), CLOSED - dt.timedelta(weeks=w))
            for w in range(1, 7)]
    got = candidates.evidence(_incident(), busy)
    assert got["control_days"] == [] and got["credited"] == {} and got["coverage_pct"] is None
    assert candidates.score({**_incident(), **got}) == 0


# ---------------------------------------------------------------- what gets credited

def test_a_sustained_slowdown_absent_on_ordinary_days_is_credited(monkeypatch):
    # AID01104 at 8 km/h from 08:55 (offset 85) to 10:00 (offset 150)
    _patch_days(monkeypatch, {"AID01104": {m: 8.0 for m in range(85, 150, 5)}})
    got = candidates.evidence(_incident(), [])
    assert list(got["credited"]) == ["AID01104"]
    only = got["credited"]["AID01104"]
    assert only["leg"] == "main_eastbound" and only["longest_min"] == 65
    assert only["onset"] == NEW - dt.timedelta(minutes=5)
    assert candidates.onset_vs_report_min({**_incident(), **got}) == -5


def test_one_slow_bin_is_not_enough():
    day = {("AID01104", NEW): _bin(10.0)}
    ref = {("AID01104", NEW - dt.timedelta(days=7)): _bin(70.0)}
    got = candidates.compare(day, ref, [NEW], dt.timedelta(0), dt.timedelta(days=7), 5)
    assert got["AID01104"]["sustained"] is False and got["AID01104"]["longest_min"] == 5


def test_a_detector_that_differs_as_long_between_two_ordinary_days_is_noise(monkeypatch):
    slow = {m: 10.0 for m in range(90, 150, 5)}
    _patch_days(monkeypatch, {"AID01108": slow}, control_b={"AID01108": slow})
    got = candidates.evidence(_incident(), [])
    assert got["credited"] == {} and got["noise"] == ["AID01108"]


def test_a_short_ordinary_day_dip_does_not_dismiss_a_long_closure(monkeypatch):
    """IN-26-06391: the tunnel detector dipped 10 minutes two weeks earlier;
    on the day it ran 5-13 km/h for 40 minutes."""
    _patch_days(monkeypatch, {"AID01107": {m: 8.0 for m in range(90, 130, 5)}},
                control_b={"AID01107": {m: 20.0 for m in (80, 85)}})
    got = candidates.evidence(_incident(), [])
    assert got["noise"] == ["AID01107"] and got["credited"]["AID01107"]["longest_min"] == 40


def test_missing_bins_neither_credit_nor_break_a_detector(monkeypatch):
    gappy = {m: ("" if m % 10 else 8.0) for m in range(85, 150, 5)}   # every other bin blank
    _patch_days(monkeypatch, {"AID01104": gappy})
    got = candidates.evidence(_incident(), [])
    assert "AID01104" not in got["credited"]                        # never two in a row


def test_a_closure_is_seen_as_no_traffic_only_when_the_control_had_traffic(monkeypatch):
    empty = _bin("", flow=0)
    _patch_days(monkeypatch,
                {"AID01104": {m: empty for m in range(100, 150, 5)},
                 "AID01217": {m: empty for m in range(100, 150, 5)}},
                control_a={"AID01217": {m: _bin("", flow=0) for m in range(100, 150, 5)}})
    got = candidates.evidence(_incident(), [])
    assert got["no_traffic"] == {"AID01104": 50}                   # not AID01217: quiet anyway


def test_zero_flow_with_lanes_offline_is_not_a_closure():
    day = {("AID01104", NEW + dt.timedelta(minutes=5 * i)): _bin("", flow=0, completeness=50)
           for i in range(4)}
    ref = {("AID01104", NEW + dt.timedelta(minutes=5 * i) - dt.timedelta(days=7)): _bin(70.0)
           for i in range(4)}
    slots = [NEW + dt.timedelta(minutes=5 * i) for i in range(4)]
    assert candidates.no_traffic(day, ref, slots, dt.timedelta(days=7), 5) == {}


# ---------------------------------------------------------------- the score

def _row(mean=-40.0, longest=45, n=1, no_traffic=None, coverage=50, others=None, onset=-5):
    credited = {f"AID0110{i}": {"mean_kmh": mean, "longest_min": longest, "leg": "main_eastbound",
                                "onset": NEW + dt.timedelta(minutes=onset)} for i in range(n)}
    return {**_incident(), "credited": credited, "no_traffic": no_traffic or {},
            "coverage_pct": coverage, "others_in_window": others or []}


def test_the_score_rewards_depth_duration_spread_a_seen_closure_and_coverage():
    base = candidates.score(_row())
    assert candidates.score(_row(mean=-10.0)) < base
    assert candidates.score(_row(longest=10)) < base
    assert candidates.score(_row(n=3)) > base
    assert candidates.score(_row(no_traffic={"AID01104": 40})) == pytest.approx(base + 1)
    assert candidates.score(_row(coverage=10)) < base


def test_the_score_penalises_an_overlapping_incident_and_an_early_onset():
    base = candidates.score(_row())
    assert candidates.score(_row(others=["IN-26-03214"])) == pytest.approx(base - 1)
    assert candidates.score(_row(onset=-45)) == pytest.approx(base - 0.5)
    assert candidates.score({}) == 0 and candidates.score(_row(n=0)) == 0


# ---------------------------------------------------------------- the table

def test_the_table_never_prints_none_and_says_what_td_wrote(tmp_path):
    rows = [_row(no_traffic={"AID01104": 40}),
            {**_incident("IN-EMPTY", lane_wording=""), "credited": {}, "no_traffic": {},
             "control_days": [], "coverage_pct": None, "others_in_window": [], "score": 0}]
    rows[0]["score"] = candidates.score(rows[0])
    text = candidates.write_markdown(rows, tmp_path / "c.md").read_text(encoding="utf-8")
    assert "None" not in text and "all lanes" in text and "AID01104 40 min" in text
    assert "IN-EMPTY" in text and "data/demo_shortlist.md" in text


def test_an_empty_screen_still_writes_a_readable_table(tmp_path):
    text = candidates.write_markdown([], tmp_path / "c.md").read_text(encoding="utf-8")
    assert "| # | Incident |" in text and "Reading the table" in text


def test_shortlist_with_no_usable_incidents_is_empty(monkeypatch):
    monkeypatch.setattr(candidates.incidents, "load", lambda a, b: [])
    assert candidates.shortlist("2026-09-18", "2026-09-18", log=lambda *a: None) == []


# ---------------------------------------------------------------- TD's lane wording

@pytest.mark.parametrize("messages,expected", [
    (["Due to traffic accident , part of the lanes of X is closed to all traffic.",
      "Due to traffic accident , all lanes of X are closed to all traffic.",
      "All lanes of X which were closed ... are re-opened to all traffic."],
     "part of the lanes -> all lanes"),
    (["the tunnel tube slow lane of Aberdeen Tunnel is closed to all traffic. "
      "Only the fast lane is available to motorists."], "tunnel tube slow lane"),
    (["the fast lane and middle lane 1 of X are closed to all traffic. Only remaining lane "
      "is available"], "fast lane + middle lane 1"),
    (["the only lane of the slip road leading from X to Y is closed"], "only lane of a slip road"),
    (["the one-lane-two-way traffic arrangement is being implemented on X",
      "The one-lane-two-way traffic arrangement ... is now cancelled."], "one-lane-two-way"),
    (["The fast lane is re-opened to all traffic. The slow lane remains closed."], "slow lane"),
    (["Traffic is busy now."], ""),
    ([], ""),
])
def test_lane_wording_repeats_td_and_skips_reopenings(messages, expected):
    assert incidents.lane_wording(messages) == expected


def test_only_accidents_short_enough_to_simulate_are_screened(monkeypatch):
    rows = [_incident("IN-A"), _incident("IN-B", detail_en="Heavy Traffic"),
            {**_incident("IN-C"), "duration_min": 3467}]
    monkeypatch.setattr(candidates.incidents, "load", lambda a, b: rows)
    monkeypatch.setattr(candidates, "evidence", lambda i, corridor, minutes: {"credited": {}})
    got = candidates.shortlist("2026-05-15", "2026-05-15", log=lambda *a: None)
    assert [r["incident_number"] for r in got] == ["IN-A"]
