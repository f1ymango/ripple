"""Bound real transport output and record the setting with model evidence."""
import json
from types import SimpleNamespace

from src import llm


def test_transport_bounds_output_and_logs_the_same_limit(tmp_path, monkeypatch):
    requests = []

    def post(url, **kwargs):
        requests.append(kwargs)
        return SimpleNamespace(raise_for_status=lambda: None,
                               json=lambda: {"message": {"content": '{"ok": true}'}})

    monkeypatch.setattr(llm.requests, "post", post)
    monkeypatch.setattr(llm, "LOG_DIR", tmp_path)
    response = llm.complete_json(component="mock-test", model="mock-model",
                                 system="mock prompt", user="mock input",
                                 schema={"type": "object"}, temperature=0)
    assert response == '{"ok": true}'
    assert requests[0]["json"]["options"]["num_predict"] == 2048
    entry = json.loads(next(tmp_path.glob("*.jsonl")).read_text(encoding="utf-8"))
    assert entry["max_output_tokens"] == requests[0]["json"]["options"]["num_predict"]
    assert entry["response"] == response
