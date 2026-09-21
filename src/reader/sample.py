"""Collect real Special Traffic News (STN) messages to test the Incident Reader on.

Pulls every archived snapshot of the STN feed between two dates from the
DATA.GOV.HK historical archive, keeps each distinct message once, picks one
message per incident, and writes a seeded shuffle of them to
data/labelled_incidents/messages.jsonl.

The order is prefix-stable: --n 20 and --n 120 with the same seed and dates
share their first 20 lines, so a dev set and a later test set never overlap
by accident.

Full incident timelines (NEW -> UPDATED -> CLOSED) are component A2's job;
this script only gathers inputs for the Reader.

    python -m src.reader.sample --start 2026-09-15 --end 2026-09-21 --n 20
"""
import argparse
import json
import random
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# The /en/ and /tc/ feeds are byte-identical: every message carries both languages.
STN_URL = "https://www.td.gov.hk/en/special_news/trafficnews.xml"
ARCHIVE_API = "https://api.data.gov.hk/v1/historical-archive"
CACHE_DIR = Path("data/raw/stn")
OUT_PATH = Path("data/labelled_incidents/messages.jsonl")

# The archive serves files from S3, which returns the odd 503 over a long pull.
http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=Retry(
    total=4, backoff_factor=2, status_forcelist=[500, 502, 503, 504])))


def list_snapshots(start: str, end: str) -> list[str]:
    """Archive timestamps (YYYYMMDD-HHmm) of every STN snapshot from start to end, inclusive."""
    resp = http.get(f"{ARCHIVE_API}/list-file-versions",
                    params={"url": STN_URL, "start": start, "end": end}, timeout=60)
    resp.raise_for_status()
    return resp.json()["timestamps"]


def fetch_snapshot(timestamp: str) -> bytes:
    """One archived snapshot, downloaded once and cached under data/raw/stn/."""
    path = CACHE_DIR / f"{timestamp}.xml"
    if not path.exists():
        resp = http.get(f"{ARCHIVE_API}/get-file",
                        params={"url": STN_URL, "time": timestamp}, timeout=60)
        resp.raise_for_status()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(resp.content)
        time.sleep(0.2)  # be polite to the archive
    return path.read_bytes()


def parse_messages(xml_bytes: bytes) -> list[dict]:
    """Every <message> in one snapshot, as {field name: text}, with '' for empty fields."""
    root = ET.fromstring(xml_bytes)
    return [{field.tag: (field.text or "").strip() for field in message}
            for message in root.findall("message")]


def pick(messages: list[dict], n: int, seed: int) -> list[dict]:
    """One message per incident, shuffled with a fixed seed, first n kept."""
    by_incident: dict[str, list[dict]] = {}
    for m in sorted(messages, key=lambda m: int(m["stn"]["ID"])):
        by_incident.setdefault(m["stn"]["INCIDENT_NUMBER"], []).append(m)
    rng = random.Random(seed)
    chosen = [rng.choice(by_incident[number]) for number in sorted(by_incident)]
    rng.shuffle(chosen)
    return chosen[:n]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", required=True, help="first day, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="last day, YYYY-MM-DD (archive ends yesterday)")
    parser.add_argument("--n", type=int, default=20, help="messages to keep")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    snapshots = list_snapshots(args.start.replace("-", ""), args.end.replace("-", ""))
    # Every message has its own ID and its text never changes, but its status can
    # flip later (e.g. UPDATED -> CLOSED) as the incident moves on. Keep the
    # version first seen, i.e. the status the message was issued with.
    distinct: dict[str, dict] = {}
    for timestamp in snapshots:
        for stn in parse_messages(fetch_snapshot(timestamp)):
            distinct.setdefault(stn["ID"], {"archive_time": timestamp, "stn": stn})

    chosen = pick(list(distinct.values()), args.n, args.seed)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="\n") as f:
        for message in chosen:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")
    incidents = len({m["stn"]["INCIDENT_NUMBER"] for m in distinct.values()})
    print(f"{len(snapshots)} snapshots, {len(distinct)} distinct messages, "
          f"{incidents} incidents -> wrote {len(chosen)} to {OUT_PATH}")


if __name__ == "__main__":
    main()
