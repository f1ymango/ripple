# Why the incident plan comparison is still a diagnostic

**Component C assessment, 13 October 2026. Decision: no accepted P0 or plan
ranking yet.** This note uses the saved Lead-plan replay at
`results/lead-draft-diagnostic-oct13/` and the original five-minute comparison
at `sim/work/evaluator/2026-05-15_ABD_P0_c50_t66_replay_lead-draft-20261013-b/evaluation.json`.
The latter is generated locally and ignored by Git; rebuild it with the command
in `docs/lead-plan-diagnostic-2026-10-13.md`. The committed result and
provenance sidecar bind the replay to its inputs. No detector value or flow was
added to the model for this assessment.

## What fails, in order of consequence

| Cause | Direct evidence | Resolution gate |
|---|---|---|
| Missing or mislocated tunnel-side traffic | In the ten closure bins available in the saved evaluation, AID01106 averages **89.5 observed versus 46.6 simulated** vehicles per five minutes (8/10 bins fail GEH), AID01107 **82.4 versus 46.6** (6/10), and AID01108 **95.7 versus 46.2** (8/10). AID01103 before the fork averages only **43.3**. The two-lane AID01106 loop is at 0.10 m on tunnel-entrance edge `1198101443`, near a junction. The network also has surface-road and Ocean Park Road joins between the flyover and tunnel. | Independently verify AID01106's physical cross-section and the gross turning/entry counts on those joins in the incident window. Re-place the detector or change demand only if that evidence supports it. The AID01106–07 deficit shows that moving a single loop is not enough by itself. |
| Ramp-dependent plan sign | With the corrected main-line origin, the earlier rehearsal P2 adds **5.2%** delay at 50% compliance; with the ramp approach retained it saves **2.7%** in that model. The physical ramp priority and where flow `f22` enters have not been independently established. The saved Lead plans also use this corrected main-line origin. | Obtain a reviewed road/turning source for the north join. Run matched P0/P1/P2 on the supported geometry; show ramp waiting separately. Do not choose the geometry from the better score. |
| Non-independent incident speed inputs | The saved P0 meets whole-run 14.44% speed MAPE, but 672 of 787 speed bins are on roads with speed signs refreshed from the incident morning itself. The model-generated-speed subset is **31.33% MAPE over 115 bins**. With ordinary-morning signs on all roads, the documented P0 speed error is **16.94%**. | Compare all plans with the same pre-incident/ordinary-day speed inputs and diagnose queue arrival and recovery; incident-day signs cannot be the evidence for counterfactual improvement. |
| Scene and route behavior chosen by fit | The 20-minute one-lane stage after 10:00 conflicts with AID01104 showing both lanes carrying vehicles from 10:04. The 40% leave-corridor rule and 20-minute outside-network delay are fitted/assumed. There are still three wrong-lane teleports in P0, seven in P1 and six in P2. | Remove the unsupported reopening stage in a labelled sensitivity, trace all wrong-lane vehicles, and obtain independent exit/turning evidence before accepting the leave rule. |

The closure-phase count result is **83.15% of 267 eligible bins**, below the
85% target. It needs only five more passing bins to cross the numeric line,
but that would not resolve the roughly twofold tunnel-side flow deficit or
the ramp-dependent reversal. Conversely, the 89.45% whole-run count result
does not validate incident behavior. The saved plans were run for one seed;
the previous rehearsal's paired-seed stability does not establish the exact
Lead plans' ranking or remove structural bias.

## Source audit and disposition

- `results/twin/oct09-evaluator-approach-audit.json` records the compiled lane
  connections, OSM tags and ramp signal. The source review in
  `docs/simulation-evaluator-review-2026-10-09.md` places AID01106 at the
  tunnel entrance and identifies the side-road joins. The reviewed sources do
  **not** contain independent incident-window turning counts for those joins.
- `docs/evaluator-replay-fixes-2026-10-10.md` isolates the ramp-origin
  sensitivity, ordinary-sign speed miss and one-stage reopening sensitivity.
  The surface detour correction removes a routing artefact, but its remaining
  flow deficit is still material.
- A refresh of `origin/main` on 13 October found no newer reviewed source for
  tunnel-side turning flow, physical ramp control or the initial closure lane.

**Practical solution now:** use the completed runs only to demonstrate that
recorded AI plans reach a seeded evaluator with exact provenance. Keep observed
incident playback and the operator review workflow as the public demonstration.
Do not state a recommended route, delay saving, or CO2 benefit. A defensible
P0/P1/P2 claim requires the independent location/turning and ramp evidence
above, then common-input paired runs and a joint Data/Simulation review. Those
measurements cannot be reconstructed from the existing detector totals alone:
net changes between detectors do not identify gross joins and exits.
