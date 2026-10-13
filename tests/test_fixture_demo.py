"""The synthetic rehearsal must label its figures and isolate operator writes."""
import json
from streamlit.testing.v1 import AppTest

from src.console import fixture_demo


def test_rehearsal_labels_inputs_and_records_only_a_mock_decision(tmp_path, monkeypatch):
    capture = tmp_path / "mock_operator_capture"
    monkeypatch.setattr(fixture_demo, "CAPTURE", capture)
    real_audit = tmp_path / "real_audit_log.jsonl"
    real_audit.write_text("existing real record\n", encoding="utf-8")
    monkeypatch.setenv("RIPPLE_AUDIT_LOG", str(real_audit))
    at = AppTest.from_string("from src.console.fixture_demo import main\nmain()").run()
    assert not at.exception
    assert any("Every plan, figure and briefing here is mock" in item.value for item in at.warning)
    assert any("SYNTHETIC FIXTURE" in item.value for item in at.markdown)
    assert at.button[0].disabled
    at.text_input[0].input("Mock operator").run()
    at.text_area[0].input("Synthetic UI demonstration only.").run()
    at.button[0].click().run()
    assert not at.exception
    records = [json.loads(line) for line in
               (capture / "mock_audit_log.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [row["action"] for row in records] == ["viewed", "approved"]
    assert all(row["incident_id"] == "MOCK-INCIDENT" for row in records)
    assert "Evidence SHA-256:" in records[-1]["note"]
    assert real_audit.read_text(encoding="utf-8") == "existing real record\n"
    assert (capture / "runs/mock_p2_result.json").read_bytes() == (
        fixture_demo.FIXTURES / "mock_p2_result.json").read_bytes()


def test_rehearsal_preserves_and_rejects_changed_existing_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(fixture_demo, "CAPTURE", tmp_path / "mock_operator_capture")
    results, _, _, audit = fixture_demo.prepare()
    path = results / "mock_p2_result.json"
    original = json.loads(path.read_text(encoding="utf-8"))
    original["metrics"]["total_vehicle_hours_delay"] = 79
    changed = json.dumps(original)
    path.write_text(changed, encoding="utf-8")
    at = AppTest.from_string("from src.console.fixture_demo import main\nmain()").run()
    assert not at.exception
    assert any("Recommendation unavailable" in item.value for item in at.warning)
    assert all(button.disabled for button in at.button)
    assert not audit.exists()
    assert path.read_text(encoding="utf-8") == changed
