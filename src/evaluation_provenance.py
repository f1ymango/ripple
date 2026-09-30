"""E captures inputs before simulation; F verifies the resulting sidecars."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from src.generation import load_json, save_json


def json_hash(value):
    """Canonical UTF-8 JSON: object key order/whitespace do not change identity."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def capture_inputs(plan, generation_inputs, simulation_files):
    """Call BEFORE running E, with every network/demand/incident/config input.

    simulation_files maps stable logical names to actual file paths. The same
    shared inputs must be used for all candidates. E must run these captured
    inputs without changing them; this is provenance, not tamper-proof signing.
    """
    if not simulation_files:
        raise ValueError("Simulation input files are required")
    return {
        "version": 1,
        "plan_id": plan["plan_id"],
        "incident_id": generation_inputs["incident"]["incident_id"],
        "plan_sha256": json_hash(plan),
        "generation_inputs_sha256": json_hash(generation_inputs),
        "simulation_inputs": {name: sha256(Path(path).read_bytes()).hexdigest()
                              for name, path in sorted(simulation_files.items())},
    }


def sidecar_path(result_path):
    return Path(result_path).with_suffix(".provenance.json")


def write_result(result_path, result, captured):
    """Save E's computed result and its captured input identity, without overwrite."""
    if any(result[key] != captured[key] for key in ("plan_id", "incident_id")):
        raise ValueError("Result identity differs from captured simulation inputs")
    result_path = Path(result_path)
    sidecar = sidecar_path(result_path)
    if result_path.exists() or sidecar.exists():
        raise ValueError("Result or provenance already exists; use a new run path")
    record = deepcopy(captured)
    record.update(run_id=result["run_id"], result_sha256=json_hash(result))
    save_json(result_path, result)
    save_json(sidecar, record)


def verify_result(result_path, result, plan, generation_inputs):
    """Fail closed on missing, stale or mismatched E provenance."""
    path = sidecar_path(result_path)
    record = load_json(path)
    expected = {
        "version": 1, "plan_id": plan["plan_id"],
        "incident_id": generation_inputs["incident"]["incident_id"],
        "run_id": result["run_id"], "plan_sha256": json_hash(plan),
        "generation_inputs_sha256": json_hash(generation_inputs),
        "result_sha256": json_hash(result),
    }
    if not isinstance(record, dict) or any(record.get(k) != v for k, v in expected.items()):
        raise ValueError("Result provenance does not match current plan, inputs or result")
    files = record.get("simulation_inputs")
    if (not isinstance(files, dict) or not files
            or any(not isinstance(k, str) or not k or not isinstance(v, str)
                   or len(v) != 64 or any(c not in "0123456789abcdef" for c in v)
                   for k, v in files.items())):
        raise ValueError("Provenance must identify simulation inputs with SHA-256 hashes")
    return files
