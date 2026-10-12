# E — two corrections to the IN-26-03365 replay, and what they change (10 October)

Prepared by Data. Follows [the 8 October replay note](evaluator-replay-2026-10-08.md)
and [the 9 October go/no-go review](evaluator-p0-go-no-go-2026-10-09.md),
which is updated with these numbers. Simulation's
[technical review](simulation-evaluator-review-2026-10-09.md) of the
uncorrected replay came in the same day; where it bears on these corrections
it is quoted below.

**In short:** two things in the 8 October replay were simulator artefacts, not
traffic. Corrected, P0 still meets both validation targets, now in all six
seeds. But the rehearsal plans' benefit disappears: **both plans add delay**,
in every seed and at every compliance level. The 8 October plan gains came
from the artefacts. How the north on-ramp is modelled still decides whether
P2 adds or saves delay overall.

## 1. The two corrections

Each was found by looking at what the model did, and each has evidence that
does not come from the bins it improves.

**1. Drivers go round the closure by Wong Chuk Hang Road, then keep to their
route** ([scenario](../sim/scenarios/evaluator_IN-26-03365_replay.json),
`closure.detour`; [simulate.py](../src/evaluator/simulate.py)).

Until now SUMO chose a new route for every driver turned away from the shut
flyover. A probe run recorded every vehicle that used the Wong Nai Chung Road
exit (`1194711688`) between 09:00 and 09:30. Of 111, 96 were bound for the
Canal Road Flyover, and SUMO had sent them through Happy Valley streets. Those
streets jammed at 1 to 2 km/h from 09:10 to the end of the run, and the jam
backed up into the tunnel exit: AID01108 counted 11 vehicles a bin during the
closure. On the real morning it counted 96, so the real exit was not blocked.
TD's 09:36 message advised "alternative routes such as Wong Chuk Hang Road".
E now sends these drivers along the same edges as the plans' detour, then the
rest of their own route.

**2. The join north of the tunnel enters on the main line**
([main_line_join.py](../src/evaluator/main_line_join.py)).

The demand puts the ordinary mornings' join between AID01108 and AID01109,
783.5 veh/h, on the one on-ramp the network has there (`46766432`). The
network's merge let far fewer in. Vehicles waited up to 27 minutes to enter
from 07:45, an hour before the crash: 448.7 of P0's 1,702 vehicle-hours. The
detector downstream, AID01109, counted 19% under the real one before the
crash, so the real ramp did let them in. The same flow now enters where the
ramp meets the main line. Nothing else in the demand changed.

Neither correction was chosen for the score. Alone, the first moves whole-run
GEH from 89.29% to 89.45% and the second to 88.30%.

Simulation's review agrees the detour's exact edges as the one provisional
surface detour in this model. On the ramp it warns that the merge's minor
priority is not proof that real priority or capacity is wrong, and that ramp
delay can be a real consequence of diversion. Correction 2 rests on AID01109's
pre-crash counts, which Simulation has not yet reviewed; section 4 shows what
the plans do without it.

## 2. P0 after the corrections

Seed 2026, 66 minutes' clearance
([result](../results/evaluator-rehearsal/runs/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.json),
[report](../results/evaluator-rehearsal/evaluator/2026-05-15_ABD_P0_c50_t66_replay_rehearsal.report.json)):

| | GEH < 5 (target 85%) | Speed error (target 15%) |
|---|---|---|
| **Whole run** | **89.45%** of 607 bins (8 Oct: 89.29%) | **14.44%** of 787 (14.54%) |
| Before the closure | 96.77% | 13.90% |
| During it | 83.15% (82.02%) | 14.15% |
| After reopening | 90.24% | 15.82% |
| Where the model makes the speed (AID01101–04) | | 31.33% |
| Where a refreshed sign sets it (20 detectors) | | 11.54% |
| Five more seeds | 89.45% to 90.44% | 13.64% to 14.42% |

Run health: nobody is still waiting to enter at 10:35 (96 before), 438
drivers were sent round, 3 teleports, **all 3 wrong-lane** (1 before).

Total delay falls from 1,702 to 871 vehicle-hours, because the two artefacts
are gone. P0 alone now moves 1.4% (one standard deviation) between seeds,
not 3.1%.

**Speeds that plans cannot inherit.** With the corrections, P0 scores:

| Speed signs | GEH | Speed error |
|---|---|---|
| Refreshed from 15 May, as above | 89.45% | 14.44% ✅ |
| Refreshed only where no plan's traffic goes (westbound, side roads); eastbound AID01101–10 ordinary | 88.96% | **16.29%** ❌ |
| Ordinary mornings everywhere | 89.12% | 16.94% ❌ |
| Refreshed until the crash, then held | 90.60% | 17.82% ❌ |

With the fair signs, the largest part of the speed error is the back of the
queue. AID01102 is off by 57% on average and AID01101 by 31%: a fifth of all
the error, in 62 of 787 bins. There the model's queue arrives 10 to 15
minutes early (AID01102 at 09:05: 6 km/h in the model, 64 measured) and
clears about 5 minutes late (10:15: 34 against 70). Next come AID01106,
AID01108 and AID01109 on the tunnel side, 28 to 34% off, where 15 May ran
faster than ordinary mornings.

**Which assumptions the pass still rests on** (each changed alone):

| Changed | GEH | Speed error |
|---|---|---|
| Vehicles 5 m, not 6.5 m | 90.77% | 15.60% ❌ |
| Reopening in one stage, not two | 88.63% | 15.78% ❌ |
| 50% of drivers leave at the exits, not 40% | 89.95% | 15.29% ❌ |
| Crawl at 10 km/h, not 7 | 91.43% | 14.94% |
| 30% leave | 89.45% | 14.16% |
| Nobody leaves | 87.31% | 14.70% |
| No give-up rule at the entry | 88.96% | 14.57% |
| Without correction 1 | 88.30% | 14.50% |
| Without correction 2 | 89.45% | 14.45% |

## 3. The tunnel side is still the gap

During the closure the model now sends 47 vehicles a bin past AID01106 (33
before correction 1); the detector counted 90. AID01108 gets 46 (11 before)
against 96. Only 28 to 50 a bin passed AID01103, the one way in the
network. So the real extra came from somewhere the model does not have. It
cannot be the drivers who left at the Aberdeen exits: with the fork removed,
no road in the network leads from those exits to the tunnel.
We tried that idea anyway, as drivers coming back by streets outside the
network, and dropped it: it rested on a road that does not exist, and it was
chosen to fix the failing bins. Three candidates remain, all Simulation's:

1. traffic joining between AID01103 and the fork, for instance from
   Ap Lei Chau, which the demand's net changes between detectors hide;
2. more capacity on the road under the flyover than the network gives it;
3. AID01106 standing somewhere other than edge `1198101443`.

## 4. The rehearsal plans now add delay

The same stand-in plans as on 8 October
([plans](../data/generated-plans/IN-26-03365-rehearsal/),
[results](../results/evaluator-rehearsal/runs/)):

| Plan | Compliance | Delay, veh-h | Against P0 | In the network | Waiting to enter | Left (vehicles) | Corridor travel time, 95th pct |
|---|---|---|---|---|---|---|---|
| **P0** | any | 870.6 | — | 457.9 | 73.3 | 339.4 (994) | 43.9 min |
| **P1** advise all | 30% | 927.4 | +6.5% | 482.7 | 85.1 | 359.6 (1,023) | 50.0 |
| | 50% | 961.3 | +10.4% | 490.1 | 97.0 | 374.2 (1,033) | 50.9 |
| | 70% | 1,004.3 | +15.4% | 498.7 | 106.7 | 398.9 (1,037) | 53.6 |
| **P2** advise half, +20 s green | 30% | 914.8 | +5.1% | 481.4 | 79.8 | 353.6 (1,022) | 49.0 |
| | 50% | 915.5 | +5.2% | 481.2 | 72.0 | 362.4 (1,035) | 51.0 |
| | 70% | 942.6 | +8.3% | 491.2 | 88.3 | 363.1 (1,033) | 50.5 |

Six seeds at 50%, paired by seed: P1 − P0 +8.5% (95% interval +7.0 to
+10.1), P2 − P0 +4.2% (+3.2 to +5.2), P1 − P2 +4.3% (+3.1 to +5.5), with the
same sign in all six. So the ranking is not seed noise. It also holds
whatever a driver who leaves is charged: from 0 to 90 minutes instead of 20,
P1 stays 6.7% to 14.4% worse and P2 4.6% to 5.8%.

**But it depends on correction 2.** With only correction 1, the ramp's merge
kept, P0's waiting at the ramp grows to 762.5 vehicle-hours (nothing drains
it any more), and the plans reduce it: P1 comes out +1.4% and P2 **−2.7%**
([results](../results/evaluator-diagnostics/runs/)). Delay inside the network
rises with both plans either way (P1 +6.4%, P2 +4.5% without correction 2).
So which representation of the ramp is right decides P2's sign.

**Why.** The road under the flyover is the only way round and it is already
full. An advised driver stops taking the Aberdeen exits and joins the queue
for it instead: 417 leave at the exits under P1 at 50%, against 638 in P0. The
queue then reaches the network's entry, where 616 drivers give up waiting,
against 356. So more vehicles queue and more are kept out. Advice to use a
road that has no spare capacity makes the morning worse.

**Three cautions.** The effect works through the drivers-leave rule, whose
40% share and entry rule are calibrated, not sourced. It lands on the tunnel
side, where the model is weakest. And P2's sign turns on the ramp. So this is
a finding about the model, not yet a finding about the road.

## 5. What this changes

- **The 8 October plan gains were artefacts.** Its tables of P1 and P2 should
  not be quoted. The 8 October note now says so at the top.
- **P0 itself is better:** it passes in all six seeds, and its pre-crash ramp
  backlog is gone. The review's stance, now joint with Simulation's, is
  updated in its section 2: still no-go.
- **For D's plans:** with one detour that is already full, a plan that only
  points drivers at it adds delay inside the network in this model. A useful
  plan needs another route or fewer trips (03-architecture.md lists
  `pt_nudge`; E does not model it).

## 6. Reproduce

As in [E's README](../src/evaluator/README.md), plus the corrected demand,
once:

```bash
python -m src.evaluator.main_line_join --routes sim/work/p0-replay-build/demand.rou.xml \
    --flow f22 --from-edge 1194711693 --out sim/work/p0-replay-build/demand-main-line-join.rou.xml
# SHA-256 8caed7394039f64155dc7605458366507481ca8abd494193ff6c606130ad0f43
```

The fair sign files are `speed_signs.py` with `--ordinary-only` naming
AID01101 to AID01110 (`speeds-boundary.add.xml`, `51a16331…`) and with
`--hold-from 09:00` (`speeds-held-0900.add.xml`, `2f854097…`). The one-change
scenarios are in [evaluator-diagnostics](../sim/scenarios/evaluator-diagnostics/)
and their results in `results/evaluator-diagnostics/`. Linux, Python 3.13.16,
SUMO 1.27.1.
