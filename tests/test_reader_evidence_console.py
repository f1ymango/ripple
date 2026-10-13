"""Recorded inference identity checks; use the committed real B evidence."""
import json
from pathlib import Path

import pytest

from src.console import incident_playback, reader_evidence

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/demo_incident_messages.jsonl"
OUTPUT = ROOT / "results/reader/2026-09-29T1608_qwen3-8b.jsonl"
LOG = ROOT / "evidence/ai-log/2026-09-29.jsonl"


@pytest.mark.parametrize("message_id,lanes,confidence", [
    ("138270", ["unspecified"], 0.7),
    ("138272", ["all"], 0.9),
])
def test_real_saved_output_matches_its_own_message_and_call(message_id, lanes, confidence):
    messages, _ = incident_playback.read_messages(ARCHIVE)
    message = next(m for m in messages if m.message_id == message_id)
    record = reader_evidence.read(message, ARCHIVE, OUTPUT, LOG)
    assert record["incident"]["lanes_closed"] == lanes
    assert record["incident"]["confidence"] == confidence
    assert record["model"] == "qwen3:8b"
    assert record["incident"]["source_message_en"] == message.english


@pytest.mark.parametrize("alteration", ["extraction", "logged_input", "duplicate", "publication"])
def test_mixed_or_changed_evidence_cannot_be_displayed(tmp_path, alteration):
    rows = [json.loads(line) for line in OUTPUT.read_text(encoding="utf-8").splitlines()]
    logs = [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines()]
    raw = [json.loads(line) for line in ARCHIVE.read_text(encoding="utf-8").splitlines()]
    if alteration == "extraction":
        rows[0]["incident"]["lanes_closed"] = ["all"]
    elif alteration == "logged_input":
        user = json.loads(logs[0]["user"])
        user["CONTENT_EN"] = "mock_changed_source"
        logs[0]["user"] = json.dumps(user)
    elif alteration == "duplicate":
        rows.append(rows[0])
    else:
        raw[0]["stn"]["ANNOUNCEMENT_DATE"] = "2026-05-15T09:36:00"
    paths = [tmp_path / f"mock_{name}.jsonl" for name in ("archive", "output", "log")]
    for path, data in zip(paths, (raw, rows, logs)):
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in data), encoding="utf-8")
    messages, _ = incident_playback.read_messages(ARCHIVE)
    with pytest.raises(ValueError):
        reader_evidence.read(messages[0], *paths)


def test_missing_saved_output_is_unavailable_not_fabricated(tmp_path):
    messages, _ = incident_playback.read_messages(ARCHIVE)
    assert reader_evidence.read(messages[0], ARCHIVE, tmp_path / "mock_missing.jsonl", LOG) is None


def test_recorded_candidates_are_separate_and_withheld_before_the_report():
    from streamlit.testing.v1 import AppTest

    script = f'''
from pathlib import Path
import streamlit as st
from src.console import incident_playback, recorded_plans
root = Path({str(ROOT)!r})
messages, _ = incident_playback.read_messages(root / "data/demo_incident_messages.jsonl")
cursor = st.selectbox("Cursor", ["09:00", "09:05"])
message = incident_playback.latest_at(messages, "IN-26-03365", "2026-05-15T" + cursor + ":00+08:00")
recorded_plans.show(root, message)
'''
    at = AppTest.from_string(script).run()
    assert not at.exception
    assert not at.json
    at.selectbox[0].select("09:05").run()
    assert not at.exception
    assert len(at.json) == 3
    assert "not evaluated" in " ".join(w.value for w in at.warning)
    assert "later-known incident details" in " ".join(c.value for c in at.caption)
    assert "Real availability is unconfirmed" in " ".join(c.value for c in at.caption)
    assert not at.button
    at.selectbox[0].select("09:00").run()
    assert not at.json
