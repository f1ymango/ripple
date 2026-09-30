"""Tests for the Incident Reader, run without any LLM.

The model is replaced by tests/fixtures/mock_llm_reply.json, a hand-written
stand-in reply for the real STN message in stn_snapshot_20260915-0000.xml.
"""
import json
from pathlib import Path

import pytest

from src import llm
from src.loaders.corridor import CORRIDOR_ROAD_NAMES
from src.reader import reader, sample

FIXTURES = Path(__file__).parent / "fixtures"
SNAPSHOT = (FIXTURES / "stn_snapshot_20260915-0000.xml").read_bytes()
MOCK_REPLY = (FIXTURES / "mock_llm_reply.json").read_text(encoding="utf-8")


@pytest.fixture
def stn():
    return sample.parse_messages(SNAPSHOT)[0]


@pytest.fixture
def model_replies(monkeypatch, tmp_path):
    """Queue the replies the fake model will give; the AI log goes to a temp dir."""
    replies = []
    monkeypatch.setattr(llm, "_send", lambda **kwargs: replies.pop(0))
    monkeypatch.setattr(llm, "LOG_DIR", tmp_path)
    return replies


def logged_calls(tmp_path):
    return [json.loads(line) for f in tmp_path.glob("*.jsonl")
            for line in f.read_text(encoding="utf-8").splitlines()]


def test_parse_messages_reads_both_languages_and_empty_fields(stn):
    assert stn["INCIDENT_NUMBER"] == "IN-26-06772"
    assert stn["CONTENT_EN"].startswith("Due to watermain emergency works")
    assert stn["CONTENT_CN"].startswith("因水管緊急維修")
    assert stn["DISTRICT_EN"] == "" and stn["LATITUDE"] == ""


def test_feed_fields_are_copied_and_model_fields_extracted(stn, model_replies, tmp_path):
    model_replies.append(MOCK_REPLY)
    incident = reader.read_message(stn)

    assert incident["incident_id"] == "IN-26-06772"
    assert incident["announced_at"] == "2026-09-14T23:00:00+08:00"
    assert incident["status"] == "NEW"
    assert incident["source_message_zh"] == stn["CONTENT_CN"]
    assert (incident["lat"], incident["lon"], incident["coords_source"]) == (None, None, "none")
    assert incident["closed_at"] is None
    assert incident["lanes_closed"] == ["slow"]
    assert incident["district"] is None  # empty in the feed, and never guessed
    assert incident["in_scope"] is False  # Wing Tai Road is in Chai Wan

    [call] = logged_calls(tmp_path)
    assert call["component"] == "reader"
    assert call["response"] == MOCK_REPLY
    assert "Wing Tai Road Garden" in call["user"]


def test_model_never_sees_coordinates_or_ids(stn, model_replies, tmp_path):
    model_replies.append(MOCK_REPLY)
    reader.read_message(stn)
    sent = json.loads(logged_calls(tmp_path)[0]["user"])
    assert not {"LATITUDE", "LONGITUDE", "ID", "INCIDENT_NUMBER"} & sent.keys()


def test_invalid_reply_is_retried_once(stn, model_replies, tmp_path):
    model_replies.extend(["not json", MOCK_REPLY])
    assert reader.read_message(stn)["road_name"] == "Wing Tai Road"
    assert len(logged_calls(tmp_path)) == 2


@pytest.mark.parametrize("bad_field", [
    {"lat": 22.26},                  # the model must not produce coordinates
    {"confidence": 1.4},             # outside 0..1
    {"lanes_closed": ["left"]},      # not a lane name in the contract
    {"lanes_closed": ["unspecified", "fast"]},  # 'unspecified' stands alone
    {"lanes_closed": ["all", "slow"]},          # so does 'all'
    {"incident_type": "accident"},   # not in the incident_type list
    {"near_landmark": "null"},       # the text "null" instead of JSON null
    {"in_scope": True},              # scope is decided by code, not the model
])
def test_reply_failing_the_contract_twice_is_flagged(stn, model_replies, bad_field):
    bad = json.dumps(json.loads(MOCK_REPLY) | bad_field)
    model_replies.extend([bad, bad])
    with pytest.raises(reader.ReaderError, match="IN-26-06772"):
        reader.read_message(stn)


def test_unspecified_lanes_pass_the_contract(stn, model_replies):
    model_replies.append(json.dumps(json.loads(MOCK_REPLY) | {"lanes_closed": ["unspecified"],
                                                              "lanes_total": None}))
    assert reader.read_message(stn)["lanes_closed"] == ["unspecified"]


def test_pick_is_prefix_stable():
    # Clearly fake messages: two per incident, ten incidents.
    messages = [{"stn": {"ID": str(i), "INCIDENT_NUMBER": f"mock-{i // 2}"}} for i in range(20)]
    first_five = sample.pick(messages, 5, seed=42)
    assert first_five == sample.pick(messages, 8, seed=42)[:5]
    assert len({m["stn"]["INCIDENT_NUMBER"] for m in first_five}) == 5  # one per incident


@pytest.mark.parametrize("snapshot, on_corridor", [
    ("stn_snapshot_20260915-0000.xml", False),  # Wing Tai Road, Chai Wan
    ("stn_snapshot_20260918-1828.xml", True),   # Pok Fu Lam Road lanes re-opened
    ("stn_snapshot_20260919-1757.xml", True),   # busy roads, Wong Nai Chung Gap Flyover second
])
def test_scope_comes_from_the_corridor_road_list(snapshot, on_corridor):
    stn = sample.parse_messages((FIXTURES / snapshot).read_bytes())[0]
    assert reader.CORRIDOR_ROAD_NAMES is CORRIDOR_ROAD_NAMES
    assert reader.names_corridor_road(stn) is on_corridor


def test_alternative_route_and_chinese_road_use_shared_scope():
    assert "Stubbs Road" in CORRIDOR_ROAD_NAMES
    assert reader.names_corridor_road({"CONTENT_EN": "Stubbs Road is closed", "CONTENT_CN": ""})
    assert reader.names_corridor_road({"CONTENT_EN": "", "CONTENT_CN": "華富道封閉"})


def test_corridor_road_only_as_destination_does_not_count():
    # Made-up variation of real message 146443: its road swapped for one off the corridor.
    stn = {"CONTENT_EN": "Traffic at the following road section has resumed normal: "
                         "– Gloucester Road (Canal Road Flyover bound).",
           "CONTENT_CN": ""}
    assert not reader.names_corridor_road(stn)


@pytest.mark.parametrize("incident_type, in_scope", [
    ("traffic_accident", True),
    ("public_transport_notice", False),
])
def test_corridor_message_scope_depends_on_type(model_replies, incident_type, in_scope):
    # The real Pok Fu Lam Road message; the model's reply is the mock with its type swapped.
    stn = sample.parse_messages((FIXTURES / "stn_snapshot_20260918-1828.xml").read_bytes())[0]
    model_replies.append(json.dumps(json.loads(MOCK_REPLY) | {"incident_type": incident_type}))
    assert reader.read_message(stn)["in_scope"] is in_scope
