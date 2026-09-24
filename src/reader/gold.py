"""The gold set: hand-written answers that the Incident Reader's accuracy is measured against.

    data/labelled_incidents/gold_messages.jsonl   the messages (src/reader/sample.py)
    data/labelled_incidents/gold_labels.jsonl     one label per message (src/reader/label.py)

A label holds the right answer for each field the model extracts, in the
contract's own values (src/reader/incident.schema.json), plus two fields for
the labeller: `unsure` and `comment`. The model's `confidence` and `notes` are
its own opinion, so they are not labelled. How to label each field:
data/labelled_incidents/LABELLING.md.
"""
import json
from pathlib import Path

import jsonschema

from src.reader import reader

ROOT = Path(__file__).resolve().parents[2]
MESSAGES_PATH = ROOT / "data" / "labelled_incidents" / "gold_messages.jsonl"
LABELS_PATH = ROOT / "data" / "labelled_incidents" / "gold_labels.jsonl"

TEXT_FIELDS = ["road_name", "direction", "near_landmark", "between_landmark"]
SCORED_FIELDS = TEXT_FIELDS + ["incident_type", "lanes_closed", "lanes_total"]

LABEL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["message_id", "incident_id", *SCORED_FIELDS, "unsure", "comment"],
    "properties": {
        "message_id": {"type": "string"},
        "incident_id": {"type": "string"},
        **{field: reader.SCHEMA["properties"][field] for field in SCORED_FIELDS},
        "unsure": {"type": "boolean", "description": "The labeller could not decide; see comment."},
        "comment": {"type": "string", "description": "The labeller's note, never scored."},
    },
}


def validate(label: dict) -> None:
    """Raise ValueError (or jsonschema.ValidationError) if a label breaks the contract's rules."""
    jsonschema.validate(label, LABEL_SCHEMA)
    reader.check_lanes(label["lanes_closed"])
    for field in TEXT_FIELDS:
        if label[field] is not None and not label[field].strip():
            raise ValueError(f"{field} is blank: use null for 'the message does not say'")


def load_messages(path: Path = MESSAGES_PATH) -> list[dict]:
    """The gold messages, in file order, each {"archive_time", "stratum", "stn"}."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def load_labels(path: Path = LABELS_PATH) -> dict[str, dict]:
    """Labels written so far, by message ID. Each one is validated on the way in."""
    if not path.exists():
        return {}
    labels = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        label = json.loads(line)
        try:
            validate(label)
        except (ValueError, jsonschema.ValidationError) as exc:
            raise ValueError(f"{path.name} line {number}: {str(exc).splitlines()[0]}") from exc
        labels[label["message_id"]] = label
    return labels


def save_labels(labels: dict[str, dict], messages: list[dict], path: Path = LABELS_PATH) -> None:
    """Rewrite the labels file in message order, so its git diff reads like the work done."""
    order = [m["stn"]["ID"] for m in messages]
    strays = set(labels) - set(order)
    if strays:
        raise ValueError(f"labels for messages not in the gold set: {sorted(strays)}")
    tmp = path.with_suffix(".part")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for message_id in order:
            if message_id in labels:
                f.write(json.dumps(labels[message_id], ensure_ascii=False) + "\n")
    tmp.replace(path)  # never a half-written file, even if the app is closed mid-save
