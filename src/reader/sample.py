"""Collect real Special Traffic News (STN) messages to test the Incident Reader on.

Reads every archived snapshot of the STN feed between two dates through the
data layer's archive cache (src/loaders/archive.py), keeps each distinct
message once, picks one message per incident, and writes a seeded shuffle of
them to a JSONL file. An existing file is never overwritten.

Two sets are made this way:

    # dev set: read freely while working on the prompt
    python -m src.reader.sample --start 2026-09-15 --end 2026-09-21 --n 20 \
        --out data/labelled_incidents/messages.jsonl

    # gold set behind the accuracy number: never looked at while tuning
    python -m src.reader.sample --start 2026-06-22 --end 2026-09-21 --n 80 --corridor 20 \
        --exclude data/labelled_incidents/messages.jsonl \
        --out data/labelled_incidents/gold_messages.jsonl

The gold set has two strata. `citywide` is a random sample of incidents off
the Aberdeen corridor; `corridor` is a separate random sample of incidents
that name a corridor road, because they are too rare (about two a week) to
turn up in a random sample. Accuracy is reported for each.

Excluded from the gold set, by incident: everything in the --exclude files,
and the prompt's worked examples (named "(message N)" in prompts/system.md).
Which messages are picked is prefix-stable: --n 80 and --n 100 with the same
seed and dates pick the same first 80 citywide incidents.

Full incident timelines (NEW -> UPDATED -> CLOSED) are component A2's job;
this script only gathers inputs for the Reader.
"""
import argparse
import json
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from src.loaders import archive
from src.reader import reader


def parse_messages(xml_bytes: bytes) -> list[dict]:
    """Every <message> in one snapshot, as {field name: text}, with '' for empty fields."""
    root = ET.fromstring(xml_bytes)
    return [{field.tag: (field.text or "").strip() for field in message}
            for message in root.findall("message")]


def distinct_messages(start: str, end: str) -> list[dict]:
    """Each message in the window once, as {"archive_time": ..., "stn": {...}}.

    Every message has its own ID and its text never changes, but its status can
    flip later (e.g. UPDATED -> CLOSED) as the incident moves on. Keep the
    version first seen, i.e. the status the message was issued with.

    Snapshots the archive does not serve (a recorded 404) or serves truncated
    are skipped and counted: the same cache always gives the same set. A
    download that fails for now stops the run instead, since skipping it would
    make the pick depend on the archive's mood; run the same command again.
    """
    timestamps = archive.list_versions("stn", start, end)
    distinct: dict[str, dict] = {}
    not_served, truncated = 0, []
    for timestamp in timestamps:
        try:
            snapshot = parse_messages(archive.fetch("stn", timestamp))
        except archive.NotArchived:
            not_served += 1
            continue
        except ET.ParseError:
            truncated.append(timestamp)
            continue
        for stn in snapshot:
            distinct.setdefault(stn["ID"], {"archive_time": timestamp, "stn": stn})
    print(f"{len(timestamps)} snapshots listed, {not_served} not served, "
          f"{len(truncated)} truncated {truncated or ''}-> {len(distinct)} distinct messages")
    return list(distinct.values())


def pick(messages: list[dict], n: int, seed: int) -> list[dict]:
    """One message per incident, shuffled with a fixed seed, first n kept."""
    by_incident: dict[str, list[dict]] = {}
    for m in sorted(messages, key=lambda m: int(m["stn"]["ID"])):
        by_incident.setdefault(m["stn"]["INCIDENT_NUMBER"], []).append(m)
    rng = random.Random(seed)
    chosen = [rng.choice(by_incident[number]) for number in sorted(by_incident)]
    rng.shuffle(chosen)
    return chosen[:n]


def worked_example_ids() -> set[str]:
    """Message IDs of the prompt's worked examples, which the prompt names as '(message 146439)'."""
    return set(re.findall(r"\(message (\d+)\)", reader.SYSTEM_PROMPT))


def excluded_incidents(messages: list[dict], exclude_files: list[Path]) -> set[str]:
    """Incidents that must stay out: those in the exclude files and the prompt's worked examples."""
    incidents = set()
    for path in exclude_files:
        for line in path.read_text(encoding="utf-8").splitlines():
            incidents.add(json.loads(line)["stn"]["INCIDENT_NUMBER"])
    examples = worked_example_ids()
    incidents |= {m["stn"]["INCIDENT_NUMBER"] for m in messages if m["stn"]["ID"] in examples}
    return incidents


def stratified(messages: list[dict], n: int, n_corridor: int, excluded: set[str],
               seed: int) -> list[dict]:
    """n citywide + n_corridor corridor messages, one per incident, never an excluded incident."""
    examples = worked_example_ids()
    pool = [m for m in messages if m["stn"]["INCIDENT_NUMBER"] not in excluded
            and m["stn"]["ID"] not in examples]
    on_corridor = [m for m in pool if reader.names_corridor_road(m["stn"])]
    corridor_incidents = {m["stn"]["INCIDENT_NUMBER"] for m in on_corridor}
    citywide = [m for m in pool if m["stn"]["INCIDENT_NUMBER"] not in corridor_incidents]

    chosen = ([{"stratum": "citywide"} | m for m in pick(citywide, n, seed)]
              + [{"stratum": "corridor"} | m for m in pick(on_corridor, n_corridor, seed)])
    for stratum, wanted in (("citywide", n), ("corridor", n_corridor)):
        got = sum(m["stratum"] == stratum for m in chosen)
        if got < wanted:
            print(f"note: only {got} {stratum} incidents in the window, not {wanted}")
    random.Random(seed).shuffle(chosen)  # so the labeller meets the strata mixed together
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", required=True, help="first day, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="last day, YYYY-MM-DD (archive ends yesterday)")
    parser.add_argument("--n", type=int, default=20, help="citywide messages to keep")
    parser.add_argument("--corridor", type=int, default=0,
                        help="corridor messages to add, from incidents that name a corridor road")
    parser.add_argument("--exclude", type=Path, action="append", default=[],
                        help="a messages .jsonl whose incidents must not be picked (repeatable)")
    parser.add_argument("--out", type=Path, required=True, help="the .jsonl to write")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"{args.out} exists and is never overwritten; delete it first if you mean to")

    messages = distinct_messages(args.start, args.end)
    print(f"{len({m['stn']['INCIDENT_NUMBER'] for m in messages})} incidents")
    if args.corridor or args.exclude:
        excluded = excluded_incidents(messages, args.exclude)
        print(f"{len(excluded)} incidents excluded (--exclude files and the prompt's worked examples)")
        chosen = stratified(messages, args.n, args.corridor, excluded, args.seed)
    else:  # how the dev set was made, kept so it can be rebuilt exactly
        chosen = pick(messages, args.n, args.seed)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as f:
        for message in chosen:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")
    print(f"wrote {len(chosen)} messages to {args.out}")


if __name__ == "__main__":
    main()
