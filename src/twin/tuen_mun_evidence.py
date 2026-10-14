"""Export source-bound Tuen Mun detector bins without fitting a simulation.

This diagnostic keeps the incident and ordinary-day series separate. A change
on an alternate road is not automatically a diversion estimate.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

from src.loaders import archive, detectors
from src.loaders.common import HK

STN_TIMES = ("20260415-1809", "20260415-1820", "20260415-1857", "20260415-2029")
CORRIDOR_IDS = tuple(f"TDS900{n:02d}" for n in range(24, 46))
ALTERNATE_IDS = ("AID03115", "AID03116", "AID03201")
WINDOWS = {"before": ("17:00", "17:55"),
           "reported_closure": ("18:00", "18:45"),
           "recovery": ("19:00", "19:30")}


def mean(values):
    return round(sum(values) / len(values), 1) if values else None


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--day", required=True, help="YYYY-MM-DD")
    p.add_argument("--locations", type=Path, required=True,
                   help="Original TD traffic_speed_volume_occ_info.csv")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--end", default="21:00", help="end of observation window")
    args = p.parse_args()
    start = datetime.fromisoformat(f"{args.day}T16:30").replace(tzinfo=HK)
    end = datetime.fromisoformat(f"{args.day}T{args.end}").replace(tzinfo=HK)
    ids = CORRIDOR_IDS + ALTERNATE_IDS
    with args.locations.open(encoding="utf-8-sig", newline="") as f:
        locations = {row["AID_ID_Number"]: row for row in csv.DictReader(f)
                     if row["AID_ID_Number"] in ids}
    missing = set(ids) - locations.keys()
    if missing:
        raise ValueError(f"detector locations missing: {sorted(missing)}")

    rows = detectors.load_window(start, end, list(ids))
    bins = detectors.bin_window(rows, 5, start=start, end=end, detector_ids=list(ids))
    summaries = {}
    for detector_id in ids:
        summaries[detector_id] = {}
        for label, (begin, finish) in WINDOWS.items():
            selected = [b for b in bins if b["detector_id"] == detector_id
                        and begin <= b["bin_start"][11:16] < finish
                        and b["coverage_pct"] >= detectors.MIN_COVERAGE_PCT
                        and b["lane_completeness_pct"] >= detectors.MIN_LANE_COMPLETENESS_PCT]
            summaries[detector_id][label] = {
                "eligible_bins": len(selected),
                "mean_flow_veh_h": mean([b["flow_veh_h"] for b in selected
                                         if b["flow_veh_h"] != ""]),
                "mean_speed_kmh": mean([b["speed_kmh"] for b in selected
                                         if b["speed_kmh"] != ""]),
            }

    stamps = detectors.window_timestamps(start, end)
    source_hashes = {}
    for stamp in stamps:
        body = archive.read_cached("detectors", stamp)
        if body is not None:
            source_hashes[stamp] = hashlib.sha256(body).hexdigest()
    messages = []
    if args.day == "2026-04-15":
        from src.loaders.incidents import parse_snapshot
        for stamp in STN_TIMES:
            body = archive.read_cached("stn", stamp)
            if body is None:
                raise FileNotFoundError(f"cache original STN snapshot {stamp} first")
            for record in parse_snapshot(body):
                if record["INCIDENT_NUMBER"] == "IN-26-02615":
                    messages.append({"archive_time": stamp,
                                     "source_sha256": hashlib.sha256(body).hexdigest(),
                                     "message": record})
    result = {
        "purpose": "Observed-data diagnostic; no SUMO network, route share or benefit inferred",
        "observation_window": [start.isoformat(), end.isoformat()],
        "selection": {"corridor_detector_ids": CORRIDOR_IDS,
                      "alternate_probe_ids": ALTERNATE_IDS,
                      "min_coverage_pct": detectors.MIN_COVERAGE_PCT,
                      "min_lane_completeness_pct": detectors.MIN_LANE_COMPLETENESS_PCT},
        "source": {"locations_path": str(args.locations),
                   "locations_sha256": hashlib.sha256(args.locations.read_bytes()).hexdigest(),
                   "detector_snapshot_sha256": source_hashes,
                   "detector_versions_listed": len(stamps),
                   "detector_versions_served": len(source_hashes)},
        "locations": locations, "stn_messages": messages,
        "lane_names_by_detector": {detector_id: sorted({r["lane"] for r in rows
                                                        if r["detector_id"] == detector_id})
                                   for detector_id in ids},
        "summaries": summaries, "bins": bins,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"{len(rows)} lane readings; {len(source_hashes)}/{len(stamps)} snapshots; -> {args.out}")


if __name__ == "__main__":
    main()
