"""Choose an operator response from completed, like-for-like simulator runs.

This reads the existing plan.json and result.json contracts. It never estimates
traffic outcomes: a missing or unvalidated run means no recommendation.
"""
from __future__ import annotations

import math
from pathlib import Path, PurePosixPath

import jsonschema

from src import validation_targets as targets
from src.briefing.results import load_ranking, select
from src.evaluation_provenance import json_hash, verify_result
from src.generation import load_json
from src.plans.generator import validate_plans
from src.plans.validator import CHECKS


def fingerprint(value: dict) -> str:
    """Stable content ID for a result or plan without assuming its filename."""
    return json_hash(value)


def read_objects(directory: Path) -> tuple[list[dict], list[str]]:
    """Read one JSON object per file, reporting malformed files to the operator."""
    artifacts, errors = read_artifacts(directory)
    return [value for _, value in artifacts], errors


def read_artifacts(directory: Path) -> tuple[list[tuple[Path, dict]], list[str]]:
    """Sidecars are checked with their result, never treated as plan runs."""
    objects, errors = [], []
    if not directory.is_dir():
        return objects, errors
    for path in sorted(directory.glob("*.json")):
        if path.name.endswith((".provenance.json", "generation-inputs.json")):
            continue
        try:
            value = load_json(path)
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            objects.append((path, value))
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
    return objects, errors


def scenario_key(result: dict) -> tuple[float, float, int] | None:
    """Runs compare only with the same compliance, clearance and seed."""
    scenario = result.get("scenario")
    if not isinstance(scenario, dict):
        return None
    try:
        compliance = float(scenario["compliance"])
        clearance = float(scenario["clearance_min"])
        seed = scenario["seed"]
    except (KeyError, TypeError, ValueError):
        return None
    if (not math.isfinite(compliance) or not 0 <= compliance <= 1
            or not math.isfinite(clearance) or clearance <= 0
            or type(seed) is not int):
        return None
    return compliance, clearance, seed


def scenarios_for(results: list[dict], incident_id: str) -> list[tuple[float, float, int]]:
    """Only offer scenarios with one baseline, broadcast plan and coordinated plan."""
    grouped: dict[tuple[float, float, int], set[str]] = {}
    for result in results:
        if result.get("incident_id") != incident_id:
            continue
        key = scenario_key(result)
        if key is not None:
            grouped.setdefault(key, set()).add(str(result.get("plan_id", "")))
    return sorted((key for key, ids in grouped.items()
                   if {"P0", "P1"} <= ids and any(
                       pid.startswith("P") and pid[1:].isdigit() and int(pid[1:]) >= 2
                   for pid in ids)), key=lambda key: (
                           key[0] != 0.5 or key[1] != 60.0, key))


def _delay(result: dict) -> float | None:
    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        return None
    try:
        value = float(metrics["total_vehicle_hours_delay"])
    except (KeyError, TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def assess(results: list[dict], plans: list[dict], incident_id: str,
           key: tuple[float, float, int], *, result_paths=None,
           generation_inputs=None, results_dir=None) -> tuple[dict | None, str]:
    """Return an evidenced recommendation or the precise reason it is withheld."""
    selected = [r for r in results if r.get("incident_id") == incident_id
                and scenario_key(r) == key]
    by_id: dict[str, dict] = {}
    for result in selected:
        pid = result.get("plan_id")
        if not isinstance(pid, str) or not pid:
            return None, "A run has no plan_id."
        if pid not in ("P0", "P1") and not (
                pid.startswith("P") and pid[1:].isdigit() and int(pid[1:]) >= 2):
            return None, f"{pid} is not a contract plan ID."
        if pid in by_id:
            return None, f"More than one {pid} run has this scenario."
        by_id[pid] = result
    if "P0" not in by_id or "P1" not in by_id or not any(
            pid.startswith("P") and pid[1:].isdigit() and int(pid[1:]) >= 2
            for pid in by_id):
        return None, "Need matching P0, P1 and at least one coordinated plan."
    for pid, result in by_id.items():
        if not isinstance(result.get("run_id"), str) or not result["run_id"]:
            return None, f"{pid} has no run_id."
        if Path(result["run_id"]).name != result["run_id"]:
            return None, f"{pid} has an unsafe run_id."
        if _delay(result) is None:
            return None, f"{pid} has no usable simulator delay metric."

    validation = by_id["P0"].get("validation")
    met, reason = targets.check(validation)          # the rule E and F use (src/validation_targets.py)
    if not met:
        return None, reason

    plan_by_id = {}
    for plan in plans:
        pid = plan.get("plan_id")
        if isinstance(pid, str):
            if pid in plan_by_id:
                return None, f"More than one {pid} plan.json was found."
            plan_by_id[pid] = plan
    for pid in by_id:
        if pid == "P0":
            continue
        if pid not in plan_by_id:
            return None, f"{pid} plan.json is missing."
        checks = plan_by_id[pid].get("constraints_checked")
        if not isinstance(checks, list) or not checks or not all(
                isinstance(check, str) and check for check in checks):
            return None, f"{pid} has no constraint validation record."
    if result_paths is None or generation_inputs is None or results_dir is None:
        return None, "Result provenance and saved plan-generation inputs are required."
    try:
        for pid in by_id:
            if pid not in plan_by_id:
                raise ValueError(f"{pid} plan.json is missing.")
            if plan_by_id[pid].get("constraints_checked") != CHECKS:
                raise ValueError(f"{pid} has no complete constraint validation record.")
        checked = validate_plans({"plans": [plan_by_id[pid] for pid in sorted(by_id)]},
                                 generation_inputs["policy_context"],
                                 generation_inputs["incident"])
        if generation_inputs["incident"]["incident_id"] != incident_id:
            raise ValueError("Saved plan inputs belong to a different incident.")
        artifacts, shared_inputs, sources = [], [], []
        for pid, result in sorted(by_id.items()):
            path = result_paths[result["run_id"]]
            source = "results/runs/" + path.relative_to(Path(results_dir)).as_posix()
            artifacts.append((source, result))
            shared_inputs.append(verify_result(path, result, plan_by_id[pid], generation_inputs))
            sources.extend((source, PurePosixPath(source).with_suffix(".provenance.json").as_posix()))
        if any(inputs != shared_inputs[0] for inputs in shared_inputs[1:]):
            raise ValueError("Compared runs used different simulation inputs.")
        ranking = load_ranking(by_id["P0"]["run_id"], Path(results_dir).parent / "rankings")
        _, winner, _, _ = select(checked, artifacts, ranking)
    except (OSError, ValueError, KeyError, TypeError, jsonschema.ValidationError) as exc:
        return None, str(exc).splitlines()[0]
    return {"runs": by_id, "plans": plan_by_id, "winner": winner,
            "baseline": by_id["P0"], "validation": validation,
            "scenario": key, "incident_id": incident_id,
            "sources": sorted(sources), "simulation_inputs": shared_inputs[0],
            "generation_inputs_sha256": json_hash(generation_inputs),
            "ranking_cells": len(ranking["cells"]) if targets.is_version_2(validation) else None}, ""


def load_comparison(results_dir: Path, plans_dir: Path, incident_id: str,
                    key: tuple[float, float, int]) -> tuple[dict | None, str]:
    """Reload saved inputs before displaying or approving a response."""
    artifacts, result_errors = read_artifacts(results_dir)
    plans, plan_errors = read_objects(plans_dir)
    if result_errors or plan_errors:
        return None, "; ".join(result_errors + plan_errors)
    try:
        inputs = load_json(plans_dir / "generation-inputs.json")
    except (OSError, ValueError) as exc:
        return None, f"Saved plan-generation inputs are unavailable: {exc}"
    paths = {result["run_id"]: path for path, result in artifacts
             if isinstance(result.get("run_id"), str)}
    return assess([result for _, result in artifacts], plans, incident_id, key,
                  result_paths=paths, generation_inputs=inputs, results_dir=results_dir)
