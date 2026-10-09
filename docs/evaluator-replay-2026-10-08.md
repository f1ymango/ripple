# E — replay of IN-26-03365 with P0, P1 and P2 (8 October)

Prepared by Data. E now runs P0, P1 and P2, and **the P0 replay meets both
validation targets over the whole run: GEH < 5 in 89.29% of count bins and
14.54% speed error.** Two things have to be said with that number wherever it
is quoted:

1. On 21 of the 25 detectors the speed is an input, taken from the detector
   itself a quarter-hour earlier. Where the model has to make the speed
   itself, on the crashed stretch, its error is 31.2%.
2. The plans are stand-ins written by a tool, not D's. They lower total delay
   by up to 5%, which is about the size of the difference between two random
   seeds.

> **9 October:** the Lead asked for a P0 go/no-go; Data's position is
> no-go for comparing plans by 14 October, in
> [evaluator-p0-go-no-go-2026-10-09.md](evaluator-p0-go-no-go-2026-10-09.md).
> Every `run_id` now ends with the plan set it evaluates (`_rehearsal` here),
> and these results moved from `results/runs/` to `results/evaluator-rehearsal/`,
> which leaves `results/runs/` for the Lead's plans. All runs were made again
> with the final code; every number is unchanged (section 6).

Everything here follows [the 7 October note](evaluator-p0-2026-10-07.md). The
scenario is
[evaluator_IN-26-03365_replay.json](../sim/scenarios/evaluator_IN-26-03365_replay.json);
how to run it is in [E's README](../src/evaluator/README.md).

## 1. Result

P0 against the 15 May detectors, seed 2026
([result](../results/evaluator-rehearsal/runs/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.json),
[report](../results/evaluator-rehearsal/evaluator/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.report.json)):

| | GEH < 5 (target 85%) | Speed error (target 15%) |
|---|---|---|
| **Whole run, 07:55–10:35** | **89.29% of 607 bins** | **14.54% of 787 bins** |
| Before the closure | 96.77% of 217 | 13.99% of 274 |
| During it | 82.02% of 267 | 14.37% of 338 |
| After reopening | 91.87% of 123 | 15.71% of 175 |
| AID01101–AID01104: the model makes the speed | | 31.24% of 115 |
| The other 21 detectors: a sign sets the speed | | 11.68% of 672 |
| 7 October baseline, for comparison | 89.95% | 42.69% |

Run health: 96 of 33,505 vehicles still waiting to enter at 10:35 (0.3%),
3 teleports, 1 of them a vehicle stuck changing lane. That one fails Data's
proposed rule of no wrong-lane teleports. The same run made twice gives an
identical result file, and the 7 October baseline still reproduces to the
byte with the new code.

The three plans at three compliance levels, seed 2026
([results](../results/evaluator-rehearsal/runs/)):

| Plan | Compliance | Delay, vehicle-hours | Against P0 | In the network | Waiting to enter | Left the corridor (assumed 20 min each) | Corridor travel time, 95th pct |
|---|---|---|---|---|---|---|---|
| **P0** do nothing | any | 1,702.1 | — | 834.2 | 522.0 | 345.9 (1,012 vehicles) | 77.0 min |
| **P1** advise everyone to use Wong Chuk Hang Road | 30% | 1,682.0 | −1.2% | 787.5 | 526.8 | 367.8 (1,043) | 69.1 |
| | 50% | 1,655.9 | −2.7% | 737.4 | 540.7 | 377.8 (1,038) | 63.3 |
| | 70% | 1,699.7 | −0.1% | 583.9 | 718.6 | 397.2 (1,043) | 55.2 |
| **P2** advise half, and 20 s more green at Tong Bin Lane | 30% | 1,675.8 | −1.5% | 811.2 | 508.4 | 356.2 (1,027) | 74.0 |
| | 50% | 1,685.2 | −1.0% | 806.1 | 517.4 | 361.8 (1,036) | 69.9 |
| | 70% | 1,687.6 | −0.9% | 787.6 | 531.9 | 368.1 (1,045) | 71.5 |

Section 5 says how to read this table. In short: do not rank P1 against P2
from it.

## 2. Which speeds are inputs

The 7 October runs had no speed signs, and their speed error was 40% before
the crash had happened. The replay has signs
([speed_signs.py](../src/evaluator/speed_signs.py)), of three kinds:

| Road | What the sign shows | Detectors |
|---|---|---|
| Not reached by the crash queue | The speed the detector itself measured in the quarter-hour before, on 15 May | 21: AID01106 to AID01110, the westbound road, Shek Pai Wan Road, Aberdeen Praya Road. One of them, TDSSPWR10003, stands on an edge that follows its neighbour TDSSPWR10002 |
| The queue's stretch, upstream of the scene | The ordinary mornings' speed, all morning | AID01101, AID01102, AID01103 |
| The last 330 m before the fork, and the flyover | No sign. E sets 66 km/h when nothing is closed | AID01103's own edge, AID01104 |

A refreshed sign is what a live twin could do 15 minutes behind the road. It
is the same idea as `--refresh` in Data's twin inputs, carried through the
run. But it means those detectors' speed error measures how well one
quarter-hour predicts the next, not the model.

The same run with ordinary-morning signs everywhere, so that no speed from
15 May goes in
([result](../results/evaluator-diagnostics/runs/2026-05-15_ABD_P0_c50_t66_ordinary-signs_rehearsal.json)):

| | GEH < 5 | Speed error | Where the model makes the speed | Where a sign sets it |
|---|---|---|---|---|
| Refreshed signs (the replay) | 89.29% | 14.54% | 31.24% | 11.68% |
| Ordinary-morning signs everywhere | 88.63% | **16.75%** | 30.04% | 14.47% |

**So the speed target is met with the refresh and missed by 1.75 points
without it.** Suggested wording for the validation slide: "GEH < 5 in 89% of
count bins. Speed error 14.5% with each detector off the crash stretch
refreshed from its last quarter-hour; 16.8% from ordinary mornings alone; 31%
on the crashed stretch, where the model has to form the queue itself."

## 3. What E assumes about the crash and the drivers

Each row is in the scenario file with its source. "Without it" is the replay
with that one thing changed, seed 2026
([scenarios](../sim/scenarios/evaluator-diagnostics/),
[results](../results/evaluator-diagnostics/runs/)).

| Assumption | Evidence | Without it: GEH / speed error |
|---|---|---|
| The flyover and the last 330 m run at 66 km/h when open | Ordinary mornings: 65–71 km/h at AID01103 and AID01104. The network says 50 | not run |
| While only the slow lane is closed, the fast lane passes at 4.7 km/h | AID01104: 456 veh/h passed at 3–9 km/h | not run |
| While both lanes are closed, the last 330 m crawl at 7 km/h | AID01103 stands there: 6–13 km/h, median 7 | at 10 km/h: 86.65% / 16.61% |
| For 20 minutes after 10:00 only one lane's worth gets past the scene, at 22 km/h | The flyover carried 72–120 a bin at 55–65 km/h while AID01103 behind it was still at 19–38 | 88.30% / 16.06% |
| Vehicles are 6.5 m long, not 5 m | **Assumed.** No classified count in the repository | 88.46% / 16.06% |
| 40% of drivers who meet the queue at an Aberdeen exit take it; drivers kept out of the network give up at the same rate | AID01101 kept counting about 90 a bin while AID01102, 520 m on, counted about 30 | nobody leaves: 87.31% / 14.85%, delay 2,154 |
| | | 30%: 88.46% / 14.51%. 50%: 89.78% / 14.47% |
| Each driver who leaves is charged 20 minutes | **Assumed, no source.** Section 5 | does not affect validation |

- **Nothing sets how many vehicles get round the flyover.** With the 7 km/h
  crawl the model passes 465 vehicles at AID01103 in the ten valid bins
  09:05–09:55. The detector counted 433. The 7 October baseline passed 603.
- **The pass does not hang on the share who leave.** 30%, 40% and 50% all meet
  both targets. It does hang on the crawl speed, the 20 slow minutes after
  reopening and the vehicle length: change any one and the speed error is
  over 16%.
- **The 20 slow minutes are an inference.** E models them as one of the
  flyover's two lanes staying closed. The detector on the flyover shows both
  lanes carrying traffic from 10:04
  ([readings](../results/data/closed-lanes_AID01104_20260515-0955_1035.md)),
  so the narrowing was at the scene, before the detector, and E's closed lane
  only stands for it.
- **One thing tried and taken out.** Shortening the green at the Tong Bin
  Lane signal from netconvert's 24 s to 15 s fitted no better than leaving it,
  in tuning runs that were not kept. In this model the signal is not what
  limits the surface road; the crawl past the scene is.

Six seeds, same scenario
([seed scenarios](../sim/scenarios/evaluator-diagnostics/)):

| | Seed 2026 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| GEH < 5 | 89.29% | 89.62% | 89.12% | 89.29% | 88.96% | 89.45% |
| Speed error | 14.54% | 13.73% | 14.35% | 14.48% | 14.15% | 13.67% |
| Where the model makes the speed | 31.24% | 25.58% | 29.21% | 30.83% | 29.30% | 25.61% |

All six meet both targets. The pinned seed, 2026, is the worst of them on
speed.

## 4. What is still wrong

1. **The crashed stretch is 31% out on speed.** The model's queue reaches
   AID01102 at about 09:05 and AID01101 at about 09:30; the real one reached
   them at about 09:15 and 09:47. After reopening the model's queue moves at
   20–30 km/h at AID01102 where the detector read 7–14 until 10:10.
2. **The tunnel gets far too little traffic during the closure.** AID01106
   and AID01107 counted 895 and 824 vehicles in the ten valid bins; the model
   sends 330 and 328. That is 36 of the 65 failing count bins (AID01106 to
   AID01109). The demand has almost no traffic joining after the flyover,
   because the ordinary mornings' net change there is near zero. Either real
   local traffic is missing or AID01106 is not where the network puts it; the
   map review already asks for it to be looked at.
3. **The model releases too much after reopening.** 860 vehicles pass
   AID01103 in the five valid bins 10:00–10:30 against 620 counted.
4. **The queue metric is at its ceiling.** In every run the queue fills the
   1,097 m path to the network's edge, so `max_queue_m` is "at least 1,095 m"
   and cannot tell plans apart.
5. **A quarter of P0's delay has nothing to do with the crash.** 448.7 of the
   522.0 vehicle-hours waiting to enter are the tunnel on-ramp (entry edge
   `46766432`), which queues with no closure too.
6. **`emergency_tt_min` is still a placeholder,** 2.9 minutes in every run.

## 5. P1 and P2

**What E models** ([actions.py](../src/evaluator/actions.py)), from 09:01
until the first lane reopens at 10:00:

- *Advice.* A driver of the od group follows it with probability share ×
  compliance, takes the road under the flyover from wherever they are, and
  does not leave at an Aberdeen exit. At reopening, drivers still short of
  the detour go back to the flyover.
- *Signal.* The green for Wong Chuk Hang Road eastbound at Tong Bin Lane
  runs 20 s longer.
- *Not modelled:* signs as such, and any shift to public transport.

**The plans** are
[stand-ins](../data/generated-plans/IN-26-03365-rehearsal/) from
[rehearsal_plans.py](../src/evaluator/rehearsal_plans.py), checked by D's
validator, on a
[new context](../data/plan-context/IN-26-03365_first-report-v2.md) that
offers the Tong Bin Lane junction. P1 advises both od groups with share 1.
P2 advises half of each and extends the green by the full 20 s.

**Six seeds at 50% compliance,** each plan against the P0 of its own seed:

| Seed | P0 delay | P1 | P2 |
|---|---|---|---|
| 2026 | 1,702.1 | −2.7% | −1.0% |
| 1 | 1,775.2 | −3.6% | −0.8% |
| 2 | 1,803.9 | −2.8% | −2.3% |
| 3 | 1,693.2 | −5.5% | −3.1% |
| 4 | 1,696.5 | −3.5% | −1.1% |
| 5 | 1,804.5 | −2.7% | −2.4% |
| Range | 1,693–1,805 | −2.7% to −5.5% | −0.8% to −3.1% |

How to read it:

- **Both plans lower delay in all six seeds, and P1 is below P2 in all six.**
  The direction is steady.
- **The sizes are small.** P0 alone moves by 3.1% (one standard deviation)
  from seed to seed. A single-seed difference under about 5% should not be
  presented as a ranking.
- **Why P1 helps at all.** Advised drivers get into the exit lane early and
  the corridor's 95th-percentile travel time falls from 77 to 63 minutes.
  They also stop leaving at the exits, so more are kept out at the network's
  edge instead: 651 against 375.
- **Why P2's signal does little.** In this model the surface road is short of
  lane at the fork, not of green.
- **P1 at 70% is an artefact warning.** Delay in the network falls to 583.9,
  but waiting at the tunnel on-ramp rises from 448.7 to 612.4 vehicle-hours,
  because more traffic reaches the tunnel and the ramp gives way to it. That
  ramp queues wrongly even with no closure. Without its waiting, P1 at 70% is
  −13.3% and at 50% −3.8%; P2 is −1.4% to −1.6% at every level.
- **The 20 minutes hardly matter here.** With 0, 10, 20 and 30 minutes for
  each driver who leaves, P1 at 50% is −4.0%, −3.3%, −2.7% and −2.2%, and P2
  −1.8%, −1.4%, −1.0% and −0.7%. The order does not change.

**What this incident lets a plan do.** The flyover was shut completely and the
network has one way round it, which was full. Advice can only change who is
in the queue, and green time cannot add a lane. A plan with more effect needs
something the twin does not have: a second route, or a way to take trips off
the road.

## 6. Format and edge checks (8 October, later)

**What goes in.** E reads D's plan folder and runs a plan only if it is exactly
what D's validator returns for the saved `generation-inputs.json`, and only on
a scenario file that passes the schema in
[scenario.py](../src/evaluator/scenario.py).

**What comes out.** Every result in `results/evaluator-rehearsal/runs/` and
`results/evaluator-diagnostics/runs/` was checked by script against
[the contract](03-architecture.md#resultjson--output-of-e): F's result schema,
the contract's keys in the contract's order, a `run_id` equal to the file name
that encodes the plan, compliance and clearance in the result, P0 with
`delay_vs_do_nothing_pct` 0 and both validation figures, P1 and P2 with empty
`validation` and a change against the P0 of the same compliance, clearance and
seed. Each sidecar holds exactly the eight contract fields, verifies against
its plan and the generation inputs, and its simulation-input hashes equal the
files in the repository now. All 32 current results pass. The three 7 October
records verify against their own plan folder and that day's code.
F's checks (`prepare_comparison`, what `--check-only` runs) and the console's
comparison accept all three compliance levels. The contract's GEH target is for the pre-incident hour: before the
closure P0 scores 96.77% of 217 bins.

**Edges, run in SUMO:**

| Case | Expected | Result |
|---|---|---|
| P1 at compliance 0 | the same as P0 | identical metrics and measurement detail |
| P1 at clearance 5: the road reopens at 08:59, before the 09:01 report | the same as P0, and the report says the plan could not act | identical; the report says "none: the first lane reopens at second 5640, before the plan can act at second 5760". P0 there misses the speed target, 38.98%: note 24 |
| P1 at compliance 100% | runs | +8.3%: waiting at the tunnel on-ramp rises from 448.7 to 706.4 vehicle-hours, the artefact of section 5 |
| P2 at compliance 100% | runs | −2.0% |
| P2 that only extends the green | the program switches at 09:01 and back at 10:00 | phase 0 goes from 24 s in a 90 s cycle to 44 s in 110 s at second 5760 (09:01) and back at 9300 (10:00); delay +0.2% |
| Clearance 80, the longest whole minute that reopens every lane before the run ends | runs | delay 1,939.6; GEH 86.82%, speed error 14.61%: still meets both targets |
| Clearance 81 and 82 | refused before SUMO starts | refused in under a second |
| Run from another folder | the same result | identical to the run from the repository |
| P0 run twice | byte-identical | byte-identical, sidecar too |
| The 7 October baseline with today's code | the same result | identical apart from the `run_id`'s plan-set suffix |
| All 32 committed runs again with today's code | the same numbers | every number identical; only the `run_id` (now ending `_rehearsal`), the sidecars' hashes of E's code and scenario, and the relabelled signal assumption changed |

**What the checks changed in E.** None of these changes a committed number
(last row above); each would have mattered for other plans or settings.

1. **Two routes for one od group:** E applied the first route's share and
   never the second. Now one draw per driver splits the group by the shares.
   The replay has one detour, so no result was affected.
2. **A plan compared with a P0 that had been edited, or made from other
   plans:** E checked only the simulation inputs. It now verifies the P0
   result against its sidecar, `P0.json` and `generation-inputs.json` first.
3. **Settings outside the contract** (compliance 1.1, clearance 0, NaN) ran
   for two minutes before the result schema refused them. They are now refused
   before SUMO starts, and so is a clearance whose last lane reopens at the
   run's final second, which never simulated an open road.
4. **Two compliance values, one `run_id`:** `c12.3457` stands for 0.1234567
   and 0.1234571. E refuses values with more decimals than the `run_id` shows.
5. **A closure phase due in the second the road reopens** (clearance 2.001
   minutes in a test scenario) was applied together with the reopening. It
   now never starts.
6. **A scenario that places a route badly:** a route that does not start on
   the road its od group avoids did nothing, and two junctions on one traffic
   light were extended twice and never restored. Both are now refused, and a
   green phase the light does not have stops the run.
7. **The console withheld the 50% comparison:** the 7 October P0 shared its
   compliance, clearance and seed with the replay's. Moved, unchanged, to
   `results/evaluator-diagnostics/`.
8. **A batch for a new plan set would have kept the old plan set's results**
   (the Lead, 9 October): `batch` skipped any `run_id` that had a result. Now
   every `run_id` ends with `--plan-set`, and `batch` keeps a result only if
   it binds the same plans, generation inputs and simulation inputs.
9. **The v2 context named a source that was never committed**
   (the Lead, 9 October). Removed; a test now fails if any plan context names
   a missing file.

`tests/test_evaluator.py` has 81 cases, up from 44, for these and the
contract's edges. What other owners should know is in
[notes-from-data.md](notes-from-data.md), notes 24 to 26: far from the
morning's own clearance P0 fails validation, so plans cannot be ranked at such
a what-if clearance; CLAUDE.md's E commands do not exist; and the console's
scenario key.

## 7. Reproduce

Inputs once, as in [E's README](../src/evaluator/README.md). Then:

```bash
python -m src.evaluator.rehearsal_plans --incident data/generated-plans/IN-26-03365-p0-only/generation-inputs.json \
    --context data/plan-context/IN-26-03365_first-report-v2.json --out-dir data/generated-plans/IN-26-03365-rehearsal
python -m src.evaluator.batch --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal \
    --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --clearance 66 \
    --results-dir results/evaluator-rehearsal
# a seed or a one-change variant
python -m src.evaluator.batch --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal \
    --scenario sim/scenarios/evaluator-diagnostics/replay_seed1.json --clearance 66 --compliance 0.5 \
    --results-dir results/evaluator-diagnostics
python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal --plan P0 \
    --scenario sim/scenarios/evaluator-diagnostics/replay_ordinary-signs.json --compliance 0.5 --clearance 66 \
    --results-dir results/evaluator-diagnostics
# the ordinary-signs variant needs its own sign file first: every detector named after --ordinary-only
```

The plans folder already exists in the repository; the first command is how it
was made (again on 9 October, from the corrected context: the plans are
unchanged, `generation-inputs.json` lost the missing source). Run on Linux, Python 3.13.16, SUMO 1.27.1. Not run on Windows.

## 8. Open

1. **Lead — how the validation is worded.** Section 2. The whole-run numbers
   meet the targets only with speeds refreshed from 15 May.
2. **Lead — D's own plans.** Generate P0/P1/P2 from the version 2 context and
   evaluate those under their own `--plan-set`, once P0 is accepted
   ([go/no-go](evaluator-p0-go-no-go-2026-10-09.md)). E refuses a plan that
   uses public transport or a junction the scenario does not place.
3. **Lead — one seed or several.** The contract has one seed per result. Plan
   differences here are within seed noise, so the briefing should either say
   so or compare several seeds.
4. **Simulation — the tunnel side.** Where AID01106 is, the traffic that
   joins after the flyover, and the on-ramp at `46766432`. Until then the
   plans' effect downstream of the flyover is not to be trusted.
5. **Simulation — review of the scene assumptions in section 3,** as for the
   7 October P0 setup.
6. **Data — the 20 minutes.** No source. It does not change the order here.
7. **Lead — plans at other clearances.** Section 6 and note 24: at 5
   minutes P0 fails the targets, so nothing can be ranked there.
