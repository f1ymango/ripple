"""Render the frozen Tuen Mun P2 detour from its SUMO edge geometry.

This is a presentation map of a simulated plan, not a vehicle replay or
live navigation advice. The route and network are read without modification.
"""

from __future__ import annotations

import json
import math
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import sumolib


ROOT = Path(__file__).resolve().parents[2]
NETWORK = ROOT / "sim/tuen-mun/network.net.xml"
SCENARIO = ROOT / "sim/scenarios/tuen-mun/evaluator_IN-26-02615_p0x-merge-at-site-s2029.json"
PROVENANCE = ROOT / ("results/demo-oct16/tuen-mun/runs/"
    "2026-04-15_TMR_P2_c50_t59_p0x-merge-at-site-s2029_lead-capacity-oct15.provenance.json")
OBSERVATIONS = ROOT / "sim/tuen-mun/observations_20260415.json"
OUT = ROOT / "docs/video/tuen-mun-route-frames"
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
W, H = 1920, 1080
BOX = (104, 278, 1816, 856)
BOUNDS = (0.0, 1050.0, 11250.0, 4850.0)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def xy(point: tuple[float, float]) -> tuple[float, float]:
    x0, y0, x1, y1 = BOUNDS
    a, b, c, d = BOX
    return a + (point[0] - x0) * (c - a) / (x1 - x0), d - (point[1] - y0) * (d - b) / (y1 - y0)


def shape(edge: ET.Element) -> list[tuple[float, float]]:
    raw = edge.get("shape") or edge.find("lane").get("shape")
    return [tuple(map(float, p.split(","))) for p in raw.split()]


def text_with_shadow(d: ImageDraw.ImageDraw, at: tuple[int, int], label: str,
                     color: str, size: int, *, bold: bool = False) -> None:
    f = font(size, bold)
    x, y = at
    d.text((x + 2, y + 2), label, font=f, fill="#071724")
    d.text((x, y), label, font=f, fill=color)


def main() -> None:
    provenance = json.loads(PROVENANCE.read_text())["simulation_inputs"]
    if hashlib.sha256(NETWORK.read_bytes()).hexdigest() != provenance["network"]:
        raise ValueError("Map network does not match the saved P2 run.")
    if hashlib.sha256(SCENARIO.read_bytes()).hexdigest() != provenance["scenario"]:
        raise ValueError("Map scenario does not match the saved P2 run.")
    if hashlib.sha256(OBSERVATIONS.read_bytes()).hexdigest() != provenance["observations"]:
        raise ValueError("Detector observations do not match the saved P2 run.")
    scenario = json.loads(SCENARIO.read_text())
    route = scenario["plan_actions"]["routes"]["Castle Peak Road"]
    edge_ids = route["with"]
    root = ET.parse(NETWORK).getroot()
    edges = {e.get("id"): e for e in root.findall("edge")}
    missing = [edge_id for edge_id in edge_ids if edge_id not in edges]
    if missing:
        raise ValueError(f"Route edges missing from frozen network: {missing}")

    base = Image.new("RGB", (W, H), "#071724")
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((64, 38, 1856, 1034), radius=36, fill="#0b2637", outline="#315565", width=2)
    d.text((104, 78), "Ripple.", font=font(47, True), fill="#f3f8f6")
    d.text((1408, 86), "CASE 02 / TUEN MUN", font=font(25, True), fill="#95ded0")
    d.line((104, 152, 1816, 152), fill="#466977", width=2)
    d.text((104, 184), "The tested detour follows real road curves", font=font(42, True), fill="#f3f8f6")
    d.text((104, 235), "P2 / 11% targeted advice / simulated candidate", font=font(27), fill="#8edac8")
    d.rounded_rectangle((BOX[0] - 15, BOX[1] - 18, BOX[2] + 15, BOX[3] + 18), radius=25,
                        fill="#102f40", outline="#355968", width=2)

    # The actual SUMO network supplies all road curves shown in the map panel.
    roads = Image.new("RGB", (W, H), "#102f40")
    rd = ImageDraw.Draw(roads)
    for edge in edges.values():
        if edge.get("function") == "internal" or edge.get("id", "").startswith(":"):
            continue
        pts = shape(edge)
        if len(pts) < 2 or not any(BOUNDS[0] <= x <= BOUNDS[2] and BOUNDS[1] <= y <= BOUNDS[3] for x, y in pts):
            continue
        if edge.get("type", "").startswith("highway.motorway"):
            color, width = "#557586", 5
        elif edge.get("type", "").startswith("highway.primary"):
            color, width = "#3f6674", 4
        else:
            color, width = "#2d4d5b", 2
        rd.line([xy(p) for p in pts], fill=color, width=width, joint="curve")
    base.paste(roads.crop((BOX[0], BOX[1], BOX[2], BOX[3])), (BOX[0], BOX[1]))

    # TD's real roadside readings for one explicit five-minute archive bin.
    net = sumolib.net.readNet(str(NETWORK))
    detector_file = json.loads(OBSERVATIONS.read_text())
    detectors = detector_file["detectors"]
    if len(detectors) != 27:
        raise ValueError("Expected the reviewed 27 Tuen Mun detectors.")
    for detector in detectors:
        reading = next((item for item in detector["observations"]
                        if item["time"][11:16] == "18:00"), None)
        if reading is None:
            raise ValueError(f"No 18:00 observation for {detector['id']}.")
        speed = reading["speed_kmh"]
        colour = ("#969fa9" if speed is None else
                  "#e1454c" if speed < 30 else
                  "#ef882f" if speed < 60 else "#10aab2")
        pos = xy(net.convertLonLat2XY(detector["lon"], detector["lat"]))
        d.ellipse((pos[0] - 7, pos[1] - 7, pos[0] + 7, pos[1] + 7),
                  fill=colour, outline="#f4f8f7", width=2)

    # Pin the incident to the precise scenario closure edge.
    incident = shape(edges[scenario["closure"]["edge_id"]])
    crash = xy(incident[len(incident) // 2])
    d.ellipse((crash[0] - 17, crash[1] - 17, crash[0] + 17, crash[1] + 17),
              fill="#e57a71", outline="#fff3f0", width=3)
    text_with_shadow(d, (int(crash[0]) - 95, int(crash[1]) - 58), "CRASH", "#ffd2ca", 22, bold=True)

    # Use the recorded ordered route edges; revealing more edges gives a genuine
    # path animation while every frame stays on the network geometry.
    for step in range(10):
        frame = base.copy()
        dr = ImageDraw.Draw(frame)
        count = math.ceil(len(edge_ids) * (step + 1) / 10)
        for edge_id in edge_ids[:count]:
            pts = [xy(p) for p in shape(edges[edge_id])]
            dr.line(pts, fill="#0d2730", width=17, joint="curve")
            dr.line(pts, fill="#d630c2", width=10, joint="curve")
            dr.line(pts, fill="#ffc9f8", width=3, joint="curve")
        # Road-network junctions are reference nodes, never vehicle positions.
        for idx in [0, 8, 17, 27, len(edge_ids) - 1]:
            if idx >= count:
                continue
            p = xy(shape(edges[edge_ids[idx]])[-1])
            dr.ellipse((p[0] - 10, p[1] - 10, p[0] + 10, p[1] + 10),
                       fill="#ffffff", outline="#894081", width=3)
        labels = [
            (edge_ids[0], "SHAM TSENG", -80, -52),
            (edge_ids[17], "TSING LUNG TAU", -70, 22),
            (edge_ids[27], "TAI LAM", -32, 22),
            (edge_ids[-1], "SIU LAM REJOIN", -76, -52),
        ]
        for edge_id, label, dx, dy in labels:
            if edge_ids.index(edge_id) >= count:
                continue
            p = xy(shape(edges[edge_id])[-1])
            text_with_shadow(dr, (int(p[0]) + dx, int(p[1]) + dy), label, "#ffffff", 21, bold=True)
        dr.rounded_rectangle((104, 904, 1816, 1008), radius=18, fill="#143648")
        dr.text((134, 923), "P2 detour / magenta", font=font(31, True), fill="#f37bdd")
        dr.text((585, 928), "Small dots: 27 TD sensors · large white dots: junctions",
                font=font(24), fill="#d6e7e9")
        dr.text((134, 967), "18:00 HKT observed speed: red <30 · orange 30–59 · teal ≥60 km/h · P2 simulated",
                font=font(20), fill="#91b9c2")
        OUT.mkdir(exist_ok=True)
        frame.save(OUT / f"route-{step:02d}.png")
    print(f"Rendered {len(edge_ids)} saved route edges to {OUT}")


if __name__ == "__main__":
    main()
