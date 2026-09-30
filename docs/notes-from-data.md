# Notes from Data for other owners

Things Data (components A and E) found while working on its own files that
touch someone else's. **Nothing in your files has been changed.** Each note
says what we found, where the proof is, and what we suggest. Pick them up when
you are next in that code; strike a note through when it is done.

## 30 Sep 2026

### For everyone: the ~15-link fallback for the 4 Oct go/no-go

**12. It is ready, and scored the way SUMO is.**
`python -m src.fallback.run --day 2026-05-15 --ordinary-day 2026-05-08 2026-04-24`
takes about 35 seconds ([replay](../results/fallback/replay_20260515.md),
[how it works](../src/fallback/README.md)). Pre-incident hour 07:55–08:55,
GEH < 5 on the usable 5-minute counts (40% / 90%) and speed MAPE on 5-minute
bins, as `src/twin/evaluate.py` scores SUMO:

| Scored on | GEH < 5 | Speed error |
|---|---|---|
| Fallback, all detectors | 97.1% of 242 bins | 16.6% (299 bins) |
| Fallback, detectors inside the chains | 97.1% of 205 bins | 17.8% (252 bins) |
| SUMO, 27 Sep diagnostic | 66.5% of 242 bins | 36.9% (296 bins) |

The four first detectors are fed 15 May's own counts, so "inside the chains" is
the fair figure for the fallback. Everything else in it, every join, exit and
speed, comes from the two ordinary Fridays. The six detectors that hold 57 of
SUMO's 81 misses (note 8) pass 10 of 10 bins each here, with the joins in place.

**13. The speed target is below what a model built from other mornings can
reach on 15 May.** Predicting every 5-minute speed on 15 May with the ordinary
Fridays' average at the same detector scores 16.6% (17.8% inside the chains):
the fallback's figure, to the decimal. It adds no error of its own before the
incident; the rest is how 15 May differed from an ordinary Friday. Two
detectors carry most of it: AID01106 ran at 8–19 km/h from 08:00 to 08:40
against an ordinary 24 km/h (35 on 8 May, 13 on 24 Apr), a 77% error, and
AID01216 ran at 15 km/h until 08:10, then 51–80, against an ordinary 28, a 66%
error. Without those two the error inside the chains is 12.1%. For the
validation slide: put the ~15% target, the result and this ordinary-mornings
figure side by side. To go lower, a model has to reproduce 15 May's own queues
at those two detectors.

**14. The incident: the queue starts on time, then runs too long, because
nobody diverts yet.** The model's queue reached AID01104 at 08:55 (observed
08:55), AID01103 at 09:00 (09:05), AID01102 at 09:10 (09:15) and AID01101 at
09:25 (09:50). After the 10:02 re-opening it has not cleared by 10:35; the
detectors cleared between 10:00 and 10:15. The detectors show why. While all
lanes were closed, 09:00–10:02, they still counted traffic that the model holds
still:

| Detector | Observed veh/h | Model veh/h |
|---|---|---|
| AID01101 | 1,084 | 352 |
| AID01102 | 457 | 86 |
| AID01103 | 519 | 0 |
| AID01104 | 21 | 0 |

AID01103's traffic left by the slip road before the flyover. And between
AID01101 and AID01102 traffic turned off: from 09:15 to 09:45 about 540
vehicles passed AID01101 at 56–66 km/h and about 180 crept past AID01102 in the
queue, while the 556 m between them holds about 230 stopped vehicles, so at
least about 130 left the road in between. In the model everyone waits for the
re-opening, so its incident figures (1,620 vehicle-hours of delay, a 1.6 km
queue plus 454 vehicles waiting to enter) are a no-diversion upper bound, not
numbers for the deck. The table above is the check for week 3's diversion.

**15. Data's recommendation for Sunday; the decision is the team's.** On the
pre-incident hour the fallback meets the GEH target and matches the speed floor
of note 13; the 27 Sep SUMO run meets neither. Unless a new SUMO run passes
85% GEH < 5 by Sunday, run week 3's plans on the fallback, and keep SUMO as a
side-by-side if it is fixed later. Diversion, which the fallback still needs,
is Data's week 3 task anyway (`docs/04-plan.md`, "parameter search over
diversion shares").

**16. For the interim report, §3 (Simulation and Impact).** A paragraph that
stays true whichever way Sunday goes: *"A simplified cell-transmission model of
the corridor's four detector chains, built from two ordinary Friday mornings,
reproduces the 15 May pre-incident hour with GEH < 5 on 97.1% of 242
five-minute counts and a 16.6% speed error. The same speed error results from
predicting that morning from the ordinary Fridays alone, against a target of
about 15%. It matches, within five minutes, when the detector at the incident
and the two behind it slowed down; without driver diversion, not yet modelled,
it overstates how far back the queue reaches and how long it lasts."* Source:
`results/fallback/replay_20260515.md`.

**17. For the Lead, if the switch happens.** `docs/03-architecture.md` §5
describes the fallback as "a simple queueing / BPR-style link model". It is a
cell transmission model instead, because a BPR link cannot hold a queue that
spills back from one link into the next, the incident's main effect. The
command lists of note 3 could add `python -m src.fallback.run`.

### For Simulation: the 27 Sep diagnostic (66.5% GEH < 5, 36.9% speed MAPE)

**8. Six detectors hold most of the GEH misses, and joining traffic has nowhere to start.**
57 of the 81 failing count bins are at AID01107, AID01110, AID01214, AID01217,
AID01218 and AID01221, where the twin carries 33–61% of the observed traffic
([diagnostic](../results/twin/may15-preincident-diagnostic.json)). The other 19
detectors already pass 158 of 182 bins (87%). Each of the six sits just after
a stretch where traffic joins the corridor, or (AID01214) at the start of the
westbound chain. `src/twin/make_routes.py` builds routes only from one
detector's edge to a later detector's edge, so traffic that really joins from a
side road has to be inserted at the next detector, in dense traffic. That fits
the 2,405 vehicles still waiting at 4,500 s.

Where traffic joins and leaves, 07:55–08:55, clear on 15 May, 8 May and 24 Apr
([flow balance](../results/data/flow-balance_20260515-0755_0855.md)):

- joins: +646 veh/h between AID01216 and AID01217 (tunnel, westbound); +637
  between AID01219 and AID01221 (AID01220 has no data); +884 between AID01108
  and AID01109; +657 between AID01109 and AID01110; +356 between AID01102 and
  AID01103. Also +342 between AID01106 and AID01107 on 15 May and 24 Apr, not
  on 8 May.
- exits: −674 between AID01103 and AID01104; −690 between AID01214 and
  AID01215; −496 just after the tunnel westbound; −427 between AID01222 and
  AID01223.

Suggestion: add entry routes from the side roads in those stretches, and exit
routes to them, sized from the 15 May column. The ordinary days are the check
that each junction is real. If the six detectors reached 9 of 10 bins each, the
overall score would be about 88% (212 of 242).

**9. Every simulated car is capped at 60 km/h.** The vType in `make_routes.py`
has `maxSpeed="16.7"` (m/s), and `fit_demand.py` copies it to every fitted
flow. In light traffic on ordinary Friday mornings the median driver is faster
than 60 km/h at 14 of 25 detectors, and 90% or more of drivers are at AID01108,
AID01216, AID01217 and TDSSPWR20003
([free-flow speeds](../results/data/free-flow_20260508_20260424_0730-1100.md)).
Suggestion: lift the cap and take desired speeds from that table.

**10. The speed error is likely dominated by a few slow detectors.** MAPE
averages percentage errors, so one bin where the road ran at 18 km/h and the
twin at 55 counts as a 200% error, as much as twenty bins that are each 10% off.
Your own `calibration.json` has AID01106 at 8–40 km/h, AID01110 at 24–44 and
AID01214 at 28–39 in all twelve pre-incident bins: recurring queues. Sorting the
`speed_bins` that `evaluate.py` writes by error will show whether these three
carry the 36.9%. If they do, the fix is the queues (the joins in note 8), not
speeds in general.

**11. When a run counts (E's side, for the team to agree).** Proposal: a run's
GEH and MAPE are reported only if, at the end of the scored window, under 1% of
loaded vehicles are still waiting to enter and there are no wrong-lane
teleports. The 27 Sep run had 13% waiting (2,405 of 17,922), so its score
measures the entry queue as much as the road.

The ~15-link fallback (notes 12–17) takes its joins and exits from the same
flow calculation, on the two ordinary Fridays only.

## 29 Sep 2026

### For the Lead

**1. Shared corridor road list — resolved 30 Sep.** The Reader imports
`CORRIDOR_ROAD_NAMES` from [src/loaders/corridor.py](../src/loaders/corridor.py)
instead of keeping its own copy. **Stubbs Road stays in scope** because
docs/02-data.md §5 names it as an over-hill alternative; it was added to the
shared list and loaders' incident screening together. **華富道** (Wah Fu Road)
comes into Reader scope from TD's `road_tc` detector name. The Reader scope
test covers both and the duplicate-list decision is closed in the README.

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
