"""Run the Incident Reader over a file of STN messages and save what it produced.

    python -m src.reader.run --model qwen3:8b --messages data/labelled_incidents/messages.jsonl

Writes results/reader/<run_id>.jsonl, one line per message: the parsed
incident, or the reason the message was flagged.
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from src import llm
from src.reader import reader


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--messages", default="data/labelled_incidents/messages.jsonl")
    parser.add_argument("--model", default=reader.MODEL,
                        help="model tag, e.g. qwen3:8b (default: MODEL in src/reader/reader.py)")
    args = parser.parse_args()
    if args.model is None:
        sys.exit("No model given: pass --model (e.g. qwen3:8b) or pin MODEL in src/reader/reader.py.")

    lines = Path(args.messages).read_text(encoding="utf-8").splitlines()
    safe_model = re.sub(r"[^\w.-]", "-", args.model)  # "qwen3:8b" is not a valid Windows file name
    run_id = f"{datetime.now(llm.HKT):%Y-%m-%dT%H%M}_{safe_model}"
    out_path = Path("results/reader") / f"{run_id}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    parsed = flagged = 0
    started = time.perf_counter()
    with out_path.open("w", encoding="utf-8", newline="\n") as out:
        for line in lines:
            stn = json.loads(line)["stn"]
            row = {"message_id": stn["ID"], "incident_id": stn["INCIDENT_NUMBER"]}
            try:
                row["incident"] = reader.read_message(stn, model=args.model)
                parsed += 1
            except reader.ReaderError as exc:
                row["flagged"] = str(exc)
                flagged += 1
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    seconds = time.perf_counter() - started
    print(f"{parsed} parsed, {flagged} flagged in {seconds:.0f}s "
          f"({seconds / len(lines):.1f}s per message) -> {out_path}")


if __name__ == "__main__":
    main()
