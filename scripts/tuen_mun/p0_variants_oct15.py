"""Write source-preserving Tuen Mun P0 lane-phase sensitivity scenarios.

Run from the repository root. These are predeclared diagnostics, not selected
calibrations. The baseline network, demand and observations remain unchanged.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "sim/scenarios/tuen-mun/evaluator_IN-26-02615_replay-v2.json"
OUT = ROOT / "sim/scenarios/tuen-mun"
SEEDS = (2029, 2030, 2031)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    variants = {
        "middle-open": [
            {"offset_seconds": 0, "lanes": ["fast"]},
            {"offset_seconds": 660, "lanes": ["fast", "slow"]},
            {"offset_seconds": 1740, "lanes": ["fast"]},
            {"offset_seconds": 3180, "lanes": ["fast", "slow"]},
        ],
        "td-one-lane": [
            {"offset_seconds": 0, "lanes": ["fast"]},
            {"offset_seconds": 660, "lanes": ["fast", "middle1"]},
        ],
    }
    manifest = {"source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
                "source_sha256": sha(SOURCE), "seeds": list(SEEDS), "variants": {}}
    for name, phases in variants.items():
        manifest["variants"][name] = []
        for seed in SEEDS:
            doc = json.loads(json.dumps(source))
            doc["seed"] = seed
            doc["run_label"] = f"p0-{name}-s{seed}"
            doc["closure"]["phases"] = phases
            doc["status"] = "Tuen Mun P0 predeclared lane-phase sensitivity; no benefit claim."
            doc["assumptions"].append({
                "choice": f"P0 sensitivity {name}; seed {seed}; phase schedule differs from replay-v2",
                "status": "assumption under review",
                "source": "docs/tuen-mun-p0-simulation-review-2026-10-14.md",
            })
            path = OUT / f"evaluator_IN-26-02615_{doc['run_label']}.json"
            path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            manifest["variants"][name].append({"scenario": str(path.relative_to(ROOT)).replace("\\", "/"),
                                                "sha256": sha(path)})
    # Preserve ordinary Ting Kau entry demand. E's existing queue-triggered
    # drivers_leave rule remains active; only the 1,141-driver subtraction is
    # removed. This is a conservation sensitivity, not a fitted replacement.
    sys.path.insert(0, str(ROOT))
    from scripts.tuen_mun import demand
    demand_source = demand.OUT / "demand_20260415.json"
    record = json.loads(demand_source.read_text(encoding="utf-8"))
    rows = record["bins"]
    removed = sum(row.get("ting_kau_decided_earlier", 0) for row in rows)
    for row in rows:
        row["ting_kau_decided_earlier"] = 0.0
    demand.write_routes(record["day"], rows, record["shares"], suffix="-no-residual")
    route_path = demand.OUT / "demand_20260415-no-residual.rou.xml"
    manifest["variants"]["no-residual"] = {"removed_subtraction": removed,
        "source_metadata_sha256": sha(demand_source), "routes_sha256": sha(route_path), "scenarios": []}
    for seed in SEEDS:
        doc = json.loads(json.dumps(source))
        doc["seed"] = seed
        doc["run_label"] = f"p0-no-residual-s{seed}"
        doc["inputs"]["routes"] = str(route_path.relative_to(ROOT)).replace("\\", "/")
        doc["status"] = "Tuen Mun P0 conservation sensitivity; no benefit claim."
        doc["assumptions"].append({
            "choice": "No upfront 1,141-driver Ting Kau subtraction; existing queue-triggered diversions remain",
            "status": "predeclared sensitivity, not accepted demand",
            "source": "docs/tuen-mun-p0-simulation-review-2026-10-14.md",
        })
        path = OUT / f"evaluator_IN-26-02615_{doc['run_label']}.json"
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        manifest["variants"]["no-residual"]["scenarios"].append({
            "scenario": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path)})
    path = OUT / "p0-variants-oct15-manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(path)


if __name__ == "__main__":
    main()
