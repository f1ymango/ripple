# IN-26-02615: Simulation review of Data's replay-v2 proposal (14 Oct 2026)

Reviewed Data branch `data/tuen-mun-oct14` at `9b434fd`, without merging its inputs into this branch. This is a diagnostic review for the 16 Oct decision, not acceptance of a traffic benefit. Keep the Aberdeen submission separate.

| Check | Simulation position | Evidence and condition |
|---|---|---|
| Scene between TDS90032 and TDS90033 | Agree with the bracket; exact position unresolved | `sim/tuen-mun/detectors-placement.json` puts TDS90032 on `389939170-approach` and TDS90033 on `389939170-b`, about 510 m apart along the model route. `389939170-scene` is a 250 m hypothesis inside that bracket. Compare both plausible ends without picking the better headline score alone. |
| Closure phases and lane IDs | Qualified | TD reports one remaining lane at 17:59 and reopening at 18:46. Detector flow can suggest changing capacity, but TDS90033 is downstream of the scene and does not directly identify which physical lane was closed or prove a shoulder was used. Fast-first, middle-open, 18:17 relaxation, and 18:41 renewed restriction are model assumptions. Keep TD-text one-lane-until-clearance as a sensitivity. Use the observed queue and downstream flow profiles to assess each. |
| Castle Peak Road route | Accept as a candidate route, conditional on connection audit | `sim/tuen-mun/demand_20260415.json` records the directed Sham Tseng exit–Castle Peak Road–Siu Lam on-slip path. `sim/tuen-mun/fixes.con.xml` restricts the on-slip to the nearside lane and repairs three dead-ending lanes. Those edits address identifiable network defects but need lane-level visual/source review at each junction before a public route highlight. |
| Sham Tseng signal and road speeds | Calibration assumptions, not observed controls | `sim/tuen-mun/signals.tll.xml` supplies an actuated programme and pedestrian clearance with no published timings. The fixed-time variant changes plan outcomes. `scripts/tuen_mun/build_network.py` scales non-motorway limits by 0.68 to fit ordinary-day segment speeds; useful for diagnosis, not an independently measured speed limit. Preserve both signal cases. |
| Ordinary-day demand | Qualified | `scripts/tuen_mun/demand.py` uses TDS90019, ordinary-day Ting Kau differences, census roads, and fitted exit shares. The Siu Lam calculation also uses an explicit 0.5 Castle Peak Road rejoin assumption. Document conservation and a sensitivity to that share. |
| Own diversion | Reject 1,141 removed vehicles as an accepted P0 input | `scripts/tuen_mun/demand.py` computes `1441 - 300` from differences in detector totals. It is a balancing residual, not a measured origin, turn, or Route 3 count. Removing it before entry can improve count GEH while lowering the vehicles exposed to the queue and the delay denominator. The 291 extra Castle Peak Road entrants also need an independent count or uncertainty range. Test queue-triggered route choice while keeping all generated vehicles in an explicit route/accounting ledger. Do not add or remove vehicles to target the detector score. |
| Current P0 outcome | NO-GO for a measured plan ranking | `docs/tuen-mun-2026-10-14.md` reports 87.2% GEH, 14.7% free-flow speed error, and 92.2% congestion agreement, yet the queue is 26–40 versus observed 8–24 km/h, clears about 30 minutes early, and discharges ~6,800 versus ~4,560 veh/h after reopening. One of three seeds has a wrong-lane teleport. These are material to the plan-delay comparison. |

## Predeclared bounded P0 comparison

Freeze the observation bins, detector exclusions, network/demand hashes, evaluator version, seeds and reporting code before rerunning. Change one scene or behaviour assumption per variant and give each a new scenario label and provenance sidecar. Use the same three seeds, one clearance time, and the same 17:30–20:30 count window. Report each candidate regardless of outcome:

1. Replay-v2 unchanged as the reference, including the 1,141 residual clearly labelled as fitted.
2. Scene near each end of the TDS90032–33 span, keeping the same 250 m length and closure phases.
3. Middle lane open in the one-lane phase, with the same timing.
4. TD-text one-lane phase through reported reopening, with no inferred 18:17 or 18:41 phase change.
5. Queue-triggered own diversion with no upfront 1,141-driver subtraction. Log route choice, number of vehicles generated/departed/arrived/waiting, and Route 3 and Castle Peak Road flows. If the trigger does not explain the upstream deficit, report the mismatch; do not rebalance demand.

For each variant, compare 5-minute TDS90024/29/32/33/34 counts, coverage and lane validity; 5-minute speeds at the queued detectors; queue onset, tail, and clearance; after-reopening discharge; ramp and Sham Tseng exit backlog; waiting to enter; teleport count and location; and the vehicle conservation ledger. A variant is credible only if it fixes the physical queue/recovery disagreement without creating an unexplained flow deficit or teleport. Do not select by aggregate GEH alone. The residual-removal variant can bound sensitivity but cannot establish an accepted P0 without independent evidence for where those drivers went.

## Decision and handoff

Data can run the bounded variants with the above frozen criteria. Simulation will review the resulting original provenance and lane-level network evidence. Until that review, matched P1/P2 stand-ins remain diagnostics; their rank varies with an unsourced Sham Tseng signal programme, and Data's draft plan context has not been approved by Lead. For the 16 Oct call, default to **no measured saving or route recommendation** if the queue, flow conservation, or signal control remains unresolved.
