# Notes from Data for other owners

Things Data (components A and E) found while working on its own files that
touch someone else's. **Nothing in your files has been changed.** Each note
says what we found, where the proof is, and what we suggest. Pick them up when
you are next in that code; strike a note through when it is done.

## 13 Oct 2026

All from [the 13 October note](evaluator-replay-v3-2026-10-13.md); section 6
of the [go/no-go review](evaluator-p0-go-no-go-2026-10-09.md) sums it up.

### For Simulation

**33. The detectors count too few vehicles in slow traffic.** AID01106 and
AID01107 have no junction between them in TD's Road Network, yet AID01106
counts 55% of AID01107's vehicles under 10 km/h, 73% at 10 to 20 and 80% at 20
to 30, and 96 to 102% from 30 km/h up (1,598 bins on 48 days, not 15 May;
`python -m src.loaders.fetch count-bias`). Two things follow for you.
`evaluate.py` scores whatever count the observations carry; replay version 3
withholds the 51 bins on 15 May measured under 30 km/h in its observations
file, so nothing in your code changes. And the flow balance's joins and exits
come from ordinary mornings when AID01106 often queues: the "+58 veh/h"
between AID01106 and AID01107, where there is no junction, is this bias.

**34. Where the tunnel side went.** Your three candidates (note 31), checked
against TD's Road Network: no road from Aberdeen or Ap Lei Chau reaches the
tunnel without AID01103's centreline, and the only road joining between
AID01103 and the fork is Yip Kan Street, from Wong Chuk Hang itself. So a
hidden join from Ap Lei Chau is ruled out. What is left is mostly measurement: AID01103 ran at 6 to 14 km/h,
so its 433 was about 600 to 790, and the 10 October replay's 7 km/h crawl held
the detour to the low count. Without the crawl the closure-phase GEH is 91.8%
(83.15% before). The road under the flyover's lanes (OSM gives one lane off
the fork and one lane back on) and its two signals are still unverified, and
they decide how much the detour passes; a site or Street View check would
settle them.

**35. The north merge: the data support your warning.** On 36 congested
mornings (AID01109 at 30 to 45 km/h) the join loses 0.51 vehicles for every
extra main-line vehicle (`python -m src.loaders.fetch merge-tradeoff`). The
as-built ramp gives about 0.40 but starves the ramp before the crash; the
main-line join (correction 2) gives 0. Version 3 runs every plan under both
as bounds. A merge built to reproduce 0.51 at the observed level would
replace both; that is a network change, so it is yours to decide.

### For the Lead

**36. Replay version 3, and what a go needs now.** P0 meets the count target
in every phase and every seed (93.5%; during the closure 91.8%) and misses the
speed target (24.8%), almost all of it on the queue at AID01102 and AID01103.
On the stand-ins, P2 saves 2.3 to 2.4% (paired over six seeds, under both
ramp bounds) and P1 shows no saving. What is left is three decisions, not
data: the slow-count rule, how the queue's speed is scored, and whether the
teleports at the instant a lane shuts count. Section 9 of the note sets them
out. If they are accepted, run your plans on
`sim/scenarios/evaluator_IN-26-03365_replay-v3.json` and report a ranking only
if it holds in every cell of the grid in section 8.

## 10 Oct 2026

All from [the 10 October note](evaluator-replay-fixes-2026-10-10.md); the
[go/no-go review](evaluator-p0-go-no-go-2026-10-09.md) is updated with it.

### For Simulation

**30. Two corrections to the replay need your review, and they change the
go/no-go evidence.** Thank you for section 4: your rows review `3b67a1b`,
from before these corrections, and the review now carries your text as you
wrote it, with a short follow-up table for the changes.
1. Drivers turned away from the shut flyover now take Wong Chuk Hang Road and
   keep their route (`closure.detour`). SUMO had sent 96 Canal Road-bound
   drivers into Happy Valley streets, which jammed until the end of the run
   and blocked the tunnel exit; AID01108 counted 11 a bin in the model against
   96 real.
2. The join between AID01108 and AID01109 enters on the main line. On ramp
   `46766432` the merge held vehicles up to 27 minutes from 07:45, before the
   crash, while AID01109 shows the real ramp let them in.
P0 now meets both targets in all six seeds (89.45%, 14.44% for seed 2026).
With signs that plans cannot inherit it scores 16.29%. Section 4 of the review
has two new rows for these corrections and one for the drivers-leave rule.

**31. Where did the extra tunnel traffic come from?** During the closure
AID01106 counted 90 a bin, the model sends 47, and only 28 to 50 passed
AID01103. It cannot be the drivers who left at the Aberdeen exits: in the
network no road leads from them to the tunnel without the fork. That leaves
your three: a join between AID01103 and the fork hidden by net flows (for
instance from Ap Lei Chau), more capacity under the flyover, or where
AID01106 stands. This gap is now the main reason plans cannot be compared.

### For the Lead

**32. The 8 October plan gains were artefacts.** Corrected, both rehearsal
plans add delay in all six seeds (paired, P1 +8.5%, P2 +4.2% at 50%): advised
drivers stop leaving at the exits and queue for the one detour, which is
full. With the ramp's merge kept instead of correction 2, P2 saves 2.7%, so
the ramp still decides P2's sign. Data and Simulation agree on no-go for
comparing plans by 14 October (review section 2 and section 4). For your
plans: in this model a plan that only points drivers at Wong Chuk Hang Road
adds delay inside the network.

## 9 Oct 2026

### For the Lead, answering your 9 Oct review of the E branch

**27. P0 go/no-go: Data says no-go for comparing plans by 14 October.**
[The review](evaluator-p0-go-no-go-2026-10-09.md) covers each check you
listed. Three findings would change which plan comes out best: the tunnel-side
flow (36 of 65 failing count bins), the on-ramp backlog (26% of P0's delay,
present with no closure), and the refreshed speed signs, which P1 and P2
inherit from the do-nothing morning. Simulation's half of the review is a
blank table in section 4. Until it is filled in, please treat the
observed-only scope ([#54](https://github.com/f1ymango/ripple/pull/54)) as
staying.

**28. Your two integration fixes are done.**
1. The v2 context no longer names
   `sim/scenarios/evaluator_IN-26-03365_signals.add.xml`, which was never
   committed. The +20 s at Tong Bin Lane is marked an assumed network control
   in the context's table and in the scenario, so every run report says so. A
   test fails if any plan context names a missing source.
2. Every `run_id` now ends with the plan set (`--plan-set`, required), and the
   rehearsal results moved to `results/evaluator-rehearsal/`. `results/runs/`
   is empty, kept for your plans. `batch` no longer skips an existing
   `run_id`; it keeps a result only if that result binds the same plans,
   generation inputs and simulation inputs, and stops otherwise. Suggested
   name for your set: `lead-v1`. The command is in section 5 of the review.

**29. The E branch for its own PR.** `data/evaluator-e-oct07` sits on `main`
and carries none of #46's commits. Opened separately from #46.

## 8 Oct 2026

All four come from [the replay note](evaluator-replay-2026-10-08.md).

### For the Lead

**20. How to word the validation.** E's P0 replay of IN-26-03365 meets both
targets over the whole run: GEH < 5 in 89.29% of count bins, speed error
14.54%. But on 21 of the 25 detectors the speed is an input, refreshed from
the detector's own previous quarter-hour. With ordinary-morning speeds only it
is 16.75%, and on the crashed stretch, where the model makes the speed, 31%.
Suggested sentence for the slide is in section 2 of the note. Your call which
figure leads.

**21. D's plans and the seed.** E now runs P1 and P2. So far only on stand-ins
from `src/evaluator/rehearsal_plans.py`, built on
[a second context](../data/plan-context/IN-26-03365_first-report-v2.md) that
offers D one junction. Two things for you: generate D's own set from that
context, and decide whether the briefing compares one seed or several. The
stand-ins lower delay by 1 to 5% and P0 alone moves 3% from seed to seed, so
one seed cannot rank them. E refuses a plan that uses public transport.

### For Simulation

**22. The tunnel side of the flyover.** During the closure AID01106 and
AID01107 counted 895 and 824 vehicles in ten bins while AID01103, before the
fork, counted 433. So about half the tunnel's traffic did not come over the
flyover, and the model has almost none of it: it sends 330 and 328. That is
36 of P0's 65 failing count bins. Two things could explain it and both are
yours to check: traffic joining after the flyover that the demand lacks, or
AID01106 standing somewhere other than edge `1198101443` (your map review
already flags it). The on-ramp at `46766432` is the other loose end: 448.7 of
P0's 1,702 vehicle-hours of delay are vehicles waiting to enter there, and it
queues with no closure too. In P1 at 70% compliance that one ramp cancels the
plan's whole gain.

**23. The scene assumptions need your review, as the 7 Oct P0 setup did.**
E now sets the speeds around the crash: 4.7 km/h past it while one lane was
shut, 7 km/h on the last 330 m while both were, and one lane's worth at
22 km/h for 20 minutes after 10:00. Vehicles are 6.5 m long. Each is in
[the scenario](../sim/scenarios/evaluator_IN-26-03365_replay.json) with its
evidence, and section 3 of the note shows the score without each. The
20 minutes after reopening are the weakest: AID01104 shows both flyover lanes
in use from 10:04, so E's closed lane only stands for a narrowing at the
scene. None of your files is changed.

### For the Lead, from testing E's edges (8 Oct, later)

**24. Far from the morning's own clearance, P0 fails validation, so F and
the console will not rank plans there.** E scores P0 against the real morning.
At 66 minutes, the clearance IN-26-03365 had, P0 meets both targets; at 80 it
still does (86.82%, 14.61%). At 5 minutes the same P0 scores 38.98% speed
error, because the twin no longer has the morning's closure, and every P1 and
P2 at that clearance inherits the fail. So the "plans × compliance ×
clearance" batch in CLAUDE.md can only be ranked near the observed clearance,
and a what-if P0 passing or failing says little about the model either way.
One reading of the contract is that the model is validated once, at the
observed clearance, and each what-if P0 points to that. That would change what
`validation` means in `result.json`, so it is your call, not ours.

**25. The E commands in CLAUDE.md are not E's.** `python -m src.evaluator.run
--incident ...` and `python -m src.evaluator.batch --incident ...` do not
exist. E takes `--plans`, `--plan`, `--scenario`, `--compliance` and
`--clearance`; [E's README](../src/evaluator/README.md#run-it) has the
commands that work.

### For Visuals

**26. The console keys a comparison by compliance, clearance and seed only.**
Two scenarios with different assumptions but the same three values look like
one, and the console withholds the comparison ("More than one P0 run has this
scenario"). That happened on 8 Oct: the 7 Oct P0 sat in `results/runs/` beside
the replay's. Data moved the old results to `results/evaluator-diagnostics/`,
and E's README now says to keep one plan set on one scenario per folder. If you want
the console to hold several, the sidecar's `simulation_inputs` tells scenarios
apart; `run_id` ends with the scenario's label too.

## 4 Oct 2026

### For Simulation and the Lead

**18. SUMO on flow-balance demand passes the count target on the no-closure hour.**
A second way to build the twin's inputs, in new files beside yours; none of
your files is changed. 15 May, same 242 count bins and 299 speed bins as your
packet: GEH < 5 96.7% (was 66.9%), speed error 15.7% (was 41.4%), 238 vehicles
waiting (was 2,390), no teleport (was 53). On 15 other day-and-hour cases,
nothing retuned, GEH passes on all 15 and speed error is at or under 15% on 5.
Method, the two network patches, every assumption, what the scores hide and
the commands: [sumo-flow-balance-2026-10-04.md](sumo-flow-balance-2026-10-04.md).
To review before it is relied on: the toll-plaza connections, the cut of edge
1198101443, the entry-road rule at AID01214, the driver settings, and the two
signals at the Wong Nai Chung Gap flyover merge (one on-ramp there still holds
1–6% of vehicles outside).

**19. A rule for `unspecified` lanes.** `python -m src.loaders.fetch closed-lanes`
reads one detector's lane readings and returns the lane that was blocked while
others moved, when every lane went empty, and when traffic was flowing again;
or `insufficient_evidence`, in which case nothing is chosen. A lane counts as
blocked when it carried no vehicle through 3 or more archived readings in a row
while another lane did, and chance would do that less than once in 1,000 times
given the lane's share of the traffic on ordinary days. For IN-26-03365 at
AID01104 it gives what note 4 found by hand
([result](../results/data/closed-lanes_AID01104_20260515-0840_1010.md)): slow
lane from the 08:54:00 reading (the one before, 08:50:30, still open; chance 1
in 14,188), every lane empty from 09:00:30, flowing again by 10:00:00. It reads
456 veh/h passing the blocked lane over those five readings; the backup
network's 360 leaves out the 09:00:00 reading. Still to
agree: that this rule is the default, and what a replay does on
`insufficient_evidence` (Data suggests: run each lane and report the range).
It does not pick the detector (use the first one past the reported place) and
does not map lane names to SUMO lane indices.

## 30 Sep 2026

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

The flow-balance table is also the input for Data's ~15-link fallback.

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
  incident. This limited comparison does not establish random gaps or unbiased
  traffic estimates. A 20% bin scales one sampled minute up five times, so count
  precision and possible selection effects still require sensitivity checks.
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
