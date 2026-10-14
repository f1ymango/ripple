"""Check staged P0 variant inputs and results against original provenance hashes."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.evaluation_provenance import json_hash

RUNS = ROOT / "results/tuen-mun-p0-variants-oct15/runs"
SCENARIOS = ROOT / "sim/scenarios/tuen-mun"
ROUTES = ROOT / "sim/tuen-mun"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(path, expected):
    relative = path.relative_to(ROOT).as_posix()
    actual = sha(path.read_bytes())
    staged = sha(subprocess.run(["git", "show", f":{relative}"], cwd=ROOT,
                                check=True, capture_output=True).stdout)
    if actual != expected or staged != expected:
        raise ValueError(f"hash mismatch {relative}: work={actual}, staged={staged}, expected={expected}")


def main():
    checked_count = 0
    for sidecar in sorted(RUNS.glob("*.provenance.json")):
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        result = sidecar.with_name(sidecar.name.replace(".provenance.json", ".json"))
        relative = result.relative_to(ROOT).as_posix()
        staged_result = json.loads(subprocess.run(["git", "show", f":{relative}"], cwd=ROOT,
                                                  check=True, capture_output=True).stdout)
        if json_hash(json.loads(result.read_text(encoding="utf-8"))) != record["result_sha256"] or \
                json_hash(staged_result) != record["result_sha256"]:
            raise ValueError(f"canonical result hash mismatch: {relative}")
        inputs = record["simulation_inputs"]
        label = result.stem.split("_t59_", 1)[1].split("_lead-capacity", 1)[0]
        checked(SCENARIOS / f"evaluator_IN-26-02615_{label}.json", inputs["scenario"])
        route = "demand_20260415-no-residual.rou.xml" if "no-residual" in label else "demand_20260415.rou.xml"
        if "no-residual" in label:
            checked(ROUTES / route, inputs["routes"])
        elif sha((ROUTES / route).read_bytes()) != inputs["routes"]:
            raise ValueError("committed Data demand changed")
        checked_count += 1
    if checked_count != 3:
        raise ValueError(f"expected 3 original run sidecars, found {checked_count}")
    print(f"verified {checked_count} P0 runs against worktree and staged Git bytes")


if __name__ == "__main__":
    main()
