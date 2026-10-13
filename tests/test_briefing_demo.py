"""Fixture model demonstration stays outside real result publication."""
import json

import pytest

from src import llm
from src.briefing import demo
from src.generation import load_json


def test_demo_checks_saved_provenance_and_logs_model_call(tmp_path, monkeypatch):
    reply = load_json(demo.FIXTURES / "mock_briefing_reply.json")
    monkeypatch.setattr(demo, "FIXTURES", tmp_path)
    monkeypatch.setattr(llm, "LOG_DIR", tmp_path / "ai-log")
    monkeypatch.setattr(llm, "_send", lambda **kwargs: json.dumps(reply))
    out = tmp_path / "mock_demo.json"
    result = demo.demo(out)
    assert load_json(out) == result
    assert result["recommended_plan_id"] == "P2"
    assert "{{" not in result["operator_briefing_en"]
    log = next((tmp_path / "ai-log").glob("*.jsonl"))
    assert json.loads(log.read_text(encoding="utf-8"))["component"] == "briefing"


@pytest.mark.parametrize("name", ["real.json", "mock_demo.txt", "outside/mock_demo.json"])
def test_demo_refuses_nonfixture_destination_before_model_call(tmp_path, monkeypatch, name):
    monkeypatch.setattr(demo, "FIXTURES", tmp_path)
    monkeypatch.setattr(llm, "_send", lambda **kwargs: pytest.fail("unexpected model call"))
    with pytest.raises(ValueError, match="Fixture output"):
        demo.demo(tmp_path / name)


def test_demo_preserves_existing_output_before_model_call(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "FIXTURES", tmp_path)
    monkeypatch.setattr(llm, "_send", lambda **kwargs: pytest.fail("unexpected model call"))
    out = tmp_path / "mock_existing.json"
    out.write_text("existing evidence", encoding="utf-8")
    with pytest.raises(ValueError, match="new fixture output"):
        demo.demo(out)
    assert out.read_text(encoding="utf-8") == "existing evidence"
