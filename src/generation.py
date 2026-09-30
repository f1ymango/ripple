"""Shared JSON validation and bounded, logged generation for D and F."""
import json
from pathlib import Path

import jsonschema

from src import llm


def validate(value, schema):
    """Reject non-finite numbers as well as schema violations."""
    json.dumps(value, allow_nan=False)
    jsonschema.validate(value, schema, format_checker=jsonschema.FormatChecker())


def load_json(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    json.dumps(value, allow_nan=False)
    return value


def save_json(path, value):
    """Do not overwrite an earlier handoff or evidence artifact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def generate_checked(*, component, prompt, payload, schema, check, model, temperature):
    system = Path(prompt).read_text(encoding="utf-8")
    errors = []
    for _ in range(2):
        request = {"input": payload, "previous_validation_errors": errors}
        reply = llm.complete_json(
            component=component, model=model, system=system,
            user=json.dumps(request, ensure_ascii=False, allow_nan=False),
            schema=schema, temperature=temperature)
        try:
            value = json.loads(reply)
            validate(value, schema)
            return check(value)
        except (ValueError, jsonschema.ValidationError) as exc:
            errors.append(str(exc).splitlines()[0])
    raise ValueError(f"{component}: invalid response after two attempts: {errors}")
