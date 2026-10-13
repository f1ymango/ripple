"""Check saved Reader inference against its TD input and original call log."""
import json
from pathlib import Path

import jsonschema

from src.reader.reader import INPUT_FIELDS, REPLY_SCHEMA, SCHEMA, assemble, check_lanes


def _rows(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"Non-object record in {path.name}")
    return rows


def _one(rows: list[dict], label: str) -> dict:
    if len(rows) != 1:
        raise ValueError(f"Expected one {label}; found {len(rows)}")
    return rows[0]


def read(message, archive: Path, output: Path, log: Path) -> dict | None:
    """Return only a matching, logged example; never call a model or infer fields."""
    if not output.exists():
        return None
    matches = [row for row in _rows(output)
               if str(row.get("message_id")) == message.message_id]
    if not matches:
        return None
    saved = _one(matches, "saved Reader output")
    raw = _one([row for row in _rows(archive)
                if str(row.get("stn", {}).get("ID")) == message.message_id],
               "archived source message")["stn"]
    if (raw["INCIDENT_NUMBER"] != message.incident_id
            or raw["CONTENT_EN"] != message.english
            or raw["CONTENT_CN"] != message.chinese
            or saved.get("incident_id") != message.incident_id):
        raise ValueError("Saved Reader identity/text differs from the displayed message")
    expected_input = {field: raw[field] for field in INPUT_FIELDS}
    calls = [row for row in _rows(log)
             if row.get("component") == "reader" and not row.get("error")
             and json.loads(row["user"]) == expected_input]
    call = _one(calls, "matching Reader call")
    extracted = json.loads(call["response"])
    jsonschema.validate(extracted, REPLY_SCHEMA)
    check_lanes(extracted["lanes_closed"])
    incident = assemble(raw, extracted)
    jsonschema.validate(incident, SCHEMA)
    if (saved.get("incident") != incident
            or incident["announced_at"] != message.published.isoformat()):
        raise ValueError("Saved Reader output differs from its logged response or publication time")
    return {"incident": incident, "model": call["model"], "timestamp": call["timestamp"]}
