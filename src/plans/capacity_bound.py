"""Bound one model-drafted P2 diversion by a documented bottleneck capacity.

This is D's deterministic parameter step. It preserves the logged model plan
set and writes a separate, complete plan set for E; it never runs a simulator.
"""
import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from math import floor, isfinite
from pathlib import Path
from shutil import copyfile

from src.generation import load_json, save_json
from src.plans.generator import validate_plans

SOURCE_FILES = ("P0.json", "P1.json", "P2.json", "generation-inputs.json")
ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def display_path(path):
    path = Path(path)
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()


def capacity_share_cap(context, rule):
    """Return a share rounded down, with reserve, at the tested compliance cap."""
    if context["incident_id"] != rule["incident_id"]:
        raise ValueError("Capacity rule belongs to another incident")
    start = datetime.fromisoformat(context["active_from"])
    end = datetime.fromisoformat(context["active_until"])
    hours = (end - start).total_seconds() / 3600
    demand = context["od_demand_vehicles"][rule["od_group"]]
    spare = rule["estimated_spare_veh_h"]
    compliance = rule["max_compliance"]
    reserve = rule["reserve_fraction"]
    step = rule["share_step"]
    if (not all(isfinite(x) for x in (hours, demand, spare, compliance, reserve, step))
            or min(hours, demand, spare, compliance, step) <= 0
            or not 0 <= reserve < 1 or compliance > 1 or step >= 1):
        raise ValueError("Capacity rule needs finite positive demand/capacity and valid fractions")
    demand_per_hour = demand / hours
    unrounded = spare * (1 - reserve) / (demand_per_hour * compliance)
    cap = min(1.0, floor(unrounded / step + 1e-9) * step)
    if cap <= 0:
        raise ValueError("Capacity rule leaves no positive diversion share")
    return round(cap, 8), demand_per_hour, unrounded


def prepare(source, rule_path, out):
    source, rule_path, out = Path(source).resolve(), Path(rule_path).resolve(), Path(out).resolve()
    if out.exists() or out == source or source in out.parents:
        raise FileExistsError("Use a new output directory outside the original plan set")
    files = {name: source / name for name in SOURCE_FILES}
    if any(not path.is_file() for path in files.values()):
        raise FileNotFoundError("Source must contain P0, P1, P2 and generation-inputs.json")
    original = {plan_id: load_json(files[f"{plan_id}.json"]) for plan_id in ("P0", "P1", "P2")}
    inputs = load_json(files["generation-inputs.json"])
    incident, context = inputs["incident"], inputs["policy_context"]
    if validate_plans({"plans": list(original.values())}, context, incident) != list(original.values()):
        raise ValueError("Source plans must already have passed D validation")
    rule = load_json(rule_path)
    cap, demand_per_hour, unrounded = capacity_share_cap(context, rule)
    p2 = deepcopy(original["P2"])
    if (len(p2["diversions"]) != 1 or p2["signals"] or p2["pt_nudge"]["mode"]
            or p2["diversions"][0]["od_group"] != rule["od_group"]
            or p2["diversions"][0]["via"] != rule["via"]):
        raise ValueError("This capacity rule needs one matching P2 detour and no other effective action")
    original_share = p2["diversions"][0]["share"]
    p2["diversions"][0]["share"] = min(original_share, cap)
    p2["label"] = "Capacity-bounded Castle Peak Road advice"
    p2["rationale"] = (
        "Limit advice to a small share so the Sham Tseng exit is less likely to overload "
        "under the fixed-signal sensitivity. No signal change is assumed; evaluate this candidate against P0."
    )
    checked = validate_plans({"plans": [original["P0"], original["P1"], p2]}, context, incident)
    if checked != [original["P0"], original["P1"], p2]:
        raise ValueError("Capacity-bounded plan changed during D validation")
    out.mkdir(parents=True)
    for name in ("P0.json", "P1.json", "generation-inputs.json"):
        copyfile(files[name], out / name)
    save_json(out / "P2.json", p2)
    save_json(out / "capacity-bound-manifest.json", {
        "incident_id": rule["incident_id"],
        "derivation": "Logged D P2 proposal, then deterministic capacity bound; not a new LLM call or result",
        "source_plan_set": display_path(source),
        "source_sha256": {name: digest(path) for name, path in files.items()},
        "rule_path": display_path(rule_path),
        "rule_sha256": digest(rule_path),
        "estimated_eligible_flow_veh_h": round(demand_per_hour, 3),
        "unrounded_capacity_share_cap": round(unrounded, 6),
        "rounded_capacity_share_cap": cap,
        "model_proposed_share": original_share,
        "selected_share": p2["diversions"][0]["share"],
        "p2_sha256": digest(out / "P2.json"),
        "status": "experimental candidate; no evaluated benefit or P0 acceptance implied",
    })
    return p2["diversions"][0]["share"]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", required=True, help="Saved D model-generated plan directory")
    parser.add_argument("--rule", required=True, help="Documented capacity-bound JSON")
    parser.add_argument("--out", required=True, help="New complete plan directory for E")
    args = parser.parse_args()
    share = prepare(args.source, args.rule, args.out)
    print(f"Capacity-bounded P2 share {share:g} written to {args.out}; no simulation or benefit claim.")


if __name__ == "__main__":
    main()
