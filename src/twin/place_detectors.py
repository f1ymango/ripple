import argparse
import csv
import math
import os
import re
from pathlib import Path

import sumolib
from src.loaders.corridor import CHAIN_EASTBOUND, CHAIN_WESTBOUND
from src.twin.common import load_json, resolve


def _sequence_vector(detector_id, detector_metadata, net):
    """Return travel direction from the registry's ordered detector chains.

    Compass metadata is rounded and can point across a flyover interchange.
    For the main corridor and the ordered Pok Fu Lam subchains, the adjacent
    detector coordinates provide a better local travel tangent.
    """
    sequences = [CHAIN_EASTBOUND, CHAIN_WESTBOUND,
                 ["TDSSPWR10001", "TDSSPWR10002", "TDSSPWR10003"],
                 ["TDSSPWR20003", "TDSSPWR20002", "TDSSPWR20001"]]
    for sequence in sequences:
        if detector_id not in sequence:
            continue
        index = sequence.index(detector_id)
        try:
            coordinates = {}
            for adjacent in sequence[max(0, index - 1):min(len(sequence), index + 2)]:
                row = detector_metadata[adjacent]
                coordinates[adjacent] = net.convertLonLat2XY(
                    float(row["longitude"]), float(row["latitude"]))
        except (KeyError, TypeError, ValueError):
            return None
        vectors = []
        if index > 0:
            ax, ay = coordinates[sequence[index - 1]]
            bx, by = coordinates[detector_id]
            vectors.append((bx - ax, by - ay))
        if index < len(sequence) - 1:
            ax, ay = coordinates[detector_id]
            bx, by = coordinates[sequence[index + 1]]
            vectors.append((bx - ax, by - ay))
        unit_vectors = []
        for dx, dy in vectors:
            length = math.hypot(dx, dy)
            if length:
                unit_vectors.append((dx / length, dy / length))
        dx = sum(v[0] for v in unit_vectors)
        dy = sum(v[1] for v in unit_vectors)
        length = math.hypot(dx, dy)
        return (dx / length, dy / length) if length else None
    return None


def _road_name_score(expected_name, candidate_name):
    """Score a candidate edge name against the detector's registry road name."""
    expected = " ".join(re.findall(r"[a-z0-9]+", expected_name.casefold()))
    actual = " ".join(re.findall(r"[a-z0-9]+", candidate_name.casefold()))
    if not expected or expected not in actual:
        return 0
    return 2 if actual.endswith(expected) else 1


def main():
    ap = argparse.ArgumentParser(description="Map WGS84 detectors to nearest SUMO edges and write E1 loops.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--detectors", required=True)
    ap.add_argument("--direction-alignment", type=float, default=0.7,
                    help="Minimum cosine similarity between road bearing and detector direction (default: 0.7).")
    args = ap.parse_args()
    cfg, data = load_json(resolve(args.config)), load_json(resolve(args.detectors))
    net_path = resolve(cfg["network"])
    net = sumolib.net.readNet(str(net_path))
    registry = resolve("data/detectors.csv")
    detector_metadata = {}
    if registry.exists():
        with registry.open(encoding="utf-8-sig", newline="") as source:
            detector_metadata = {row["detector_id"]: row for row in csv.DictReader(source)}
    xml_path = resolve(cfg.get("detector_additional", "sim/detectors.add.xml"))
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    results_dir = resolve(cfg.get("output_dir", "sim/work/results"))
    rows = []
    temporary_xml = xml_path.with_suffix(xml_path.suffix + ".tmp")
    with open(temporary_xml, "w", encoding="utf-8") as out:
        out.write('<additional>\n')
        for d in data["detectors"]:
            if d.get("edge_id"):
                edge = net.getEdge(d["edge_id"])
                if d.get("position_m") is None:
                    raise ValueError(f"Detector {d['id']} has edge_id but no position_m; set both after map review.")
                pos = float(d["position_m"])
                if not 0 <= pos <= edge.getLength():
                    raise ValueError(f"Detector {d['id']} position {pos} m is outside edge {edge.getID()} "
                                     f"(length {edge.getLength():.2f} m).")
                if d.get("lon") is not None and d.get("lat") is not None:
                    x, y = net.convertLonLat2XY(float(d["lon"]), float(d["lat"]))
                    projected_pos, distance = edge.getLane(0).getClosestLanePosAndDist((x, y))
                    position_delta = abs(projected_pos - pos)
                else:
                    distance, position_delta = float("nan"), float("nan")
            else:
                x, y = net.convertLonLat2XY(float(d["lon"]), float(d["lat"]))
                edges = net.getNeighboringEdges(x, y, r=100)
                if not edges:
                    raise ValueError(f"No network edge within 100 m of detector {d['id']}; check bbox/network.")
                direction = d.get("direction") or detector_metadata.get(d["id"], {}).get("direction", "")
                expected = _sequence_vector(d["id"], detector_metadata, net)
                if expected is None:
                    words = set(direction.casefold().split())
                    expected_x = float("east" in words) - float("west" in words)
                    expected_y = float("north" in words) - float("south" in words)
                    magnitude = math.hypot(expected_x, expected_y)
                    expected = (expected_x / magnitude, expected_y / magnitude) if magnitude else None
                directed = []
                if expected is not None:
                    expected_x, expected_y = expected
                    for candidate, distance in edges:
                        shape = candidate.getShape()
                        dx, dy = shape[-1][0] - shape[0][0], shape[-1][1] - shape[0][1]
                        length = math.hypot(dx, dy)
                        alignment = ((dx * expected_x + dy * expected_y) / length
                                     if length else -1)
                        if alignment >= args.direction_alignment:
                            directed.append((candidate, distance, alignment))
                if expected is not None and not directed:
                    raise ValueError(f"No directed edge within 100 m of detector {d['id']} "
                                     f"matches its corridor travel direction (registry: {direction!r}) "
                                     f"at cosine threshold "
                                     f"{args.direction_alignment}; set edge_id/position_m only after map review.")
                if directed:
                    road_en = detector_metadata.get(d["id"], {}).get("road_en", "")
                    expected_name = re.split(r"\s+near\s+", road_en, maxsplit=1, flags=re.IGNORECASE)[0]
                    expected_name = re.sub(r"\s+-\s+[^-]+$", "", expected_name).strip()
                    named = [(candidate, distance, alignment,
                              _road_name_score(expected_name, candidate.getName()))
                             for candidate, distance, alignment in directed]
                    named = [row for row in named if row[3] > 0]
                    if expected_name and not named:
                        nearby = sorted({candidate.getName() for candidate, _, _ in directed})
                        raise ValueError(f"No directed edge within 100 m of detector {d['id']} "
                                         f"matches registry road {expected_name!r}; nearby directed OSM names: "
                                         f"{nearby}. Review the map or set edge_id/position_m by hand.")
                    if named:
                        edge, distance, _, _ = min(named, key=lambda row: (-row[3], row[1], -row[2]))
                    else:
                        edge, distance, _ = min(directed, key=lambda row: (row[1], -row[2]))
                else:
                    edge, distance = min(edges, key=lambda pair: pair[1])
                # Projection to the nearest point along edge shape.
                pos, _ = edge.getLane(0).getClosestLanePosAndDist((x, y))
                position_delta = 0.0
            pos = max(0.1, min(float(pos), edge.getLength() - 0.1))
            did = str(d["id"]).replace('"', "")
            for lane in edge.getLanes():
                loop_id = f"{did}_{lane.getIndex()}"
                output = results_dir / f"e1_{did}_{lane.getIndex()}.xml"
                out.write(f'  <inductionLoop id="{loop_id}" lane="{lane.getID()}" pos="{pos:.2f}" freq="{int(data.get("interval_seconds",300))}" file="{Path(os.path.relpath(output, xml_path.parent)).as_posix()}"/>\n')
                rows.append([did, loop_id, edge.getID(), lane.getID(), f"{pos:.2f}",
                             f"{distance:.2f}", f"{position_delta:.2f}"])
        out.write('</additional>\n')
    temporary_xml.replace(xml_path)
    with open(xml_path.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["detector_id", "loop_id", "edge_id", "lane_id", "position_m",
                                       "distance_from_coordinate_m", "position_delta_m"]); w.writerows(rows)
    print(f"Proposal written: {xml_path}\nMapping table: {xml_path.with_suffix('.csv')}\nReview every location and lane direction before trusting it.")


if __name__ == "__main__":
    main()
