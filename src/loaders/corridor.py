"""The Aberdeen corridor: which detectors are ours, and which roads are ours (component A3).

Two different jobs need "is this on our corridor?" and they need different
answers, so both live here:

  * DETECTOR_IDS -- the 28 Transport Department detectors on the corridor.
    Every one was checked against the live raw feed and the locations CSV on
    22 Sep 2026: all 28 present in both.
  * CORRIDOR_ROADS -- road-name fragments, for screening Special Traffic News
    messages, whose LATITUDE/LONGITUDE and DISTRICT fields are usually empty
    (docs/02-data.md section 2).

    python -m src.loaders.fetch corridor      # -> data/detectors.csv
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import requests

from src.loaders.common import write_csv

LOCATIONS_CSV = ("https://static.data.gov.hk/td/traffic-data-strategic-major-roads/"
                 "info/traffic_speed_volume_occ_info.csv")
OUT_PATH = Path("data/detectors.csv")

# docs/02-data.md section 5. Chain 1 runs Aberdeen -> Wan Chai / Causeway Bay,
# chain 2 comes back, and the TDS* detectors cover the western alternative
# via Pok Fu Lam Road, past Queen Mary Hospital.
CHAIN_EASTBOUND = [f"AID011{n:02d}" for n in range(1, 11)]      # AID01101..AID01110
CHAIN_WESTBOUND = [f"AID012{n:02d}" for n in range(14, 24)]     # AID01214..AID01223
WESTERN_ALTERNATIVE = [
    "TDSSPWR10001", "TDSSPWR10002", "TDSSPWR10003",
    "TDSSPWR20001", "TDSSPWR20002", "TDSSPWR20003",
    "TDSAPR10001", "TDSAPR20001",
]
# Directed station order for the two Western Alternative carriageways. These
# orders follow the direction fields and HK1980 coordinates in data/detectors.csv;
# WESTERN_ALTERNATIVE above remains the loader's inventory of those stations.
CHAIN_WESTERN_EASTBOUND = [
    "TDSSPWR10001", "TDSSPWR10002", "TDSSPWR10003", "TDSAPR10001",
]
CHAIN_WESTERN_WESTBOUND = [
    "TDSAPR20001", "TDSSPWR20003", "TDSSPWR20002", "TDSSPWR20001",
]
DETECTOR_IDS: list[str] = CHAIN_EASTBOUND + CHAIN_WESTBOUND + WESTERN_ALTERNATIVE

# Which leg each detector belongs to, so results can be reported per leg.
LEG = ({d: "main_eastbound" for d in CHAIN_EASTBOUND}
       | {d: "main_westbound" for d in CHAIN_WESTBOUND}
       | {d: "western_alternative" for d in WESTERN_ALTERNATIVE})

# The two detectors either side of the Aberdeen Tunnel. A corridor incident
# that does not move these is probably not worth simulating.
TUNNEL_DETECTORS = ["AID01107", "AID01217"]

# Lower-cased fragments matched against an STN message's LOCATION_EN and
# CONTENT_EN. Deliberately broad: a false positive costs one row in a
# shortlist, a false negative loses a candidate incident we never see again.
CORRIDOR_ROADS = [
    "aberdeen tunnel",
    "aberdeen praya road",
    "wong chuk hang road",
    "wong nai chung gap",
    "canal road flyover",
    "pok fu lam road",
    "shek pai wan road",
    "aberdeen police station",
    "wah fu",
]


def on_corridor(*texts: str) -> str | None:
    """The first corridor road named in any of these texts, or None.

    Code decides scope, not a language model -- the same rule the Incident
    Reader follows (see the repo README).
    """
    haystack = " ".join(t for t in texts if t).lower()
    for road in CORRIDOR_ROADS:
        if road in haystack:
            return road
    return None


def fetch_locations() -> list[dict[str, str]]:
    """The Transport Department's detector locations CSV, as rows."""
    resp = requests.get(LOCATIONS_CSV, timeout=60)
    resp.raise_for_status()
    # utf-8-sig: the file ships with a byte-order mark that otherwise ends up
    # glued to the first column name.
    return list(csv.DictReader(io.StringIO(resp.content.decode("utf-8-sig"))))


def build_table(out_path: Path = OUT_PATH) -> list[dict[str, str]]:
    """Write data/detectors.csv: our 28 detectors with position, road and leg.

    Latitude/Longitude are WGS-84 and go straight into a map or into SUMO's
    edge lookup. Easting/Northing (HK1980 Grid) are carried through unused, in
    case the Simulation owner wants them.
    """
    by_id = {row["AID_ID_Number"].strip(): row for row in fetch_locations()}
    missing = [d for d in DETECTOR_IDS if d not in by_id]
    if missing:
        raise RuntimeError(
            f"{len(missing)} corridor detectors are not in the locations CSV: {missing}. "
            "The Transport Department has changed the feed -- check docs/02-data.md "
            "section 5 before going further.")

    rows = []
    for detector_id in DETECTOR_IDS:
        source = by_id[detector_id]
        rows.append({
            "detector_id": detector_id,
            "leg": LEG[detector_id],
            "road_en": source["Road_EN"].strip(),
            "road_tc": source["Road_TC"].strip(),
            "district": source["District"].strip(),
            "direction": source["Direction"].strip(),
            "latitude": source["Latitude"].strip(),
            "longitude": source["Longitude"].strip(),
            "easting": source["Easting"].strip(),
            "northing": source["Northing"].strip(),
            "rotation": source["Rotation"].strip(),
        })

    write_csv(rows, out_path)
    return rows
