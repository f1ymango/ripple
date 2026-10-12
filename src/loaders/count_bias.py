"""Do the detectors count every vehicle in slow traffic? Two detectors on one road, compared (component A).

A pair of detectors with no junction between them must count the same
vehicles. Whatever differs is the detectors, and if the difference grows as
the traffic slows, a detector's counts in slow traffic cannot be scored
against: a model that moves the right number of vehicles would fail GEH there.

TD's Road Network (2nd generation, data.gov.hk, RdNet_IRNP.gdb.zip of
9 Oct 2026) has no junction between AID01106 and AID01107: centrelines 17374,
17378, 15939 and 15938 follow each other with nothing joining or leaving, 394 m
in all. That pair is the default here.

Only 30-second periods in which both detectors report every lane valid are
used, from the cached snapshots alone, so the comparison sees the same
seconds at both ends. Each 5-minute bin is placed in a band by the upstream
detector's vehicle-weighted speed.

    python -m src.loaders.fetch count-bias --exclude-day 2026-05-15
    -> results/data/count-bias_AID01106_AID01107.md (+ .json)
"""
from __future__ import annotations

import datetime as dt
import gzip
import json
from collections import defaultdict
from pathlib import Path

from src.loaders import archive
from src.loaders.detectors import parse_snapshot

BANDS_KMH = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, None)]
MIN_PERIODS = 3          # matched 30-second periods a 5-minute bin needs before it is used
OUT_DIR = Path("results/data")


def cached_days() -> list[str]:
    """Every day ('YYYYMMDD') with at least one cached detector snapshot."""
    folder = archive.CACHE_ROOT / "detectors"
    return sorted({p.name[:8] for p in folder.glob("*.xml.gz")})


def _volume_and_speed(group: list[dict]) -> tuple[float, float, float]:
    """(volume, speed x volume, volume that has a speed) over a detector's lanes in one period."""
    weighted = [(r["speed_kmh"], r["volume"] or 0) for r in group if r["speed_kmh"] is not None]
    return (sum(r["volume"] or 0 for r in group), sum(s * v for s, v in weighted), sum(v for _, v in weighted))


def matched_periods(up: str, down: str, days: list[str]) -> dict:
    """{period start: (up (volume, speed x volume, volume with speed), down (the same))} for fully valid periods."""
    folder = archive.CACHE_ROOT / "detectors"
    lanes: dict[tuple, list[dict]] = defaultdict(list)
    seen = set()
    for day in days:
        for path in sorted(folder.glob(f"{day}-*.xml.gz")):
            try:
                rows = parse_snapshot(gzip.decompress(path.read_bytes()), {up, down})
            except Exception:                              # a snapshot that does not parse is skipped
                continue
            for row in rows:
                key = (row["timestamp"], row["detector_id"], row["lane"])
                if key in seen:
                    continue
                seen.add(key)
                lanes[(row["timestamp"], row["detector_id"])].append(row)
    out = {}
    for (stamp, detector), group in lanes.items():
        if detector != up or not all(r["valid"] for r in group):
            continue
        other = lanes.get((stamp, down))
        if not other or not all(r["valid"] for r in other):
            continue
        out[stamp] = (_volume_and_speed(group), _volume_and_speed(other))
    return out


def band_of(speed: float) -> str:
    for low, high in BANDS_KMH:
        if speed >= low and (high is None or speed < high):
            return f"{low}-{high}" if high is not None else f"{low}+"
    raise ValueError(speed)


def compare(up: str = "AID01106", down: str = "AID01107", exclude_days: tuple[str, ...] = (),
            days: list[str] | None = None) -> dict:
    """Upstream count over downstream count per speed band of the upstream detector, 5-minute bins."""
    days = [d for d in (days or cached_days()) if d not in exclude_days]
    bins: dict[dt.datetime, list] = defaultdict(lambda: [0, 0, 0.0, 0, 0])   # up, down, speed x vol, vol, periods
    for stamp, ((up_vol, speed_vol, speed_w), (down_vol, _, _)) in matched_periods(up, down, days).items():
        start = stamp.replace(minute=stamp.minute - stamp.minute % 5, second=0, microsecond=0)
        b = bins[start]
        b[0] += up_vol
        b[1] += down_vol
        b[2] += speed_vol
        b[3] += speed_w
        b[4] += 1
    bands: dict[str, list] = {band_of(low): [0, 0, 0, []] for low, _ in BANDS_KMH}
    for start, (u, d, sv, w, n) in bins.items():
        if n < MIN_PERIODS or not w or not d:
            continue
        band = bands[band_of(sv / w)]
        band[0] += u
        band[1] += d
        band[2] += 1
        band[3].append(start.strftime("%Y-%m-%d"))
    rows = []
    for name, (u, d, n, used_days) in bands.items():
        rows.append({"band_kmh": name, "bins": n, "days": len(set(used_days)),
                     "up_vehicles": round(u), "down_vehicles": round(d),
                     "up_over_down": round(u / d, 3) if d else None})
    return {"up": up, "down": down, "days_read": days, "days_excluded": list(exclude_days),
            "min_matched_periods_per_bin": MIN_PERIODS, "bands": rows}


def day_label(compact: str) -> str:
    return f"{compact[:4]}-{compact[4:6]}-{compact[6:]}"


def write(result: dict, out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / f"count-bias_{result['up']}_{result['down']}"
    stem.with_suffix(".json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    lines = [f"# Counts in slow traffic: {result['up']} against {result['down']}", "",
             "Generated by `python -m src.loaders.fetch count-bias"
             + "".join(f" --exclude-day {day_label(d)}" for d in result["days_excluded"])
             + "`. Regenerate rather than edit.", "",
             f"No junction between the two detectors (TD Road Network, 2nd generation). Matched 30-second "
             f"periods with every lane valid at both, {len(result['days_read'])} cached days"
             + (f", leaving out {', '.join(day_label(d) for d in result['days_excluded'])}"
                if result["days_excluded"] else "")
             + f"; a 5-minute bin needs {result['min_matched_periods_per_bin']} matched periods. "
             f"Bands by {result['up']}'s own vehicle-weighted speed.", "",
             f"| {result['up']} speed, km/h | Bins | Days | {result['up']} vehicles | {result['down']} vehicles "
             f"| {result['up']} / {result['down']} |", "|---|---|---|---|---|---|"]
    for row in result["bands"]:
        lines.append(f"| {row['band_kmh']} | {row['bins']} | {row['days']} | {row['up_vehicles']} "
                     f"| {row['down_vehicles']} | {row['up_over_down'] if row['up_over_down'] is not None else '-'} |")
    stem.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return stem.with_suffix(".md")
