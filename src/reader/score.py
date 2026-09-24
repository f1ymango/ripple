"""Score one Incident Reader run against the gold labels: the Reader's accuracy number.

    python -m src.reader.run --messages data/labelled_incidents/gold_messages.jsonl
    python -m src.reader.score --run results/reader/<run_id>.jsonl

Prints the table and writes results/reader/<run_id>_score.json. The matching
rules were fixed before any score was seen (LABELLING.md, "How it is scored"):

- text fields match after trimming, collapsing spaces and ignoring case;
- lanes_closed matches as a set; every other field must be equal;
- a flagged message (the Reader gave up on it) is wrong on every field;
- labels marked unsure are scored like the rest, and counted.

Each figure comes with a 95% Wilson interval: on ~100 messages, one message
is one percentage point, so the interval is part of the number.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from src.reader import gold


def normalise(text: str | None) -> str | None:
    """'  Aberdeen   tunnel ' -> 'aberdeen tunnel'; None stays None."""
    return None if text is None else " ".join(text.split()).casefold()


def field_correct(field: str, predicted, expected) -> bool:
    """Does the Reader's value for one field match the label, under the rules above?"""
    if field == "lanes_closed":
        return set(predicted) == set(expected)
    if field in gold.TEXT_FIELDS:
        return normalise(predicted) == normalise(expected)
    return predicted == expected


def wilson(correct: int, n: int, z: float = 1.96) -> list[float] | None:
    """95% confidence interval for a proportion; sensible even at 0% or 100%."""
    if n == 0:
        return None
    p = correct / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(centre - half, 3), round(centre + half, 3)]


def score(run_rows: list[dict], labels: dict[str, dict], strata: dict[str, str]) -> dict:
    """Per-stratum and overall accuracy of one run, on every labelled message."""
    by_id = {row["message_id"]: row for row in run_rows}
    missing = sorted(set(labels) - set(by_id))
    if missing:
        raise ValueError(f"the run has no output for labelled messages {missing}")

    groups = {"all": list(labels)}
    for message_id in labels:
        groups.setdefault(strata.get(message_id, "unknown"), []).append(message_id)

    report = {}
    for group, ids in groups.items():
        counts = dict.fromkeys(gold.SCORED_FIELDS + ["all_fields"], 0)
        wrong = []
        for message_id in ids:
            incident = by_id[message_id].get("incident")  # absent when the Reader flagged it
            right = [incident is not None
                     and field_correct(f, incident[f], labels[message_id][f])
                     for f in gold.SCORED_FIELDS]
            for field, ok in zip(gold.SCORED_FIELDS, right):
                counts[field] += ok
            counts["all_fields"] += all(right)
            if not all(right):
                wrong.append(message_id)
        n = len(ids)
        report[group] = {
            "messages": n,
            "flagged": sum("incident" not in by_id[i] for i in ids),
            "labelled_unsure": sum(labels[i]["unsure"] for i in ids),
            "fields": {field: {"correct": c, "accuracy": round(c / n, 3) if n else None,
                               "ci95": wilson(c, n)} for field, c in counts.items()},
            "not_all_right": wrong,
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, required=True, help="results/reader/<run_id>.jsonl")
    parser.add_argument("--labels", type=Path, default=gold.LABELS_PATH)
    parser.add_argument("--messages", type=Path, default=gold.MESSAGES_PATH)
    args = parser.parse_args()

    messages = gold.load_messages(args.messages)
    labels = gold.load_labels(args.labels)
    if not labels:
        parser.error(f"no labels in {args.labels}")
    run_rows = [json.loads(line) for line in args.run.read_text(encoding="utf-8").splitlines()]
    strata = {m["stn"]["ID"]: m.get("stratum", "unknown") for m in messages}

    report = score(run_rows, labels, strata)
    out = {
        "run": args.run.name,
        "labels": args.labels.name,
        # Hash of the labels themselves, not the file's bytes, so a CRLF checkout hashes the same.
        "labels_sha256": hashlib.sha256(json.dumps(
            labels, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "labelled": len(labels),
        "gold_messages": len(messages),
        "strata": report,
    }
    out_path = args.run.with_name(f"{args.run.stem}_score.json")
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    if len(labels) < len(messages):
        print(f"!! only {len(labels)} of {len(messages)} gold messages are labelled: "
              f"not the final number")
    for group, result in report.items():
        print(f"\n{group}: {result['messages']} messages, {result['flagged']} flagged, "
              f"{result['labelled_unsure']} labelled unsure")
        for field, f in result["fields"].items():
            low, high = f["ci95"]
            print(f"  {field:18} {f['correct']:>3}/{result['messages']:<3} "
                  f"{f['accuracy']:>6.1%}   95% CI {low:.0%}-{high:.0%}")
    print(f"\n-> {out_path}")


if __name__ == "__main__":
    main()
