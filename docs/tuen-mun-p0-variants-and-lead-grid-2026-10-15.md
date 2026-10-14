# Tuen Mun: Simulation's P0 variants and the Lead's fresh grid. Run plan, frozen before any run (Data, 15 Oct 2026, 01:30 HKT)

This plan carries out two predeclared requests, without changing either:
- Simulation's predeclared P0 comparison: `docs/tuen-mun-p0-simulation-review-2026-10-14.md`, from `sim/tuen-mun-p0-spike-oct14` at 600c158.
- The Lead's fresh plan grid: `docs/tuen-mun-lead-plans-2026-10-15.md`, at 3db6045.

All inputs below were committed before any of these runs. Nothing changes after outcomes are seen. A change means a new label and a rerun.

## Frozen inputs (sha256, first 12 hex)

| File | sha256 |
|---|---|
| `sim/tuen-mun/network.net.xml` | 97f5a64ba610 |
| `sim/tuen-mun/network-fixed-time.net.xml` | 4bd7241f977b |
| `sim/tuen-mun/network-scene-upstream.net.xml` | 258de014ebe1 |
| `sim/tuen-mun/network-scene-downstream.net.xml` | 9e448d1b5087 |
| `sim/tuen-mun/demand_20260415.rou.xml` | 6bab6f898fab |
| `sim/tuen-mun/demand_20260415-no-residual.rou.xml` | 7716b383403e |
| `sim/tuen-mun/observations_20260415.json` | 415a66fd2daa |
| `sim/tuen-mun/detectors.add.xml` | 1759e7265a5e |
| `sim/tuen-mun/detectors-scene-upstream.add.xml` | 47585c4a1886 |
| `sim/tuen-mun/detectors-scene-downstream.add.xml` | 665b6393e1dd |
| Lead plan set `data/generated-plans/IN-26-02615-lead-capacity-oct15/P0.json` | 832b2646e691 |
| Lead plan set `P1.json` | 51cc3ab9b448 |
| Lead plan set `P2.json` (share 0.11) | 0defc99a1f4a |
| Lead plan set `generation-inputs.json` | a8479854edeb |

The evaluator is E as committed on this branch. Its code is unchanged since 4c5db06.

## Part A: Simulation's P0 variants (diagnostic)
- **Results:** `results/tuen-mun-p0-variants-oct15/`.
- **Plan set:** `IN-26-02615-p0-only`.
- **Every variant:** seeds 2026, 2027 and 2028, clearance 59 min. P0 does not depend on compliance, so each run uses 0.5.

| Simulation # | Label | One change from replay-v2 |
|---|---|---|
| 1 | `p0v-reference` | none (rerun; the 1,141 removed Ting Kau drivers stay, labelled as a fitted residual) |
| 2 | `p0v-scene-up` / `p0v-scene-down` | the same 250 m scene and approach at the upstream end (2,605–2,855 m) or the downstream end (2,845–3,095 m) of the TDS90032–33 span |
| 3 | `p0v-middle-open` | the middle lane, not the slow lane, stays open in the one-lane phases |
| 4 | `p0v-td-text` | one lane from 17:59 until the reopening; no 18:17 or 18:41 change |
| 5 | `p0v-no-residual` | the 1,141 are not removed. Own diversion only through the queue-triggered Route 3 rule, share 0.2 as before. Demand is not rebalanced. |

**Reported per variant and seed** (`scripts/tuen_mun/p0_variants_report.py`):
- 5-minute counts at TDS90024/29/32/33/34, against TD's counts with their coverage and lane validity;
- 5-minute speeds at the queued detectors;
- queue onset, tail extent and clearance at each detector;
- discharge after the reopening at TDS90033;
- the Sham Tseng exit backlog and waiting to enter;
- teleports, with count and location;
- a vehicle ledger: loaded, inserted, arrived, still driving, waiting, left at Ting Kau by exit;
- Route 3 and Castle Peak Rd flows.

**Selection**, as Simulation set it:
- A variant is credible only if it fixes the queue and recovery disagreement without an unexplained flow deficit or teleport.
- No variant is chosen on aggregate GEH alone.
- The residual-removal variant only bounds the sensitivity.

## Part B: the Lead's fresh grid
- **Results:** `results/tuen-mun-lead-grid-oct15/`.
- **Plan set:** `IN-26-02615-lead-capacity-oct15`, which is final and does not change after results.
- **Grid:**
  - seeds 2029, 2030 and 2031, never used before;
  - compliance 0.3, 0.5 and 0.7;
  - Sham Tseng signals vehicle-actuated (`replay-v2-s20xx`) and fixed-time (`replay-v2-fixed-s20xx`);
  - P0, P1 and P2 in every cell: 54 runs.
- **Delay measure:** `scripts/tuen_mun/report.py`, with the longer Castle Peak Rd drive charged and 0, 4 and 10 minutes outside.
- **Also reported:** cars diverted, exit queues, waiting to enter, teleports, and P0's detector and queue checks.
- **Decision rule, unchanged:** P2 is lower than P0 in every cell and under each outside value. P1 is reported the same way.
- **This P0 is replay-v2,** the P0 the Lead's request names. Simulation rates it no-go for a measured ranking (queue too fast, clears about 30 min early). So any P2 result here is a candidate for the 16 Oct review, not a measured saving.
- If a Part A variant turns out credible, the same plan set may be run on it as a further labelled grid. That decision rests on Simulation's criteria, not on plan outcomes.

## Part C: Data's candidates after the variant runs (15 Oct, written before they run)
None of Simulation's five fixes the queue speed, and neither does Data's `p0x-merge-at-site` (drivers learn of the closure on the 250 m approach, not along the 2.45 km edge before it). Lane by lane, every one of those runs shows the same thing at TDS90025–32, 18:00–18:15:
- **Open lane at the scene:** stands still (0–80 veh/h at 1–10 km/h).
- **Lanes shut ahead:** run past it at 45–65 km/h, and their drivers cut in at the end of the approach.
- **Loop speeds:** a loop's speed is the volume-weighted mean over the vehicles that pass, so the moving lanes set it. The standing lane barely registers, which is how the model reads 40–45 km/h.
- **What TD saw:** all three lanes queued at 7–20 km/h, occupancy 60–100% (raw lane readings, `src/loaders/detectors.py`).
- **Knock-on effects:** the standing queue is in the nearside lane, which is also the Sham Tseng exit lane. So the exit's flow fell from about 670 to 36–170 veh/h, and the queue reached the Ting Kau merge in that lane alone.

A network zipper at the scene (diagonal links from each lane into the one beside it) was tried and dropped before any replay. SUMO took the diagonal link even with every lane open, which left the fast lane at the scene empty in ordinary traffic.

| Label | Changes from replay-v2 |
|---|---|
| `p0x-zipper` (+ `-s2027`, `-s2028`) | move over on the approach, and **merging in turn** (`merge_in_turn`, E `src/evaluator/simulate.py` sha256 6587b72dafad…): a driver in a lane shut ahead keeps to it and moves over one lane at its end only behind a driver of that lane who did not just move in (one each); a slow driver behind holds back 3 s |
| `p0x-zipper-sigma05` (+ `-s2027`, `-s2028`) | the same, and drivers' imperfection sigma 0.5 (SUMO's default; the twin had 0), `sim/tuen-mun/demand_20260415-sigma05.rou.xml` sha256 3f9dcadcfff2…. It lowers the flow out of a standing queue. TD measured 4,560–4,896 veh/h at TDS90033 after the reopening; every run so far gave 6,100–6,900. |

**sigma 0.5 on ordinary Wednesdays** (`results/tuen-mun-p0-variants-oct15/ordinary-days-driver-imperfection.json`): both days still meet version 2.

| Day | sigma | GEH | Free-flow speed error | Congestion state |
|---|---|---|---|---|
| 22 Apr | 0.5 | 90.38% | 11.38% | 100% |
| 22 Apr | 0 | 97.22% | 10.92% | 100% |
| 6 May | 0.5 | 96.36% | 12.64% | 99.34% |
| 6 May | 0 | 96.67% | 11.53% | 99.34% |

Same criteria as Part A: the queue speed and extent at TDS90024–32, the recovery and the discharge after the reopening, no unexplained flow deficit, no wrong-lane teleport, and the ledger. A candidate is credible only if it meets Simulation's criteria as well as version 2. If one is, the Lead's plan set from Part B runs on it as its own labelled grid (`results/tuen-mun-lead-grid-oct15-<label>/`), with the same seeds, compliances and decision rule.
