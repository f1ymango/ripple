"""The one place where Ripple talks to an LLM (Reader, Plan Generator, Briefing Writer).

Every call is appended to evidence/ai-log/<date>.jsonl with the prompt, the
reply, the model, its settings and a timestamp (CLAUDE.md rule 5).

For now models run locally through Ollama (https://ollama.com). Switching
provider means rewriting `_send` only.
"""
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

HKT = timezone(timedelta(hours=8))
LOG_DIR = Path("evidence/ai-log")

OLLAMA_URL = "http://localhost:11434/api/chat"
SEED = 42              # runs are seeded (CLAUDE.md rule 7)
CONTEXT_TOKENS = 8192  # room for prompt + message: Ollama silently cuts whatever overflows
MAX_OUTPUT_TOKENS = 2048  # bound malformed/repeating structured replies before context shifting


def complete_json(*, component: str, model: str, system: str, user: str,
                  schema: dict, temperature: float) -> str:
    """Ask the model for one JSON reply that follows `schema`, and return the raw text.

    The reply is only a candidate: validating it is the caller's job.
    """
    sent_at = datetime.now(HKT)
    started = time.perf_counter()
    entry = {
        "timestamp": sent_at.isoformat(timespec="seconds"),
        "component": component,
        "model": model,
        "temperature": temperature,
        "seed": SEED,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "system": system,
        "user": user,
    }
    try:
        reply = _send(model=model, system=system, user=user, schema=schema, temperature=temperature)
    except Exception as exc:
        _log({**entry, "duration_s": round(time.perf_counter() - started, 2),
              "response": None, "error": str(exc)})
        raise
    _log({**entry, "duration_s": round(time.perf_counter() - started, 2), "response": reply})
    return reply


def _send(*, model: str, system: str, user: str, schema: dict, temperature: float) -> str:
    """Send one request to the local Ollama server and return the model's reply text.

    `format` requests schema-constrained output. Truncation or model failures
    can still produce an invalid reply; parsing and validation belong to the
    caller. The output limit bounds repetitive generation.
    """
    resp = requests.post(OLLAMA_URL, timeout=600, json={
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "format": schema,
        "think": False,  # Qwen3's "thinking" mode is for reasoning; this is extraction
        "stream": False,
        "options": {"temperature": temperature, "seed": SEED, "num_ctx": CONTEXT_TOKENS,
                    "num_predict": MAX_OUTPUT_TOKENS},
    })
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _log(entry: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / f"{entry['timestamp'][:10]}.jsonl").open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
