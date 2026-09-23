"""Shared constants and helpers for the data layer (component A).

One definition of each, so two commands can never disagree about them.
(src/llm.py has its own Hong Kong timezone; it belongs to component B and is
left alone.)
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

HK = dt.timezone(dt.timedelta(hours=8))   # every Transport Department time is GMT+8

# Shortest incident worth replaying: a clear NEW and CLOSED at least this many
# minutes apart (roles/data-experiments.md).
MIN_DURATION_MIN = 20


def write_csv(rows: list[dict], path: Path, encoding: str = "utf-8") -> Path:
    """Write dict rows to CSV, with the columns taken from the first row.

    An empty list raises ValueError with the path in it. Before, the
    three copies of this function each failed with an IndexError.
    Use encoding="utf-8-sig" for files people open in Excel on Windows, so the
    Chinese text survives.
    """
    if not rows:
        raise ValueError(f"no rows to write to {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
