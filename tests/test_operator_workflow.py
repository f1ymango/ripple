"""Real operator controls tested against explicitly synthetic saved artifacts."""
from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing
from pathlib import Path
import shutil

import pytest
from streamlit.testing.v1 import AppTest

from src.console import app, operator_workflow, recommendation

FIXTURES = Path(__file__).parent / "fixtures" / "mock_recommendation"
SCENARIO = (0.5, 60.0, 42)


@pytest.fixture
def saved(tmp_path, monkeypatch):
    results = tmp_path / "runs"
    plans = tmp_path / "plans"
    briefings = tmp_path / "briefings"
    data = tmp_path / "data"
    for directory in (results, plans, briefings, data):
        directory.mkdir()
    for source in FIXTURES.glob("mock_p*.json"):
        shutil.copy(source, (results if "_result" in source.name else plans) / source.name)
    shutil.copy(FIXTURES / "mock_generation-inputs.json", plans / "generation-inputs.json")
    briefing = briefings / "mock_briefing.json"
    shutil.copy(FIXTURES / briefing.name, briefing)
    shutil.copy(Path(__file__).resolve().parents[1] / "data/detectors.csv", data / "detectors.csv")
    audit = tmp_path / "mock_audit_log.jsonl"
    for variable, path in {"RIPPLE_RESULTS_DIR": results, "RIPPLE_PLANS_DIR": plans,
                           "RIPPLE_BRIEFINGS_DIR": briefings, "RIPPLE_DATA_DIR": data,
                           "RIPPLE_AUDIT_LOG": audit}.items():
        monkeypatch.setenv(variable, str(path))
    return results, plans, briefing, audit


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def change(path, edit):
    value = read(path)
    edit(value)
    path.write_text(json.dumps(value), encoding="utf-8")


def selected(saved):
    results, plans, briefing_path, _ = saved
    comparison, reason = recommendation.load_comparison(results, plans, "MOCK-INCIDENT", SCENARIO)
    assert comparison is not None, reason
    return comparison, operator_workflow.load_briefing(briefing_path, comparison)


@pytest.mark.parametrize("problem", ["missing_sidecar", "changed_result", "changed_plan",
                                    "changed_generation_inputs", "mixed_simulation"])
def test_invalid_input_identity_withholds_recommendation(saved, problem):
    results, plans, _, _ = saved
    if problem == "missing_sidecar":
        (results / "mock_p2_result.provenance.json").unlink()
    elif problem == "changed_result":
        change(results / "mock_p2_result.json",
               lambda r: r["metrics"].update(total_vehicle_hours_delay=70))
    elif problem == "changed_plan":
        change(plans / "mock_p2.json", lambda p: p["diversions"][0].update(share=0.4))
    elif problem == "changed_generation_inputs":
        change(plans / "generation-inputs.json",
               lambda g: g["policy_context"].update(active_until="2026-05-15T11:00:00+08:00"))
    else:
        change(results / "mock_p2_result.provenance.json",
               lambda p: p["simulation_inputs"].update(mock_network="0" * 64))
    comparison, reason = recommendation.load_comparison(results, plans, "MOCK-INCIDENT", SCENARIO)
    assert comparison is None and reason


@pytest.mark.parametrize("problem", ["wrong_run", "wrong_sources", "wrong_sign", "long_message"])
def test_unmatched_briefing_cannot_be_used_for_a_decision(saved, problem):
    comparison, _ = selected(saved)
    path = saved[2]
    if problem == "wrong_run":
        change(path, lambda b: b.update(run_id="mock-other-run"))
    elif problem == "wrong_sources":
        change(path, lambda b: b["sources"].__setitem__(0, "results/runs/mock-other.json"))
    elif problem == "wrong_sign":
        change(path, lambda b: b["vms_messages"][0].update(sign_id="MOCK-OTHER-SIGN"))
    else:
        change(path, lambda b: b["vms_messages"][0].update(text_zh="字" * 61))
    with pytest.raises(ValueError):
        operator_workflow.load_briefing(path, comparison)


def decide(saved, key, action="approved", operator="Mock operator"):
    results, plans, briefing, audit = saved
    return operator_workflow.record_decision(
        results_dir=results, plans_dir=plans, briefing_path=briefing,
        incident_id="MOCK-INCIDENT", scenario=SCENARIO, displayed_key=key,
        audit_path=audit, action=action, operator=operator, note="Mock review note.")


def test_changed_draft_between_display_and_click_is_not_approved(saved):
    comparison, briefing = selected(saved)
    shown_key = operator_workflow.evidence_key(comparison, briefing)
    change(saved[2], lambda b: b.update(operator_briefing_en="Changed mock draft awaiting review."))
    with pytest.raises(ValueError, match="Inputs changed"):
        decide(saved, shown_key)
    assert not saved[3].exists()


def test_changed_result_between_display_and_click_is_not_approved(saved):
    comparison, briefing = selected(saved)
    shown_key = operator_workflow.evidence_key(comparison, briefing)
    change(saved[0] / "mock_p2_result.json", lambda r: r["metrics"].update(co2_kg=1))
    with pytest.raises(ValueError, match="Decision unavailable"):
        decide(saved, shown_key)
    assert not saved[3].exists()


def test_decisions_append_the_existing_audit_shape_and_require_an_operator(saved):
    comparison, briefing = selected(saved)
    key = operator_workflow.evidence_key(comparison, briefing)
    with pytest.raises(ValueError, match="operator"):
        decide(saved, key, operator=" ")
    assert not saved[3].exists()
    first = decide(saved, key, operator="模擬操作員")
    second = decide(saved, key, "rejected")
    records = [json.loads(line) for line in saved[3].read_text(encoding="utf-8").splitlines()]
    assert records == [first, second]
    assert set(first) == {"timestamp", "incident_id", "run_id", "plan_id", "action", "operator", "note"}
    assert first["timestamp"].endswith("+08:00")
    assert first["plan_id"] == "P2" and key in first["note"]
    assert first["operator"] == "模擬操作員"


def _append_many(path, comparison, briefing, worker, note):
    """A spawned writer exercises the native OS lock, including Windows."""
    for _ in range(5):
        operator_workflow.append_action(path, comparison, briefing, "approved",
                                        f"模擬操作員 {worker}", note)


def test_concurrent_processes_append_complete_utf8_audit_records(saved):
    comparison, briefing = selected(saved)
    note = "模擬審核記錄" * 8192  # Larger than the text stream's write buffer.
    with ProcessPoolExecutor(max_workers=4,
                             mp_context=multiprocessing.get_context("spawn")) as pool:
        writers = [pool.submit(_append_many, saved[3], comparison, briefing, worker, note)
                   for worker in range(4)]
        for writer in writers:
            writer.result(timeout=60)
    records = [json.loads(line) for line in saved[3].read_text(encoding="utf-8").splitlines()]
    assert len(records) == 20
    for worker in range(4):
        assert sum(row["operator"] == f"模擬操作員 {worker}" for row in records) == 5
    assert all(row["note"].startswith(note + "\nEvidence SHA-256: ") for row in records)


def _hold_lock(path, ready, release):
    with operator_workflow.audit_lock(path):
        ready.set()
        if not release.wait(15):
            raise RuntimeError("Test lock was not released.")


def _write_after_signal(path, comparison, briefing, started, done):
    started.set()
    operator_workflow.append_action(path, comparison, briefing, "approved", "Mock operator", "")
    done.set()


def test_audit_writer_waits_for_another_process_to_release_the_lock(saved):
    comparison, briefing = selected(saved)
    context = multiprocessing.get_context("spawn")
    ready, release, started, done = [context.Event() for _ in range(4)]
    holder = context.Process(target=_hold_lock, args=(saved[3], ready, release))
    writer = context.Process(target=_write_after_signal,
                             args=(saved[3], comparison, briefing, started, done))
    holder.start()
    try:
        assert ready.wait(15)
        writer.start()
        assert started.wait(15)
        assert not done.wait(0.5)
        assert not saved[3].exists()
    finally:
        release.set()
        holder.join(15)
        if writer.pid is not None:
            writer.join(15)
        for process in (holder, writer):
            if process.is_alive():
                process.terminate()
                process.join(5)
    assert holder.exitcode == writer.exitcode == 0
    assert done.is_set()
    assert read(saved[3])["action"] == "approved"


def test_ui_records_one_view_and_both_decisions_without_duplicate_views(saved):
    at = AppTest.from_file(str(Path(app.__file__))).run()
    assert not at.exception
    approval = lambda: next(b for b in at.button if b.label == "Record approval")
    rejection = lambda: next(b for b in at.button if b.label == "Record rejection")
    assert approval().disabled and rejection().disabled
    at.text_input[0].input("Mock operator").run()
    assert not approval().disabled
    approval().click().run()
    assert not at.exception
    assert any("approved" in success.value for success in at.success)
    rejection().click().run()
    assert not at.exception
    records = [json.loads(line) for line in saved[3].read_text(encoding="utf-8").splitlines()]
    assert [row["action"] for row in records] == ["viewed", "approved", "rejected"]


def test_missing_results_leave_controls_disabled_and_write_no_audit(saved):
    for path in saved[0].glob("*.json"):
        path.unlink()
    at = AppTest.from_file(str(Path(app.__file__))).run()
    assert not at.exception
    decisions = [b for b in at.button if b.label.startswith("Record ")]
    assert len(decisions) == 2 and all(b.disabled for b in decisions)
    assert not saved[3].exists()


def test_malformed_run_identity_is_reported_without_crashing_the_console(saved):
    change(saved[0] / "mock_p2_result.json", lambda r: r.update(run_id=["invalid"]))
    at = AppTest.from_file(str(Path(app.__file__))).run()
    assert not at.exception
    assert any("has no run_id" in warning.value for warning in at.warning)
    assert not saved[3].exists()
