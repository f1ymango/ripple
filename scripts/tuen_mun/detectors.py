"""Tuen Mun twin, step 2: TD's westbound Tuen Mun Road detectors as loops in the network, and their readings.

    python scripts/tuen_mun/detectors.py
    -> sim/tuen-mun/detectors.add.xml            one loop per lane at each detector
       sim/tuen-mun/detectors-placement.json     edge, position and distance from TD's coordinates
       sim/tuen-mun/observations_20260415.json   15 Apr 17:00-20:30, the replay's validation data
       sim/tuen-mun/observations_<day>.json      the same clock window on the three ordinary Wednesdays

Positions are TD's (data/tuen-mun/td-detector-locations.csv, the
traffic_speed_volume_occ_info.csv of docs/02-data.md). Each detector goes on the
nearest Tuen Mun Road edge heading towards Tuen Mun, on every lane. Readings use
the corridor's rules (src/loaders/twin_export.py): a count only where the
archive kept at least 40% of the bin and 90% of lane readings are valid, and
none where the bin's speed is under 30 km/h; speed wherever a vehicle was
measured.

Some detectors' counts do not agree with their neighbours on ordinary days
although no road joins or leaves between them (scripts/tuen_mun/README.md has
the table). Their counts are withheld from the observations, with the reason;
their speeds stay.
"""
import csv
import datetime as dt
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.loaders import detectors, twin_export   # noqa: E402

NET = ROOT / "sim/tuen-mun/network.net.xml"
LOCATIONS = ROOT / "data/tuen-mun/td-detector-locations.csv"
OUT = ROOT / "sim/tuen-mun"
WESTBOUND = [f"TDS900{n}" for n in range(17, 44)]       # Yau Kom Tau to Harrow International School
INCIDENT_DAY, ORDINARY_DAYS = "2026-04-15", ["2026-04-22", "2026-04-29", "2026-05-06"]
WINDOW = ("17:00", "20:30")
SLOW_KMH = 30
# Counts withheld: on all three ordinary Wednesdays, 16:00-20:30, these read 10-45% below (or, TDS90018,
# 30-40% above) the detectors either side with no junction between (scripts/tuen_mun/README.md).
COUNT_WITHHELD = {
    "TDS90018": "reads 35-50% above TDS90017/19 on ordinary days; its speeds read 160-190 km/h",
    "TDS90021": "reads 10-12% above TDS90019/20 on ordinary days with no junction between",
    "TDS90022": "reads 40-45% below TDS90024 on ordinary days; covers only some lanes of the merge",
    "TDS90023": "reads 15-20% below TDS90024 on ordinary days; on the five-lane merge",
    "TDS90026": "too few archived readings on 15 Apr",
    "TDS90027": "reads 25-30% below TDS90029 on ordinary days",
    "TDS90028": "reads 18-20% below TDS90029 on ordinary days",
    "TDS90030": "reads 12% below TDS90029/31 on ordinary days",
    "TDS90032": "too few archived readings on ordinary days",
    "TDS90034": "reads 17-20% below TDS90033 on ordinary days",
    "TDS90035": "reads 15-20% below TDS90033 on ordinary days",
    "TDS90036": "reads 9-13% below TDS90033 on ordinary days; buses leave for the bus-bus interchange nearby",
    "TDS90037": "reads 9-13% below TDS90033 on ordinary days; buses leave for the bus-bus interchange nearby",
    "TDS90038": "almost no archived readings",
}


def locations():
    with open(LOCATIONS, encoding="utf-8-sig") as f:
        return {r["AID_ID_Number"]: r for r in csv.DictReader(f)}


def heading_at(shape, x, y):
    best = None
    for (x0, y0), (x1, y1) in zip(shape, shape[1:]):
        dx, dy = x1 - x0, y1 - y0
        length2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / length2))
        d = math.hypot(x0 + t * dx - x, y0 + t * dy - y)
        if best is None or d < best[0]:
            best = (d, (math.degrees(math.atan2(dx, dy)) + 360) % 360)
    return best


def place(net, row):
    """The westbound Tuen Mun Road edge nearest TD's coordinates, and the position along it."""
    x, y = net.convertLonLat2XY(float(row["Longitude"]), float(row["Latitude"]))
    candidates = []
    for edge, _ in net.getNeighboringEdges(x, y, 40):
        if "Tuen Mun Road" not in (edge.getName() or ""):
            continue
        distance, heading = heading_at(edge.getShape(), x, y)
        if 150 <= heading <= 350:                          # towards Tuen Mun: south-west to north-west
            candidates.append((distance, edge))
    if not candidates:
        return None
    distance, edge = min(candidates, key=lambda c: c[0])
    lane = edge.getLane(0)
    position = min(max(sumolib_position(lane, x, y), 1.0), lane.getLength() - 1.0)
    return {"edge_id": edge.getID(), "position_m": round(position, 2), "lanes": edge.getLaneNumber(),
            "metres_from_td_coordinates": round(distance, 1)}


def sumolib_position(lane, x, y):
    import sumolib
    return sumolib.geomhelper.polygonOffsetWithMinimumDistanceToPoint((x, y), lane.getShape())


def observations(day, ids, placement):
    hk = dt.timezone(dt.timedelta(hours=8))
    start = dt.datetime.fromisoformat(f"{day}T{WINDOW[0]}").replace(tzinfo=hk)
    end = dt.datetime.fromisoformat(f"{day}T{WINDOW[1]}").replace(tzinfo=hk)
    rows = detectors.load_window(start, end, ids, log=lambda *a: None)
    where = locations()
    twin_export._positions = lambda: {d: {"longitude": where[d]["Longitude"], "latitude": where[d]["Latitude"],
                                          "direction": where[d]["Direction"], "leg": "Tuen Mun Road westbound"}
                                      for d in ids}
    doc = twin_export.build(start, end, detector_ids=ids, rows=rows, min_count_speed_kmh=SLOW_KMH)
    withheld = 0
    for d in doc["detectors"]:
        d["edge_id"], d["position_m"] = placement[d["id"]]["edge_id"], placement[d["id"]]["position_m"]
        if d["id"] in COUNT_WITHHELD:
            d["count_withheld"] = COUNT_WITHHELD[d["id"]]
            for obs in d["observations"]:
                withheld += obs["count"] is not None
                obs["count"] = None
    doc["source"]["generated_by"] = "python scripts/tuen_mun/detectors.py"
    doc["source"]["count_rule"] += "; counts withheld at detectors that disagree with their neighbours on ordinary days " \
                                   "(each detector's count_withheld says why)"
    doc["source"]["counts_withheld_as_inconsistent"] = withheld
    return doc


def main():
    import argparse
    import sumolib
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--network", default=str(NET.relative_to(ROOT)))
    parser.add_argument("--suffix", default="", help="a network variant's loops: detectors<suffix>.add.xml, no new observations")
    args = parser.parse_args()
    net = sumolib.net.readNet(str(ROOT / args.network))
    where = locations()
    placement = {}
    for detector_id in WESTBOUND:
        p = place(net, where[detector_id])
        if p:
            placement[detector_id] = {"road": where[detector_id]["Road_EN"].strip(), **p}
    lines = ["<?xml version='1.0' encoding='utf-8'?>",
             "<!-- TD's westbound Tuen Mun Road detectors, one loop per lane: scripts/tuen_mun/detectors.py -->",
             "<additional>"]
    for detector_id, p in placement.items():
        for lane in range(p["lanes"]):
            lines.append(f'  <inductionLoop id="{detector_id}_{lane}" lane="{p["edge_id"]}_{lane}" '
                         f'pos="{p["position_m"]:.2f}" freq="300" file="results/e1_{detector_id}_{lane}.xml" />')
    lines.append("</additional>")
    (OUT / f"detectors{args.suffix}.add.xml").write_text("\n".join(lines) + "\n")
    (OUT / f"detectors-placement{args.suffix}.json").write_text(json.dumps(placement, indent=1) + "\n")
    if args.suffix:
        return
    ids = list(placement)
    for day in [INCIDENT_DAY] + ORDINARY_DAYS:
        doc = observations(day, ids, placement)
        (OUT / f"observations_{day.replace('-', '')}.json").write_text(json.dumps(doc, indent=1) + "\n")
        print(day, twin_export.summary(doc), file=sys.stderr)
    print(f"{len(placement)} detectors placed; furthest from TD's coordinates "
          f"{max(p['metres_from_td_coordinates'] for p in placement.values())} m", file=sys.stderr)


if __name__ == "__main__":
    main()
