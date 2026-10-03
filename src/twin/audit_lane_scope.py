"""Summarize TD lane labels from explicitly selected cached archive snapshots."""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from src.loaders import archive, detectors
from src.twin.common import ROOT, resolve
from src.twin.network_sources import sha256


DEFAULT_DETECTORS = (
    "AID01105,AID01220,TDSSPWR20002,AID01221,AID01222,TDSAPR10001"
)


def build_report(cache, timestamps, detector_ids):
    """Read only the named cache entries; never fetch or infer missing records."""
    observations = defaultdict(lambda: defaultdict(lambda: {"lanes": set(), "sources": set()}))
    sources = []
    for stamp in timestamps:
        path = cache / f"{stamp}.xml.gz"
        body = archive.read_cached("detectors", stamp)
        if body is None:
            marker = archive.missing_marker("detectors", stamp)
            sources.append({
                "archive_timestamp": stamp,
                "status": "archive_404" if marker.exists() else "not_cached",
            })
            continue
        source_path = path if path.exists() else cache / f"{stamp}.xml"
        sources.append({"archive_timestamp": stamp, "status": "read",
                        "path": source_path.relative_to(ROOT).as_posix()
                        if source_path.is_relative_to(ROOT) else source_path.as_posix(),
                        "sha256": sha256(source_path)})
        for row in detectors.parse_snapshot(body, keep=set(detector_ids)):
            if not row["lane"]:
                continue
            period = row["timestamp"].isoformat()
            observations[row["detector_id"]][period]["lanes"].add(row["lane"])
            observations[row["detector_id"]][period]["sources"].add(stamp)

    detector_report = {}
    for detector_id in detector_ids:
        periods = []
        for timestamp, record in sorted(observations[detector_id].items()):
            lanes = sorted(record["lanes"])
            periods.append({"timestamp": timestamp, "lanes": lanes,
                            "lane_count": len(lanes),
                            "archive_timestamps": sorted(record["sources"])})
        counts = sorted({row["lane_count"] for row in periods})
        lane_sets = sorted({tuple(row["lanes"]) for row in periods})
        detector_report[detector_id] = {
            "observed_periods": len(periods),
            "lane_counts": counts,
            "stable_lane_count_in_sample": counts[0] if len(counts) == 1 else None,
            "lane_sets": [list(lanes) for lanes in lane_sets],
            "periods": periods,
        }
    return {
        "source": "DATA.GOV.HK historical archive, TD raw detector feed",
        "purpose": "Cross-check lane labels on a separate day; not incident-window calibration.",
        "selection_rule": "Only the explicitly listed archive timestamps are read; cached XML internal timestamps are reported.",
        "archive_timestamps": timestamps,
        "snapshots": sources,
        "detectors": detector_report,
        "limitations": [
            "This sample does not fill missing May 15 incident-window observations.",
            "A repeated feed lane count does not prove that a SUMO edge is mapped to the right physical carriageway.",
            "No detector mapping, OSM tag, geometry, lane count, or traffic observation is changed.",
        ],
    }


def write_markdown(report, path):
    lines = ["# TD lane-scope cross-check", "",
             f"Source: {report['source']}.", report["purpose"], "",
             "Only the listed archive snapshots are used. Timestamps below come from the XML periods, not filenames.", "",
             "| Detector | Observed periods | Lane counts | Lane sets |", "|---|---:|---|---|"]
    for detector_id, row in report["detectors"].items():
        counts = ", ".join(map(str, row["lane_counts"])) or "no observations"
        sets = "; ".join(" / ".join(lanes) for lanes in row["lane_sets"]) or "no lane labels observed"
        lines.append(f"| {detector_id} | {row['observed_periods']} | {counts} | {sets} |")
    lines += ["", "## Source snapshots", "",
              "| Archive timestamp | Status | SHA-256 |", "|---|---|---|"]
    for row in report["snapshots"]:
        lines.append(f"| {row['archive_timestamp']} | {row['status']} | {row.get('sha256', '—')} |")
    lines += ["", "## Limits", ""]
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamps", required=True,
                        help="comma-separated DATA.GOV.HK archive timestamps, YYYYMMDD-HHmm")
    parser.add_argument("--detectors", default=DEFAULT_DETECTORS,
                        help="comma-separated detector IDs")
    parser.add_argument("--cache", default="data/raw/detectors")
    parser.add_argument("--out", default="results/twin/may14-lane-scope-crosscheck.json")
    parser.add_argument("--fetch", action="store_true",
                        help="fetch only the named archive timestamps through component A's cache client")
    args = parser.parse_args()
    timestamps = [value.strip() for value in args.timestamps.split(",") if value.strip()]
    if not timestamps or any(not re.fullmatch(r"\d{8}-\d{4}", stamp) for stamp in timestamps):
        parser.error("--timestamps must contain one or more YYYYMMDD-HHmm values")
    if len(set(timestamps)) != len(timestamps):
        parser.error("--timestamps must not repeat values")
    detector_ids = [value.strip() for value in args.detectors.split(",") if value.strip()]
    if not detector_ids or len(set(detector_ids)) != len(detector_ids):
        parser.error("--detectors must contain unique detector IDs")
    if args.fetch:
        archive.prefetch("detectors", timestamps)
    report = build_report(resolve(args.cache), timestamps, detector_ids)
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(report, out.with_suffix(".md"))
    print(f"Read {sum(row['status'] == 'read' for row in report['snapshots'])} of "
          f"{len(timestamps)} selected snapshots; wrote {out}")


if __name__ == "__main__":
    main()
