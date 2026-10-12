# IN-26-03365 replay, version 3: the detectors, the crawl, and what is left of the no-go (13 October)

Prepared by Data. Follows the [10 October corrections](evaluator-replay-fixes-2026-10-10.md)
and answers, item by item, section 3 of the
[go/no-go review](evaluator-p0-go-no-go-2026-10-09.md): what would turn it into a go.
The scenario is [`evaluator_IN-26-03365_replay-v3.json`](../sim/scenarios/evaluator_IN-26-03365_replay-v3.json).
Its rehearsal results are in `results/evaluator-rehearsal-v3/`, the one-change runs in
`results/evaluator-diagnostics/` (labels starting `v3-`). The plans are still the
validator-built stand-ins, not the Lead's.

**In one paragraph.** Three findings from data outside 15 May change the picture.
First, the corridor's detectors count too few vehicles in slow traffic: on a road
with no junction, AID01106 counts 55% of what AID01107 counts when it runs under
10 km/h. Second, the 10 October replay's 7 km/h crawl, AID01103's own speed set as
a limit, held the detour to the number AID01103 counted in that slow traffic, and
that is why the tunnel side was half empty. Third, on congested mornings the north
on-ramp loses about half a vehicle for every extra vehicle through the tunnel, so
neither ramp representation is right, and they bound the truth. Version 3 drops
the crawl, opens both lanes at 10:00, shows ordinary-morning speeds on every sign,
withholds counts measured under 30 km/h, and refits the one share fitted to the
morning to when the queue reached AID01101. **Counts now pass in every phase and
every seed. The speed target is still missed (24.8%), almost all of it on the
queue at AID01102 and AID01103.** On the stand-in plans, whether P2 beats doing
nothing turns on whether both lanes reopened at 10:00 or 10:04 (section 8). Data's
position stays no-go for ranking plans against doing nothing; a conditional go
for using version 3 as P0 needs three decisions (section 9).

## 1. The detectors count too few vehicles in slow traffic

TD's Road Network (2nd Generation, data.gov.hk, `RdNet_IRNP.gdb.zip` of 9 October)
has no junction between AID01106 and AID01107: centrelines 17374, 17378, 15939 and
15938 follow one another, 394 m, with nothing joining or leaving. So the two must
count the same vehicles. Comparing them second by second (matched 30-second
periods, every lane valid at both), on every cached day except 15 May:

| AID01106 speed | 5-minute bins | Days | AID01106 / AID01107 |
|---|---|---|---|
| under 10 km/h | 18 | 7 | **0.55** |
| 10 to 20 | 57 | 19 | **0.73** |
| 20 to 30 | 58 | 24 | **0.80** |
| 30 to 40 | 144 | 31 | 0.96 |
| 40 to 50 | 960 | 48 | 1.02 |
| 50 and over | 360 | 45 | 0.99 |

[results/data/count-bias_AID01106_AID01107.md](../results/data/count-bias_AID01106_AID01107.md),
made by `python -m src.loaders.fetch count-bias --exclude-day 2026-05-15`.

AID01216 to AID01217, with one join between them, shows the same direction: its ratio falls from 0.67 at free flow to
0.52 under 10 km/h. We have not found why (the AID detectors are TD's; their type
is not in the feed's documentation we hold), only that it is there.

**What follows.** A count bin measured in slow traffic cannot score a model: a
model that moves the right number of vehicles fails GEH there. Version 3's
observations withhold the count (not the speed) in the 51 bins whose measured
speed is under 30 km/h (`python -m src.loaders.fetch withhold-slow-counts
--min-count-speed 30`). Two earlier choices rested on such counts:

- the 7 km/h crawl (section 2), and
- the 40% drivers-leave share, fitted to AID01102 counting about 30 a bin against
  AID01101's 90 while AID01102 ran at 3 to 12 km/h (section 4).

It also explains much of the tunnel-side gap. During the closure AID01103 ran at 6
to 14 km/h and counted 433 vehicles in the ten valid bins 09:05 to 09:55; at
0.55 to 0.73 that is about 600 to 790.

## 2. The crawl held the detour to AID01103's count

TD's Road Network confirms what the OSM network shows: no road leads from Aberdeen
or Ap Lei Chau to the tunnel without passing AID01103 (forward search from
AID01101 with AID01103's centreline 624 and the flyover 3075 removed: no route;
the Wong Chuk Hang streets reach the tunnel, but nothing from Aberdeen reaches
them). So the tunnel's extra traffic either crossed AID01103 uncounted, or came
from Wong Chuk Hang, or both.

The 10 October replay set the last 330 m before the fork, AID01103's loop
included, to 7 km/h once both lanes were shut. A speed limit at the bottleneck is
also a flow limit: the model passed 47 to 49 vehicles a bin onto the detour, the
same as AID01103's slow-traffic count. One change, the crawl removed and nothing
else:

| P0, seed 2026, as 10 October otherwise | GEH, whole run | GEH during the closure | AID01103, 09:05 to 09:55 | AID01106 | Speed MAPE |
|---|---|---|---|---|---|
| Crawl at 7 km/h (10 October) | 89.45% | 83.15% | 472 | 466 | 14.44% |
| No crawl | 92.25% | **89.89%** | 717 | 646 | 23.54% |
| Observed | | | 433 counted, about 600 to 790 corrected | 895 | |

Without the crawl the model's AID01103 count lands where the slow-traffic
correction puts the real one, and the tunnel side gets two thirds of its count,
up from half. A crawl over only the last 77 m (the taper) gave the same trade:
at 7 km/h 89.12% and 21.5%, at 10 km/h 91.10% and 25.9%. Any limit at the
bottleneck trades counts for speed. Version 3 sets none.

## 3. Version 3 against the targets

P0, seed 2026, compliance 50%, clearance 66 minutes. Signs: ordinary mornings for
all 24 detectors, the same for P0, P1 and P2. Count bins under 30 km/h withheld.

| | Whole run | Before the closure | During | After |
|---|---|---|---|---|
| GEH < 5 (target 85%) | **93.52%** of 556 | 97.97% of 197 | **91.80%** of 244 | 89.57% of 115 |
| Speed MAPE (target 15%) | **24.83%** of 787 | 15.90% | 33.16% | 22.71% |

Six seeds: GEH 92.98 to 93.52%, MAPE 23.91 to 25.13%. The closure phase is at 91.4
to 93.4% in every seed and both ramp bounds (section 8 table).

**Where the speed error is.** AID01102 and AID01103 carry 11.1 of the 24.8 points:
during the closure they measured 3 to 14 km/h and the model's loops 24 to 42.
Without those two detectors the whole-run MAPE is 14.9%. Measured another way:

| Speed bins | All | Before | During | After |
|---|---|---|---|---|
| Congestion state agrees (both under 30 km/h, or both over) | 93.3% | 93.8% | 92.9% | 93.1% |
| MAPE where the measured speed is 30 km/h or more | 12.99% | 12.85% | 12.44% | 14.24% |

The model's queue is in the right places at about the right times (it reaches
AID01101 at 09:55 against 09:50, section 4) but runs too fast inside. Lane by lane,
AID01103 during the closure: the fast lane carried 420 vehicles an hour at 9.5 km/h
and the middle and slow lanes almost nothing (31 and 55); the model has the same
pattern, 658, 185 and 26, but its fast lane moves at 40 km/h. The model's queue
in that lane starts nearer the fork. Why the real one reached back past AID01103
is not something these detectors can tell; the lanes and signal timings of the
road under the flyover are OSM's and netconvert's and are not verified. Putting a
speed on that stretch (the 10 October answer) passes MAPE but caps the flow
again (section 2).

**Tunnel side.** In the ten valid bins 09:05 to 09:55: AID01106 895 counted
against 613 modelled, AID01107 824 against 619, AID01108 957 against 603. Two bins
fail at each of AID01106 and AID01108 (eight each on 10 October). AID01109 fails
six bins: it also carries the north join (section 6).

**After reopening.** One stage at 10:00 sends a surge over the flyover (AID01104
at 10:05: 221 modelled, 120 counted) that jams briefly at AID01108 (10:15: 267
modelled, 95 counted; 35 km/h against 80). The after phase still passes (89.57%).

## 4. Drivers who leave: the one value fitted to the morning

The share of drivers who take an Aberdeen exit when they meet the queue was 0.4,
fitted to AID01102's slow-traffic count (section 1). Version 3 fits it to an
observable the count bias cannot touch: when the queue reached AID01101, the first
bin it ran under 30 km/h. Observed 09:50.

| Share | Queue reaches AID01101 (first bin under 30 km/h) |
|---|---|
| 0 (nobody leaves) | 09:20 |
| 0.1 | 09:30 |
| **0.2 (version 3)** | **09:55** |
| 0.25 | never (lowest 33 km/h) |
| 0.3, 0.4 | never |

The share stays a fitted value with no source, and where those drivers went is not
observed (the western road's detectors show no rise). Section 8 runs the plans at
0.1 and 0.3 as well. A leaver is still charged 20 minutes outside the network;
the run report keeps that part separate.

## 5. Teleports

A new scene rule, `let_in_after_seconds` (60 s): a driver stopped that long at the
end of a lane it cannot follow its route from is let in, the slow driver just
behind in the lane it needs holding back for up to 5 s. In seed 2026 it lets in
three drivers and leaves **one wrong-lane teleport** (`f145.50`, 08:59:04, the same
driver as on 8 October, stuck in the middle lane from the second the slow lane
shut). Across the six seeds: one to three, every one a driver stuck from the
second a lane shut, on the last 77 m before the fork (SUMO lifts it off five
minutes later). Two kinds remain:

- **At 08:54:00**, when the slow lane shuts, a driver already in a lane that leads
  only to it within the last 77 m. The closure shuts the whole 543 m lane at once,
  where on the road the driver would merge at the crash.
- **At 09:00:30**, when both lanes shut, a driver on the last 18 m in a lane that
  leads only onto the flyover. A fix is tested (such drivers keep their route over
  the flyover; it removed that kind in the two seeds tried) but not in these results, because any
  change to E's code means making every result again.

Data's proposed rule was none. These are artefacts of a closure that starts in one
second; they move one or two vehicles.

## 6. The north on-ramp: what the data say

AID01108 counts the tunnel's traffic, AID01109 the same after the on-ramp from Wong
Nai Chung Road joins. Quarter-hours on 48 cached days, not 15 May, both detectors
at 30 km/h or more ([results/data/merge-tradeoff_AID01108_AID01109.md](../results/data/merge-tradeoff_AID01108_AID01109.md)):

| AID01108, veh/h | Join when AID01109 runs 30 to 45 km/h (142 quarter-hours, 36 days) |
|---|---|
| 750 to 999 | 1,295 |
| 1,000 to 1,249 | 1,087 |
| 1,250 to 1,499 | 946 |
| 1,500 to 1,749 | 891 |

When the merged road is congested, **each extra main-line vehicle costs the ramp
0.51 vehicles** (least squares). When it flows freely the two do not compete.
15 May agrees: the join rose from 751 to 914 vehicles in ten bins when the
closure cut the main line from 1,225 to 957.

So Simulation's warning holds: diverting traffic through the tunnel does cost the
ramp. Neither model representation is right:

| | Ramp lost per extra main-line vehicle | Ramp's flow before the crash |
|---|---|---|
| Observed | 0.51 | 901 veh/h |
| On-ramp as built (minor priority) | about 0.40 | 586 veh/h (starved; 600+ veh-h waiting) |
| Join on the main line (correction 2) | 0 | 752 veh/h |

The as-built ramp has nearly the right trade-off and the wrong level; the main-line
join the right level and no trade-off. Section 8 runs every plan under both and
treats them as bounds.

## 7. What version 3 changes, in one list

| Change | Why | File |
|---|---|---|
| Count bins measured under 30 km/h withheld from GEH | Section 1 | `sim/work/v3/detectors-slow-withheld.json`, `src/loaders/twin_export.py` |
| No crawl | Section 2 | scenario `closure.scene.crawl_kmh` = `open_kmh` |
| Both lanes reopen at 10:00 | AID01104: both lanes from 10:04; Simulation rejected the 20-minute stage | scenario, `reopening` removed |
| Ordinary-morning signs on all 24 detectors | Simulation's condition for plan runs | `speeds-ordinary.add.xml` |
| Leave share 0.2, fitted to the queue at AID01101 | Section 4 | scenario `drivers_leave.share` |
| Let-in rule for drivers stuck at a lane end | Section 5 | `src/evaluator/simulate.py` |
| New evidence commands: `count-bias`, `merge-tradeoff`, `withhold-slow-counts` | Sections 1, 6 | `src/loaders/` |

Unchanged: Simulation's network, loops and demand (with correction 2's main-line
join), the detour (correction 1), the 6.5 m vehicle, the closure times, the plan
actions.

## 8. The stand-in plans on version 3

P0, P1 and P2 are the validator-built stand-ins (P1: advise all of the flyover's
traffic onto Wong Chuk Hang Road; P2: advise half and give Tong Bin Lane +20 s
of green, an ASSUMED NETWORK CONTROL). Every row is a full set of runs; "P1 vs
P0" is the change in total delay, paired on the same seed.

| Six seeds, paired, compliance 50% | P0 delay, mean veh-h | P1 vs P0 (95% interval) | P2 vs P0 (95% interval) | P2 below P0 in | P2 below P1 in |
|---|---|---|---|---|---|
| Join on the main line (correction 2), both lanes at 10:00 | 815 | +1.4% (-2.8 to +5.5) | -2.4% (-4.2 to -0.5) | 6 of 6 seeds | 5 of 6 |
| On-ramp as built, both lanes at 10:00 | 1,498 | +2.1% (+0.1 to +4.1) | -2.3% (-4.0 to -0.6) | 5 of 6 seeds | 6 of 6 |
| Join on the main line, both lanes at 10:04 | 856 | +12.4% (+9.6 to +15.2) | +3.7% (+1.3 to +6.1) | 0 of 6 seeds | 6 of 6 |

| One change from version 3, seed 2026 (unless named) | P0 GEH | P0 MAPE | P0 delay, veh-h | P1 vs P0 | P2 vs P0 | P2 minus P1, veh-h |
|---|---|---|---|---|---|---|
| Compliance 30% | 93.52% | 24.83% | 814 | -2.3% | -2.5% | -2 |
| Compliance 70% | 93.52% | 24.83% | 814 | +1.3% | -2.7% | -32 |
| Leave share 0.1 | 92.80% | 24.48% | 849 | -0.0% | -2.7% | -23 |
| Leave share 0.3 | 93.70% | 26.18% | 764 | +2.7% | -2.5% | -40 |
| Nobody leaves | 91.72% | 23.87% | 958 | -6.2% | -6.1% | +1 |
| 5 m vehicles, seed 2026 | 93.34% | 24.26% | 786 | +2.8% | -13.6% | -129 |
| 5 m, seed 1 | 92.80% | 25.35% | 741 | -0.8% | -19.5% | -138 |
| 5 m, seed 2 | 92.62% | 25.05% | 765 | -5.6% | -19.5% | -106 |

Every run's result and report are in `results/evaluator-rehearsal-v3/` and
`results/evaluator-diagnostics/`. What the rows say:

- **At 10:00, P2 saves about 2.4%**, under either ramp bound, at 30, 50 and 70%
  compliance, with 0.1 to 0.3 leaving and with nobody leaving. Its saving
  survives charging a leaver nothing (6 of 6 seeds with the main-line join, 5 of
  6 with the ramp as built). With 5 m vehicles it is far larger (14 to 20%): the
  size is not robust, only the sign. **P1's effect cannot be told from zero**
  over six seeds, and it ranges from −6.2% (nobody leaves) to +7.0% (seed 5).
- **The ramp no longer decides P2's sign** (it did on 10 October). Its cost is
  visible, as the data say it should be: with the ramp as built, P1 adds 16 to
  81 vehicle-hours of ramp waiting in four of the six seeds.
- **But four minutes of reopening decide it.** Both lanes are back at 10:04 by
  AID01104; traffic first passes at 10:00. With both lanes reopening at 10:04,
  **both plans add delay in all six seeds** (P1 +12.4%, P2 +3.7%). The advice runs
  until the reopening, the queue it keeps on the road is at its longest then,
  and in those four minutes it reaches back to where drivers enter the network
  (waiting to enter rises by 35 vehicle-hours for P2 in seed 2026). The
  reopening time is not known closer than those four minutes.
- **P2 beats P1 almost everywhere**: in 17 of the 18 paired seeds above and in
  every one-change run except "nobody leaves", where they tie (P2 minus P1:
  +1 vehicle-hour). The exception is seed 3 at 10:00, +6 vehicle-hours.

So on this model, with the stand-ins, "P2 is better than P1" nearly holds
everywhere, and "P2 is better than doing nothing" does not.

## 9. Go/no-go, against section 3 of the review

| Item (review section 3) | 10 October | Version 3 | Met? |
|---|---|---|---|
| 1. Tunnel side, closure GEH ≥ 85% | 83.15% | 91.80% (91.3 to 93.4% in every seed, both ramp bounds, 10:00 or 10:04) | **Yes** |
| 2. Ramp settled by evidence | ranking depended on it | Measured: 0.51 per vehicle. Both representations run as bounds; P2's sign the same under both | **Bounded**, not built |
| 3. Speeds ≤ 15% on signs P0, P1 and P2 share | 16.94% | 24.83% (23.6 to 26.2% across all runs). 14.9% without AID01102 and AID01103; 12.99% where measured ≥ 30 km/h; congestion state agrees in 93.3% of bins | **No**, as written |
| 4. One-stage reopening | 20 minutes on one lane (one-stage run: 15.78% speed) | Both lanes at 10:00; 10:04 run too | **Yes**; and the plans are sensitive to it |
| 5. No wrong-lane teleport | 3 | 1 in seed 2026, 1 to 3 across seeds, all at the instant a lane shuts | **No**, as written |
| 6. Seeds | done | Six, paired, under both bounds and both reopening times | **Yes** |
| 7. Drivers-leave rule agreed or sourced | 0.4, fitted to biased counts | 0.2, fitted to when the queue reached AID01101; plans run at 0 to 0.3 | **Partly**: still fitted, no source |

**Data's position: still NO-GO for ranking plans against doing nothing, as of
13 October.** Two items fail as written (3 and 5), and on the stand-ins the
answer to "does this plan beat doing nothing?" changes with four minutes of
reopening time that the detectors cannot narrow. Even if items 3 and 5 were
waived, a ranking against P0 would not survive the grid.

What has changed is what a go now needs. No new data are needed for items 1,
2, 4, 6 and 7. The rest are decisions for the Lead and Simulation:

1. **Accept the slow-count rule** (section 1): counts measured under 30 km/h are
   not scored. It rests on 48 days that are not 15 May.
2. **Decide how the queue's speed is scored.** A MAPE over bins measured at 3 to
   14 km/h can only be met by putting the measured speed into the model, which
   is what the 10 October replay did, and that caps the flow. A proposal: score
   speeds by MAPE where the measured speed is 30 km/h or more (12.99%, target 15%)
   and by congestion state everywhere (93.3%, target 85%), and report the full
   MAPE beside them.
3. **Decide whether a teleport in the first minutes after a lane shuts counts
   against a run.** The fix for the 09:00:30 kind is tested and waiting for the
   next code change.
4. **Adopt the grid as the rule for any ranking**: a claim is made only if it
   holds in every cell (six seeds, both ramp bounds, reopening at 10:00 and
   10:04, leave share 0.1 to 0.3, 5 and 6.5 m vehicles). Seed noise alone is not
   the test.

With 1 to 3 accepted, version 3 is a defensible P0 for the Lead's plans
**(conditional go)**, and rule 4 decides what may be said about them. On the
stand-ins, rule 4 would allow "P2 is better than P1" with its two near-ties
stated, and nothing against doing nothing. The Lead's plans may separate more
clearly if they differ in timing or scale, or act on the entry queue.

Not settled by any of this: the lanes and signal timings of the road under the
flyover (they set the detour's capacity, and P2 acts on one of the signals), the
+20 s at Tong Bin Lane as a real control, and where leaving drivers went.

## 10. Reproduce

```bash
# once: the replay inputs, as in src/evaluator/README.md, then
python -m src.evaluator.speed_signs --build sim/work/p0-replay-build \
    --inputs sim/work/p0-replay/twin-inputs_20260515_no-mainline-join.json \
    --observations sim/work/p0-replay/detectors.json \
    --ordinary-only AID01101 AID01102 AID01103 AID01104 AID01106 AID01107 AID01108 AID01109 AID01110 \
        AID01214 AID01215 AID01216 AID01217 AID01218 AID01219 AID01221 AID01222 AID01223 \
        TDSAPR10001 TDSAPR20001 TDSSPWR10001 TDSSPWR10002 TDSSPWR10003 TDSSPWR20001 TDSSPWR20003 \
    --drop-edge 44419212 "814979901#0" 1198059118 1198059119 1198059120 \
    --out sim/work/p0-replay-build/speeds-ordinary.add.xml
python -m src.loaders.fetch withhold-slow-counts --observations sim/work/p0-replay/detectors.json \
    --min-count-speed 30 --out sim/work/v3/detectors-slow-withheld.json

# the evidence (reads data/raw/detectors only)
python -m src.loaders.fetch count-bias --exclude-day 2026-05-15
python -m src.loaders.fetch merge-tradeoff --exclude-day 2026-05-15

# the rehearsal set, then any one-change run
python -m src.evaluator.batch --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal \
    --scenario sim/scenarios/evaluator_IN-26-03365_replay-v3.json --clearance 66 \
    --results-dir results/evaluator-rehearsal-v3
python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal --plan P0 \
    --scenario sim/scenarios/evaluator-diagnostics/v3/v3-ramp.json --compliance 0.5 --clearance 66 \
    --results-dir results/evaluator-diagnostics
```

`speeds-ordinary.add.xml` must hash `bc56f690…0947a` and
`detectors-slow-withheld.json` `5ad28fea…a8d40`. Linux, Python 3.13.16, SUMO
1.27.1; not run on Windows. The 10 October P0 was re-made first from the same
inputs and matched its committed result in every field.
