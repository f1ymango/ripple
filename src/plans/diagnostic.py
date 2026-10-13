"""Prepare two predeclared, model-free P2 diagnostics from a saved D plan set.

    python -m src.plans.diagnostic --source SOURCE_PLAN_DIR --out NEW_OUTPUT_DIR

The original model output is never changed. Each new folder is a complete
P0/P1/P2 plan set for E, with the exact original P0, P1 and generation inputs.
These are Lead parameter-search derivatives, not fresh LLM generations.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from shutil import copyfile

from src.generation import load_json, save_json
from src.plans.generator import validate_plans

EXPECTED_INCIDENT = "IN-26-03365"
EXPECTED_DIVERSION = (
    ("Aberdeen->Canal Road Flyover", "Wong Chuk Hang Road", 0.8),
    ("Aberdeen->Wong Nai Chung Road", "Wong Chuk Hang Road", 0.7),
)
EXPECTED_SIGNAL = [{"junction_id": "Wong Chuk Hang Road / Tong Bin Lane", "green_extend_s": 20}]
VARIANTS = {
    "lead-p2-nosignal-oct13": (1.0, "Original advice shares; remove the unverified signal action."),
    "lead-p2-half-nosignal-oct13": (0.5, "Halve both proposed advice shares; remove the unverified signal action."),
}
SOURCE_FILES = ("P0.json", "P1.json", "P2.json", "generation-inputs.json")
SOURCE_SHA256 = {
    "P0.json": "4198ec674296e0a1413b3ef3d0758fdf3e60124afbe9d51728b912b69ed898ff",
    "P1.json": "dae8a9c06f0e7d34b77407193ff36eb1d814311b8a8d0739fe508190da27dade",
    "P2.json": "3afc8b638a7abd2d9a290541d07032ab9a9f269fa4196c14f479ef7284eea20c",
    "generation-inputs.json": "8726acd9be7023a9483f3e46128fa172abb6bebf5f1361970194144d904f33a1",
}
ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def source_plans(source):
    """Fail closed if the saved model proposal or reviewed context has drifted."""
    source = Path(source)
    files = {name: source / name for name in SOURCE_FILES}
    if any(not path.is_file() for path in files.values()):
        raise FileNotFoundError("Source plan set must contain P0, P1, P2 and generation-inputs.json")
    if {name: digest(path) for name, path in files.items()} != SOURCE_SHA256:
        raise ValueError("Source plan set bytes changed; review the evidence before deriving variants")
    original = {plan_id: load_json(files[f"{plan_id}.json"]) for plan_id in ("P0", "P1", "P2")}
    inputs = load_json(files["generation-inputs.json"])
    incident, context = inputs["incident"], inputs["policy_context"]
    if incident["incident_id"] != EXPECTED_INCIDENT:
        raise ValueError("This bounded diagnostic is for IN-26-03365 only")
    checked = validate_plans({"plans": list(original.values())}, context, incident)
    if checked != list(original.values()):
        raise ValueError("Source files must be the saved, fully validated P0/P1/P2 set")
    diversions = tuple((d["od_group"], d["via"], d["share"]) for d in original["P2"]["diversions"])
    if diversions != EXPECTED_DIVERSION or original["P2"]["signals"] != EXPECTED_SIGNAL:
        raise ValueError("Original P2 actions changed; review before defining new variants")
    return original, inputs, files


def variant(original, multiplier, description):
    candidate = deepcopy(original)
    candidate["label"] = "Diagnostic P2 share/signal ablation"
    candidate["rationale"] = (f"Lead parameter-search derivative of the saved model proposal: {description} "
                              "No traffic benefit has been established.")
    candidate["signals"] = []
    for diversion in candidate["diversions"]:
        diversion["share"] = round(diversion["share"] * multiplier, 4)
    return candidate


def prepare(source, out):
    """Create complete, provenance-ready plan folders without running SUMO or a model."""
    source, out = Path(source).resolve(), Path(out).resolve()
    if out.exists() or out == source or source in out.parents:
        raise FileExistsError("Use a new output directory outside the source plan set")
    original, inputs, files = source_plans(source)
    candidates = {}
    for plan_set, (multiplier, description) in VARIANTS.items():
        p2 = variant(original["P2"], multiplier, description)
        checked = validate_plans({"plans": [original["P0"], original["P1"], p2]},
                                 inputs["policy_context"], inputs["incident"])
        if checked != [original["P0"], original["P1"], p2]:
            raise ValueError(f"Variant {plan_set} changed during constraint validation")
        candidates[plan_set] = p2

    out.mkdir(parents=True)
    manifest = {
        "status": "diagnostic only; no accepted P0 or measured benefit",
        "incident_id": EXPECTED_INCIDENT,
        "derivation": "deterministic Lead parameter search; no LLM call",
        "source_plan_set": (source.relative_to(ROOT).as_posix() if source.is_relative_to(ROOT)
                            else str(source)),
        "source_sha256": {name: digest(path) for name, path in files.items()},
        "variants": {},
    }
    for plan_set, p2 in candidates.items():
        folder = out / plan_set
        folder.mkdir()
        for name in ("P0.json", "P1.json", "generation-inputs.json"):
            copyfile(files[name], folder / name)
        save_json(folder / "P2.json", p2)
        manifest["variants"][plan_set] = {
            "description": VARIANTS[plan_set][1],
            "p2_sha256": digest(folder / "P2.json"),
            "unchanged_comparators": ["P0.json", "P1.json", "generation-inputs.json"],
        }
    save_json(out / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", required=True, help="Saved model-generated P0/P1/P2 plan folder")
    parser.add_argument("--out", required=True, help="New folder for the diagnostic plan sets")
    args = parser.parse_args()
    manifest = prepare(args.source, args.out)
    print(f"Prepared {len(manifest['variants'])} diagnostic plan sets in {args.out}; "
          "no model or simulator was called, and no benefit is claimed.")


if __name__ == "__main__":
    main()
