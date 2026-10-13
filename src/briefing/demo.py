"""Exercise the real briefing model with visibly synthetic, saved fixtures.

Run from the repository root: python -m src.briefing.demo --check-only
or --out tests/fixtures/mock_genai_briefing_<date>_a.json.
Nothing here evaluates traffic or supplies an operational recommendation.
"""
import argparse
from pathlib import Path

from src.briefing.writer import prepare_comparison, write_briefing
from src.generation import load_json, save_json

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
INPUTS = FIXTURES / "mock_recommendation"


def demo(out=None, model="qwen3:8b"):
    """Check existing fixture provenance, then optionally make a logged model call."""
    if out is not None:
        out = Path(out).resolve()
        if out.parent != FIXTURES.resolve() or not out.name.startswith("mock_") or out.suffix != ".json":
            raise ValueError("Fixture output must be tests/fixtures/mock_*.json")
        if out.exists():
            raise ValueError("Use a new fixture output file to preserve earlier evidence")
    plans = [load_json(INPUTS / f"mock_p{i}.json") for i in range(3)]
    paths = [INPUTS / f"mock_p{i}_result.json" for i in range(3)]
    inputs = load_json(INPUTS / "mock_generation-inputs.json")
    selected, _, _, _ = prepare_comparison(
        plans, paths, generation_inputs=inputs, results_root=INPUTS)
    print(f"SYNTHETIC FIXTURE DEMO: provenance checked; selected {selected['plan_id']}.")
    if out is None:
        return None
    result = write_briefing(plans, paths, model, generation_inputs=inputs, results_root=INPUTS)
    save_json(out, result)
    print(f"Fixture model output saved to {out}. No real traffic benefits are measured.")
    print("Source aliases results/runs/mock_* refer to tests/fixtures/mock_recommendation/mock_*.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--out")
    parser.add_argument("--model", default="qwen3:8b")
    args = parser.parse_args()
    if args.check_only == bool(args.out):
        parser.error("Choose exactly one of --check-only or --out")
    demo(args.out, args.model)


if __name__ == "__main__":
    main()
