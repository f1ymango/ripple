"""D/F handoff tests. Every fabricated traffic input lives in mock_* fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import jsonschema
import pytest

from src import llm
from src.evaluation_provenance import capture_inputs, write_result, verify_result
from src.briefing import run as briefing_run
from src.briefing.results import load_results, select
from src.briefing.writer import assemble, check_vms, prepare_comparison, render_text, write_briefing
from src.generation import load_json, save_json
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
        write_briefing(checked(inputs), paths,
                       generation_inputs={"incident": inputs[0], "policy_context": inputs[1]},
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


def test_zero_second_signal_does_not_make_a_distinct_plan(inputs):
    incident, context, value = inputs
    value["plans"][2] = {**deepcopy(value["plans"][0]), "plan_id": "P2"}
    value["plans"][2]["signals"] = [{"junction_id": "MOCK-J", "green_extend_s": 0}]
    with pytest.raises(jsonschema.ValidationError):
        validate_plans(value, context, incident)


@pytest.mark.parametrize("text", [
    "Delay falls by twenty percent.", "Travel time is halved.",
    "Capacity doubles.", "A quarter of drivers divert.",
    "延誤減少百分之二十。", "行車時間減半。", "流量增加兩倍。", "延誤減少半成。",
    "Delay falls by twen\u200bty percent.", "Delay falls by ｔｗｅｎｔｙ percent.",
])
def test_worded_quantities_cannot_bypass_numeric_guard(text):
    with pytest.raises(ValueError, match="literal numeric"):
        render_text(text, {})


def test_metric_tokens_still_render_with_conservative_word_guard():
    assert render_text("Delay is {{delay_hours}} vehicle-hours.", {"delay_hours": "80"}) == (
        "Delay is 80 vehicle-hours.")


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
    saved_inputs = load_json(plans_dir / "generation-inputs.json")
    for _, result in artifacts():
        path = results_dir / f"{result['run_id']}.json"
        plan = load_json(plans_dir / f"{result['plan_id']}.json")
        captured = capture_inputs(plan, saved_inputs, {"mock_context": context_path})
        write_result(path, result, captured)
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
    result_sources = {p for p, _ in artifacts()}
    assert set(briefing["sources"]) == result_sources | {
        str(Path(p).with_suffix(".provenance.json")).replace("\\", "/") for p in result_sources}


@pytest.mark.parametrize("changed", ["plan", "result", "context", "missing"])
def test_provenance_rejects_stale_inputs_and_results(inputs, tmp_path, changed):
    plans = checked(inputs)
    saved = {"incident": inputs[0], "policy_context": inputs[1]}
    result = artifacts()[2][1]
    path = tmp_path / "mock_result.json"
    captured = capture_inputs(plans[2], saved, {"mock_network": FIXTURES / "mock_plan_context.json"})
    if changed != "missing":
        write_result(path, result, captured)
        verify_result(path, result, plans[2], saved)
    if changed == "plan":
        plans[2]["diversions"][0]["share"] = 0.4
    elif changed == "result":
        result["metrics"]["total_vehicle_hours_delay"] = 70
    elif changed == "context":
        saved["policy_context"]["active_until"] = "2026-05-15T11:00:00+08:00"
    with pytest.raises((ValueError, FileNotFoundError)):
        verify_result(path, result, plans[2], saved)


@pytest.mark.parametrize("problem", ["stale_plan", "mixed_network", "missing_sidecar"])
def test_writer_checks_provenance_before_any_model_call(inputs, model, tmp_path, problem):
    plans = checked(inputs)
    saved = {"incident": inputs[0], "policy_context": inputs[1]}
    paths = []
    for plan, (_, result) in zip(plans, artifacts()):
        path = tmp_path / f"{result['run_id']}.json"
        if problem == "missing_sidecar":
            path.write_text(json.dumps(result), encoding="utf-8")
        else:
            fixture = "mock_plan_set.json" if problem == "mixed_network" and plan["plan_id"] == "P2" else "mock_plan_context.json"
            captured = capture_inputs(plan, saved, {"mock_network": FIXTURES / fixture})
            write_result(path, result, captured)
        paths.append(path)
    if problem == "stale_plan":
        plans[2]["diversions"][0]["share"] = 0.4
    with pytest.raises((ValueError, FileNotFoundError)):
        write_briefing(plans, paths, generation_inputs=saved, results_root=tmp_path)
    assert logs(tmp_path) == []


def test_provenance_does_not_overwrite_previous_run(inputs, tmp_path):
    plan = checked(inputs)[2]
    saved = {"incident": inputs[0], "policy_context": inputs[1]}
    result = artifacts()[2][1]
    path = tmp_path / "mock_result.json"
    captured = capture_inputs(plan, saved, {"mock_network": FIXTURES / "mock_plan_context.json"})
    write_result(path, result, captured)
    original = path.read_bytes()
    result["metrics"]["total_vehicle_hours_delay"] = 70
    with pytest.raises(ValueError, match="already exists"):
        write_result(path, result, captured)
    assert path.read_bytes() == original


@pytest.fixture
def saved_handoff(inputs, tmp_path):
    plans = checked(inputs)
    saved = {"incident": inputs[0], "policy_context": inputs[1]}
    directory = tmp_path / "plans"
    save_json(directory / "generation-inputs.json", saved)
    paths = []
    for plan, (_, result) in zip(plans, artifacts()):
        save_json(directory / f"{plan['plan_id']}.json", plan)
        path = tmp_path / "results" / "runs" / f"{result['run_id']}.json"
        captured = capture_inputs(plan, saved, {"mock_network": FIXTURES / "mock_plan_context.json"})
        write_result(path, result, captured)
        paths.append(path)
    return directory, plans, saved, paths


def test_plans_check_only_does_not_call_model_or_write(inputs, model, tmp_path, monkeypatch, capsys):
    context_path = tmp_path / "mock_context.json"
    save_json(context_path, inputs[1])
    before = set(tmp_path.rglob("*"))
    monkeypatch.setattr(sys, "argv", ["plans", "--incident", str(READER_RUN),
        "--message-id", "138270", "--context", str(context_path), "--check-only"])
    plans_run.main()
    assert "context checks passed" in capsys.readouterr().out
    assert set(tmp_path.rglob("*")) == before
    assert logs(tmp_path) == []
    inputs[1]["reviewed"] = False
    context_path.write_text(json.dumps(inputs[1]), encoding="utf-8")
    with pytest.raises(jsonschema.ValidationError):
        plans_run.main()


def test_briefing_check_only_verifies_provenance_without_writing(
        saved_handoff, model, tmp_path, monkeypatch, capsys):
    directory, _, _, paths = saved_handoff
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["briefing", "--plans", str(directory),
        "--results", *map(str, paths), "--check-only"])
    briefing_run.main()
    assert "lowest-delay candidate: P2" in capsys.readouterr().out
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
    paths[2].with_suffix(".provenance.json").unlink()
    with pytest.raises(FileNotFoundError):
        briefing_run.main()
    assert logs(tmp_path) == []


def test_comparison_accepts_result_path_iterator_and_checks_every_sidecar(saved_handoff, tmp_path):
    _, plans, saved, paths = saved_handoff
    kwargs = {"generation_inputs": saved, "results_root": tmp_path / "results" / "runs"}
    assert prepare_comparison(plans, iter(paths), **kwargs)[0]["plan_id"] == "P2"
    paths[-1].with_suffix(".provenance.json").unlink()
    with pytest.raises(FileNotFoundError):
        prepare_comparison(plans, iter(paths), **kwargs)


def test_direct_writer_rejects_unsafe_plan_even_with_matching_provenance(
        saved_handoff, model, tmp_path):
    _, plans, saved, _ = saved_handoff
    # A caller could otherwise bypass the CLI's constraint checks with a
    # pre-populated constraints_checked field and matching captured hashes.
    diversion(plans[2], "Mock Emergency Route")
    result = artifacts()[2][1]
    path = tmp_path / "mock_unsafe.json"
    captured = capture_inputs(plans[2], saved, {"mock_network": FIXTURES / "mock_plan_context.json"})
    write_result(path, result, captured)
    verify_result(path, result, plans[2], saved)
    with pytest.raises(ValueError, match="emergency"):
        write_briefing(plans, [path], generation_inputs=saved, results_root=tmp_path)
    assert logs(tmp_path) == []


@pytest.mark.parametrize("module,args", [
    (plans_run, ["--incident", "unused", "--context", "unused", "--out-dir", "unused"]),
    (briefing_run, ["--plans", "unused", "--results", "unused", "--out", "unused"]),
])
def test_check_only_rejects_output_arguments(module, args, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["check", *args, "--check-only"])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert exc.value.code == 2


def version_2(records):
    """The fixture runs as E writes them since 13 October: run_ids ending in the plan set, a version 2 block."""
    for _, record in records:
        record["run_id"] = f"mock_{record['plan_id']}_c50_t60_mock-scenario_mock-set"
    records[0][1]["validation"] = {"geh_under_5_pct": 93.5, "speed_mape_pct": 24.8, "speed_mape_free_flow_pct": 13.0,
                                   "congestion_state_agreement_pct": 93.3, "wrong_lane_teleports_not_at_lane_shut": 0}
    return records


def mock_ranking(records, first="P2"):
    return {"plan_set": "mock-set", "incident_id": records[0][1]["incident_id"], "first": first,
            "verdicts": ["P1 before P0", "P2 before P0", "P2 before P1"] if first else ["P1 and P2 tie"],
            "cells": [{"run_ids": {r["plan_id"]: r["run_id"] for _, r in records},
                       "total_vehicle_hours_delay": {r["plan_id"]: r["metrics"]["total_vehicle_hours_delay"]
                                                     for _, r in records}}]}


def test_a_version_2_baseline_needs_a_ranking_that_puts_the_winner_before_both_others(inputs):
    records = version_2(artifacts())
    with pytest.raises(ValueError, match="No ranking"):
        select(checked(inputs), records)
    plan, result, _, _ = select(checked(inputs), records, mock_ranking(records))
    assert plan["plan_id"] == result["plan_id"] == "P2"
    with pytest.raises(ValueError, match=r"puts no plan before both others \(P1 and P2 tie\)"):
        select(checked(inputs), records, mock_ranking(records, first=None))


@pytest.mark.parametrize("change, error", [
    (lambda r: r.update(plan_set="other-set"), "another plan set"),
    (lambda r: r["cells"][0]["run_ids"].update(P1="other"), "not a cell"),
    (lambda r: r["cells"][0]["total_vehicle_hours_delay"].update(P2=79), "delays differ"),
    (lambda r: r.update(first="P1"), "disagree"),
])
def test_a_ranking_for_other_runs_is_refused(inputs, change, error):
    records = version_2(artifacts())
    ranking = mock_ranking(records)
    change(ranking)
    with pytest.raises(ValueError, match=error):
        select(checked(inputs), records, ranking)
