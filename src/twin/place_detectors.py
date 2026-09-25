import argparse
import csv
import math
import os
from pathlib import Path

import sumolib
from src.twin.common import load_json, resolve


def main():
    ap = argparse.ArgumentParser(description="Map WGS84 detectors to nearest SUMO edges and write E1 loops.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--detectors", required=True)
    args = ap.parse_args()
    cfg, data = load_json(resolve(args.config)), load_json(resolve(args.detectors))
    net_path = resolve(cfg["network"])
    net = sumolib.net.readNet(str(net_path))
    xml_path = resolve(cfg.get("detector_additional", "sim/detectors.add.xml"))
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    results_dir = resolve(cfg.get("output_dir", "sim/work/results"))
    rows = []
    with open(xml_path, "w", encoding="utf-8") as out:
        out.write('<additional>\n')
        for d in data["detectors"]:
            if d.get("edge_id"):
                edge = net.getEdge(d["edge_id"])
                pos = float(d["position_m"])
                distance = 0.0
            else:
                x, y = net.convertLonLat2XY(float(d["lon"]), float(d["lat"]))
                edges = net.getNeighboringEdges(x, y, r=100)
                if not edges:
                    raise ValueError(f"No network edge within 100 m of detector {d['id']}; check bbox/network.")
                direction = d.get("direction", "")
                words = set(direction.casefold().split())
                expected_x = float("east" in words) - float("west" in words)
                expected_y = float("north" in words) - float("south" in words)
                magnitude = math.hypot(expected_x, expected_y)
                directed = []
                if magnitude:
                    expected_x, expected_y = expected_x / magnitude, expected_y / magnitude
                    for candidate, distance in edges:
                        shape = candidate.getShape()
                        dx, dy = shape[-1][0] - shape[0][0], shape[-1][1] - shape[0][1]
                        length = math.hypot(dx, dy)
                        alignment = ((dx * expected_x + dy * expected_y) / length
                                     if length else -1)
                        if alignment > 0.3:
                            directed.append((candidate, distance, alignment))
                if magnitude and not directed:
                    raise ValueError(f"No directed edge within 100 m of detector {d['id']} "
                                     f"matches its {direction!r} direction.")
                if directed:
                    edge, distance, _ = min(directed, key=lambda row: (row[1], -row[2]))
                else:
                    edge, distance = min(edges, key=lambda pair: pair[1])
                # Projection to the nearest point along edge shape.
                pos, _ = edge.getLane(0).getClosestLanePosAndDist((x, y))
            pos = max(0.1, min(float(pos), edge.getLength() - 0.1))
            did = str(d["id"]).replace('"', "")
            for lane in edge.getLanes():
                loop_id = f"{did}_{lane.getIndex()}"
                output = results_dir / f"e1_{did}_{lane.getIndex()}.xml"
                out.write(f'  <inductionLoop id="{loop_id}" lane="{lane.getID()}" pos="{pos:.2f}" freq="{int(data.get("interval_seconds",300))}" file="{Path(os.path.relpath(output, xml_path.parent)).as_posix()}"/>\n')
                rows.append([did, loop_id, edge.getID(), lane.getID(), f"{pos:.2f}", f"{distance:.2f}"])
        out.write('</additional>\n')
    with open(xml_path.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["detector_id", "loop_id", "edge_id", "lane_id", "position_m", "distance_from_coordinate_m"]); w.writerows(rows)
    print(f"Proposal written: {xml_path}\nMapping table: {xml_path.with_suffix('.csv')}\nReview every location and lane direction before trusting it.")


if __name__ == "__main__":
    main()
