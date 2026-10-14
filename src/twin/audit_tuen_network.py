"""List direction and lane-consistent SUMO edges near Tuen Mun detectors.

Candidate edges are not approved detector placements or an incident location.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import sumolib


def angle_gap(a, b):
    return abs((a - b + 180) % 360 - 180)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--network", type=Path, required=True)
    p.add_argument("--observed", type=Path, required=True)
    p.add_argument("--osm", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    net = sumolib.net.readNet(str(args.network))
    obs = json.loads(args.observed.read_text(encoding="utf-8"))
    mapped = {}
    for n in range(28, 37):
        detector_id = f"TDS900{n:02d}"
        loc = obs["locations"][detector_id]
        x, y = net.convertLonLat2XY(float(loc["Longitude"]), float(loc["Latitude"]))
        bearing = float(loc["Rotation"])
        expected_lanes = len(obs["lane_names_by_detector"][detector_id])
        candidates = []
        for edge, distance in net.getNeighboringEdges(x, y, 55):
            if "tuen mun road" not in edge.getName().lower():
                continue
            shape = edge.getShape()
            head, tail = shape[0], shape[-1]
            edge_bearing = (math.degrees(math.atan2(tail[0]-head[0], tail[1]-head[1])) + 360) % 360
            difference = angle_gap(bearing, edge_bearing)
            if difference > 40:
                continue
            candidates.append({"edge_id": edge.getID(), "distance_m": round(distance, 1),
                               "bearing_deg": round(edge_bearing), "bearing_gap_deg": round(difference),
                               "lanes": len(edge.getLanes()), "length_m": round(edge.getLength(), 1),
                               "lane_count_matches_feed": len(edge.getLanes()) == expected_lanes})
        candidates.sort(key=lambda row: (not row["lane_count_matches_feed"],
                                         row["distance_m"], row["bearing_gap_deg"]))
        mapped[detector_id] = {"source_bearing_deg": bearing,
                               "source_lane_names": obs["lane_names_by_detector"][detector_id],
                               "candidate_edges": candidates[:8]}
    result = {
        "purpose": "candidate detector edges only; physical incident location and closure lane remain unapproved",
        "inputs_sha256": {"network": hashlib.sha256(args.network.read_bytes()).hexdigest(),
                          "observed": hashlib.sha256(args.observed.read_bytes()).hexdigest(),
                          "osm": hashlib.sha256(args.osm.read_bytes()).hexdigest()},
        "detectors": mapped,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for detector_id, row in mapped.items():
        print(detector_id, row["candidate_edges"][:2])
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
