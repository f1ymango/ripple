# Tuen Mun matched comparison: protocol (Data, 14 Oct 2026, 20:15 HKT)

This was written and committed **before any P1 or P2 run**. Nothing below may change after outcomes are seen. A changed input means a new label and a rerun of every cell.

## Frozen P0: `replay-v2`

**Scenarios:** `sim/scenarios/tuen-mun/evaluator_IN-26-02615_replay-v2{,-s2027,-s2028}.json`, written by `scripts/tuen_mun/write_scenario.py` with its defaults.

**Network:** `sim/tuen-mun/network.net.xml`, sha256 97f5a64b…. It is built by `scripts/tuen_mun/build_network.py` and includes:
- OpenStreetMap geometry and TD speed limits;
- non-motorway roads at 0.68 × the limit, fitted to TD's ordinary-day segment speeds;
- corrections to OSM, `sim/tuen-mun/fixes.*`;
- Sham Tseng Interchange stages, `sim/tuen-mun/signals.tll.xml`.

**Demand:** `sim/tuen-mun/demand_20260415.rou.xml`, sha256 6bab6f89….
- TDS90019 on the day.
- The Ting Kau merge as on ordinary Wednesdays, less 1,141 drivers who decided before reaching Ting Kau.
- Castle Peak Rd from the 2024 census, plus 291 drivers from the Tsuen Wan end.
- Vehicles: tau 1.0 s, no start-up delay, 7.0 m long.

**Closure:**

| From | Lanes shut |
|---|---|
| 17:48 | fast |
| 17:59 | fast and middle |
| 18:17 | fast |
| 18:41 | fast and middle |
| 18:47 | reopened (clearance 59 min) |

The open lanes pass the scene at 30 km/h.

**Drivers' own diversion:**
- Share 0.2 at Ting Kau, once traffic at TDS90024/25 is under 15 km/h.
- 4 minutes charged outside the model for each driver who leaves.

**Fit record:** P0 fits fit-a … fit-n are in `sim/work/tuen-mun/fit` and are not committed.

The criteria were fixed before choosing:
- validation v2;
- counts at TDS90024/29/33 over 17:30–20:30;
- drivers leaving at Ting Kau close to the Route 3 gain at AID03115/16 (about 300);
- congested detector-bins.

fit-n met validation v2:

| GEH | Free-flow speed error | Congestion-state agreement | Wrong-lane teleports |
|---|---|---|---|
| 87.2% | 14.7% | 92.2% | 0 |

Counts came within 193–356 of TD's, and 371 drivers left.

**Known shortfalls, reported with every result:**
- The model's queue between Sham Tseng and Hong Kong Garden moves at 26–40 km/h, against 8–24 km/h measured.
- It clears at Ting Kau about 30 minutes early.
- After the reopening the model discharges about 6,800 veh/h at TDS90033, against 4,560 measured.
- P0's delay is therefore probably understated.

## Plans: `data/generated-plans/IN-26-02615-rehearsal`
Written by `src.evaluator.rehearsal_plans` from `data/plan-context/IN-26-02615_data-draft.json`, Data's draft context, for the Lead to revise.

- **P0:** do nothing.
- **P1:** everyone heading through the crash site for Tuen Mun is advised to take Castle Peak Rd: leave at the Sham Tseng exit, rejoin at Siu Lam. Share 1.
- **P2:** the same advice to 30% of them.

**Why 30%, before any run:**
- Castle Peak Rd's spare capacity through the Sham Tseng Interchange's exit-slip stage is about 1,000 veh/h. That is the stage's 40 s maximum in a cycle of about 90 s on two lanes, less the ordinary exit flow of about 600 veh/h.
- The Tuen Mun-bound demand through the site while plans act (17:59–18:47) is 2,083 vehicles, about 2,600 veh/h.
- 1,000 ÷ 2,600 is about 0.38 at full compliance. 30% leaves a margin.

**Not in any plan:**
- signal changes, since TD publishes no timings;
- signs as a separate effect;
- public transport;
- drivers heading for Siu Lam, whose exit slip Castle Peak Rd cannot reach in this network.

Plans act from TD's 17:59 message until the reopening at 18:47.

## Grid
- 3 seeds: 2026, 2027, 2028.
- Compliance 0.3, 0.5 and 0.7.
- Clearance 59 min.
- P0, P1 and P2 in each cell: 27 runs, E as committed on this branch.

## Outcome measures
Computed by `scripts/tuen_mun/report.py`:

1. **E's total delay:** timeLoss, plus waiting to enter, plus 4 minutes per driver who left at Ting Kau.
2. **The same with the longer drive charged.** For each car on a longer route than its flow's normal one, add its ideal driving time minus the normal route's ideal time, both from SUMO. E's timeLoss does not charge Castle Peak Rd's extra distance.
3. Measure 2 recomputed with 0 and 10 minutes charged per driver who left.
4. Also reported:
   - drivers who took the advised route;
   - Castle Peak Rd queues and teleports;
   - vehicles still driving or waiting at the end;
   - each run's validation block.

## Decision rule
P2 "beats P0" only if measure 2 is lower than P0's in **every** cell (3 seeds × 3 compliance) and under each of the 0, 4 and 10 minutes outside.

Anything less is reported as **mixed** or **no improvement**, with the numbers. P1 is reported the same way.

**Regardless of outcome:**
- No saving or recommendation goes into the materials until the Lead's 16 Oct go/no-go, given P0's known shortfalls.
- The result stays separate from the Aberdeen submission.
