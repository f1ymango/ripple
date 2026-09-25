"""Edge cases for the data layer: boundaries, empty inputs, malformed data.

Written to find problems, not to confirm fixes. No network: archive calls go to
a local stub or are replaced.
"""
import csv
import datetime as dt
import gzip
import io
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from src.loaders import archive, candidates, common, detectors, incidents, lanes, live
from src.loaders import fetch as fetch_cli
from src.loaders.corridor import on_corridor

HK = common.HK
FIXTURES = Path(__file__).parent / "fixtures"
T0 = dt.datetime(2026, 9, 21, 8, 0, tzinfo=HK)


def reading(at, lane="Fast Lane", valid=True, volume=10.0, speed=50.0, occ=10.0,
            detector="AID01107", period_s=30.0):
    return {"timestamp": at, "detector_id": detector, "direction": "", "lane": lane,
            "speed_kmh": speed if valid else None, "volume": volume if valid else None,
            "occupancy_pct": occ if valid else None, "speed_sd": 0, "valid": valid,
            "period_s": period_s}


def every_30s(n, start=T0, **kw):
    return [reading(start + dt.timedelta(seconds=30 * i), **kw) for i in range(n)]


def message(i, status, when, number="IN-1", location="Aberdeen Tunnel", first="20260918-1700",
            last="20260918-1800", content=""):
    return {"first_seen": first, "last_seen": last,
            "stn": {"ID": str(i), "INCIDENT_NUMBER": number, "INCIDENT_STATUS_EN": status,
                    "ANNOUNCEMENT_DATE": when, "LOCATION_EN": location, "CONTENT_EN": content}}


# ---------------------------------------------------------------- detectors

def test_empty_input_everywhere_downstream_of_the_parser():
    assert detectors.bin_window([]) == []
    assert detectors.usable_for_calibration([]) == []
    report = detectors.coverage_report([])
    assert report["bins"] == 0 and "warning" in report
    assert detectors.coverage_bias_check([])["looks_unbiased"] is False


def test_readings_land_in_the_right_bin_at_an_hour_boundary():
    rows = [reading(T0.replace(minute=59, second=30) - dt.timedelta(hours=1)),
            reading(T0.replace(hour=9))]
    starts = [b["bin_start"][11:16] for b in detectors.bin_window(rows)]
    assert starts == ["07:55", "09:00"]


@pytest.mark.parametrize("width,expected", [(60, "08:00"), (30, "08:30"), (1, "08:47")])
def test_bin_floors_for_every_allowed_width(width, expected):
    rows = [reading(T0.replace(minute=47, second=30))]
    assert detectors.bin_window(rows, width)[0]["bin_start"][11:16] == expected


def test_a_bin_with_no_traffic_has_zero_flow_and_no_speed():
    b = detectors.bin_window(every_30s(10, volume=0.0))[0]
    assert b["flow_veh_h"] == 0 and b["count_bin"] == 0
    assert b["speed_kmh"] == ""               # no vehicle, no speed -- not the limit


def test_speed_is_weighted_only_by_readings_that_have_a_speed():
    rows = every_30s(2) + [reading(T0, lane="Slow Lane", speed=None, volume=100.0)]
    assert detectors.bin_window(rows)[0]["speed_kmh"] == 50.0


def test_a_lane_absent_from_some_periods_is_rated_on_its_own_seconds():
    rows = every_30s(10) + every_30s(4, lane="Slow Lane")
    b = detectors.bin_window(rows)[0]
    assert b["count_bin"] == 200                # 100 fast + 10/30s over its 4 periods
    assert b["lane_completeness_pct"] == 70     # 14 of 20 lane slots


def test_per_lane_bins_add_up_to_the_detector_bin():
    rows = every_30s(10) + every_30s(10, lane="Slow Lane", volume=4.0)
    total = detectors.bin_window(rows)[0]["count_bin"]
    by_lane = detectors.bin_window(rows, per_lane=True)
    assert {b["lane"] for b in by_lane} == {"Fast Lane", "Slow Lane"}
    assert sum(b["count_bin"] for b in by_lane) == total


def test_a_period_running_past_the_bin_end_counts_only_its_inside_part():
    # Nine 30 s periods to 08:04:30, then one 60 s period 08:04:30-08:05:30.
    rows = every_30s(9) + [reading(T0 + dt.timedelta(seconds=270), period_s=60.0)]
    b = detectors.bin_window(rows)[0]
    assert b["coverage_pct"] == 100            # 270 + 30 inside; was 110
    assert b["flow_veh_h"] == 1091             # 100 veh over 330 s: full lengths for the rate


@pytest.mark.parametrize("text,expected", [("", None), (None, None), ("abc", None),
                                           (" 12 ", 12.0), ("0", 0.0), ("-3", None)])
def test_number_parsing_never_invents_a_value(text, expected):
    assert detectors._number(text) == expected


def test_duplicate_readings_across_overlapping_snapshots_count_once(monkeypatch):
    xml = (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes()
    monkeypatch.setattr(detectors, "window_timestamps", lambda a, b: ["a", "b"])
    monkeypatch.setattr(detectors.archive, "iter_snapshots",
                        lambda feed, ts: ((t, xml) for t in ts))        # same file twice
    rows = detectors.load_window(T0, T0 + dt.timedelta(hours=1))
    once = detectors.parse_snapshot(xml, set(detectors.DETECTOR_IDS))
    assert len(rows) == len(once)


def test_an_empty_window_returns_nothing(monkeypatch):
    monkeypatch.setattr(detectors, "window_timestamps", lambda a, b: [])
    assert detectors.load_window(T0, T0) == []


def test_a_window_across_midnight_asks_the_archive_for_both_days(monkeypatch):
    asked = []
    monkeypatch.setattr(detectors.archive, "list_versions",
                        lambda feed, a, b: asked.append((a, b)) or [])
    detectors.window_timestamps(T0.replace(hour=23, minute=50),
                                T0.replace(hour=0, minute=10) + dt.timedelta(days=1))
    assert asked == [("20260921", "20260922")]


def test_calibration_thresholds_are_inclusive_and_exact():
    def b(cov, lanes_pct):
        return {"coverage_pct": cov, "lane_completeness_pct": lanes_pct, "count_bin": 50}
    kept = detectors.usable_for_calibration([b(40, 90), b(39, 100), b(100, 89)])
    assert kept == [b(40, 90)]


# ---------------------------------------------------------------- incidents

def test_closed_announced_before_new_is_not_usable_and_does_not_crash():
    rows = incidents.build_incidents({"1": message(1, "NEW", "2026-09-18T18:00:00"),
                                      "2": message(2, "CLOSED", "2026-09-18T17:00:00")})
    assert rows[0]["duration_min"] == -60
    assert incidents.usable_corridor_incidents(rows) == []


def test_an_unreadable_announcement_date_leaves_blanks_not_a_crash():
    rows = incidents.build_incidents({"1": message(1, "NEW", "yesterday-ish"),
                                      "2": message(2, "CLOSED", "2026-09-18T17:40:00")})
    assert rows[0]["new_at"] == "" and rows[0]["duration_min"] == ""
    assert rows[0]["left_censored"] is True


def test_messages_without_an_incident_number_are_ignored():
    rows = incidents.build_incidents({"1": message(1, "NEW", "2026-09-18T17:00:00", number="")})
    assert rows == []


def test_a_reopened_incident_clears_at_its_last_closed():
    rows = incidents.build_incidents({
        "1": message(1, "NEW", "2026-09-18T17:00:00"),
        "2": message(2, "CLOSED", "2026-09-18T17:30:00"),
        "3": message(3, "UPDATED", "2026-09-18T17:45:00"),
        "4": message(4, "CLOSED", "2026-09-18T18:10:00")})
    assert rows[0]["closed_at"].startswith("2026-09-18T18:10")
    assert rows[0]["duration_min"] == 70


@pytest.mark.parametrize("minutes,usable", [(20, True), (19, False)])
def test_the_duration_threshold_is_inclusive(minutes, usable):
    closed = (dt.datetime(2026, 9, 18, 17, 0) + dt.timedelta(minutes=minutes)).isoformat()
    rows = incidents.build_incidents({"1": message(1, "NEW", "2026-09-18T17:00:00"),
                                      "2": message(2, "CLOSED", closed)})
    assert bool(incidents.usable_corridor_incidents(rows)) is usable


def test_corridor_matching_ignores_case_whitespace_and_none():
    assert on_corridor("  ABERDEEN   TUNNEL ") is None     # internal spacing matters
    assert on_corridor("ABERDEEN TUNNEL") == "aberdeen tunnel"
    assert on_corridor(None, "", "wong chuk hang road flyover") == "wong chuk hang road"


def test_a_message_seen_in_many_snapshots_is_one_message(monkeypatch):
    snap = (FIXTURES / "stn_snapshot_20260918-1828.xml").read_bytes()
    monkeypatch.setattr(incidents.archive, "iter_snapshots",
                        lambda feed, ts: ((t, snap) for t in ts))
    messages = incidents.collect_messages(["20260918-1828", "20260918-1832", "20260918-1840"])
    assert len(messages) == 1
    only = next(iter(messages.values()))
    assert only["first_seen"] == "20260918-1828" and only["last_seen"] == "20260918-1840"


def test_an_empty_stn_snapshot_has_no_messages():
    assert incidents.parse_snapshot(b"<list></list>") == []


# ---------------------------------------------------------------- archive

class _Stub:
    def __init__(self):
        self.hits = []
        self.respond = lambda path: (200, b"")


@pytest.fixture
def stub(tmp_path, monkeypatch):
    state = _Stub()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            state.hits.append(self.path)
            status, body = state.respond(self.path)
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setattr(archive, "ARCHIVE_API", f"http://127.0.0.1:{server.server_address[1]}")
    monkeypatch.setattr(archive, "CACHE_ROOT", tmp_path / "raw")
    monkeypatch.setattr(archive, "RETRY", archive.RETRY.new(backoff_factor=0))
    monkeypatch.setattr(archive, "REQUEST_PAUSE_S", 0.0)
    archive._local.__dict__.pop("session", None)
    yield state
    server.shutdown()
    archive._local.__dict__.pop("session", None)


def test_every_real_fixture_is_recognised_as_its_own_feed():
    assert archive.looks_like_feed("detectors",
                                   (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes())
    for f in FIXTURES.glob("stn_snapshot_*.xml"):
        assert archive.looks_like_feed("stn", f.read_bytes()), f.name
    assert not archive.looks_like_feed("stn", b"")
    assert not archive.looks_like_feed("stn", b"\x00\x01 not xml")


def test_an_unknown_feed_is_an_archive_error():
    with pytest.raises(archive.ArchiveError):
        archive.fetch("weather", "20990101-0000")


def test_a_truncated_cache_file_is_refetched(stub):
    good = (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes()
    stub.respond = lambda path: (200, good)
    path = archive.cache_path("detectors", "20990101-0000")
    path.parent.mkdir(parents=True)
    path.write_bytes(gzip.compress(good)[:40])                 # cut off mid-stream
    assert archive.fetch("detectors", "20990101-0000") == good
    assert len(stub.hits) == 1


def test_the_readers_legacy_cache_is_used_when_valid_and_never_deleted(stub, tmp_path):
    stn = (FIXTURES / "stn_snapshot_20260918-1828.xml").read_bytes()
    legacy = archive.CACHE_ROOT / "stn" / "20990101-0000.xml"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(stn)
    assert archive.fetch("stn", "20990101-0000") == stn and stub.hits == []
    legacy.write_bytes(b"<html>oops</html>")
    stub.respond = lambda path: (200, stn)
    assert archive.fetch("stn", "20990101-0000") == stn        # refetched into our cache
    assert legacy.exists()                                     # the Reader's file is left alone


def test_prefetch_with_nothing_to_do_does_nothing(stub):
    counts = archive.prefetch("detectors", [], log=io.StringIO())
    assert counts["downloaded"] == counts["missing"] == counts["failed"] == 0
    assert stub.hits == []


def test_prefetch_with_mixed_outcomes_retries_only_the_transient_ones(stub):
    good = (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes()
    stub.respond = lambda path: ((200, good) if "0000" in path else
                                 (404, b"") if "0001" in path else (503, b""))
    stamps = ["20990101-0000", "20990101-0001", "20990101-0002"]
    first = archive.prefetch("detectors", stamps, workers=3, log=io.StringIO())
    assert (first["downloaded"], first["missing"], first["failed"]) == (1, 1, 1)
    before = len(stub.hits)
    second = archive.prefetch("detectors", stamps, workers=3, log=io.StringIO())
    assert (second["cached"], second["known_missing"], second["failed"]) == (1, 1, 1)
    assert all("0002" in p for p in stub.hits[before:])        # only the 503 is retried


def test_iter_snapshots_can_be_made_strict(stub):
    stub.respond = lambda path: (404, b"")
    with pytest.raises(archive.NotArchived):
        list(archive.iter_snapshots("detectors", ["20990101-0000"], skip_missing=False))
    assert list(archive.iter_snapshots("detectors", ["20990101-0000"])) == []


# ---------------------------------------------------------------- candidates

@pytest.mark.parametrize("row", [{}, {"new_at": "garbled", "closed_at": ""},
                                 {"new_at": "2026-09-18T17:00:00+08:00"}])
def test_window_for_refuses_missing_or_garbled_times(row):
    assert candidates.window_for(row) is None


def test_score_survives_an_empty_row():
    assert candidates.score({}) == 0


def test_measure_with_no_tunnel_readings_has_no_drop(monkeypatch):
    other = {"bin_start": "2026-09-18T17:00:00+08:00", "detector_id": "AID01101",
             "speed_kmh": 40.0, "coverage_pct": 60, "lane_completeness_pct": 100,
             "count_bin": 50, "periods_observed": 6, "lanes_valid": 2, "lanes_offline": 0}
    monkeypatch.setattr(candidates.detectors, "load_window", lambda a, b: ["x"])
    monkeypatch.setattr(candidates.detectors, "bin_window", lambda rows, w: [other])
    got = candidates.measure({"new_at": "2026-09-18T18:00:00+08:00",
                              "closed_at": "2026-09-18T19:00:00+08:00"})
    assert got["speed_drop_kmh"] is None and got["drop_detector"] is None


def test_shortlist_with_no_usable_incidents_is_empty(monkeypatch):
    monkeypatch.setattr(candidates.incidents, "load", lambda a, b: [])
    assert candidates.shortlist("2026-09-18", "2026-09-18", log=lambda *a: None) == []


def test_an_empty_shortlist_still_writes_a_readable_table(tmp_path):
    text = candidates.write_markdown([], tmp_path / "c.md").read_text(encoding="utf-8")
    assert "| # | Incident |" in text and "The team picks one incident" in text


def test_retrievability_of_a_window_with_nothing_listed(monkeypatch):
    monkeypatch.setattr(candidates.detectors, "window_timestamps", lambda a, b: [])
    got = candidates.estimate_retrievability(T0, T0)
    assert got == {"listed": 0, "sampled": 0, "served": 0, "retrievable_pct": 0}


# ---------------------------------------------------------------- live

class _Resp:
    def __init__(self, body, status=200):
        self.content, self.status = body, status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")


@pytest.fixture
def live_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "LIVE_ROOT", tmp_path / "live")
    monkeypatch.setattr(live, "_last_hash", {})
    return tmp_path / "live"


def test_a_feed_that_changes_and_changes_back_is_stored_each_time(monkeypatch, live_dir):
    a, b = b"<list></list>", b"<list><message/></list>"
    stored = []
    for i, body in enumerate([a, b, a]):
        monkeypatch.setattr(live.http, "get", lambda url, timeout, body=body: _Resp(body))
        stored.append(live.poll_once("stn", T0 + dt.timedelta(seconds=i))[1])
    assert stored == [True, True, True]


def test_live_detector_files_are_named_by_the_data(monkeypatch, live_dir):
    xml = (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes()
    monkeypatch.setattr(live.http, "get", lambda url, timeout: _Resp(xml))
    stamp, stored = live.poll_once("detectors")
    assert stamp == "20260921-082100" and stored


def test_a_failed_live_poll_stores_nothing(monkeypatch, live_dir):
    monkeypatch.setattr(live.http, "get", lambda url, timeout: _Resp(b"", status=503))
    with pytest.raises(RuntimeError):
        live.poll_once("stn")
    assert not live_dir.exists()


# ---------------------------------------------------------------- lanes

def test_lane_analysis_skips_a_corrupt_cache_file(tmp_path):
    bad = tmp_path / "bad.xml.gz"
    bad.write_bytes(b"not gzip at all")
    good = tmp_path / "good.xml"
    good.write_bytes((FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes())
    by_lane = lanes.collect("AID01217", [bad, good])
    assert set(by_lane) == {"Fast Lane", "Middle Lane 1", "Middle Lane 2", "Slow Lane"}


def test_time_bands_only_report_bands_with_readings():
    rows = [reading(T0.replace(hour=3), lane="Middle Lane 1")]
    assert list(lanes.by_time_band({"Middle Lane 1": rows})) == ["00-06"]


# ---------------------------------------------------------------- common / CLI

def test_csv_round_trips_chinese_for_excel(tmp_path):
    path = common.write_csv([{"road": "香港仔隧道"}], tmp_path / "x.csv", encoding="utf-8-sig")
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")      # BOM, so Excel reads UTF-8
    with path.open(encoding="utf-8-sig") as f:
        assert next(csv.DictReader(f))["road"] == "香港仔隧道"


@pytest.mark.parametrize("text", ["abc", "0", "-5", "7", "90"])
def test_the_cli_refuses_a_bad_bin_width(text):
    with pytest.raises(Exception):
        fetch_cli._bin_width(text)


@pytest.mark.parametrize("text", ["1", "5", "15", "60"])
def test_the_cli_accepts_every_divisor_of_an_hour(text):
    assert fetch_cli._bin_width(text) == int(text)


def test_cli_times_are_hong_kong_time():
    assert fetch_cli._moment("2026-09-21T07:00").utcoffset() == dt.timedelta(hours=8)


# ---------------------------------------------------------------- feed markers found on 21 Sep

def _lane_xml(volume, speed, occupancy):
    return (f"<raw_speed_volume_list><date>2026-09-21</date><periods><period>"
            f"<period_from>03:00:00</period_from><period_to>03:00:30</period_to><detectors>"
            f"<detector><detector_id>AID01107</detector_id><direction>East</direction><lanes>"
            f"<lane><lane_id>Slow Lane</lane_id><speed>{speed}</speed>"
            f"<occupancy>{occupancy}</occupancy><volume>{volume}</volume><s.d.>0</s.d.>"
            f"<valid>Y</valid></lane></lanes></detector></detectors></period></periods>"
            f"</raw_speed_volume_list>").encode()


def test_an_empty_lane_reports_no_speed_not_the_speed_limit():
    """With no vehicle, the feed reports the road's speed limit (70, 80, 100...)."""
    row = detectors.parse_snapshot(_lane_xml(volume=0, speed=80, occupancy=0))[0]
    assert row["speed_kmh"] is None and row["volume"] == 0


def test_occupancy_minus_one_on_an_empty_lane_is_zero():
    """-1 appeared 2,143 times on 21 Sep, every time with volume 0."""
    row = detectors.parse_snapshot(_lane_xml(volume=0, speed=80, occupancy=-1))[0]
    assert row["occupancy_pct"] == 0.0


def test_occupancy_minus_one_with_traffic_stays_unknown():
    """Never seen, but if it happens it is a marker, not a reading."""
    row = detectors.parse_snapshot(_lane_xml(volume=5, speed=60, occupancy=-1))[0]
    assert row["occupancy_pct"] is None and row["speed_kmh"] == 60.0


def test_a_lane_with_traffic_keeps_its_measured_speed():
    row = detectors.parse_snapshot(_lane_xml(volume=3, speed=42, occupancy=4))[0]
    assert (row["speed_kmh"], row["volume"], row["occupancy_pct"]) == (42.0, 3.0, 4.0)


def test_prefetch_skips_cached_files_without_reading_them(stub, monkeypatch):
    path = archive.cache_path("detectors", "20990101-0000")
    path.parent.mkdir(parents=True)
    path.write_bytes(gzip.compress(b"<raw_speed_volume_list/>"))
    monkeypatch.setattr(archive, "read_cached",
                        lambda *a: pytest.fail("prefetch decompressed a cached file"))
    counts = archive.prefetch("detectors", ["20990101-0000"], log=io.StringIO())
    assert counts["cached"] == 1 and stub.hits == []


def test_a_bad_file_skipped_by_prefetch_is_still_caught_when_read(stub):
    good = (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes()
    stub.respond = lambda path: (200, good)
    path = archive.cache_path("detectors", "20990101-0000")
    path.parent.mkdir(parents=True)
    path.write_bytes(gzip.compress(b"<html>error page</html>"))
    archive.prefetch("detectors", ["20990101-0000"], log=io.StringIO())   # skipped: exists
    assert archive.fetch("detectors", "20990101-0000") == good            # caught on read


# ---------------------------------------------------------------- timelines (23 Sep)

import json as _json
from urllib.parse import parse_qs, urlparse


def _stn(*messages):
    """An STN snapshot from (id, status, announced, content) tuples."""
    body = "".join(
        f"<message><INCIDENT_NUMBER>IN-T</INCIDENT_NUMBER><ID>{i}</ID>"
        f"<INCIDENT_STATUS_EN>{st}</INCIDENT_STATUS_EN><ANNOUNCEMENT_DATE>{at}</ANNOUNCEMENT_DATE>"
        f"<LOCATION_EN>Wong Chuk Hang Road</LOCATION_EN><CONTENT_EN>{text}</CONTENT_EN></message>"
        for i, st, at, text in messages)
    return f"<list>{body}</list>".encode()


def _timeline(monkeypatch, *snapshots, unreadable=None):
    monkeypatch.setattr(incidents.archive, "iter_snapshots",
                        lambda feed, ts: ((f"20260509-{n:04d}", b) for n, b in enumerate(snapshots)))
    msgs = incidents.collect_messages(list(range(len(snapshots))), unreadable)
    return incidents.build_incidents(msgs)[0]


NEW_MSG = ("1", "NEW", "2026-05-09T09:29:00", "Due to traffic accident, part of the lanes is closed.")


def test_a_closed_status_arriving_on_an_existing_message_is_kept(monkeypatch):
    """TD closes an incident by switching its last message to CLOSED, same ID.
    Keeping messages as first seen lost ~70% of closures."""
    later = ("2", "UPDATED", "2026-05-09T10:32:00", "Traffic is busy now.")    # no re-open wording
    row = _timeline(monkeypatch, _stn(NEW_MSG), _stn(NEW_MSG, later),
                    _stn(("2", "CLOSED") + later[2:]))
    assert row["right_censored"] is False
    assert row["closed_at"].startswith("2026-05-09T10:32")
    assert row["clearance_source"] == "CLOSED status" and row["duration_min"] == 63


def test_a_captured_reopened_message_is_the_clearance_when_closed_was_missed(monkeypatch):
    reopened = ("2", "UPDATED", "2026-05-09T10:32:00",
                "Part of the lanes which was closed due to traffic accident is re-opened to all traffic.")
    row = _timeline(monkeypatch, _stn(NEW_MSG), _stn(NEW_MSG, reopened))
    assert row["closed_at"].startswith("2026-05-09T10:32")
    assert row["clearance_source"] == "re-opened message" and row["duration_min"] == 63


def test_a_partial_reopening_is_not_a_clearance(monkeypatch):
    partial = ("2", "UPDATED", "2026-05-09T10:00:00",
               "The fast lane is re-opened to all traffic. The slow lane remains closed.")
    row = _timeline(monkeypatch, _stn(NEW_MSG), _stn(NEW_MSG, partial))
    assert row["right_censored"] is True and row["duration_min"] == ""


def test_a_cancelled_traffic_arrangement_is_a_clearance(monkeypatch):
    cancelled = ("2", "UPDATED", "2026-08-19T13:23:00",
                 "The one-lane-two-way traffic arrangement which was implemented due to "
                 "traffic accident is now cancelled.")
    row = _timeline(monkeypatch, _stn(("1", "NEW", "2026-08-19T11:31:00", "Accident.")),
                    _stn(cancelled))
    assert row["duration_min"] == 112


def test_nul_padding_is_recovered_and_truncation_still_raises():
    doc = _stn(NEW_MSG)
    assert common.parse_xml(doc + b"\r\n" + b"\x00" * 118).tag == "list"
    with pytest.raises(Exception):
        common.parse_xml(doc[:-20])


def test_a_truncated_stn_snapshot_is_skipped_and_reported_not_fatal(monkeypatch):
    skipped = []
    later = ("2", "UPDATED", "2026-05-09T10:32:00", "Lanes are re-opened to all traffic.")
    row = _timeline(monkeypatch, _stn(NEW_MSG), _stn(NEW_MSG, later)[:-25],
                    _stn(NEW_MSG, later) + b"\x00" * 50, unreadable=skipped)
    assert skipped == ["20260509-0001"]                  # the truncated one only
    assert row["duration_min"] == 63                     # the padded one was used


def test_a_truncated_detector_snapshot_is_skipped_not_fatal(monkeypatch):
    good = (FIXTURES / "detector_snapshot_20260921-0830.xml").read_bytes()
    monkeypatch.setattr(detectors, "window_timestamps", lambda a, b: ["a", "b"])
    monkeypatch.setattr(detectors.archive, "iter_snapshots",
                        lambda feed, ts: iter([("a", good[:5000]), ("b", good)]))
    rows = detectors.load_window(T0.replace(hour=8, minute=21), T0.replace(hour=8, minute=22))
    assert rows and {r["timestamp"].strftime("%H:%M:%S") for r in rows} == {"08:21:00", "08:21:30"}


@pytest.mark.parametrize("start,end,expected", [
    ("2026-03-22", "2026-06-05", [("20260322", "20260331"), ("20260401", "20260430"),
                                  ("20260501", "20260531"), ("20260601", "20260605")]),
    ("2026-09-18", "2026-09-18", [("20260918", "20260918")]),
    ("2025-12-20", "2026-01-10", [("20251220", "20251231"), ("20260101", "20260110")]),
    ("2024-02-10", "2024-03-02", [("20240210", "20240229"), ("20240301", "20240302")]),  # leap year
])
def test_archive_listings_are_requested_a_month_at_a_time(stub, start, end, expected):
    """The archive returns at most 10,000 versions per request; six months of
    STN alone is ~18,400."""
    asked = []

    def respond(path):
        q = parse_qs(urlparse(path).query)
        asked.append((q["start"][0], q["end"][0]))
        return 200, _json.dumps({"timestamps": [f"{q['start'][0]}-0000",
                                                f"{q['end'][0]}-2359"]}).encode()
    stub.respond = respond
    stamps = archive.list_versions("stn", start, end)
    assert asked == expected
    assert stamps == list(dict.fromkeys(s for a, b in expected for s in (f"{a}-0000", f"{b}-2359")))
