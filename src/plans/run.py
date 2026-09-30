"""python -m src.plans.run --incident PATH --context PATH --out-dir PATH"""
import argparse
import json
from pathlib import Path

from src.generation import load_json, save_json
from src.plans.generator import generate


def read_incident(path, message_id=None):
    path = Path(path)
    if path.suffix == ".jsonl":
        if not message_id:
            raise ValueError("--message-id is required for Reader JSONL; never choose an update silently")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        matches = [r["incident"] for r in rows if r.get("message_id") == message_id and "incident" in r]
        if len(matches) != 1:
            raise ValueError("Expected exactly one parsed incident with that message ID")
        return matches[0]
    return load_json(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incident", required=True)
    parser.add_argument("--message-id")
    parser.add_argument("--context", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--model", default="qwen3:8b")
    args = parser.parse_args()
    out = Path(args.out_dir)
    if out.exists():
        raise ValueError("Use a new output directory to preserve earlier handoffs")
    context = load_json(args.context)
    incident = read_incident(args.incident, args.message_id)
    plans = generate(incident, context, args.model)
    out.mkdir(parents=True)
    for plan in plans:
        save_json(out / f"{plan['plan_id']}.json", plan)
    save_json(out / "generation-inputs.json", {"incident": incident, "policy_context": context})
    print(f"Validated P0/P1/P2 written to {out}; not yet simulated or approved.")


if __name__ == "__main__":
    main()
