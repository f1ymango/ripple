# IN-26-03365: the Lead's plans on replay 3.1, validation version 2 and the ranking (13 October)

Prepared by Data. Follows [replay version 3](evaluator-replay-v3-2026-10-13.md),
whose section 9 listed the four decisions a go needed. The team took them on
13 October, and this note reports what the Lead's plans
(`data/generated-plans/IN-26-03365-lead-draft-20261013-b`, plan set
`lead-draft-20261013-b`) show under them. Code: E 3.2, commits `8d233dd` and
`346e2f0` on `data/lead-plans-v3-oct13`. Results: `results/evaluator-lead-draft-20261013-b/`
and `results/rankings/lead-draft-20261013-b.json`.

**In one paragraph.** Every one of the 33 baselines meets validation version 2:
GEH 91.5 to 94.2%, free-flow speed error 12.6 to 13.5%, congestion state agreeing
in 92.8 to 94.0% of bins (whole-run speed MAPE 22.9 to 26.9%, for information).
Three cells do not count, each for one wrong-lane teleport the rule does not
excuse; the limit is three. Over the other 30, **doing nothing beats P1** (P1
adds 3.4% delay, 95% interval 1.2 to 5.5%), **P2 beats P1** (4.8% less, 3.0 to
6.6%, lower in 28 of 30 cells), and **P2 and doing nothing tie** (P2 1.4% less,
interval from 4.1% less to 1.2% more). No plan comes before both others, so F
and the console recommend nothing. **The system is a go for ranking plans; for
these three plans the ranking is "P0 and P2 ahead of P1, P0 and P2 not
separable".** Whether P2 helps depends on how the road reopened, which the
detectors cannot settle (section 4).

## 1. What the team decided on 13 October

1. **Slow counts are not scored.** Counts measured under 30 km/h are left out of
   GEH, because the detectors miss many vehicles in slow traffic
   (`results/data/count-bias_AID01106_AID01107.md`). This was already in the
   version 3 detector data.
2. **Speeds are scored in two parts.** Speed MAPE at most 15% over bins measured
   at 30 km/h or more, and the model agreeing with the detector on congested or
   not (under 30 km/h) in at least 85% of speed bins. The whole-run MAPE is
   reported beside them, as information.
3. **Wrong-lane teleports.** One that begins at the moment a lane shuts (the
   driver's wait began within 60 s after the lane closed) is accepted and
   reported. So is one inside a jam: a jam teleport on the same or the next edge
   during the driver's 300 s wait or in the 300 s before it, meaning the lane it
   needed stood still too. Any other wrong-lane teleport fails the run, P0 or
   plan.
4. **The ranking rule** (it replaced "every cell" once the first cells showed
   that rule could not separate plans whose effects are smaller than seed noise).
   For each pair of plans, each counting cell gives the difference in total
   delay as a % of that cell's P0 delay. A plan is **before** another if the 95%
   confidence interval of the mean difference lies wholly on its side of zero;
   otherwise they **tie**. A cell counts if its P0 meets the targets and none of
   its three runs has a wrong-lane teleport of the failing kind; if more than
   10% of cells do not count, no order is stated. The rule and the 33 cells
   were committed after 4 cells had been seen and before the other 29 were run.
5. **The contract is extended**: three fields in `result.validation`, a ranking
   file from E to F, and F and the console recommend a plan only if the ranking
   puts it before both others (`docs/03-architecture.md`).

## 2. What changed in the code (E 3.2)

- `src/validation_targets.py`: the one rule E, F and the console use. A result
  without the new fields is still judged by the original GEH and speed targets.
- `src/evaluator/metrics.py`: the three new validation fields, and every run's
  wrong-lane teleports read from SUMO's log and sorted into at a lane shutting,
  in a jam, or other. Each run report lists them.
- `src/evaluator/ranking.py`: reads a grid file
  (`sim/scenarios/rankings/IN-26-03365_lead-draft-20261013-b.json`), checks every
  cell's results against their sidecars, plans and code, and writes the ranking once.
- `src/briefing/results.py` and `src/console/`: a version 2 baseline needs the
  ranking, its runs must be one of the ranking's cells with the same delays, and
  the winner must be the ranking's `first`; otherwise no recommendation.
- **Simulation:** a driver stopped 60 s at the end of a lane that cannot take it
  on its way is now also let in along the AID01103 queue path
  (`closure.scene.let_in_edges`), not only next to the crash. On 814979902, a
  lane drop, drivers had been lifted off by SUMO in 2 of the first 6 cells. It
  applies the same way to every plan. The one in seed 4 that remained stood in a
  jam: the lane beside it was stopped for over four minutes (decision 3).

## 3. The grid

Replay 3.1 as committed: seed 2026, compliance 50%, one-stage reopening at 10:00
(clearance 66), 20% of drivers leaving at the queue, 6.5 m vehicles, the ramp
joining the main line. Each other cell changes one thing:

| Cells | What changes | Why |
|---|---|---|
| seed1 to seed5 | seed | run-to-run noise |
| clearing, clearing-seed1 to 5 | fast lane at 4.7 km/h 10:00 to 10:04, slow lane shut, then both open | the reopening the detectors suggest |
| reopen-10:04, and seeds 1 to 5 | both lanes at 10:04 (clearance 70) | the other end of the reopening |
| ramp, ramp-seed1 to 5 | the ramp as built | the other bound on the north on-ramp |
| compliance-30, compliance-70 | 30% and 70% of advised drivers divert | 03-architecture.md section 4 |
| leave-0, -10, -30, -40 | 0 to 40% of drivers leave at the queue | the one value fitted to the morning |
| length-5m, and seeds 1 and 2 | 5 m vehicles | queue length per vehicle |

## 4. Results

Delay in vehicle-hours, `results/rankings/lead-draft-20261013-b.json`:

| Cells | Counting | P1 against P0 (mean, range) | P2 against P0 (mean, range) |
|---|---|---|---|
| One-stage reopening at 10:00, six seeds | 5 of 6 | −0.2% (−5.6 to +6.9) | −3.4% (−6.5 to +2.5) |
| Clearing stage, six seeds | 6 of 6 | +9.5% (+6.9 to +13.9) | +4.6% (+2.3 to +6.9) |
| Both lanes at 10:04, six seeds | 6 of 6 | +7.8% (+4.6 to +11.0) | +2.3% (−0.3 to +4.6) |
| Ramp as built, six seeds | 5 of 6 | −0.7% (−3.0 to +3.4) | −3.8% (−4.8 to −0.7) |
| Compliance 30% and 70% | 2 of 2 | +4.3% (+3.8 to +4.8) | +4.9% (+4.1 to +5.7) |
| Leave share 0, 10, 30, 40% | 3 of 4 | −0.3% (−7.9 to +7.7) | −1.2% (−8.1 to +4.1) |
| 5 m vehicles, three seeds | 3 of 3 | −1.8% (−5.4 to +0.3) | −18.1% (−18.9 to −16.9) |

| Pair, over 30 counting cells | Mean difference, % of P0 delay | 95% interval | Lower delay in | Verdict |
|---|---|---|---|---|
| P0 − P1 | −3.39 | −5.53 to −1.24 | P0 19, P1 11 | **P0 before P1** |
| P0 − P2 | +1.42 | −1.22 to +4.06 | P0 16, P2 14 | **tie** |
| P1 − P2 | +4.80 | +3.03 to +6.58 | P1 2, P2 28 | **P2 before P1** |

Checked independently with a separate script that does not use
`src/evaluator/ranking.py`: the delays read straight from the 99 result files,
the same counting cells and, with scipy's exact t distribution instead of the
tool's table, the same three verdicts. With all 33 cells counted, for information, the verdicts are also
the same.

**What does not count, and why.** Seed 5 and ramp-seed5: in P1, the same driver
stood on the approach (1198059119 lane 1) from 38 s after the reopening, so the
run fails. Leave-40: in P2, a driver stood in the dropping lane on 814979902
with no jam on that edge or the next. **What counted only because of the jam
rule:** 12 cells had one wrong-lane teleport in one run, every one in the
dropping lane on 814979902 (lane 0), with a jam teleport on the next edge
during or just before the wait. Under the rule as first written they would not
count, more than 10% of cells would fail, and no order could be stated. The
seed 4 debug log showed the lane beside it stood still for over four minutes
too. Every run's report lists its wrong-lane teleports by kind.

**Reading it.** P1 sends every advised driver under the flyover, which the
morning was already using as its detour, and is worse than doing nothing
wherever the road reopened late or slowly. P2 sends 80% and 70% and gives the
Tong Bin Lane signal 20 more seconds; it helps by 3 to 4% when both lanes
reopened at 10:00 or with the ramp as built, and costs 2 to 5% with the
clearing stage or a 10:04 reopening. The detectors cannot tell which reopening
happened. P2's 18% gain with 5 m vehicles says the queue's length per vehicle
matters as much as the reopening; 6.5 m stays the replay's choice. The cells are
not independent draws: compliance-30 and -70 share the main cell's P0, and
the one-change families weigh each assumption by how many cells it has.

## 5. Go/no-go

| Item | Version 3 (morning of 13 October) | Now | Met? |
|---|---|---|---|
| Counts (GEH ≥ 85%, slow counts left out) | 91.8%, every seed | 91.5 to 94.2% in all 33 baselines | **Yes** |
| Speed, version 2 (free-flow ≤ 15%, state ≥ 85%) | 12.99% and 93.3%, proposed | 12.6 to 13.5% and 92.8 to 94.0% in all 33 | **Yes** |
| Wrong-lane teleports | 1 to 3 per run, at a lane shutting | 93 at a lane shutting, 12 in a jam, 3 other (3 cells left out) | **Yes**, within the rule |
| A ranking rule decided before the results | proposed (every cell) | 95% paired interval, ties allowed, committed after 4 of 33 cells | **Yes** |
| F and the console bound to the ranking | no | refuse unless one plan is before both; tested on these results | **Yes** |

**Data's position: GO for ranking plans on replay 3.1 with E 3.2.** The
evaluator validates its baseline under the agreed targets in every cell and
states only the orders the grid supports. For the Lead's plans that is: **P0
and P2 tie, both before P1; no plan is recommended.** The honest headline is
that coordinating the detour (P2) is clearly better than broadcasting it to
everyone (P1), but on this morning neither beats doing nothing reliably.

Following the team's decision of 13 October, the main-case runs go into
`results/runs/` only if the ranking passes; it names no plan before both
others, so they stay in `results/evaluator-lead-draft-20261013-b/`. If the
console should show this refusal in the demo, the three main-case runs can be
copied there unchanged, with the ranking in `results/rankings/`.

Not settled: how the road reopened (the largest single effect on P2), the lanes
and signals of the road under the flyover, the +20 s at Tong Bin Lane as a real
control, where leaving drivers went, and the queue length per vehicle.

## 6. Reproduce

```bash
# every cell (99 runs; about 3.5 minutes each on one core), then the ranking
python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-lead-draft-20261013-b \
    --plan-set lead-draft-20261013-b --plan P0 --scenario <cell scenario> --compliance <c> \
    --clearance <t> --results-dir results/evaluator-lead-draft-20261013-b      # then P1 and P2
python -m src.evaluator.ranking --grid sim/scenarios/rankings/IN-26-03365_lead-draft-20261013-b.json
```

The cells' scenarios, compliance and clearance are in the grid file. Linux,
Python 3.13, SUMO 1.27.1, with the replay inputs as in
`docs/evaluator-replay-v3-2026-10-13.md` section 10.
