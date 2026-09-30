"""D/F handoff tests. Every fabricated traffic input lives in mock_* fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import jsonschema
import pytest

from src import llm
from src.briefing import run as briefing_run
from src.briefing.results import load_results, select
from src.briefing.writer import assemble, check_vms, write_briefing
from src.generation import load_json
from src.plans import run as plans_run
from src.plans.generator import generate, validate_plans
from src.plans.validator import CHECKS, validate_plan

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
READER_RUN = ROOT / "results" / "reader" / "2026-09-29T1608_qwen3-8b.jsonl"


@pytest.fixture
def inputs():
    incident = plans_run.read_incident(READER_RUN, "138270")
    return (incident, load_json(FIXTURES / "mock_plan_context.json"),
            load_json(FIXTURES / "mock_plan_set.json"))


@pytest.fixture
def model(monkeypatch, tmp_path):
    replies = []
    monkeypatch.setattr(llm, "_send", lambda **kwargs: replies.pop(0))
    monkeypatch.setattr(llm, "LOG_DIR", tmp_path / "ai-log")
    return replies


def logs(tmp_path):
    return [json.loads(line) for p in (tmp_path / "ai-log").glob("*.jsonl")
            for line in p.read_text(encoding="utf-8").splitlines()]


def artifacts():
    return [(f"results/runs/{r['run_id']}.json", r)
            for r in load_json(FIXTURES / "mock_evaluator_results.json")]


def checked(inputs):
    incident, context, value = inputs
    return validate_plans(value, context, incident)


def diversion(plan, via, share=0.5):
    plan["diversions"] = [{"od_group": "Mock origin->Mock destination", "via": via, "share": share}]


def test_generation_checks_plans_and_logs_retry_without_changing_source(inputs, model, tmp_path):
    incident, context, value = inputs
    original = deepcopy(incident)
    invalid = deepcopy(value)
    invalid["plans"][0]["vms"] = invalid["plans"][1]["vms"]
    model.extend([json.dumps(invalid), json.dumps(value)])
    plans = generate(incident, context)
    assert [p["plan_id"] for p in plans] == ["P0", "P1", "P2"]
    assert all(p["constraints_checked"] == CHECKS for p in plans)
    assert incident == original and incident["lanes_closed"] == ["unspecified"]
    calls = logs(tmp_path)
    assert [c["component"] for c in calls] == ["plans", "plans"]
    assert json.loads(calls[1]["user"])["previous_validation_errors"]


@pytest.mark.parametrize("via,error", [
    ("Missing route", "Unknown"), ("Mock Blocked", "blocked"),
    ("Mock Emergency Route", "emergency"), ("Mock Residential", "Residential"),
])
def test_route_checks_reject_unsupported_and_protected_diversions(inputs, via, error):
    incident, context, value = inputs
    plan = value["plans"][2]
    diversion(plan, via, 0.01)  # 1% of total demand is still 100% of diverted demand.
    with pytest.raises(ValueError, match=error):
        validate_plan(plan, context, incident)


def test_residential_limit_uses_diverted_vehicle_share(inputs):
    incident, context, value = inputs
    plan = value["plans"][2]
    plan["diversions"] = [
        {"od_group": "Mock origin->Mock destination", "via": "Mock Detour", "share": 0.85},
        {"od_group": "Mock origin->Mock destination", "via": "Mock Residential", "share": 0.15}]
    validate_plan(plan, context, incident)
    plan["diversions"][0]["share"] = 0.84
    with pytest.raises(ValueError, match="Residential"):
        validate_plan(plan, context, incident)


def test_school_check_uses_entire_horizon_and_hong_kong_time(inputs):
    incident, context, value = inputs
    plan = value["plans"][2]
    diversion(plan, "Mock School")
    context.update(active_from="2026-05-15T06:50:00Z", active_until="2026-05-15T07:10:00Z")
    with pytest.raises(ValueError, match="school peak"):
        validate_plan(plan, context, incident)
    context.update(active_from="2026-05-16T08:30:00+08:00", active_until="2026-05-16T09:00:00+08:00")
    validate_plan(plan, context, incident)


def test_residential_limit_weights_different_od_demands(inputs):
    incident, context, value = inputs
    context["od_demand_vehicles"]["Mock small OD"] = 10
    route = deepcopy(context["routes"][2])
    route["od_group"] = "Mock small OD"
    context["routes"].append(route)
    plan = value["plans"][2]
    diversion(plan, "Mock Detour", 0.9)
    plan["diversions"].append({"od_group": "Mock small OD", "via": route["via"], "share": 1})
    validate_plan(plan, context, incident)  # 10 residential / 100 diverted vehicles.
    context["od_demand_vehicles"]["Mock small OD"] = 20
    with pytest.raises(ValueError, match="Residential"):
        validate_plan(plan, context, incident)


def test_reordered_duplicate_plan_is_rejected(inputs):
    incident, context, value = inputs
    context["od_demand_vehicles"]["Mock second OD"] = 10
    route = deepcopy(context["routes"][0])
    route["od_group"] = "Mock second OD"
    context["routes"].append(route)
    value["plans"][1]["diversions"].append(
        {"od_group": "Mock second OD", "via": route["via"], "share": 1})
    value["plans"][2] = {**deepcopy(value["plans"][1]), "plan_id": "P2"}
    value["plans"][2]["diversions"].reverse()
    value["plans"][2]["diversions"][0]["via"] = route["via"].upper()
    with pytest.raises(ValueError, match="distinct"):
        validate_plans(value, context, incident)


def test_writer_rejects_consistently_wrong_incident_before_model(inputs, model, tmp_path):
    paths = []
    for _, result in artifacts():
        result["incident_id"] = "other-incident"
        path = tmp_path / f"{result['run_id']}.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        paths.append(path)
    with pytest.raises(ValueError, match="different incident"):
        write_briefing(checked(inputs), paths, incident_id=inputs[0]["incident_id"],
                       results_root=tmp_path)
    assert logs(tmp_path) == []


def test_od_sum_and_unknown_junction_fail(inputs):
    incident, context, value = inputs
    plan = value["plans"][2]
    for d in plan["diversions"]:
        d["share"] = 0.6
    with pytest.raises(ValueError, match="exceed one"):
        validate_plan(plan, context, incident)
    plan["diversions"][0]["share"] = 0.2
    plan["signals"] = [{"junction_id": "NOT-REVIEWED", "green_extend_s": 1}]
    with pytest.raises(ValueError, match="signal"):
        validate_plan(plan, context, incident)


def test_missing_metadata_and_pre_report_actions_fail_before_model(inputs, model):
    incident, context, _ = inputs
    context["routes"][0].pop("school")
    with pytest.raises(jsonschema.ValidationError):
        generate(incident, context)
    context["routes"][0]["school"] = False
    context["active_from"] = "2026-05-15T08:55:00+08:00"
    with pytest.raises(ValueError, match="at/after"):
        generate(incident, context)


def test_p1_must_reach_all_groups_and_p2_must_differ(inputs):
    incident, context, value = inputs
    context["od_demand_vehicles"]["Unserved mock OD"] = 10
    with pytest.raises(ValueError, match="all supplied OD"):
        validate_plans(value, context, incident)
    context["od_demand_vehicles"].pop("Unserved mock OD")
    value["plans"][2] = {**deepcopy(value["plans"][1]), "plan_id": "P2"}
    with pytest.raises(ValueError, match="distinct"):
        validate_plans(value, context, incident)


def test_invalid_model_json_is_retried_once_then_flagged(inputs, model, tmp_path):
    incident, context, _ = inputs
    model.extend(["not json", '{"plans": NaN}'])
    with pytest.raises(ValueError, match="after two attempts"):
        generate(incident, context)
    assert len(logs(tmp_path)) == 2


def test_transport_failure_is_logged(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "LOG_DIR", tmp_path / "ai-log")
    def fail(**kwargs):
        raise ConnectionError("Test offline")
    monkeypatch.setattr(llm, "_send", fail)
    with pytest.raises(ConnectionError):
        llm.complete_json(component="plans", model="test", system="test", user="test",
                          schema={}, temperature=0)
    [call] = logs(tmp_path)
    assert call["response"] is None and call["error"] == "Test offline"


@pytest.mark.parametrize("change,error", [
    ("seed", "share incident"), ("incident", "share incident"), ("missing", "every candidate"),
    ("validation", "validation targets"), ("nan", "JSON compliant"),
    ("plan_validation", "only for baseline"),
])
def test_result_gate_rejects_incomparable_or_unvalidated_runs(inputs, change, error):
    records = artifacts()
    if change == "seed":
        records[1][1]["scenario"]["seed"] += 1
    elif change == "incident":
        records[1][1]["incident_id"] = "other-incident"
    elif change == "missing":
        records.pop()
    elif change == "validation":
        records[0][1]["validation"]["geh_under_5_pct"] = 66.94
    elif change == "nan":
        records[1][1]["metrics"]["co2_kg"] = float("nan")
    else:
        records[1][1]["validation"] = records[0][1]["validation"]
    with pytest.raises(ValueError, match=error):
        select(checked(inputs), records)


def test_selection_can_recommend_baseline_and_keeps_actual_sources(inputs):
    records = artifacts()
    records[0][1]["metrics"]["total_vehicle_hours_delay"] = 70
    plan, result, baseline, sources = select(checked(inputs), records)
    assert plan["plan_id"] == result["plan_id"] == baseline["plan_id"] == "P0"
    assert sources == sorted(p for p, _ in records)


def test_briefing_inserts_source_numbers_and_counts_rendered_signs(inputs):
    plan, result, baseline, sources = select(checked(inputs), artifacts())
    draft = load_json(FIXTURES / "mock_briefing_reply.json")
    draft["vms_messages"][0]["text_en"] = "DELAY {{delay_hours}} HOURS"
    output = assemble(draft, plan, result, baseline, sources)
    assert output["run_id"] == result["run_id"] and output["recommended_plan_id"] == "P2"
    assert "80 vehicle-hours" in output["operator_briefing_en"]
    assert output["vms_messages"][0]["chars_en"] == len("DELAY 80 HOURS")
    assert output["sources"] == sources


@pytest.mark.parametrize("change,error", [
    ("invented", "literal numeric"), ("token", "Unknown evidence"),
    ("sign", "signs must match"), ("uncertainty", "assumptions"), ("length", "60 characters"),
])
def test_briefing_rejects_untraceable_numbers_and_invalid_messages(inputs, change, error):
    plan, result, baseline, sources = select(checked(inputs), artifacts())
    draft = load_json(FIXTURES / "mock_briefing_reply.json")
    if change == "invented":
        draft["operator_briefing_en"] = draft["operator_briefing_en"].replace("{{delay_hours}}", "999")
    elif change == "token":
        draft["operator_briefing_en"] = draft["operator_briefing_en"].replace("{{delay_hours}}", "{{invented}}")
    elif change == "sign":
        draft["vms_messages"][0]["sign_id"] = "invented-sign"
    elif change == "uncertainty":
        draft["uncertainty_note_en"] = "Assumptions unknown."
    else:
        draft["vms_messages"][0]["text_zh"] = "字" * 61
    with pytest.raises(ValueError, match=error):
        assemble(draft, plan, result, baseline, sources)


def test_vms_line_limits_cover_both_separator_styles():
    check_vms("A" * 60 + "//" + "字" * 60 + "\nOK")
    with pytest.raises(ValueError):
        check_vms("A//B//C//D")


def test_source_files_must_be_under_results_runs(tmp_path):
    with pytest.raises(ValueError, match="results/runs"):
        load_results([FIXTURES / "mock_evaluator_results.json"], tmp_path / "results/runs")


def test_cli_path_uses_saved_plans_and_results_and_logs_both_components(
        inputs, model, tmp_path, monkeypatch):
    _, context, value = inputs
    context_path = tmp_path / "mock_context.json"
    context_path.write_text(json.dumps(context), encoding="utf-8")
    plans_dir = tmp_path / "plans"
    model.append(json.dumps(value))
    monkeypatch.setattr(sys, "argv", ["plans", "--incident", str(READER_RUN),
        "--message-id", "138270", "--context", str(context_path), "--out-dir", str(plans_dir)])
    plans_run.main()
    results_dir = tmp_path / "results" / "runs"
    results_dir.mkdir(parents=True)
    paths = []
    for _, result in artifacts():
        path = results_dir / f"{result['run_id']}.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        paths.append(str(path))
    model.append((FIXTURES / "mock_briefing_reply.json").read_text(encoding="utf-8"))
    out = tmp_path / "briefing.json"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["briefing", "--plans", str(plans_dir),
                                     "--results", *paths, "--out", str(out)])
    briefing_run.main()
    briefing = load_json(out)
    assert briefing["recommended_plan_id"] == "P2"
    assert [c["component"] for c in logs(tmp_path)] == ["plans", "briefing"]
    assert set(briefing["sources"]) == {p for p, _ in artifacts()}
