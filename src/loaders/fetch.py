"""Command line for the data layer (component A).

    python -m src.loaders.fetch corridor
    python -m src.loaders.fetch holidays
    python -m src.loaders.fetch prefetch  --feed stn --start 2026-03-22 --end 2026-09-21
    python -m src.loaders.fetch prefetch  --feed stn_tc --start 2026-03-22 --end 2026-09-21
    python -m src.loaders.fetch prefetch  --feed stn_sc --start 2026-03-22 --end 2026-09-21
    python -m src.loaders.fetch incidents --start 2026-03-22 --end 2026-09-21
    python -m src.loaders.fetch detectors --start 2026-09-21T07:00 --end 2026-09-21T10:00
    python -m src.loaders.fetch twin-detectors --start 2026-05-15T08:00 --end 2026-05-15T10:30
    python -m src.loaders.fetch bin-survival --start 2026-05-15T07:55 --end 2026-05-15T10:35 \
        --split 2026-05-15T08:55
    python -m src.loaders.fetch lane-evidence --detector AID01104 --start 2026-05-15T08:40 \
        --end 2026-05-15T09:20 --ordinary-day 2026-05-08

`prefetch` is the long one and the only one that needs to run unattended: it
fills data/raw/ in parallel and is resumable, so a dropped connection costs
the snapshots in flight and nothing else. Everything afterwards reads the
cache, which is why the other commands take seconds.
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from src.loaders import (archive, bin_survival, candidates, corridor, detectors, holidays,
                         incidents, lane_evidence, lanes, live, twin_export)
from src.loaders.common import HK, MIN_DURATION_MIN


def _bin_width(text: str) -> int:
    """--bin-minutes: a positive divisor of 60, refused at the command line."""
    try:
        minutes = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a whole number of minutes: {text!r}") from None
    if minutes <= 0 or 60 % minutes:
        raise argparse.ArgumentTypeError(
            f"must be a positive divisor of 60 (5, 10, 15, 20, 30, 60), got {minutes}")
    return minutes


def _moment(text: str) -> dt.datetime:
    """'2026-09-21' or '2026-09-21T07:00' -> a Hong Kong datetime."""
    return dt.datetime.fromisoformat(text).replace(tzinfo=HK)


def cmd_corridor(args) -> None:
    rows = corridor.build_table()
    print(f"wrote {len(rows)} corridor detectors to {corridor.OUT_PATH}")
    for leg in ("main_eastbound", "main_westbound", "western_alternative"):
        print(f"  {leg:22} {len([r for r in rows if r['leg'] == leg])}")


def cmd_holidays(args) -> None:
    rows = holidays.download()
    years = sorted({r["date"][:4] for r in rows})
    print(f"wrote {len(rows)} general holidays ({', '.join(years)}) to {holidays.OUT_PATH}")


def cmd_prefetch(args) -> None:
    stamps = archive.list_versions(args.feed, args.start, args.end)
    print(f"{args.feed}: archive lists {len(stamps)} snapshots for {args.start}..{args.end}")
    counts = archive.prefetch(args.feed, stamps, workers=args.workers)
    not_served = counts["missing"] + counts["known_missing"]
    if not_served:
        # About a third of listed detector versions 404 persistently. Expected,
        # not a bug, but the number belongs in the run log.
        print(f"note: {not_served} listed snapshots are not actually served "
              f"({not_served / max(len(stamps), 1) * 100:.0f}% of the window)")
    if counts["failed"]:
        print(f"note: {counts['failed']} failed transiently -- run the same command "
              f"again to retry only those")


def cmd_incidents(args) -> None:
    rows = incidents.load(args.start, args.end)
    if not rows:
        print(f"no incidents in the archived STN snapshots for {args.start}..{args.end}")
        return
    out = Path(f"data/incidents_{args.start}_{args.end}.csv")
    incidents.write_csv(rows, out)
    on_corridor = [r for r in rows if r["corridor_road"]]
    usable = incidents.usable_corridor_incidents(on_corridor)
    print(f"{len(rows)} incidents -> {out}")
    print(f"  on the corridor:            {len(on_corridor)}")
    print(f"  with a clear NEW and CLOSED >= {MIN_DURATION_MIN} min apart: {len(usable)}")
    for row in usable:
        print(f"    {row['incident_number']}  {row['new_at'][:16]}  "
              f"{row['duration_min']:>4} min  {row['location_en']} ({row['corridor_road']})")


def cmd_detectors(args) -> None:
    start, end = _moment(args.start), _moment(args.end)
    rows = detectors.load_window(start, end)
    if not rows:
        print("no detector readings in that window -- the archive's latest day is yesterday")
        return
    # Every slot of every corridor detector, empty ones included, so the CSV
    # is a series anyone can line up by position.
    binned = detectors.bin_window(rows, args.bin_minutes, start=start, end=end)
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
    rows = candidates.shortlist(args.start, args.end, args.bin_minutes)
    if not rows:
        print("no usable corridor incidents in that window -- widen the dates")
        return
    path = candidates.write_markdown(rows, Path(args.out))
    print(f"\n{len(rows)} candidates -> {path}")
    print("Top of the list (the team picks from the whole table):")
    for row in rows[:args.top]:
        print(f"  {row['incident_number']}  score {row['score']:<5} {row['duration_min']:>4} min  "
              f"{len(row['credited'])} detectors credited  {row['location_en']} "
              f"({row['lane_wording'] or 'lanes not stated'})")


def cmd_lanes(args) -> None:
    summary, conclusion, bands = lanes.analyse(args.detector)
    if not summary:
        print(f"no cached readings for {args.detector} -- run `prefetch` or `live` first")
        return
    out = lanes.OUT_DIR / f"lane_identity_{args.detector}.md"
    print(lanes.report(args.detector, summary, conclusion, out, bands))
    print(f"written to {out}")


def cmd_twin_detectors(args) -> None:
    start, end = _moment(args.start), _moment(args.end)
    out = Path(args.out)
    try:
        doc = twin_export.build(start, end, args.bin_minutes, min_coverage_pct=args.min_coverage,
                                keep_from=out)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from None
    twin_export.write(doc, out)
    s = twin_export.summary(doc)
    print(f"{s['detectors']} detectors x {s['slots_per_detector']} slots of {args.bin_minutes} min "
          f"-> {out}")
    print(f"  with a count usable for calibration: {s['with_count']} of {s['observations']}")
    print(f"  with a measured speed:               {s['with_speed']} of {s['observations']}")
    print(f"  with both (what the twin compares):  {s['with_both']} of {s['observations']}")
    print(f"Observation grid begins {start:%Y-%m-%d %H:%M}; set "
          "observation_start_sim_seconds to its offset after any warm-up, and "
          "time the incident against the detector-observed queue onset.")


def cmd_bin_survival(args) -> None:
    start, end, split = _moment(args.start), _moment(args.end), _moment(args.split)
    if not start < split < end:
        raise SystemExit("error: --split must fall inside the window")
    doc = bin_survival.build(start, end, split)
    command = (f"python -m src.loaders.fetch bin-survival --start {args.start} "
               f"--end {args.end} --split {args.split}")
    md, js = bin_survival.write(doc, command)
    default = doc["thresholds"][0]
    print(f"{doc['archive']}")
    print(f"usable at {default['min_coverage_pct']}% / {default['min_lane_completeness_pct']}%: "
          f"{default['before']} of {doc['slots']['before']} before the split, "
          f"{default['after']} of {doc['slots']['after']} from it -> {md}, {js}")


def cmd_lane_evidence(args) -> None:
    start, end = _moment(args.start), _moment(args.end)
    days = [dt.date.fromisoformat(d) for d in args.ordinary_day]
    doc = lane_evidence.build(args.detector, start, end, days)
    if not doc["incident"]["readings"]:
        raise SystemExit(f"error: no complete readings for {args.detector} in that window")
    command = (f"python -m src.loaders.fetch lane-evidence --detector {args.detector} "
               f"--start {args.start} --end {args.end} --ordinary-day {' '.join(args.ordinary_day)}")
    md, js = lane_evidence.write(doc, command)
    for lane, s in doc["incident"]["summary"].items():
        print(f"  {lane:14} empty while another moved in {s['empty_while_moving']} of "
              f"{s['readings']} readings, longest run {s['longest_run']}")
    print(f"-> {md}, {js}")


def cmd_live(args) -> None:
    live.run(minutes=args.minutes, poll_seconds=args.poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("corridor", help="write data/detectors.csv").set_defaults(func=cmd_corridor)
    sub.add_parser("holidays", help="write data/hk_holidays.csv, the official list the "
                                    "candidate screen skips").set_defaults(func=cmd_holidays)

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
    p.add_argument("--bin-minutes", type=_bin_width, default=detectors.BIN_MINUTES,
                   dest="bin_minutes",
                   help="bin width; 5 for incident dynamics, 15 for demand "
                        "calibration where a stable count beats fine timing "
                        "(default %(default)s)")
    p.add_argument("--min-coverage", type=int, default=detectors.MIN_COVERAGE_PCT,
                   dest="min_coverage",
                   help="sampling-fraction threshold for the calibration export "
                        "(default %(default)s%%; see docs/02-data.md section 7)")
    p.set_defaults(func=cmd_detectors)

    p = sub.add_parser("candidates",
                       help="shortlist demo incidents on detector evidence against ordinary days")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--top", type=int, default=6,
                   help="how many to print; the table has them all (default %(default)s)")
    p.add_argument("--out", default=str(candidates.OUT_PATH),
                   help="where the table goes (default %(default)s); point a one-day "
                        "re-check elsewhere so it never replaces the full table")
    p.add_argument("--bin-minutes", type=_bin_width, default=detectors.BIN_MINUTES,
                   dest="bin_minutes")
    p.set_defaults(func=cmd_candidates)

    p = sub.add_parser("twin-detectors",
                       help="write the twin's observed data, one row per slot (A -> C)")
    p.add_argument("--start", required=True,
                   help="YYYY-MM-DDTHH:MM on a slot boundary: the simulation's time 0")
    p.add_argument("--end", required=True, help="YYYY-MM-DDTHH:MM on a slot boundary")
    p.add_argument("--bin-minutes", type=_bin_width, default=detectors.BIN_MINUTES,
                   dest="bin_minutes", help="the twin expects 5 (default %(default)s)")
    p.add_argument("--min-coverage", type=int, default=detectors.MIN_COVERAGE_PCT,
                   dest="min_coverage")
    p.add_argument("--out", default=str(twin_export.OUT_PATH))
    p.set_defaults(func=cmd_twin_detectors)

    p = sub.add_parser("bin-survival",
                       help="how many bins each calibration threshold leaves (-> results/data/)")
    p.add_argument("--start", required=True, help="YYYY-MM-DDTHH:MM on a slot boundary")
    p.add_argument("--end", required=True, help="YYYY-MM-DDTHH:MM on a slot boundary")
    p.add_argument("--split", required=True,
                   help="YYYY-MM-DDTHH:MM: pre-incident before it, incident from it")
    p.set_defaults(func=cmd_bin_survival)

    p = sub.add_parser("lane-evidence",
                       help="one detector lane by lane, incident day vs ordinary days "
                            "(-> results/data/)")
    p.add_argument("--detector", required=True)
    p.add_argument("--start", required=True, help="YYYY-MM-DDTHH:MM, Hong Kong time")
    p.add_argument("--end", required=True, help="YYYY-MM-DDTHH:MM, Hong Kong time")
    p.add_argument("--ordinary-day", nargs="+", required=True, dest="ordinary_day",
                   help="YYYY-MM-DD, one or more: same clock times for comparison")
    p.set_defaults(func=cmd_lane_evidence)

    p = sub.add_parser("lanes", help="evidence on which physical lane Middle Lane 1 is")
    p.add_argument("--detector", default="AID01217",
                   help="4-lane detector to analyse (default %(default)s, the only "
                        "4-lane one on our corridor)")
    p.set_defaults(func=cmd_lanes)

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
