"""Evidence-time and fallback checks using the committed real TD archive."""
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.console import app, incident_playback as playback

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "demo_incident_messages.jsonl"


@pytest.fixture
def messages():
    records, errors = playback.read_messages(ARCHIVE)
    assert not errors
    return records


@pytest.mark.parametrize("cursor,expected", [
    ("2026-05-15T08:50:00+08:00", None),
    ("2026-05-15T09:00:00+08:00", None),
    ("2026-05-15T09:01:00+08:00", "138270"),
    ("2026-05-15T09:35:00+08:00", "138270"),
    ("2026-05-15T01:36:00Z", "138272"),
    ("2026-05-15T09:40:00+08:00", "138272"),
    ("not-a-time", None),
])
def test_message_is_withheld_until_publication_even_inside_current_bin(messages, cursor, expected):
    message = playback.latest_at(messages, "IN-26-03365", cursor)
    assert (message.message_id if message else None) == expected


def test_wrong_day_and_unknown_incident_never_reuse_demo_text(messages):
    assert playback.for_window(messages, "2026-09-21T08:00:00+08:00",
                               "2026-09-21T09:00:00+08:00") == []
    assert playback.latest_at(messages, "unknown", "2026-05-15T09:40:00+08:00") is None


def test_window_keeps_earlier_same_day_message_for_late_start(messages):
    selected = playback.for_window(messages, "2026-05-15T09:20:00+08:00",
                                    "2026-05-15T10:35:00+08:00")
    assert playback.latest_at(selected, "IN-26-03365", "2026-05-15T09:20:00+08:00").message_id == "138270"


def test_missing_and_malformed_archives_do_not_supply_fallback_text(tmp_path):
    assert playback.read_messages(tmp_path / "absent.jsonl") == ([], [])
    messages, errors = playback.read_messages(ROOT / "tests/fixtures/mock_archived_messages_invalid.jsonl")
    assert messages == []
    assert len(errors) == 3


def test_callout_uses_named_eastbound_road_and_reports_approximation(messages):
    import json
    from dataclasses import replace
    from src.console import incident_callout
    geometry = json.loads((ROOT / "tests/fixtures/mock_incident_geometry.json").read_text(encoding="utf-8"))
    point = incident_callout.reported_area(messages[0], geometry)
    assert point["edge_id"] == "mock_eastbound"
    assert point["position"] == pytest.approx([114.165, 22.25])
    partial = incident_callout.annotation(messages[0], None, geometry)
    assert "Partial lane closure reported" in partial["label"]
    assert "Approx. location" in partial["label"]
    latest = incident_callout.annotation(messages[-1], None, geometry)
    assert "All lanes reported closed" in latest["label"]
    cleared = incident_callout.annotation(messages[-1], playback.local_time("2026-05-15T10:02:00+08:00"), geometry)
    assert "Clearance reported" in cleared["label"]
    assert "closed" not in cleared["label"]
    assert incident_callout.reported_area(messages[0], {"roads": []}) is None
    assert incident_callout.reported_area(replace(messages[0], english="Another road"), geometry) is None


def test_markers_preserve_exact_update_and_clearance_report_times(messages, tmp_path, monkeypatch):
    # Real announcement/clearance row, also used in test_console.py.
    pd.DataFrame([{"incident_number": "IN-26-03365", "corridor_road": "aberdeen tunnel",
                   "new_at": "2026-05-15T09:01:00+08:00",
                   "closed_at": "2026-05-15T10:02:00+08:00"}]).to_csv(
        tmp_path / "incidents.csv", index=False)
    monkeypatch.setattr(app, "INCIDENT_GLOB", str(tmp_path / "incidents.csv"))
    markers = app.load_incident_markers("2026-05-15T07:55:00+08:00",
                                        "2026-05-15T10:35:00+08:00", messages)
    assert list(markers["bin_start"]) == [
        "2026-05-15T09:01:00+08:00", "2026-05-15T09:36:00+08:00",
        "2026-05-15T10:02:00+08:00"]
    assert list(markers["label"]) == ["IN-26-03365 TD report", "IN-26-03365 TD update",
                                      "IN-26-03365 TD clearance report"]


def test_card_updates_and_rewinds_without_retaining_future_message(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "INCIDENT_GLOB", str(tmp_path / "absent.csv"))
    script = '''
import pandas as pd
import streamlit as st
from pathlib import Path
from src.console import app, incident_playback
messages, _ = incident_playback.read_messages(Path(app.ROOT) / "data/demo_incident_messages.jsonl")
cursor = st.selectbox("Cursor", ["09:00", "09:05", "09:35", "09:40", "10:05"])
markers = pd.DataFrame([{"incident_id": "IN-26-03365", "kind": "clearance",
                         "bin_start": "2026-05-15T10:02:00+08:00"}])
app.show_incident_card(messages, "2026-05-15T" + cursor + ":00+08:00", markers)
'''
    at = AppTest.from_string(script).run()
    assert not at.exception
    assert not at.text
    assert "Later message text is withheld" in " ".join(c.value for c in at.caption)
    at.selectbox[0].select("09:40").run()
    assert not at.exception
    assert "全線現已封閉" in " ".join(t.value for t in at.text)
    at.selectbox[0].select("10:05").run()
    assert "TD clearance report · 10:02" in " ".join(i.value for i in at.info)
    at.selectbox[0].select("09:05").run()
    assert not at.exception
    assert not at.info
    assert "part of the lanes" in " ".join(t.value for t in at.text)
    assert "全線現已封閉" not in " ".join(t.value for t in at.text)
