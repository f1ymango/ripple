"""Incident Reader (component B, GenAI #1): one Special Traffic News message -> incident.json.

The model extracts only what is written in the message: road, direction,
lanes, incident type, scope, confidence. Fields the feed already carries
(ID, text, time, status, coordinates) are copied by code, never by the model.
A reply that fails validation is retried once, then flagged, never used.
"""
import json
from pathlib import Path

import jsonschema

from src import llm

HERE = Path(__file__).parent
SCHEMA = json.loads((HERE / "incident.schema.json").read_text(encoding="utf-8"))
SYSTEM_PROMPT = (HERE / "prompts" / "system.md").read_text(encoding="utf-8")

MODEL = None       # pin once a provider is chosen (see src/llm.py)
TEMPERATURE = 0.0  # extraction, not creativity

# STN fields the model sees. IDs, times, status and coordinates are withheld:
# code copies those, so the model has no reason to repeat them.
INPUT_FIELDS = [
    "INCIDENT_HEADING_EN", "INCIDENT_HEADING_CN", "INCIDENT_DETAIL_EN", "INCIDENT_DETAIL_CN",
    "LOCATION_EN", "LOCATION_CN", "DISTRICT_EN", "DISTRICT_CN", "DIRECTION_EN", "DIRECTION_CN",
    "NEAR_LANDMARK_EN", "NEAR_LANDMARK_CN", "BETWEEN_LANDMARK_EN", "BETWEEN_LANDMARK_CN",
    "CONTENT_EN", "CONTENT_CN",
]

# The model's reply: exactly the [llm] fields of the contract, nothing more.
LLM_FIELDS = ["district", "road_name", "direction", "near_landmark", "between_landmark",
              "incident_type", "lanes_closed", "lanes_total", "in_scope", "confidence", "notes"]
REPLY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": LLM_FIELDS,
    "properties": {field: SCHEMA["properties"][field] for field in LLM_FIELDS},
}


class ReaderError(Exception):
    """The model's reply failed validation twice, so the message is flagged instead of parsed."""


def read_message(stn: dict) -> dict:
    """Turn one STN message ({feed field: text}) into a validated incident.json dict."""
    user = json.dumps({field: stn[field] for field in INPUT_FIELDS}, ensure_ascii=False, indent=2)
    problems = []
    for _attempt in range(2):
        reply = llm.complete_json(component="reader", model=MODEL, system=SYSTEM_PROMPT,
                                  user=user, schema=REPLY_SCHEMA, temperature=TEMPERATURE)
        try:
            extracted = json.loads(reply)
            jsonschema.validate(extracted, REPLY_SCHEMA)
            incident = assemble(stn, extracted)
            jsonschema.validate(incident, SCHEMA)
            return incident
        except (json.JSONDecodeError, jsonschema.ValidationError) as exc:
            problems.append(str(exc).splitlines()[0])
    raise ReaderError(f"{stn['INCIDENT_NUMBER']} (message {stn['ID']}): {problems}")


def assemble(stn: dict, extracted: dict) -> dict:
    """incident.json in contract order: feed fields copied by code, the rest from the model."""
    has_coords = bool(stn["LATITUDE"] and stn["LONGITUDE"])
    return {
        "incident_id": stn["INCIDENT_NUMBER"],
        "source_message_en": stn["CONTENT_EN"],
        "source_message_zh": stn["CONTENT_CN"],
        "announced_at": stn["ANNOUNCEMENT_DATE"] + "+08:00",  # feed times are Hong Kong time
        "closed_at": None,  # needs the whole incident timeline: component A2 sets it
        "status": stn["INCIDENT_STATUS_EN"],
        "district": stn["DISTRICT_EN"] or extracted["district"],
        "road_name": extracted["road_name"],
        "direction": extracted["direction"],
        "near_landmark": extracted["near_landmark"],
        "between_landmark": extracted["between_landmark"],
        "lat": float(stn["LATITUDE"]) if has_coords else None,
        "lon": float(stn["LONGITUDE"]) if has_coords else None,
        "coords_source": "source" if has_coords else "none",
        "incident_type": extracted["incident_type"],
        "lanes_closed": extracted["lanes_closed"],
        "lanes_total": extracted["lanes_total"],
        "in_scope": extracted["in_scope"],
        "confidence": extracted["confidence"],
        "notes": extracted["notes"],
    }
