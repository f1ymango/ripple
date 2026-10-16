"""Tuen Mun: a diagnostic plan set that sweeps the Castle Peak Road share, for calibration seeds only.

    python scripts/tuen_mun/share_sweep_plans.py --share 0.2 \
        --out data/generated-plans/IN-26-02615-data-share-0.2-oct15

P0, P1 (the broadcast, which D requires) and the generation inputs are the Lead's
(data/generated-plans/IN-26-02615-lead-capacity-oct15), byte for byte. P2 here is not a Ripple plan: it is
the Lead's P2 with another share, checked by D's own validator, so E can run it. They exist to show how the saving moves with the share on seeds 2026-2028
(the seeds every P0 was built on), so plan generation can choose a share before any fresh seed is used.
No LLM is called.
"""
import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.generation import load_json, save_json   # noqa: E402
from src.plans.generator import validate_plans     # noqa: E402

LEAD = ROOT / "data/generated-plans/IN-26-02615-lead-capacity-oct15"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--share", type=float, required=True, help="P2's share")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = ROOT / args.out
    if out.exists():
        raise FileExistsError(f"{out} exists; a plan set is never rewritten")
    inputs = load_json(LEAD / "generation-inputs.json")
    p2 = deepcopy(load_json(LEAD / "P2.json"))
    p2["diversions"][0]["share"] = args.share
    p2["label"] = f"Share sweep: Castle Peak Road advice to {args.share:g} of the group (diagnostic, not a Ripple plan)"
    p2["rationale"] = ("Data's calibration-seed sweep of the Lead's P2 share; it shows how the saving moves "
                       "with the share and proposes nothing.")
    plans = [load_json(LEAD / "P0.json"), load_json(LEAD / "P1.json"), p2]
    checked = validate_plans({"plans": plans}, inputs["policy_context"], inputs["incident"])
    if checked != plans:
        raise ValueError("D's validator changed a sweep plan")
    out.mkdir(parents=True)
    for name in ("P0.json", "P1.json", "generation-inputs.json"):
        copyfile(LEAD / name, out / name)
    save_json(out / "P2.json", p2)
    save_json(out / "sweep-manifest.json", {"derived_from": str(LEAD.relative_to(ROOT)), "p2_share": args.share,
               "generated_by": "python scripts/tuen_mun/share_sweep_plans.py",
               "status": "diagnostic for calibration seeds 2026-2028 only; not a Ripple plan set"})
    print(out, file=sys.stderr)


if __name__ == "__main__":
    main()
