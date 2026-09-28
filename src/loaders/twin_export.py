"""Loader bins -> sim/scenarios/detectors.json, the twin's observed data (A -> C).

The twin (src/twin/) reads one observation per detector per 5-minute slot.
`evaluate.py` matches each observation timestamp to the corresponding SUMO
interval, offset by `observation_start_sim_seconds` when the scenario uses a
warm-up. The full slot grid keeps missing archive periods explicit and visible.

What goes in each observation:

  count      count_bin, but only where the bin is good enough for calibration
             (>= 40% archive coverage and >= 90% of lane readings valid,
             docs/02-data.md section 7); null otherwise. Never zero-filled.
  speed_kmh  the measured speed wherever a vehicle was measured; null where
             none was -- speed survives low coverage, counts do not.

Nothing is interpolated or invented (CLAUDE.md rule 4). Detector positions come
from data/detectors.csv; an edge_id / position_m already filled in by hand in
an existing output file is kept.

    python -m src.loaders.fetch twin-detectors --start 2026-05-15T08:00 --end 2026-05-15T10:30
"""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

from src.loaders import detectors
from src.loaders.corridor import DETECTOR_IDS, OUT_PATH as DETECTORS_CSV

OUT_PATH = Path("sim/scenarios/detectors.json")


def _positions() -> dict[str, dict]:
    path = DETECTORS_CSV
    if not path.exists():
        raise RuntimeError(f"{path} is missing -- run `python -m src.loaders.fetch corridor` first")
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {r["detector_id"]: r for r in csv.DictReader(f)}


def _kept_mapping(path: Path) -> dict[str, dict]:
    """edge_id / position_m already in an earlier output, by detector id."""
    if not path.exists():
        return {}
    old = json.loads(path.read_text(encoding="utf-8"))
    return {d["id"]: {"edge_id": d.get("edge_id"), "position_m": d.get("position_m")}
            for d in old.get("detectors", []) if d.get("id")}


def _number(value):
    return None if value == "" or value is None else value


def build(start: dt.datetime, end: dt.datetime, bin_minutes: int = detectors.BIN_MINUTES,
          detector_ids: list[str] | None = None,
          min_coverage_pct: int = detectors.MIN_COVERAGE_PCT,
          rows: list[dict] | None = None, keep_from: Path | None = None) -> dict:
    """The twin's observed-data document for [start, end).

    `start` and `end` must sit on slot boundaries. The first observation time
    is explicit in the export; the scenario can map it after a warm-up.
    """
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("start and end must carry a timezone (Hong Kong time, +08:00)")
    if end <= start:
        raise ValueError(f"end {end.isoformat()} is not after start {start.isoformat()}")
    for label, moment in (("start", start), ("end", end)):
        if moment.minute % bin_minutes or moment.second or moment.microsecond:
            raise ValueError(f"{label} {moment:%H:%M:%S} is not on a {bin_minutes}-minute "
                             f"boundary; observation 0 must be the simulation's time 0")
    ids = list(detector_ids) if detector_ids is not None else list(DETECTOR_IDS)
    positions = _positions()
    unknown = [d for d in ids if d not in positions]
    if unknown:
        raise RuntimeError(f"no position in {DETECTORS_CSV} for {unknown}")
    kept = _kept_mapping(keep_from) if keep_from else {}

    if rows is None:
        rows = detectors.load_window(start, end, detector_ids=ids)
    binned = detectors.bin_window(rows, bin_minutes, start=start, end=end, detector_ids=ids)
    series = detectors.calibration_series(binned, min_coverage_pct)
    slots = len(detectors.slot_starts(start, end, bin_minutes))

    out = []
    for detector_id in ids:
        mine = [b for b in series if b["detector_id"] == detector_id]
        if len(mine) != slots:        # cannot happen with a full grid; guard the contract anyway
            raise AssertionError(f"{detector_id}: {len(mine)} rows for {slots} slots")
        where = positions[detector_id]
        out.append({
            "id": detector_id,
            "lon": float(where["longitude"]),
            "lat": float(where["latitude"]),
            "direction": where.get("direction", ""),
            "leg": where.get("leg", ""),
            "edge_id": kept.get(detector_id, {}).get("edge_id"),
            "position_m": kept.get(detector_id, {}).get("position_m"),
            "observations": [{"time": b["bin_start"],
                              "count": _number(b["count_bin"]),
                              "speed_kmh": _number(b["speed_kmh"]),
                              "coverage_pct": b["coverage_pct"]} for b in mine],
        })
    return {
        "timezone": "Asia/Hong_Kong",
        "interval_seconds": bin_minutes * 60,
        "source": {
            "window": [start.isoformat(), end.isoformat()],
            "simulation_time_0": start.isoformat(),
            "count_rule": (f"count_bin where archive coverage >= {min_coverage_pct}% and "
                           f">= {detectors.MIN_LANE_COMPLETENESS_PCT}% of lane readings valid; "
                           "else null"),
            "speed_rule": "measured speed; null where no vehicle was measured",
            "generated_by": "python -m src.loaders.fetch twin-detectors",
        },
        "detectors": out,
    }


def summary(doc: dict) -> dict:
    """How much of the document is real measurement, for the run log."""
    obs = [o for d in doc["detectors"] for o in d["observations"]]
    return {"detectors": len(doc["detectors"]),
            "slots_per_detector": len(doc["detectors"][0]["observations"]) if doc["detectors"] else 0,
            "observations": len(obs),
            "with_count": sum(o["count"] is not None for o in obs),
            "with_speed": sum(o["speed_kmh"] is not None for o in obs),
            "with_both": sum(o["count"] is not None and o["speed_kmh"] is not None for o in obs)}


def write(doc: dict, path: Path = OUT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
