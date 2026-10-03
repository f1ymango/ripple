"""Render sampled SUMO FCD snapshots as an animated GIF for review/presentation."""
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import sumolib
from PIL import Image, ImageDraw, ImageFont

from src.twin.common import resolve


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fcd", required=True)
    ap.add_argument("--network", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--incident-edge", required=True)
    ap.add_argument("--every-seconds", type=float, default=60)
    args = ap.parse_args()
    net = sumolib.net.readNet(str(resolve(args.network)))
    shapes = [edge.getShape() for edge in net.getEdges() if edge.getShape()]
    xs = [pt[0] for shape in shapes for pt in shape]
    ys = [pt[1] for shape in shapes for pt in shape]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    width, height, pad = 1200, 760, 28
    scale = min((width - 2 * pad) / (xmax - xmin), (height - 2 * pad - 65) / (ymax - ymin))

    def xy(x, y):
        return (int(pad + (x - xmin) * scale), int(height - pad - 65 - (y - ymin) * scale))

    base = Image.new("RGB", (width, height), "#101821")
    road = ImageDraw.Draw(base)
    for shape in shapes:
        road.line([xy(x, y) for x, y in shape], fill="#43515e", width=2)
    incident = net.getEdge(args.incident_edge)
    road.line([xy(x, y) for x, y in incident.getShape()], fill="#e25858", width=5)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
        small = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = small = ImageFont.load_default()
    frames, times = [], []
    last_selected = -args.every_seconds
    try:
        for event, elem in ET.iterparse(resolve(args.fcd), events=("end",)):
            if elem.tag != "timestep":
                continue
            t = float(elem.get("time", 0))
            if t - last_selected >= args.every_seconds:
                frame = base.copy()
                draw = ImageDraw.Draw(frame)
                n = 0
                for vehicle in elem.findall("vehicle"):
                    px, py = xy(float(vehicle.get("x")), float(vehicle.get("y")))
                    v = float(vehicle.get("speed", 0))
                    color = "#70d6a6" if v > 3 else "#f4bf63"
                    draw.ellipse((px - 4, py - 4, px + 4, py + 4), fill=color)
                    n += 1
                draw.rectangle((0, height - 58, width, height), fill="#17222e")
                draw.text((pad, height - 48), f"SUMO 1.27.1  |  simulation time {t:,.0f}s  |  vehicles {n}", fill="white", font=font)
                draw.text((pad, 12), "ABERDEEN CORRIDOR • RECORDED SUMO FCD • DIAGNOSTIC EXCERPT", fill="#dce6ee", font=small)
                draw.text((width - 280, 12), "Red: incident lane edge", fill="#f28b82", font=small)
                frames.append(frame)
                times.append(t)
                last_selected = t
            elem.clear()
    except ET.ParseError:
        # A user-stopped SUMO run can leave the final XML timestep unfinished;
        # retain complete earlier FCD timesteps, never fabricate vehicle states.
        pass
    if not frames:
        raise ValueError("No complete FCD timesteps found in the input")
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # A compact overview clip: each frame keeps its actual SUMO timestamp onscreen.
    duration_ms = 250
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=duration_ms, loop=0, optimize=True)
    print(f"Rendered {len(frames)} actual FCD snapshots ({times[0]:.0f}–{times[-1]:.0f}s) to {out}")


if __name__ == "__main__":
    main()
