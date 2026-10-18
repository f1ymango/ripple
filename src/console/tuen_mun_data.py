"""Read the archived Tuen Mun detector window for the operator console.

The observations are TD measurements prepared by the data layer, not SUMO
output. A missing count is not zero traffic, and a missing speed is not a
stopped vehicle. Keeping those distinctions lets the existing console render
unknown readings in grey.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OBSERVATIONS = ROOT / "sim" / "tuen-mun" / "observations_20260415.json"


def _number(value: object, label: str, *, allow_null: bool = False) -> float | None:
    if value is None and allow_null:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number" + (" or null" if allow_null else ""))
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _hkt(value: object) -> pd.Timestamp:
    if not isinstance(value, str):
        raise ValueError("observation time must be an ISO timestamp with an offset")
    try:
        stamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid observation time: {value}") from exc
    if stamp.tzinfo is None:
        raise ValueError("observation time must carry a timezone offset")
    return stamp.tz_convert("Asia/Hong_Kong")


def load_playback(
    path: str | Path = DEFAULT_OBSERVATIONS,
    placements_path: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(detectors, bins)`` for archived Tuen Mun playback.

    ``detectors`` has console-ready ``detector_id``, ``latitude``,
    ``longitude``, ``road_en``, ``direction``, ``edge_id`` and ``position_m``.
    ``bins`` has one row per detector and five-minute interval: ISO
    ``bin_start`` (with +08:00), timezone-aware ``bin_time``, nullable
    ``speed_kmh`` and ``volume_observed``, ``coverage_pct``, ``bin_minutes``,
    and ``state`` (``speed``, ``no_vehicles`` or ``unknown``). ``no_vehicles``
    requires an explicit zero count with some archive coverage. A null count
    can never create that state. If supplied, ``placements_path`` contributes
    more specific TD road names; it does not replace measured coordinates.
    """
    source = Path(path)
    with source.open(encoding="utf-8") as file:
        document = json.load(file)
    if not isinstance(document, dict) or not isinstance(document.get("detectors"), list):
        raise ValueError("Tuen Mun observations must contain a detectors list")
    interval = _number(document.get("interval_seconds"), "interval_seconds")
    if interval <= 0 or interval % 60:
        raise ValueError("interval_seconds must be a positive whole number of minutes")
    width = int(interval / 60)

    placements: dict = {}
    if placements_path is not None:
        with Path(placements_path).open(encoding="utf-8") as file:
            placements = json.load(file)
        if not isinstance(placements, dict):
            raise ValueError("detector placements must be a JSON object")

    detector_rows: list[dict] = []
    bin_rows: list[dict] = []
    seen_ids: set[str] = set()
    seen_bins: set[tuple[str, str]] = set()
    for detector in document["detectors"]:
        if not isinstance(detector, dict) or not isinstance(detector.get("observations"), list):
            raise ValueError("each detector must have an observations list")
        detector_id = detector.get("id")
        if not isinstance(detector_id, str) or not detector_id or detector_id in seen_ids:
            raise ValueError("detector IDs must be nonempty and unique")
        seen_ids.add(detector_id)
        latitude = _number(detector.get("lat"), f"{detector_id} latitude")
        longitude = _number(detector.get("lon"), f"{detector_id} longitude")
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError(f"{detector_id} coordinates are outside WGS84 bounds")
        placement = placements.get(detector_id, {})
        if not isinstance(placement, dict):
            raise ValueError(f"{detector_id} placement must be an object")
        detector_rows.append({
            "detector_id": detector_id,
            "latitude": latitude,
            "longitude": longitude,
            "road_en": placement.get("road") or detector.get("leg") or "Tuen Mun Road",
            "direction": detector.get("direction") or "",
            "edge_id": detector.get("edge_id") or "",
            "position_m": detector.get("position_m"),
        })
        for observation in detector["observations"]:
            if not isinstance(observation, dict):
                raise ValueError(f"{detector_id} observation must be an object")
            stamp = _hkt(observation.get("time"))
            bin_start = stamp.isoformat()
            key = (detector_id, bin_start)
            if key in seen_bins:
                raise ValueError(f"duplicate observation for {detector_id} at {bin_start}")
            seen_bins.add(key)
            speed = _number(observation.get("speed_kmh"), "speed_kmh", allow_null=True)
            count = _number(observation.get("count"), "count", allow_null=True)
            coverage = _number(observation.get("coverage_pct"), "coverage_pct", allow_null=True)
            if ((speed is not None and speed < 0) or (count is not None and count < 0)
                    or (coverage is not None and not 0 <= coverage <= 100)):
                raise ValueError(f"invalid detector reading for {detector_id} at {bin_start}")
            state = ("speed" if speed is not None else
                     "no_vehicles" if count == 0 and coverage is not None and coverage > 0
                     else "unknown")
            bin_rows.append({
                "bin_start": bin_start,
                "bin_time": stamp,
                "detector_id": detector_id,
                "speed_kmh": speed,
                "volume_observed": count,
                "coverage_pct": coverage,
                "bin_minutes": width,
                "state": state,
            })

    detectors = pd.DataFrame.from_records(detector_rows)
    bins = pd.DataFrame.from_records(bin_rows)
    if not bins.empty:
        bins = bins.sort_values(["bin_time", "detector_id"], kind="stable").reset_index(drop=True)
    return detectors, bins
