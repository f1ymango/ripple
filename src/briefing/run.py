"""python -m src.briefing.run --plans DIR --results FILE... --out FILE"""
import argparse
from pathlib import Path

from src.briefing.writer import prepare_comparison, write_briefing
from src.generation import load_json, save_json
from src.plans.generator import validate_plans


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plans", required=True, help="Directory written by src.plans.run")
    parser.add_argument("--results", nargs="+", required=True, help="E's saved results/runs/*.json")
    parser.add_argument("--out")
    parser.add_argument("--check-only", action="store_true",
                        help="Validate plans, results and provenance without a model call or output")
    parser.add_argument("--model", default="qwen3:8b")
    args = parser.parse_args()
    if args.check_only and args.out:
        parser.error("--check-only cannot be combined with --out")
    if not args.check_only and not args.out:
        parser.error("--out is required unless --check-only is used")
    if args.out and Path(args.out).exists():
        raise ValueError("Use a new briefing output file")
    directory = Path(args.plans)
    inputs = load_json(directory / "generation-inputs.json")
    plans = validate_plans({"plans": [load_json(directory / f"P{i}.json") for i in range(3)]},
                           inputs["policy_context"], inputs["incident"])
    if args.check_only:
        plan, result, _, _ = prepare_comparison(plans, args.results, generation_inputs=inputs)
        print(f"Handoff checks passed; lowest-delay candidate: {plan['plan_id']} "
              f"({result['run_id']}). No model called or output written; "
              "full incident validation and human review remain required.")
        return
    briefing = write_briefing(plans, args.results, args.model,
                              generation_inputs=inputs)
    save_json(args.out, briefing)
    print(f"Operator draft saved to {args.out}; human approval is required.")


if __name__ == "__main__":
    main()
