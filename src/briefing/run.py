"""python -m src.briefing.run --plans DIR --results FILE... --out FILE"""
import argparse
from pathlib import Path

from src.briefing.writer import write_briefing
from src.generation import load_json, save_json
from src.plans.generator import validate_plans


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plans", required=True, help="Directory written by src.plans.run")
    parser.add_argument("--results", nargs="+", required=True, help="E's saved results/runs/*.json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="qwen3:8b")
    args = parser.parse_args()
    if Path(args.out).exists():
        raise ValueError("Use a new briefing output file")
    directory = Path(args.plans)
    inputs = load_json(directory / "generation-inputs.json")
    plans = validate_plans({"plans": [load_json(directory / f"P{i}.json") for i in range(3)]},
                           inputs["policy_context"], inputs["incident"])
    briefing = write_briefing(plans, args.results, args.model,
                              generation_inputs=inputs)
    save_json(args.out, briefing)
    print(f"Operator draft saved to {args.out}; human approval is required.")


if __name__ == "__main__":
    main()
