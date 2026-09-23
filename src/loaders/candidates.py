"""Shortlist real corridor incidents to replay, scored on how well we can see them.

The archive keeps under half the detector minutes, and which minutes survive is
essentially random (docs/02-data.md section 3). We cannot recover the rest --
so instead of fighting the gaps, we **choose an incident that happens to fall
where the gaps are smallest**. Coverage becomes a selection criterion, and it
costs nothing but a column.

Screening runs in two stages so it fits in an afternoon rather than a night:

  Stage 1  cheap. For every corridor incident, sample a handful of the archive
           versions in its window and measure what fraction actually serve.
           ~12 requests per incident instead of ~200.
  Stage 2  full. For the best few only, pull the whole window and measure real
           coverage, detector health and the size of the speed drop.

    python -m src.loaders.fetch candidates --start 2026-06-22 --end 2026-09-21 --top 6
"""
from __future__ import annotations

import datetime as dt
import random
from pathlib import Path

from src.loaders import archive, detectors, incidents
from src.loaders.corridor import TUNNEL_DETECTORS

OUT_PATH = Path("data/candidates.md")

# How much road time to pull around an incident: enough pre-incident hour to
# calibrate against, enough after clearance to see recovery (docs/02-data.md).
BEFORE_MIN, AFTER_MIN = 90, 60

SAMPLE_VERSIONS = 12      # stage-1 probes per incident
MIN_DURATION_MIN = 20     # roles/data-experiments.md


def window_for(incident: dict) -> tuple[dt.datetime, dt.datetime] | None:
    """The (start, end) of detector data we would need for this incident."""
    try:
        new_at = dt.datetime.fromisoformat(incident["new_at"])
        closed_at = dt.datetime.fromisoformat(incident["closed_at"])
    except (ValueError, KeyError):
        return None
    return new_at - dt.timedelta(minutes=BEFORE_MIN), closed_at + dt.timedelta(minutes=AFTER_MIN)


def estimate_retrievability(start: dt.datetime, end: dt.datetime,
                            sample: int = SAMPLE_VERSIONS, seed: int = 42) -> dict:
    """Stage 1: what fraction of this window's archive versions actually serve?

    Downloads `sample` files, not the window. About a third to a half of listed
    detector versions are a persistent 404, and the rate varies window to
    window -- this is how we find out before committing to a full pull.
    """
    stamps = detectors.window_timestamps(start, end)
    if not stamps:
        return {"listed": 0, "sampled": 0, "served": 0, "retrievable_pct": 0}

    rng = random.Random(seed)
    probe = rng.sample(stamps, min(sample, len(stamps)))
    served = 0
    for ts in probe:
        try:
            archive.fetch("detectors", ts)
            served += 1
        except archive.ArchiveError:
            pass
    return {
        "listed": len(stamps),
        "sampled": len(probe),
        "served": served,
        "retrievable_pct": round(served / len(probe) * 100),
    }


def measure(incident: dict, bin_minutes: int = 5) -> dict:
    """Stage 2: pull the whole window and measure what we would really have.

    `speed_drop_kmh` compares the quietest five minutes during the incident
    against the pre-incident hour, on the tunnel detectors. An incident that
    does not move those is not worth simulating, whatever the message says.
    """
    window = window_for(incident)
    if window is None:
        return {}
    start, end = window
    rows = detectors.load_window(start, end)
    if not rows:
        return {"bins": 0}

    binned = detectors.bin_window(rows, bin_minutes)
    report = detectors.coverage_report(binned)
    new_at = dt.datetime.fromisoformat(incident["new_at"])

    def speeds(bins, where):
        return [float(b["speed_kmh"]) for b in bins
                if b["speed_kmh"] != "" and b["detector_id"] in TUNNEL_DETECTORS
                and where(dt.datetime.fromisoformat(b["bin_start"]))]

    before = speeds(binned, lambda t: t < new_at)
    during = speeds(binned, lambda t: t >= new_at)
    drop = round(min(during) - (sum(before) / len(before)), 1) if before and during else None

    offline = sum(b["lanes_offline"] for b in binned)
    lanes = sum(b["lanes_valid"] + b["lanes_offline"] for b in binned)
    return {
        "bins": report["bins"],
        "mean_coverage_pct": report["mean_coverage_pct"],
        "usable_pct": report["usable_pct"],
        "detectors_seen": report["detectors"],
        "lanes_valid_pct": round((lanes - offline) / lanes * 100) if lanes else 0,
        "speed_drop_kmh": drop,
    }


def score(row: dict) -> float:
    """Rank candidates. Coverage and a visible speed drop matter most.

    Deliberately simple and deliberately visible: the team picks the incident,
    this only decides which few are worth a full pull.
    """
    coverage = row.get("retrievable_pct", 0) / 100
    drop = min(abs(row.get("speed_drop_kmh") or 0) / 30, 1.0)
    duration = min((row.get("duration_min") or 0) / 60, 1.0)
    return round(2 * coverage + 2 * drop + duration, 3)


def shortlist(start: str, end: str, top: int = 6, bin_minutes: int = 5,
              log=print) -> list[dict]:
    """Every usable corridor incident, stage-1 screened, best `top` measured."""
    all_incidents = incidents.load(start, end)
    usable = incidents.usable_corridor_incidents(all_incidents, MIN_DURATION_MIN)
    log(f"{len(all_incidents)} incidents, {len(usable)} on the corridor with a "
        f"clear NEW and CLOSED at least {MIN_DURATION_MIN} min apart")

    rows = []
    for n, incident in enumerate(usable, 1):
        window = window_for(incident)
        if window is None:
            continue
        probe = estimate_retrievability(*window)
        row = {**incident, **probe}
        row["score"] = score(row)
        rows.append(row)
        log(f"  [{n}/{len(usable)}] {incident['incident_number']} "
            f"{incident['duration_min']:>4} min  "
            f"{probe['retrievable_pct']:>3}% retrievable  score {row['score']}")

    rows.sort(key=lambda r: r["score"], reverse=True)
    for row in rows[:top]:
        log(f"  full pull: {row['incident_number']} ...")
        row.update(measure(row, bin_minutes))
        row["score"] = score(row)
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows


def write_markdown(rows: list[dict], path: Path = OUT_PATH, top: int = 6) -> Path:
    """data/candidates.md -- the table the team picks the demo incident from."""
    today = dt.date.today().isoformat()
    lines = [
        "# Candidate demo incidents",
        "",
        f"Generated {today} by `python -m src.loaders.fetch candidates`. "
        "Regenerate rather than edit.",
        "",
        "**Coverage is a selection criterion, not a defect.** The historical archive "
        "keeps under half the detector minutes and which minutes survive is "
        "effectively random, so rather than fight the gaps we pick an incident that "
        "falls where they are smallest. See `docs/02-data.md` section 3.",
        "",
        "| # | Incident | Date | Road | Duration | Retrievable | Coverage | Usable bins | Lanes valid | Speed drop | Score |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for n, r in enumerate(rows, 1):
        measured = "bins" in r
        lines.append(
            f"| {n} | `{r['incident_number']}` | {r['new_at'][:16].replace('T', ' ')} "
            f"| {r['location_en']} {r['direction_en']} "
            f"| {r['duration_min']} min "
            f"| {r.get('retrievable_pct', '?')}% "
            f"| {str(r.get('mean_coverage_pct', '—')) + '%' if measured else '—'} "
            f"| {str(r.get('usable_pct', '—')) + '%' if measured else '—'} "
            f"| {str(r.get('lanes_valid_pct', '—')) + '%' if measured else '—'} "
            f"| {r.get('speed_drop_kmh') if measured else '—'} "
            f"| {r['score']} |")

    lines += [
        "",
        f"Columns are blank below the top {top}: those were screened on a "
        f"{SAMPLE_VERSIONS}-version sample only, not pulled in full.",
        "",
        "## What the columns mean",
        "",
        "- **Retrievable** — of the archive versions listed for this window, the share "
        "that actually serve rather than returning a persistent 404. Sampled.",
        "- **Coverage** — mean share of each bin we actually observed, from the full pull. "
        "Higher means counts are closer to measurements than to estimates.",
        "- **Usable bins** — share at or above the calibration threshold "
        f"({detectors.MIN_COVERAGE_PCT}%). This is what Simulation has to fit demand against.",
        "- **Lanes valid** — share of lane readings with `valid=\"Y\"`. Low means detectors "
        "were offline, which is a different problem from archive gaps.",
        "- **Speed drop** — quietest 5 minutes during the incident against the "
        "pre-incident mean, on the tunnel detectors. An incident that does not move "
        "these is not worth simulating.",
        "",
        "## Decision",
        "",
        "🔒 The team picks one incident from this table. Record the choice in the README "
        "and in `docs/04-plan.md`, then everything downstream replays that one incident.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path
