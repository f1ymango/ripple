# Notes from Data for other owners

Things Data (components A and E) found while working on its own files that
touch someone else's. **Nothing in your files has been changed.** Each note
says what we found, where the proof is, and what we suggest. Pick them up when
you are next in that code; strike a note through when it is done.

## 29 Sep 2026

### For the Lead

**1. One corridor road list (README open decision).** Data's side is ready:
`CORRIDOR_ROAD_NAMES` in [src/loaders/corridor.py](../src/loaders/corridor.py),
English and Chinese. Every Chinese name is copied from TD's own detector list
(`road_tc` in `data/detectors.csv`), and a test keeps it that way. Suggested
change in `src/reader/reader.py`: drop its own `CORRIDOR_ROADS` and
`from src.loaders.corridor import CORRIDOR_ROAD_NAMES`. What changes for the
Reader if you do:

- **Stubbs Road** drops out. It is in the Reader's list only and is not in the
  corridor inventory (docs/02-data.md §5). If it belongs, tell Data and we add
  it to the shared list and to the loaders' screening together.
- **華富道** (Wah Fu Road) comes in; the Reader's list has the English name only.
  No effect on messages that carry English, which is all of them so far.
- Then run `tests/test_reader.py::test_scope_comes_from_the_corridor_road_list`
  and close the open decision in the README.

The loaders' own screening (`CORRIDOR_ROADS`) stays broader on purpose: it
also matches "wah fu", "wong nai chung gap" and "aberdeen police station", and
does not drop "(X bound)" brackets. A false positive only adds a row to the
shortlist; a false negative loses an incident.

**2. `data/candidates.md` predates two bug fixes.** The screen used to accept
public holidays as ordinary days, and never checked control days before
`--start` for incidents. The demo incident is re-checked and unchanged
([results/data/candidates_2026-05-15.md](../results/data/candidates_2026-05-15.md)).
The other rows are not. If the backup (IN-26-06391) or the ranking is needed
again, regenerate the full table (over an hour on a fresh cache):

    python -m src.loaders.fetch candidates --start 2026-03-22 --end 2026-09-21

Rows likely to move: IN-26-04482 (the Friday a week before it was Tuen Ng,
19 Jun), IN-26-03639 (it happened on a holiday, 25 May), and IN-26-02105,
IN-26-02398, IN-26-02316, IN-26-02266 and IN-26-02349 (at least one ordinary
day before 22 Mar, never checked). IN-26-06391, the backup, is not among them.

**3. Command lists.** `CLAUDE.md` and `AGENTS.md` could list the new data
commands: `fetch holidays`, `fetch bin-survival` and `fetch lane-evidence`
(usage at the top of [src/loaders/fetch.py](../src/loaders/fetch.py)).

### For Simulation

**4. Which lane to close first for IN-26-03365 (Data's proposal).** The
**slow lane** of the Wong Chuk Hang Road flyover eastbound, at AID01104. Proof:
[results/data/lane-evidence_AID01104_20260515-0840_0920.md](../results/data/lane-evidence_AID01104_20260515-0840_0920.md).

- 08:54:00–09:00:00: the slow lane carried no vehicle in 5 archived readings in
  a row while the fast lane crawled past at 3–9 km/h (occupancy up to 47%). The
  last slow-lane vehicles were in the 08:50:30 reading; the archive has nothing
  for 08:51–08:53. On 8 May and 24 Apr this happened in 1 reading of 30 each.
- From 09:00:30 both lanes carried almost nothing (2 vehicles at 09:09 in the
  slow lane, 4 around 09:14 in the fast lane): effectively a full closure long
  before TD's "all lanes" at 09:36.
- The raw files report a measured occupancy of 0 for those empty readings, not
  the -1 "not measured" marker, so the slow lane was empty over the loop, not
  holding a standing queue.
- AID01105, the other flyover detector, is missing from the feed that morning,
  so AID01104 is the only lane-by-lane view of the flyover.

This is about which lane. When each phase starts in the replay (detector onset
or TD's message times) stays your call with the Lead, as in
`data/demo_shortlist.md`.

**5. Calibration thresholds (Data + Simulation).**
[results/data/bin-survival_20260515-0755_1035.md](../results/data/bin-survival_20260515-0755_1035.md)
reproduces your 242 usable count bins before 08:55 at 40% / 90%.

- Coverage comes in steps (a bin holds whole archived minutes): 30% adds 7 bins,
  20% adds 56 (298 of 336), 75% instead of 90% for lane readings adds none.
- Low- and high-coverage bins differ by 0.2 km/h in mean speed before the
  incident, so the 20% bins are the same traffic measured less precisely
  (one sampled minute, scaled up five times), not different traffic.
- Suggestion: keep 40% / 90% for the headline GEH figure, and show GEH at
  20% / 90% next to it as the sensitivity check. The validation slide then
  states both.

**6. Three detectors are missing from the feed on 15 May, 07:55–10:35:**
AID01105, AID01220 and TDSSPWR20002. No readings at all, so no GEH or speed
target for them that morning. They show as `coverage_pct` 0 like an archive
gap, but it is a feed outage.

### For Visuals

**7.** On 15 May, AID01105, AID01220 and TDSSPWR20002 have no reading at all,
so the console draws them grey all morning. That is right, but for the Q&A:
those three were missing from TD's feed, not dropped by the archive.
