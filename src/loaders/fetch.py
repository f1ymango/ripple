"""Command line for the data layer (component A).

    python -m src.loaders.fetch corridor
    python -m src.loaders.fetch prefetch  --feed stn --start 2026-06-22 --end 2026-09-21
    python -m src.loaders.fetch incidents --start 2026-06-22 --end 2026-09-21
    python -m src.loaders.fetch detectors --start 2026-09-21T07:00 --end 2026-09-21T10:00

`prefetch` is the long one and the only one that needs to run unattended: it
fills data/raw/ in parallel and is resumable, so a dropped connection costs
the snapshots in flight and nothing else. Everything afterwards reads the
cache, which is why the other commands take seconds.
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from src.loaders import archive, candidates, corridor, detectors, incidents, live

HK = dt.timezone(dt.timedelta(hours=8))


def _moment(text: str) -> dt.datetime:
    """'2026-09-21' or '2026-09-21T07:00' -> a Hong Kong datetime."""
    return dt.datetime.fromisoformat(text).replace(tzinfo=HK)


def cmd_corridor(args) -> None:
    rows = corridor.build_table()
    print(f"wrote {len(rows)} corridor detectors to {corridor.OUT_PATH}")
    for leg in ("main_eastbound", "main_westbound", "western_alternative"):
        print(f"  {leg:22} {len([r for r in rows if r['leg'] == leg])}")


def cmd_prefetch(args) -> None:
    stamps = archive.list_versions(args.feed, args.start, args.end)
    print(f"{args.feed}: archive lists {len(stamps)} snapshots for {args.start}..{args.end}")
    counts = archive.prefetch(args.feed, stamps, workers=args.workers)
    if counts["missing"]:
        # About a third of listed detector versions 404 persistently. Expected,
        # not a bug, but the number belongs in the run log.
        print(f"note: {counts['missing']} listed snapshots are not actually served "
              f"({counts['missing'] / max(len(stamps), 1) * 100:.0f}% of the window)")


def cmd_incidents(args) -> None:
    rows = incidents.load(args.start, args.end)
    out = Path(f"data/incidents_{args.start}_{args.end}.csv")
    incidents.write_csv(rows, out)
    on_corridor = [r for r in rows if r["corridor_road"]]
    usable = incidents.usable_corridor_incidents(on_corridor)
    print(f"{len(rows)} incidents -> {out}")
    print(f"  on the corridor:            {len(on_corridor)}")
    print(f"  with a clear NEW and CLOSED >= 20 min apart: {len(usable)}")
    for row in usable:
        print(f"    {row['incident_number']}  {row['new_at'][:16]}  "
              f"{row['duration_min']:>4} min  {row['location_en']} ({row['corridor_road']})")


def cmd_detectors(args) -> None:
    start, end = _moment(args.start), _moment(args.end)
    rows = detectors.load_window(start, end)
    if not rows:
        print("no detector readings in that window -- the archive's latest day is yesterday")
        return
    binned = detectors.bin_window(rows, args.bin_minutes)
    usable = detectors.usable_for_calibration(binned, args.min_coverage)
    stem = f"{start:%Y%m%d-%H%M}_{end:%H%M}_b{args.bin_minutes}"

    detectors.write_csv(rows, Path(f"data/detector_readings_{stem}.csv"))
    detectors.write_csv(binned, Path(f"data/detector_5min_{stem}.csv"))
    # The threshold is in the filename so a stale export can never be mistaken
    # for the full set, nor the full set for a calibration-ready one.
    if usable:
        detectors.write_csv(usable,
                            Path(f"data/detector_5min_{stem}_cov{args.min_coverage}.csv"))

    print(f"{len(rows)} lane readings -> {len(binned)} bins of {args.bin_minutes} min")
    report = detectors.coverage_report(binned, args.min_coverage)
    for key, value in report.items():
        if key != "warning":
            print(f"  {key:24} {value}")
    print()
    print(detectors.format_warning(report))
    bias = detectors.coverage_bias_check(binned, args.min_coverage)
    if bias["mean_speed_gap_kmh"] is not None and not bias["looks_unbiased"]:
        print(f"\n!! Low-coverage bins average {bias['low_coverage_mean_speed']} km/h vs "
              f"{bias['high_coverage_mean_speed']} km/h for high-coverage bins "
              f"({bias['mean_speed_gap_kmh']} km/h apart). Filtering by coverage may be "
              f"selecting for traffic conditions -- say so on the validation slide.")


def cmd_candidates(args) -> None:
    rows = candidates.shortlist(args.start, args.end, args.top, args.bin_minutes)
    if not rows:
        print("no usable corridor incidents in that window -- widen the dates")
        return
    path = candidates.write_markdown(rows, top=args.top)
    print(f"\n{len(rows)} candidates -> {path}")
    print("Top of the list (the team picks one):")
    for row in rows[:args.top]:
        print(f"  {row['incident_number']}  score {row['score']:<6} "
              f"{row['duration_min']:>4} min  coverage {row.get('mean_coverage_pct', '?')}%  "
              f"drop {row.get('speed_drop_kmh', '?')} km/h  {row['location_en']}")


def cmd_live(args) -> None:
    live.run(minutes=args.minutes, poll_seconds=args.poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("corridor", help="write data/detectors.csv").set_defaults(func=cmd_corridor)

    p = sub.add_parser("prefetch", help="fill the archive cache in parallel (resumable)")
    p.add_argument("--feed", choices=sorted(archive.FEEDS), required=True)
    p.add_argument("--start", required=True, help="first day, YYYY-MM-DD")
    p.add_argument("--end", required=True, help="last day, YYYY-MM-DD (archive ends yesterday)")
    p.add_argument("--workers", type=int, default=6)
    p.set_defaults(func=cmd_prefetch)

    p = sub.add_parser("incidents", help="rebuild incident timelines from cached STN snapshots")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.set_defaults(func=cmd_incidents)

    p = sub.add_parser("detectors", help="tidy + 5-minute bins for one time window")
    p.add_argument("--start", required=True, help="YYYY-MM-DDTHH:MM, Hong Kong time")
    p.add_argument("--end", required=True, help="YYYY-MM-DDTHH:MM, Hong Kong time")
    p.add_argument("--bin-minutes", type=int, default=detectors.BIN_MINUTES,
                   dest="bin_minutes",
                   help="bin width; 5 for incident dynamics, 15 for demand "
                        "calibration where a stable count beats fine timing "
                        "(default %(default)s)")
    p.add_argument("--min-coverage", type=int, default=detectors.MIN_COVERAGE_PCT,
                   dest="min_coverage",
                   help="sampling-fraction threshold for the calibration export "
                        "(default %(default)s%%; see docs/02-data.md section 7)")
    p.set_defaults(func=cmd_detectors)

    p = sub.add_parser("candidates", help="shortlist demo incidents, scored on coverage")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--top", type=int, default=6,
                   help="how many to pull in full after the cheap screen (default %(default)s)")
    p.add_argument("--bin-minutes", type=int, default=detectors.BIN_MINUTES,
                   dest="bin_minutes")
    p.set_defaults(func=cmd_candidates)

    p = sub.add_parser("live", help="poll the live feeds at full rate (component A4)")
    p.add_argument("--minutes", type=int, default=0,
                   help="0 runs until stopped (default %(default)s)")
    p.add_argument("--poll-seconds", type=int, default=live.POLL_SECONDS,
                   dest="poll_seconds")
    p.set_defaults(func=cmd_live)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
