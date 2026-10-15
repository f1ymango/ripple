# Simulation final call for the 16 Oct claims freeze

**Incident:** IN-26-02615, Tuen Mun Road near Hong Kong Garden, 15 Apr 2026.
**Status:** ready for a **labelled modelled-candidate comparison** in the two-incident pack; **not ready** for a measured traffic-improvement or physically validated incident-replay claim.
**Frozen plans:** `data/generated-plans/IN-26-02615-lead-capacity-oct15/` (Lead's 11% P2). Keep the raw model plan set and later share tests out of the frozen comparison.

## Evidence reviewed

Data branch `data/tuen-mun-oct14` at `c4ec872` contains the frozen bundle in `results/demo-oct16/`, the matched grid in `results/tuen-mun-lead-grid-oct15-p0x-merge-at-site/`, and the team's ranking in `results/rankings/lead-capacity-oct15-p0x-merge-at-site.json`. The source narrative and limitations are `docs/tuen-mun-go-no-go-evidence-2026-10-15.md` and `docs/demo-two-incidents-2026-10-16.md` on that branch. Simulation's independent first-seed sensitivities and original sidecars are in `results/tuen-mun-p0-variants-oct15/` on this branch at `a186ef0`; `scripts/tuen_mun/verify_p0_variants_oct15.py` verified their committed scenario and route hashes.

The frozen comparison uses `p0x-merge-at-site`: replay-v2 with move-over on the 250 m approach. Data reports that its P0 passes the formal validation targets for all 18 fresh-grid cells (seeds 2029–2031, compliance 0.3/0.5/0.7, actuated and fixed-time Sham Tseng signals): GEH 86.3–88.7%, free-flow speed error 13.8–14.0%, congestion-state agreement 91.5–92.1%, and no disqualifying wrong-lane teleport. The result card at 50% compliance, seed 2029 shows modelled delay P0 1,300.6, P1 1,545.9 and P2 1,235.1 vehicle-hours. Under the team's pre-existing paired ranking rule, P2 is before P0 by 4.31% of P0 delay (95% interval 3.03–5.59%) and before P1. With the longer Castle Peak Road drive charged, Data reports 3.70% (2.43–4.97%).

**Qualification:** Data's stricter Tuen Mun protocol required P2 to beat P0 in every cell and every outside-delay sensitivity; it fails that rule at actuated seed 2030 and 30% compliance. P1 is worse than P0 in aggregate, but it is better in some low-compliance cells. Use “ranks ahead across the model grid,” not “wins every case.”
The reported 95% interval summarizes variation across simulated grid cells, which reuse three seeds and one demand model; it is not a confidence interval for real-road savings.

## P0 physical call: NO-GO for measured benefit

The chosen P0 satisfies aggregate validation but misses material incident physics:

| Check | TD observation | Chosen P0 | Consequence |
|---|---:|---:|---|
| Queue speed, Sham Tseng to crash | about 20.6 km/h | 41–43 km/h | Too little severe congestion in the replay |
| Difference between lane speeds in the queue | about 6.0 km/h | 36–37 km/h | Model leaves lanes moving beside a standing lane |
| Ting Kau queue recovery | later observed recovery | clears early | Delay and route-choice timing are not physically matched |
| Post-reopening downstream discharge | 4,560–4,896 veh/h | 6,100–6,200 veh/h | Recovery is too fast |

These comparisons come from Data's committed 5-minute detector and lane audit in `docs/tuen-mun-go-no-go-evidence-2026-10-15.md` and `docs/tuen-mun-p0-variants-and-lead-grid-2026-10-15.md`. The alternative merging-in-turn replay brought queue speeds closer to observed but failed count validation and sometimes stalled; it cannot replace the frozen P0. Simulation's middle-open sensitivity also passed aggregate targets while leaving TDS90024 at 37.1 km/h versus 10.6 observed at 18:15 and clearing too early. The no-residual sensitivity failed aggregate targets and produced a wrong-lane teleport. No tested P0 clears both the flow and physical-queue checks.

The 1,141 drivers removed from Ting Kau entry remain a detector-balancing residual, not a measured destination or detour count. The 291 extra Castle Peak Road entrants, 0.5 Siu Lam rejoin share and Sham Tseng signal timings are assumptions. They limit the causal interpretation of any plan effect. Do not imply that the result estimates actual delay saved on 15 Apr.

## Wording and handoff

**Approved technical wording:** “In a matched SUMO experiment on the frozen Tuen Mun scenario, the Lead's 11% targeted Castle Peak Road plan ranked ahead of no advice and blanket advice under the team's ranking rule. The incident baseline still reproduces the upstream queue and recovery poorly, so this is a modelled candidate, not a measured road benefit.”

**Short slide/video caveat:** “Modelled comparison; observed queue was slower and lasted longer than the replay.”

**Avoid:** “proven improvement,” “saved 4% on the road,” “P2 wins every run,” or a Tuen Mun map/route animation that is not tied to the frozen scenario. For the visual capture, use the Tuen Mun comparison panel/result card; the existing map depicts Aberdeen.

**Final Simulation artifact:** this file on `sim/tuen-mun-p0-variants-oct15`, alongside `docs/tuen-mun-p0-variants-first-seed-2026-10-15.md`.
**Ready/not-ready:** ready for the frozen **two-case presentation with the caveat above**; not ready for a validated benefit claim.
**Blocker:** no P0 yet matches the observed lane-wide queue, recovery and post-reopening discharge while passing the count checks; demand diversion and Sham Tseng signal control also lack direct measurements. The frozen results should not be changed to fix this after the freeze without a team correctness review.
