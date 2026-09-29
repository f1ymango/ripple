"""Hong Kong general holidays, so an "ordinary day" is never a public holiday.

The candidate screen (candidates.py) compares each incident with the same
weekday 1-6 weeks earlier. Until 29 Sep 2026 it did not skip public holidays:
the headline demo incident, Fri 15 May, was measured against Fri 1 May, Labour
Day, when the morning peak is lighter than on a working Friday.

The list is the government's own (1823). It is saved in the repo, so the
screen reads a committed file and gives the same answer offline:

    python -m src.loaders.fetch holidays       # -> data/hk_holidays.csv
"""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

import requests

from src.loaders.common import write_csv

SOURCE_URL = "https://www.1823.gov.hk/common/ical/en.json"
OUT_PATH = Path("data/hk_holidays.csv")


def parse(body: bytes) -> list[dict]:
    """1823's calendar JSON -> [{"date": "2026-05-01", "name": "Labour Day"}, ...]."""
    # utf-8-sig: the file starts with a byte-order mark.
    events = json.loads(body.decode("utf-8-sig"))["vcalendar"][0]["vevent"]
    rows = [{"date": dt.datetime.strptime(e["dtstart"][0], "%Y%m%d").date().isoformat(),
             "name": e["summary"]} for e in events]
    return sorted(rows, key=lambda r: r["date"])


def download(out_path: Path = OUT_PATH) -> list[dict]:
    """Fetch the official list and write data/hk_holidays.csv."""
    resp = requests.get(SOURCE_URL, timeout=60)
    resp.raise_for_status()
    rows = parse(resp.content)
    write_csv(rows, out_path)
    return rows


def load(path: Path = OUT_PATH) -> dict[dt.date, str]:
    """{date: holiday name} from the committed list."""
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing -- run `python -m src.loaders.fetch holidays`")
    with path.open(encoding="utf-8", newline="") as f:
        return {dt.date.fromisoformat(r["date"]): r["name"] for r in csv.DictReader(f)}


def require_years(holidays: dict[dt.date, str], first: dt.date, last: dt.date) -> None:
    """Refuse to screen a year the list does not cover, rather than call every day ordinary."""
    have = {d.year for d in holidays}
    missing = [y for y in range(first.year, last.year + 1) if y not in have]
    if missing:
        raise ValueError(f"the holiday list has no {missing}; run `python -m src.loaders.fetch "
                         f"holidays` for a newer one")
