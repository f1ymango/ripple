"""Local source evidence for OSM detector mapping; never downloads data."""
import gzip
import hashlib
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta

from src.loaders.detectors import ARCHIVE_LAG_MIN, parse_snapshot
from src.twin.common import load_json, resolve


def cached_osm_path(cfg):
    output = resolve(cfg.get("osm_output", "sim/work/osm/aberdeen.osm.xml"))
    return output.with_name(output.name.removesuffix(".osm.xml") + "_bbox.osm.xml")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def apply_mapping_overrides(data, path, network, registry, lane_evidence=None):
    """Apply explicit reviewed placements only to their exact source versions."""
    overrides = load_json(path)
    for label, source in (("network", network), ("registry", registry)):
        if overrides[f"{label}_sha256"] != sha256(source):
            raise ValueError(f"Detector override {label} hash differs; review placements against the new source")
    window = data.get('source', {}).get('window')
    if overrides.get('window') != window:
        raise ValueError("Detector override replay window differs; review placements for the current hand-over")
    replacements = overrides["detectors"]
    unknown = set(replacements) - {d['id'] for d in data['detectors']}
    if unknown:
        raise ValueError(f"Overrides refer to detectors absent from the hand-over: {sorted(unknown)}")
    for detector_id, replacement in replacements.items():
        expected_lanes = replacement.get('evidence', {}).get('td_lanes')
        measured = (lane_evidence or {}).get(detector_id)
        if not expected_lanes or not measured or measured.get('lane_count') is None:
            raise ValueError(f"Detector override {detector_id} needs verified cached TD lane evidence")
        if sorted(expected_lanes) != measured.get('lane_sets', [None])[0] or len(expected_lanes) != measured['lane_count']:
            raise ValueError(f"Detector override {detector_id} lane evidence differs; re-review the placement")
    return {**data, "detectors": [
        {**d, **{key: replacements[d['id']][key] for key in ('edge_id', 'position_m')}}
        if d['id'] in replacements else dict(d) for d in data['detectors']]}


def verify_lane_evidence(evidence, window, detector_data, registry):
    """Require an audit built from the same hand-over and exact cached sources."""
    lane = evidence['lane_evidence']
    if lane['window'] != window:
        raise ValueError("Lane evidence and detector observations must cover the same source window")
    for label, source in (("registry", registry), ("observations", detector_data)):
        audited = evidence.get('sources', {}).get(label, {})
        if not audited.get('sha256') or audited['sha256'] != sha256(source):
            raise ValueError(f"Lane evidence {label} hash differs; regenerate the audit from current inputs")
    for snapshot in lane['sources']:
        source = resolve(snapshot['path'])
        if not source.exists() or sha256(source) != snapshot['sha256']:
            raise ValueError("A cached raw snapshot used by lane evidence is missing or has changed")
    return lane['detectors']


def read_osm_ways(path):
    """Preserve OSM's alternative street/bridge names as source evidence."""
    ways = {}
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "way":
            tags = {tag.get("k"): tag.get("v") for tag in element.findall("tag")}
            ways[element.get("id")] = tags
            element.clear()
        elif element.tag in {"node", "relation"}:
            element.clear()
    return ways


def edge_names(edge, ways):
    # netconvert appends #N when splitting an OSM way and prefixes - for reverse.
    way_id = edge.getID().split("#", 1)[0].lstrip("-")
    tags = ways.get(way_id, {})
    names = {edge.getName()}
    for key, value in tags.items():
        if key in {"name", "name:en", "alt_name", "alt_name:en",
                   "official_name", "official_name:en", "street:name",
                   "street:name:en", "highway:name", "highway:name:en",
                   "bridge:name", "bridge:name:en"}:
            names.update(value.split(";"))
    return sorted(name.strip() for name in names if name.strip())


def cached_lane_evidence(cache, window, detector_ids):
    """Count distinct lane labels per actual feed period, preserving conflicts.

    Archive filenames are not observation times. Use the loader's timestamps
    inside each cached XML; offline/zero-volume lanes still identify the scope.
    A varying lane set yields no trusted count, rather than taking its union.
    """
    start, end = (datetime.fromisoformat(value) for value in window)
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise ValueError("Lane audit needs an increasing timezone-aware source window")
    variants = defaultdict(set)
    periods_seen = defaultdict(set)
    sources, skipped = [], []
    # Same padded archive window as the data loader; internal timestamps still
    # determine inclusion. No archive index or other network request is made.
    lower = (start - timedelta(minutes=ARCHIVE_LAG_MIN)).strftime('%Y%m%d-%H%M')
    upper = (end + timedelta(minutes=ARCHIVE_LAG_MIN)).strftime('%Y%m%d-%H%M')
    for path in sorted(cache.glob("*.xml.gz")):
        if not lower <= path.name.removesuffix('.xml.gz') <= upper:
            continue
        try:
            with gzip.open(path, "rb") as stream:
                readings = parse_snapshot(stream.read(), keep=set(detector_ids))
        except (ET.ParseError, OSError, EOFError) as exc:
            skipped.append({"path": path.as_posix(), "error": str(exc)})
            continue
        periods = defaultdict(set)
        for row in readings:
            if start <= row["timestamp"] < end and row["lane"]:
                periods[(row["detector_id"], row["timestamp"].isoformat())].add(row["lane"])
        if periods:
            sources.append({"path": path.as_posix(), "sha256": sha256(path)})
        for (detector_id, timestamp), lanes in periods.items():
            variants[detector_id].add(tuple(sorted(lanes)))
            periods_seen[detector_id].add(timestamp)
    evidence = {}
    for detector_id in sorted(detector_ids):
        lane_sets = sorted(variants[detector_id])
        evidence[detector_id] = {
            "lane_sets": [list(lanes) for lanes in lane_sets],
            "lane_count": len(lane_sets[0]) if len(lane_sets) == 1 else None,
            "observed_periods": len(periods_seen[detector_id]),
        }
    return {"window": list(window), "sources": sources, "skipped": skipped, "detectors": evidence}
