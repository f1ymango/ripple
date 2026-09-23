"""Raw traffic detector archive -> tidy 5-minute series (component A1).

What the feed actually is, measured on 21 Sep 2026 rather than taken from the
spec (both findings belong in docs/02-data.md):

  * `lane_id` and `direction` are text ("Fast Lane", "North East"), not the
    numeric codes the data dictionary describes. No lane-count mapping needed.
  * **The archive timestamp is not the data timestamp.** A file archived at
    08:30 held the periods 08:21:00-08:22:00 -- a lag of about nine minutes.
    Always take the time from `date` + `period_from` inside the file.
  * **Coverage is partial.** Over the hour 08:00-09:00 the archive listed 41
    versions, served 28 (13 were a persistent 404), and those held 28 distinct
    data minutes out of 60: about 47% of the clock, with gaps of up to five
    minutes. The feed publishes every minute; the archive did not keep them all.

That last point decides how a bin is built. A five-minute bin usually holds
one to three sampled minutes, so **summing raw volume would understate flow by
roughly half** and any GEH comparison built on it would calibrate the twin to
half the real traffic. Instead each bin reports a flow *rate* over the seconds
actually observed, plus the coverage behind it, and `count_5min` is the
comparable count derived from that rate.

    python -m src.loaders.fetch detectors --start 2026-09-21T07:00 --end 2026-09-21T10:00
"""
from __future__ import annotations

import csv
import datetime as dt
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from src.loaders import archive
from src.loaders.corridor import DETECTOR_IDS

HK = dt.timezone(dt.timedelta(hours=8))
PERIOD_SECONDS = 30       # each <period> covers 30 seconds
BIN_MINUTES = 5
ARCHIVE_LAG_MIN = 15      # widen a wanted window by this before hitting the archive

# A bin below this sampling fraction is mostly inference: fine for a speed
# chart, not fine for a GEH count. Changing it is a team decision, because it
# trades precision against how many points Simulation has left to fit.
MIN_COVERAGE_PCT = 40


def parse_snapshot(xml_bytes: bytes, keep: set[str] | None = None) -> list[dict]:
    """One raw snapshot -> lane rows, timed from inside the file.

    `keep` filters to a set of detector IDs; the feed carries all 765 detectors
    in Hong Kong and we want 28 of them.
    """
    root = ET.fromstring(xml_bytes)
    day = root.findtext("date", "").strip()
    rows: list[dict] = []
    for period in root.find("periods").findall("period"):
        period_from = period.findtext("period_from", "").strip()
        try:
            timestamp = dt.datetime.fromisoformat(f"{day}T{period_from}").replace(tzinfo=HK)
        except ValueError:
            continue
        for detector in period.iter("detector"):
            detector_id = (detector.findtext("detector_id") or "").strip()
            if keep is not None and detector_id not in keep:
                continue
            direction = (detector.findtext("direction") or "").strip()
            for lane in detector.iter("lane"):
                valid = (lane.findtext("valid") or "").strip().upper() == "Y"
                rows.append({
                    "timestamp": timestamp,
                    "detector_id": detector_id,
                    "direction": direction,
                    "lane": (lane.findtext("lane_id") or "").strip(),
                    "speed_kmh": _number(lane.findtext("speed")),
                    "volume": _number(lane.findtext("volume")),
                    "occupancy_pct": _number(lane.findtext("occupancy")),
                    # The tag really is <s.d.> -- a dot in the tag name.
                    "speed_sd": _number(lane.findtext("s.d.")),
                    "valid": valid,
                })
    return rows


def _number(text: str | None) -> float | None:
    """'26' -> 26.0, '' or None or rubbish -> None. Never 0.0 by accident."""
    if text is None or not text.strip():
        return None
    try:
        return float(text.strip())
    except ValueError:
        return None


def window_timestamps(start: dt.datetime, end: dt.datetime) -> list[str]:
    """Archive timestamps that could hold data for [start, end].

    Padded by ARCHIVE_LAG_MIN at both ends because of the publish lag above:
    the file holding 08:21 data was archived at 08:30.
    """
    low = start - dt.timedelta(minutes=ARCHIVE_LAG_MIN)
    high = end + dt.timedelta(minutes=ARCHIVE_LAG_MIN)
    # list-file-versions works in whole days, so ask for every day the padded
    # window touches -- a window that crosses midnight needs both.
    stamps = archive.list_versions("detectors",
                                   low.strftime("%Y%m%d"), high.strftime("%Y%m%d"))
    return [t for t in stamps
            if low.strftime("%Y%m%d-%H%M") <= t <= high.strftime("%Y%m%d-%H%M")]


def load_window(start: dt.datetime, end: dt.datetime,
                detector_ids: list[str] | None = None) -> list[dict]:
    """Every corridor lane reading whose own timestamp falls inside [start, end].

    Consecutive archived files overlap, so identical readings are dropped on
    (timestamp, detector, lane) rather than counted twice.
    """
    keep = set(detector_ids or DETECTOR_IDS)
    seen: set[tuple] = set()
    rows: list[dict] = []
    for _, xml_bytes in archive.iter_snapshots("detectors", window_timestamps(start, end)):
        for row in parse_snapshot(xml_bytes, keep):
            if not (start <= row["timestamp"] <= end):
                continue
            key = (row["timestamp"], row["detector_id"], row["lane"])
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    rows.sort(key=lambda r: (r["timestamp"], r["detector_id"], r["lane"]))
    return rows


def bin_window(rows: list[dict], minutes: int = BIN_MINUTES,
               per_lane: bool = False) -> list[dict]:
    """Aggregate lane readings into fixed-width bins.

    `minutes` trades time resolution against precision, and the right answer
    depends on the job. The archive keeps under half the minutes, so a bin holds
    only a sample: widening it multiplies the samples behind each count.

      5 minutes   incident dynamics -- when the queue formed, when it cleared
      15 minutes  demand calibration for the pre-incident hour, where a stable
                  count matters far more than fine timing (3x the samples)

    Must divide 60 so bins align to the hour.

    Per bin:
      flow_veh_h   vehicles per hour, over the seconds actually observed
      count_bin    the count this bin width implies -- the number to put
                   against a modelled count in a GEH calculation
      speed_kmh    volume-weighted mean over valid lanes (a plain mean would
                   let an empty fast lane outvote a loaded slow lane)
      coverage_pct how much of the five minutes we actually saw
      offline      lane readings with valid="N", counted, never treated as zero
    """
    if 60 % minutes:
        raise ValueError(f"bin width must divide 60 minutes, got {minutes}")

    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        floor = row["timestamp"].replace(
            minute=row["timestamp"].minute - row["timestamp"].minute % minutes,
            second=0, microsecond=0)
        key = (floor, row["detector_id"], row["lane"]) if per_lane else (floor, row["detector_id"])
        buckets[key].append(row)

    out = []
    for key, group in sorted(buckets.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        bin_start, detector_id = key[0], key[1]
        valid = [r for r in group if r["valid"]]
        offline = len(group) - len(valid)
        periods = {r["timestamp"] for r in valid}
        observed_s = len(periods) * PERIOD_SECONDS
        bin_seconds = minutes * 60
        volume = sum(r["volume"] or 0 for r in valid)
        flow = (volume / observed_s * 3600) if observed_s else None

        weight = sum(r["volume"] or 0 for r in valid if r["speed_kmh"] is not None)
        if weight:
            speed = sum((r["speed_kmh"] or 0) * (r["volume"] or 0)
                        for r in valid if r["speed_kmh"] is not None) / weight
        else:  # no traffic in the bin: fall back to the plain mean of the readings
            speeds = [r["speed_kmh"] for r in valid if r["speed_kmh"] is not None]
            speed = sum(speeds) / len(speeds) if speeds else None
        occupancies = [r["occupancy_pct"] for r in valid if r["occupancy_pct"] is not None]

        row = {
            "bin_start": bin_start.isoformat(),
            "detector_id": detector_id,
            "speed_kmh": round(speed, 1) if speed is not None else "",
            "flow_veh_h": round(flow) if flow is not None else "",
            "count_bin": round(flow * minutes / 60) if flow is not None else "",
            "bin_minutes": minutes,
            "occupancy_pct": round(sum(occupancies) / len(occupancies), 1) if occupancies else "",
            "volume_observed": round(volume),   # int: these are whole vehicles
            "periods_observed": len(periods),
            "coverage_pct": round(observed_s / bin_seconds * 100),
            "lanes_valid": len(valid),
            "lanes_offline": offline,
        }
        if per_lane:
            row["lane"] = key[2]
        out.append(row)
    return out


def write_csv(rows: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def usable_for_calibration(binned: list[dict],
                           min_coverage_pct: int = MIN_COVERAGE_PCT) -> list[dict]:
    """Bins with enough observed time to put a count against a modelled count.

    Use this for GEH. Do NOT use it for the speed chart -- speed survives low
    coverage, counts do not, and throwing away sparse bins would leave the
    chart with holes it does not need.
    """
    return [b for b in binned if b["coverage_pct"] >= min_coverage_pct]


def coverage_bias_check(binned: list[dict],
                        min_coverage_pct: int = MIN_COVERAGE_PCT) -> dict:
    """Is filtering by coverage a precision filter, or is it biasing the sample?

    Dropping bins by coverage is only safe if coverage is unrelated to traffic
    conditions. It should be -- the archive dropped snapshots for its own
    reasons -- but it is one comparison to check, and it belongs on the
    validation slide either way.

    A large gap in mean speed between the low- and high-coverage groups means
    the filter is selecting for something, and that has to be said out loud.
    """
    def mean_speed(rows):
        speeds = [float(b["speed_kmh"]) for b in rows if b["speed_kmh"] != ""]
        return round(sum(speeds) / len(speeds), 1) if speeds else None

    low = [b for b in binned if b["coverage_pct"] < min_coverage_pct]
    high = [b for b in binned if b["coverage_pct"] >= min_coverage_pct]
    low_speed, high_speed = mean_speed(low), mean_speed(high)
    gap = (round(abs(low_speed - high_speed), 1)
           if low_speed is not None and high_speed is not None else None)
    return {
        "low_coverage_bins": len(low), "low_coverage_mean_speed": low_speed,
        "high_coverage_bins": len(high), "high_coverage_mean_speed": high_speed,
        "mean_speed_gap_kmh": gap,
        "looks_unbiased": gap is not None and gap <= 5,
    }


def coverage_report(binned: list[dict],
                    min_coverage_pct: int = MIN_COVERAGE_PCT) -> dict:
    """What the Simulation owner needs to know before calibrating against this.

    `warning` is not decoration. The archive keeps under half the minutes, so a
    bin's count is an estimate scaled up from the seconds actually observed. A
    label nobody reads is the same as no label at all.
    """
    if not binned:
        return {"bins": 0, "warning": "no bins -- nothing was observed in this window"}
    usable = usable_for_calibration(binned, min_coverage_pct)
    report = {
        "bins": len(binned),
        "detectors": len({b["detector_id"] for b in binned}),
        "empty_bins": len([b for b in binned if b["periods_observed"] == 0]),
        "mean_coverage_pct": round(sum(b["coverage_pct"] for b in binned) / len(binned)),
        "bins_with_offline_lanes": len([b for b in binned if b["lanes_offline"]]),
        "min_coverage_pct": min_coverage_pct,
        "usable_for_calibration": len(usable),
        "usable_pct": round(len(usable) / len(binned) * 100),
    }
    report["warning"] = (
        f"count_5min is an ESTIMATE scaled from {report['mean_coverage_pct']}% mean "
        f"coverage. Calibrate counts only on the {report['usable_for_calibration']} "
        f"bins at >= {min_coverage_pct}% coverage; use every bin for speed.")
    return report


def format_warning(report: dict) -> str:
    """The coverage warning as a block meant to be impossible to scroll past."""
    if report.get("bins", 0) == 0:
        return f"!! {report.get('warning', 'no data')}"
    bar = "!" * 74
    return (f"{bar}\n"
            f"!! COVERAGE WARNING -- read before using these numbers\n"
            f"!! {report['warning']}\n"
            f"!! See docs/02-data.md section 7.\n"
            f"{bar}")


def bin_5min(rows: list[dict], per_lane: bool = False) -> list[dict]:
    """Five-minute bins: the default resolution for incident dynamics."""
    return bin_window(rows, BIN_MINUTES, per_lane)
