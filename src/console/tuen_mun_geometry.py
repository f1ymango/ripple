"""Map overlay for the Tuen Mun case, using only saved SUMO network shapes.

This selects named roads from the same projected network used by the case.
The blue and purple paths identify road geography, not measured speed, a
validated route, or an operator recommendation.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import html
from pathlib import Path
import re

import pandas as pd

from src.console import road_geometry


ROOT = Path(__file__).resolve().parents[2]
NETWORK = ROOT / "sim" / "tuen-mun" / "network.net.xml"

MAIN = "Main corridor"
ALTERNATIVE = "Alternative roads"
COLOURS = {MAIN: [40, 100, 220, 220], ALTERNATIVE: [133, 72, 184, 220]}


def road_group(name: str) -> str | None:
    """Classify full English road names; similar names must not be included."""
    if not isinstance(name, str):
        return None
    # SUMO names are bilingual, e.g. "屯門公路 Tuen Mun Road". Keep the English
    # suffix intact, including the en dash in Castle Peak Road section names.
    english = re.search(r"[A-Za-z][A-Za-z ./'’–-]*$", html.unescape(name))
    normalized = " ".join(english.group().casefold().split()) if english else ""
    if normalized == "tuen mun road":
        return MAIN
    if (normalized == "castle peak road"
            or re.fullmatch(r"castle peak road\s*[–-]\s*[a-z][a-z ./'’–-]*", normalized)):
        return ALTERNATIVE
    return None


def select_overlay(geometry: dict) -> list[dict]:
    """Select actual road paths and only source junctions between selected edges.

    ``app.build_map`` accepts these records directly as its ``roads`` argument.
    No missing connection is drawn as a straight line.
    """
    selected = []
    by_edge = {}
    for road in geometry["roads"]:
        group = road_group(road["road_name"])
        if group is None:
            continue
        record = {**road, "group": group, "colour": COLOURS[group], "width": 3}
        selected.append(record)
        by_edge[record["edge_id"]] = record

    for junction in geometry["junctions"]:
        source = by_edge.get(junction["from_edge"])
        if source is None or junction["to_edge"] not in by_edge:
            continue
        selected.append({**junction, "group": source["group"],
                         "colour": source["colour"], "width": 3})
    return selected


@lru_cache(maxsize=4)
def _load_source(path: str, sha256: str) -> dict:
    return road_geometry.load_geometry(Path(path), sha256)


def load_overlay(network: Path = NETWORK) -> list[dict]:
    """Read a content-identified Tuen Mun network and return PyDeck path records."""
    path = network.expanduser().resolve()
    fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
    return select_overlay(_load_source(str(path), fingerprint))


def overlay_frame(network: Path = NETWORK) -> pd.DataFrame:
    """Inspection-friendly table; use ``load_overlay`` to pass roads to the map."""
    return pd.DataFrame.from_records(load_overlay(network))
