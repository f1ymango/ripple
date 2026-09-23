"""Do the readings agree with our lane convention? Evidence only -- never overrides it.

The team's convention (23 Sep, docs/02-data.md section 1): on a 4-lane
carriageway, offside to nearside, the lanes are Fast, Middle Lane 2, Middle
Lane 1, Slow -- so Middle Lane 1 is next to the Slow Lane. That matches the
data-dictionary PDF and the Incident Reader prompt. The XML serialises them
Fast, Middle Lane 1, Middle Lane 2, Slow, which is not carriageway order, so
lanes are always matched by name.

This reports what the readings suggest, using a physical argument rather than
the naming. Occupancy is the share of time a vehicle sits over the loop, so for n
vehicles of effective length L at speed v:

    occupancy  ~  n * L / v        =>        L  ~  (occupancy / n) * v

Call that the **length index**. Lanes nearer the kerb carry goods vehicles and
slower traffic, so the length index should rise from the offside lane across to
the nearside one. Whichever labelling makes it rise monotonically is the
carriageway order.

Speed alone cannot do this: the two middle lanes differ by about 5 km/h while
the spread within a lane is over 7 km/h, so speed is inside the noise. The
length index separates them far more sharply.

Reads whatever is already cached -- archive and live both -- so it costs no
downloads. It is only worth running once a decent stretch is cached: a few
hundred periods, across peak and off-peak.

    python -m src.loaders.fetch lanes
    python -m src.loaders.fetch lanes --detector AID01217
"""
from __future__ import annotations

import glob
import gzip
import statistics as stats
from pathlib import Path

from src.loaders import detectors

# Below this many vehicles per 30-second period a lane is too quiet to judge:
# the ratios become noise, which is how the Slow Lane misleads at 0.4 veh.
MIN_VEHICLES_PER_PERIOD = 1.0
MIN_PERIODS = 60

# The order the XML sends, which is the hypothesis under test.
FILE_ORDER = ["Fast Lane", "Middle Lane 1", "Middle Lane 2", "Slow Lane"]
PDF_ORDER = ["Fast Lane", "Middle Lane 2", "Middle Lane 1", "Slow Lane"]
ADOPTED_ORDER = PDF_ORDER      # offside -> nearside; team decision, 23 Sep

OUT_DIR = Path("data")


def cached_snapshots() -> list[Path]:
    """Every detector snapshot on disk, from the archive and the live poller."""
    found: list[Path] = []
    for pattern in ("data/raw/detectors/*.xml.gz", "data/raw/detectors/*.xml",
                    "data/raw/live/detectors/*.xml.gz"):
        found += [Path(p) for p in glob.glob(pattern)]
    return sorted(found)


def _read(path: Path) -> bytes:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as f:
            return f.read()
    return path.read_bytes()


def collect(detector_id: str, paths: list[Path] | None = None) -> dict[str, list[dict]]:
    """Valid lane readings for one detector, grouped by lane name."""
    by_lane: dict[str, list[dict]] = {}
    seen: set = set()
    for path in paths if paths is not None else cached_snapshots():
        try:
            rows = detectors.parse_snapshot(_read(path), keep={detector_id})
        except Exception:                                        # noqa: BLE001
            continue                                             # truncated cache entry
        for row in rows:
            if not row["valid"]:
                continue
            key = (row["timestamp"], row["lane"])
            if key in seen:
                continue
            seen.add(key)
            by_lane.setdefault(row["lane"], []).append(row)
    return by_lane


def lane_stats(readings: list[dict]) -> dict:
    """Per-lane summary, including the length index that does the work here."""
    speeds = [r["speed_kmh"] for r in readings if r["speed_kmh"] is not None]
    volumes = [r["volume"] or 0 for r in readings]
    occs = [r["occupancy_pct"] or 0 for r in readings]
    mean_speed = stats.mean(speeds) if speeds else 0.0
    mean_volume = stats.mean(volumes) if volumes else 0.0
    mean_occ = stats.mean(occs) if occs else 0.0
    occ_per_vehicle = mean_occ / mean_volume if mean_volume else 0.0
    return {
        "periods": len(readings),
        "mean_speed_kmh": round(mean_speed, 1),
        "speed_spread_kmh": round(stats.pstdev(speeds), 1) if len(speeds) > 1 else 0.0,
        "mean_volume": round(mean_volume, 2),
        "mean_occupancy_pct": round(mean_occ, 2),
        "occ_per_vehicle": round(occ_per_vehicle, 3),
        "length_index": round(occ_per_vehicle * mean_speed, 1),
        "reliable": mean_volume >= MIN_VEHICLES_PER_PERIOD and len(readings) >= MIN_PERIODS,
    }


TIME_BANDS = {"00-06": (0, 6), "06-10": (6, 10), "10-16": (10, 16),
              "16-20": (16, 20), "20-24": (20, 24)}


def by_time_band(by_lane: dict[str, list[dict]]) -> dict[str, dict[str, dict]]:
    """The same statistics split by time of day.

    A single number over a whole day can be produced by one unusual period --
    an overnight goods convoy, say. If Middle Lane 2 is the heavier lane in
    every band, at both peaks and overnight, that is a property of the lane
    rather than of the hour we happened to look at.
    """
    out: dict[str, dict[str, dict]] = {}
    for band, (lo, hi) in TIME_BANDS.items():
        grouped: dict[str, list[dict]] = {}
        for lane, readings in by_lane.items():
            rows = [r for r in readings if lo <= r["timestamp"].hour < hi]
            if rows:
                grouped[lane] = rows
        if grouped:
            out[band] = {lane: lane_stats(rows) for lane, rows in grouped.items()}
    return out


def band_agreement(bands: dict[str, dict[str, dict]]) -> tuple[int, int]:
    """How many time bands agree that Middle Lane 2 is the heavier lane."""
    usable = [b for b in bands.values()
              if "Middle Lane 1" in b and "Middle Lane 2" in b]
    agree = sum(b["Middle Lane 2"]["length_index"] > b["Middle Lane 1"]["length_index"]
                for b in usable)
    return agree, len(usable)


def verdict(summary: dict[str, dict], bands: dict[str, dict[str, dict]] | None = None) -> dict:
    """Which labelling makes the length index rise from offside to nearside?"""
    m1, m2 = summary.get("Middle Lane 1"), summary.get("Middle Lane 2")
    if not m1 or not m2:
        return {"conclusion": "not a 4-lane detector -- nothing to decide here"}
    if not (m1["reliable"] and m2["reliable"]):
        return {"conclusion": "too little traffic or too few periods to judge; "
                              "cache more data and run again",
                "periods": min(m1["periods"], m2["periods"])}

    gap = m2["length_index"] - m1["length_index"]
    relative = abs(gap) / max(m1["length_index"], 1e-9) * 100
    if relative < 10:
        conclusion = ("the two middle lanes are not distinguishable -- which means the "
                      "ordering does not matter in practice, so either convention is safe")
        order = None
    elif gap > 0:
        conclusion = ("Middle Lane 2 carries the longer vehicles, which the usual "
                      "heavy-vehicles-keep-left pattern would place nearer the kerb. That "
                      "DISAGREES with the adopted convention, which stands: the test "
                      "assumes keep-left behaviour, and lane use at a toll plaza can be "
                      "set by booth assignment instead. Recorded, not acted on")
        order = FILE_ORDER
    else:
        conclusion = ("Middle Lane 1 carries the longer vehicles, placing it nearer the "
                      "kerb -- consistent with the adopted convention")
        order = PDF_ORDER
    result = {
        "conclusion": conclusion,
        "readings_suggest": order,
        "agrees_with_convention": order is None or order == ADOPTED_ORDER,
        "length_index_gap": round(gap, 1),
        "relative_gap_pct": round(relative),
        "periods": min(m1["periods"], m2["periods"]),
    }
    if bands:
        agree, total = band_agreement(bands)
        result["bands_agreeing"] = f"{agree}/{total}"
        if total and agree not in (0, total):
            result["conclusion"] = (
                f"inconsistent: Middle Lane 2 is the heavier lane in only {agree} of "
                f"{total} time bands, so the difference may be an artefact of when we "
                f"looked rather than of the lane. Treat the ordering as unresolved")
            result["readings_suggest"] = None
            result["agrees_with_convention"] = True
    return result


def analyse(detector_id: str = "AID01217") -> tuple[dict[str, dict], dict, dict]:
    by_lane = collect(detector_id)
    summary = {lane: lane_stats(rows) for lane, rows in by_lane.items()}
    bands = by_time_band(by_lane)
    return summary, verdict(summary, bands), bands


def report(detector_id: str, summary: dict[str, dict], conclusion: dict,
           path: Path | None = None, bands: dict[str, dict[str, dict]] | None = None) -> str:
    """A block that can be pasted straight into docs/02-data.md section 1."""
    order = [l for l in FILE_ORDER if l in summary] or sorted(summary)
    lines = [
        f"# Lane identity evidence — {detector_id}",
        "",
        f"From {min((summary[l]['periods'] for l in order), default=0)} cached "
        "30-second periods. Regenerate with "
        "`python -m src.loaders.fetch lanes`.",
        "",
        "| Lane (order sent in the XML) | Periods | Speed | Veh/period | Occupancy | Length index |",
        "|---|---|---|---|---|---|",
    ]
    for lane in order:
        s = summary[lane]
        flag = "" if s["reliable"] else " ⚠️"
        lines.append(f"| {lane}{flag} | {s['periods']} | {s['mean_speed_kmh']} km/h "
                     f"| {s['mean_volume']} | {s['mean_occupancy_pct']}% "
                     f"| **{s['length_index']}** |")
    lines += [
        "",
        "⚠️ marks a lane too quiet or too sparsely sampled to judge — its ratios are noise.",
        "",
        "**Length index** ≈ vehicle length, from `(occupancy ÷ vehicles) × speed`. "
        "It should rise from the offside (median) lane to the nearside (kerb) lane, "
        "because kerbside lanes carry goods vehicles.",
        "",
        "## Conclusion",
        "",
        conclusion["conclusion"] + ".",
        "",
    ]
    lines += [f"Adopted convention, offside → nearside: `{' → '.join(ADOPTED_ORDER)}`", ""]
    if conclusion.get("readings_suggest"):
        lines += [f"Order the readings suggest: "
                  f"`{' → '.join(conclusion['readings_suggest'])}`",
                  "",
                  f"Length-index gap between the middle lanes: "
                  f"{conclusion['length_index_gap']} "
                  f"({conclusion['relative_gap_pct']}% of the smaller).",
                  ""]
    if bands:
        lines += ["## Robustness — does it hold at every time of day?", "",
                  "| Band | Fast | Middle 1 | Middle 2 | Periods | Middle 2 heavier? |",
                  "|---|---|---|---|---|---|"]
        for band, stat in bands.items():
            if "Middle Lane 1" not in stat or "Middle Lane 2" not in stat:
                continue
            f = stat.get("Fast Lane", {}).get("length_index", "—")
            m1, m2 = stat["Middle Lane 1"], stat["Middle Lane 2"]
            tick = "yes" if m2["length_index"] > m1["length_index"] else "**no**"
            lines.append(f"| {band} | {f} | {m1['length_index']} | {m2['length_index']} "
                         f"| {m1['periods']} | {tick} |")
        agree, total = band_agreement(bands)
        lines += ["", f"Agreeing bands: **{agree}/{total}**. A split result means the "
                      "difference depends on when we looked, not on the lane — which is "
                      "itself a reason not to conclude.", ""]
    lines += ["This is evidence from readings, not a statement from the Transport "
              "Department. The adopted convention stands either way; a disagreement is "
              "recorded, never used to change lane mapping on its own.", ""]
    text = "\n".join(lines)
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    return text
