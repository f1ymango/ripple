"""Render paired SUMO FCD trajectories for a validated operator plan.

The image is generated only from recorded SUMO positions. Its paired result
files determine the recommendation; the renderer never supplies traffic data.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.console.recommendation import fingerprint, load_comparison, read_objects, scenarios_for

ROOT = Path(__file__).resolve().parents[2]
WIDTH, HEIGHT = 1200, 760
PANEL_WIDTH = WIDTH // 2
TOP, BOTTOM = 96, 54


def _points(shape: str) -> list[tuple[float, float]]:
    return [tuple(map(float, pair.split(","))) for pair in shape.split()]


def road_shapes(network: Path, incident_edge: str) -> tuple[list[list[tuple]], list[tuple]]:
    """Read SUMO's actual lane geometry; the incident edge must be reviewed."""
    root = ET.parse(network).getroot()
    roads, incident = [], None
    for edge in root.findall("edge"):
        if edge.get("function") == "internal":
            continue
        lane = edge.find("lane")
        if lane is None or not lane.get("shape"):
            continue
        shape = _points(lane.get("shape"))
        roads.append(shape)
        if edge.get("id") == incident_edge:
            incident = shape
    if not roads or incident is None:
        raise ValueError("Network has no road shapes or the reviewed incident edge is absent")
    return roads, incident


def fcd_frames(path: Path, every_seconds: float, start: float,
               end: float) -> dict[float, list[tuple[float, float, float]]]:
    """Read complete FCD timestamps; each dot is a SUMO vehicle observation."""
    frames: dict[float, list[tuple[float, float, float]]] = {}
    context = ET.iterparse(path, events=("start", "end"))
    _, root = next(context)
    last = start - every_seconds
    for event, elem in context:
        if event != "end" or elem.tag != "timestep":
            continue
        t = float(elem.get("time", "nan"))
        if math.isfinite(t) and start <= t <= end and t - last >= every_seconds:
            frames[t] = [(float(v.get("x")), float(v.get("y")),
                          float(v.get("speed", 0))) for v in elem.findall("vehicle")]
            last = t
        root.clear()
    return frames


def _bounds(roads: list[list[tuple]], bbox: list[float] | None) -> tuple[float, ...]:
    if bbox is not None:
        xmin, ymin, xmax, ymax = bbox
    else:
        xs = [x for shape in roads for x, _ in shape]
        ys = [y for shape in roads for _, y in shape]
        xmin, ymin, xmax, ymax = min(xs), min(ys), max(xs), max(ys)
    if not all(map(math.isfinite, (xmin, ymin, xmax, ymax))) or xmin >= xmax or ymin >= ymax:
        raise ValueError("Map bounds must be finite and have positive width and height")
    return xmin, ymin, xmax, ymax


def _project(x: float, y: float, bounds: tuple[float, ...], panel: int) -> tuple[int, int]:
    xmin, ymin, xmax, ymax = bounds
    pad = 20
    map_height = HEIGHT - TOP - BOTTOM
    scale = min((PANEL_WIDTH - pad * 2) / (xmax - xmin),
                (map_height - pad * 2) / (ymax - ymin))
    px = panel * PANEL_WIDTH + (PANEL_WIDTH - (xmax - xmin) * scale) / 2
    py = TOP + (map_height - (ymax - ymin) * scale) / 2
    px += (x - xmin) * scale
    py += (ymax - y) * scale
    return round(px), round(py)


def _font(size: int):
    for name in ("DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw_frame(roads: list[list[tuple]], incident: list[tuple],
               baseline: list[tuple], plan: list[tuple], bounds: tuple[float, ...],
               stamp: str, plan_label: str, via: str) -> Image.Image:
    """Two views share one map extent and timestamp for an honest comparison."""
    frame = Image.new("RGB", (WIDTH, HEIGHT), "#101821")
    draw = ImageDraw.Draw(frame)
    title, body = _font(21), _font(15)
    draw.text((20, 12), "ABERDEEN · RECORDED SUMO REPLAY", fill="#e7eef4", font=title)
    draw.text((20, 46), f"Baseline · {stamp}", fill="#e7eef4", font=body)
    draw.text((PANEL_WIDTH + 20, 46), f"{plan_label} · {stamp}",
              fill="#e7eef4", font=body)
    for panel, vehicles in enumerate((baseline, plan)):
        map_image = Image.new("RGB", (PANEL_WIDTH, HEIGHT - TOP - BOTTOM), "#101821")
        map_draw = ImageDraw.Draw(map_image)
        def on_panel(x: float, y: float) -> tuple[int, int]:
            px, py = _project(x, y, bounds, panel)
            return px - panel * PANEL_WIDTH, py - TOP

        for shape in roads:
            map_draw.line([on_panel(x, y) for x, y in shape], fill="#43515e", width=2)
        map_draw.line([on_panel(x, y) for x, y in incident], fill="#e25858", width=5)
        for x, y, speed in vehicles:
            px, py = on_panel(x, y)
            color = "#70d6a6" if speed > 3 else "#f4bf63"
            map_draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=color)
        frame.paste(map_image, (panel * PANEL_WIDTH, TOP))
    draw.line((PANEL_WIDTH, TOP, PANEL_WIDTH, HEIGHT - BOTTOM), fill="#81909e", width=2)
    draw.rectangle((0, HEIGHT - BOTTOM, WIDTH, HEIGHT), fill="#17222e")
    draw.text((20, HEIGHT - BOTTOM + 12),
              f"Simulated vehicle positions · red: incident edge · plan via: {via}",
              fill="#e7eef4", font=body)
    return frame


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--incident-id", default="IN-26-03365")
    ap.add_argument("--compliance", type=float)
    ap.add_argument("--clearance-min", type=float)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--results-dir", type=Path, default=ROOT / "results" / "runs")
    ap.add_argument("--plans-dir", type=Path, default=ROOT / "results" / "plans")
    ap.add_argument("--network", type=Path, required=True)
    ap.add_argument("--incident-edge", required=True)
    ap.add_argument("--baseline-fcd", type=Path, required=True)
    ap.add_argument("--plan-fcd", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results" / "replays")
    ap.add_argument("--every-seconds", type=float, default=30)
    ap.add_argument("--start-seconds", type=float, default=0)
    ap.add_argument("--end-seconds", type=float, default=float("inf"))
    ap.add_argument("--clock-start", help="ISO timestamp at SUMO second zero")
    ap.add_argument("--bbox", type=float, nargs=4, metavar=("XMIN", "YMIN", "XMAX", "YMAX"))
    args = ap.parse_args()
    if (not math.isfinite(args.every_seconds) or args.every_seconds <= 0
            or not math.isfinite(args.start_seconds) or args.start_seconds < 0
            or args.end_seconds <= args.start_seconds):
        ap.error("Choose a positive frame interval and an increasing simulation window")
    results, result_errors = read_objects(args.results_dir)
    plans, plan_errors = read_objects(args.plans_dir)
    if result_errors or plan_errors:
        ap.error("Invalid input: " + "; ".join(result_errors + plan_errors))
    scenarios = scenarios_for(results, args.incident_id)
    if not scenarios:
        ap.error("No matching P0/P1/P2 scenario results")
    chosen = [s for s in scenarios
              if (args.compliance is None or s[0] == args.compliance)
              and (args.clearance_min is None or s[1] == args.clearance_min)
              and (args.seed is None or s[2] == args.seed)]
    if not chosen:
        ap.error("No complete matching scenario for the requested assumptions")
    comparison, reason = load_comparison(args.results_dir, args.plans_dir,
                                         args.incident_id, chosen[0])
    if comparison is None:
        ap.error("No recommendation: " + reason)
    winner = comparison["winner"]
    if winner["plan_id"] == "P0":
        ap.error("P0 wins; there is no diversion to animate")
    plan = comparison["plans"][winner["plan_id"]]
    via = ", ".join(sorted({d["via"] for d in plan.get("diversions", [])
                            if isinstance(d, dict) and isinstance(d.get("via"), str)})) or "unspecified"
    roads, incident = road_shapes(args.network, args.incident_edge)
    bounds = _bounds(roads, args.bbox)
    baseline_frames = fcd_frames(args.baseline_fcd, args.every_seconds,
                                 args.start_seconds, args.end_seconds)
    plan_frames = fcd_frames(args.plan_fcd, args.every_seconds,
                             args.start_seconds, args.end_seconds)
    times = sorted(baseline_frames.keys() & plan_frames.keys())
    if not times:
        ap.error("The FCD files have no shared complete timestamps in the selected window")
    if times[0] > args.start_seconds + args.every_seconds or (
            math.isfinite(args.end_seconds) and
            times[-1] < args.end_seconds - args.every_seconds):
        ap.error("The paired FCD files do not cover the requested replay window")
    clock = dt.datetime.fromisoformat(args.clock_start) if args.clock_start else None
    frames = []
    for second in times:
        stamp = ((clock + dt.timedelta(seconds=second)).strftime("%d %b %H:%M")
                 if clock else f"simulation {second:,.0f}s")
        frames.append(draw_frame(roads, incident, baseline_frames[second],
                                 plan_frames[second], bounds, stamp,
                                 plan.get("label", winner["plan_id"]), via))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    basename = f"{comparison['baseline']['run_id']}__{winner['run_id']}"
    gif = args.out_dir / f"{basename}.gif"
    frames[0].save(gif, save_all=True, append_images=frames[1:],
                   duration=250, loop=0, optimize=True)
    meta = {"incident_id": args.incident_id, "baseline_run_id": comparison["baseline"]["run_id"],
            "plan_run_id": winner["run_id"], "scenario": comparison["scenario"],
            "baseline_result_sha256": fingerprint(comparison["baseline"]),
            "plan_result_sha256": fingerprint(winner),
            "plan_sha256": fingerprint(plan),
            "simulation_seconds": [times[0], times[-1]], "frame_count": len(times),
            "source_sha256": {str(path): _sha256(path) for path in
                              (args.network, args.baseline_fcd, args.plan_fcd)}}
    gif.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Rendered {len(times)} matched SUMO frames to {gif}")


if __name__ == "__main__":
    main()
