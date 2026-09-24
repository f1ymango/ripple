"""Tests for the gold set: sampling it, validating labels, and scoring a run. No LLM, no network.

Messages built here are clearly fake (IDs "mock-..."), except the corridor
check, which reuses the real Pok Fu Lam Road fixture.
"""
import json
from pathlib import Path

import jsonschema
import pytest

from src.reader import gold, sample, score

FIXTURES = Path(__file__).parent / "fixtures"
POK_FU_LAM = sample.parse_messages((FIXTURES / "stn_snapshot_20260918-1828.xml").read_bytes())[0]


def fake_message(message_id: int, incident: str, text: str = "Mock Road is busy.") -> dict:
    return {"archive_time": "20260101-0000",
            "stn": {"ID": str(message_id), "INCIDENT_NUMBER": incident,
                    "CONTENT_EN": text, "CONTENT_CN": ""}}


def label(message_id: str, **fields) -> dict:
    """A valid label for a made-up message, with any field overridden."""
    return {"message_id": message_id, "incident_id": f"mock-{message_id}",
            "road_name": "Mock Road", "direction": "Mock bound", "near_landmark": None,
            "between_landmark": None, "incident_type": "traffic_accident",
            "lanes_closed": ["fast"], "lanes_total": 2, "unsure": False, "comment": ""} | fields


# --- sampling -----------------------------------------------------------------

def test_worked_examples_are_read_from_the_prompt():
    assert sample.worked_example_ids() == {"146439", "146525", "146509", "146286", "146213"}


def test_gold_sample_never_picks_an_excluded_incident_or_a_worked_example():
    messages = [fake_message(i, f"mock-{i // 2}") for i in range(40)]  # 20 incidents
    messages.append(fake_message(146439, "mock-example"))               # a worked example's ID
    messages.append(fake_message(999, "mock-example"))                  # ...and its incident
    excluded = {"mock-0", "mock-1"} | sample.excluded_incidents(messages, [])

    chosen = sample.stratified(messages, n=100, n_corridor=0, excluded=excluded, seed=42)

    incidents = {m["stn"]["INCIDENT_NUMBER"] for m in chosen}
    assert len(chosen) == len(incidents) == 18  # 20 incidents, 2 excluded, one message each
    assert not incidents & {"mock-0", "mock-1", "mock-example"}


def test_strata_are_disjoint_and_corridor_messages_name_a_corridor_road():
    corridor = {"archive_time": "20260918-1828", "stn": POK_FU_LAM}
    same_incident = fake_message(1, POK_FU_LAM["INCIDENT_NUMBER"])  # off-corridor text, same incident
    messages = [corridor, same_incident] + [fake_message(i, f"mock-{i}") for i in range(10, 20)]

    chosen = sample.stratified(messages, n=5, n_corridor=3, excluded=set(), seed=42)

    by_stratum = {s: [m for m in chosen if m["stratum"] == s] for s in ("citywide", "corridor")}
    assert [m["stn"]["ID"] for m in by_stratum["corridor"]] == [POK_FU_LAM["ID"]]
    assert len(by_stratum["citywide"]) == 5
    assert POK_FU_LAM["INCIDENT_NUMBER"] not in {m["stn"]["INCIDENT_NUMBER"]
                                                 for m in by_stratum["citywide"]}


def test_sampler_refuses_to_overwrite(tmp_path, monkeypatch):
    out = tmp_path / "messages.jsonl"
    out.write_text("keep me\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["sample", "--start", "2026-09-15", "--end", "2026-09-21",
                                     "--out", str(out)])
    with pytest.raises(SystemExit):
        sample.main()
    assert out.read_text(encoding="utf-8") == "keep me\n"


# --- labels -------------------------------------------------------------------

@pytest.mark.parametrize("bad", [
    {"lanes_closed": ["unspecified", "slow"]},  # 'unspecified' stands alone
    {"road_name": "  "},                        # blank text: null is how 'not stated' is written
    {"incident_type": "crash"},                 # not in the contract
    {"lanes_total": 0},
    {"confidence": 0.9},                        # the model's opinion, never labelled
])
def test_bad_labels_are_refused(bad):
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        gold.validate(label("1", **bad))


def test_labels_round_trip_in_message_order(tmp_path):
    messages = [fake_message(i, f"mock-{i}") for i in (3, 1, 2)]
    path = tmp_path / "labels.jsonl"
    gold.save_labels({"2": label("2"), "3": label("3", lanes_closed=["unspecified"],
                                                  lanes_total=None)}, messages, path)
    assert [json.loads(line)["message_id"] for line in path.read_text().splitlines()] == ["3", "2"]
    assert gold.load_labels(path)["3"]["lanes_closed"] == ["unspecified"]


def test_labels_for_messages_outside_the_gold_set_are_refused(tmp_path):
    with pytest.raises(ValueError, match="not in the gold set"):
        gold.save_labels({"7": label("7")}, [fake_message(1, "mock-1")], tmp_path / "l.jsonl")


# --- scoring ------------------------------------------------------------------

def test_matching_rules():
    assert score.field_correct("road_name", " Aberdeen  tunnel", "Aberdeen Tunnel")
    assert not score.field_correct("road_name", "Aberdeen Tunnel Road", "Aberdeen Tunnel")
    assert score.field_correct("near_landmark", None, None)
    assert not score.field_correct("near_landmark", "Mock Park", None)
    assert score.field_correct("lanes_closed", ["slow", "fast"], ["fast", "slow"])
    assert not score.field_correct("lanes_closed", [], ["unspecified"])
    assert not score.field_correct("lanes_total", None, 2)


def test_score_counts_a_flagged_message_wrong_on_every_field():
    labels = {"1": label("1"), "2": label("2", unsure=True)}
    run = [{"message_id": "1", "incident": {f: label("1")[f] for f in gold.SCORED_FIELDS}},
           {"message_id": "2", "flagged": "mock failure"}]
    report = score.score(run, labels, {"1": "citywide", "2": "corridor"})

    assert report["all"]["flagged"] == 1 and report["all"]["labelled_unsure"] == 1
    assert report["all"]["fields"]["road_name"]["correct"] == 1
    assert report["all"]["fields"]["all_fields"]["correct"] == 1
    assert report["corridor"]["fields"]["all_fields"]["correct"] == 0
    assert report["corridor"]["not_all_right"] == ["2"]


def test_score_refuses_a_run_missing_labelled_messages():
    with pytest.raises(ValueError, match="no output"):
        score.score([], {"1": label("1")}, {})


def test_wilson_interval_brackets_the_rate_even_at_the_edges():
    low, high = score.wilson(90, 100)
    assert low < 0.9 < high and high - low < 0.13
    assert score.wilson(100, 100)[1] == 1.0 and score.wilson(100, 100)[0] < 1.0
    assert score.wilson(0, 0) is None
