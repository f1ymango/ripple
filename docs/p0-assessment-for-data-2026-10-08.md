# IN-26-03365: Simulation assessment for Data review, 8 October HKT

> **Superseded on 9 October:** Simulation has reviewed Data's newer evaluator
> replay and completed section 4 on `data/evaluator-e-oct07` at `cfb4d04`.
> [Shared decision](https://github.com/f1ymango/ripple/blob/cfb4d04/docs/evaluator-p0-go-no-go-2026-10-09.md)
> and [technical review](https://github.com/f1ymango/ripple/blob/cfb4d04/docs/simulation-evaluator-review-2026-10-09.md).
> Both positions are NO-GO for public plan comparison by 14 October. The newer
> E replay already reroutes at full closure. Independent control and earlier
> move-over runs completed on 10 October; the earlier warning did not remove
> the wrong-lane teleport or closure count gap. The older route-assignment gap
> below is not a complete diagnosis of that newer run. Retained as the dated
> assessment made before Data's newer artifacts were available here.

**Status: cannot yet justify a corrective P0 rerun or accept P0 for plan
comparison.** This is Simulation's side of the requested joint assessment.
Data/E should add its independent evidence and agreement before anyone calls
the outcome joint. The evidence cutoff below is the last locally reviewed
PR #46 revision `647b13c` and the 7 October P0 audits; a newer team branch
has not been verified here.

## Checked evidence and unresolved questions

| Question | Evidence presently available | Consequence |
|---|---|---|
| How did vehicles reach Aberdeen Tunnel while the flyover was empty? | In the three eligible 09:45–10:00 bins, AID01104 observed **0**, AID01106 **228**, AID01107 **204**. P0 simulated **0/33/34**. The provisional OSM network contains a 694 m passenger path via the surface road, but **zero generated flow definitions** follow it through to the tunnel. Two ordinary-day joins contribute 125 veh/h. [Route-cut audit](../results/twin/oct07-p0-cut-audit.json). | The model has the road connection but lacks an evidence-backed incident route choice and surface entry flow. Do not set an arbitrary diversion percentage. |
| Is the bypass physically plausible? | The provisional network connects the surface fork to the tunnel through named Wong Chuk Hang Road segments; it also shows entries from Nam Long Shan Road, Tong Bin Lane and Ocean Park Road. The ordered path is in [Simulation's demo handoff](simulation-demo-handoff-2026-10-07.md). | **Plausible in the OSM graph, not physically approved** for an operator recommendation. Check actual junction access, turning rules and road use against an independent map/source. |
| Are detector and closure positions defensible? | AID01104 matches the two-lane flyover at 136.31 m on `44419212`. AID01106 is projected 20.73 m from lane 0 at the start of a short tunnel edge. TD's 09:01 first report leaves the lane unspecified; 09:36 all-lane and 10:02 clearance are report times. [Network audit](../results/twin/osm-network-audit.md), [P0 setup](p0-setup-proposal-2026-10-06.md). | The first slow-lane and physical phase seconds remain assumptions. AID01106's exact cross-section and the closure extent require review. |
| Does the ramp explain the P0 failure? | Ramp flow `f22` schedules 2,481 vehicles; 1,641 inserted by 10:35, matching 840 pending. A same-input no-closure control still has 964 waiting. The compiled signal has 80 s green, 5 s yellow, 5 s red and a minor-priority merge; actual control is unsourced. [P0 follow-up](p0-followup-2026-10-07.md). | A separate bottleneck affects completeness and queue credibility. Do not change signal timing or priority solely to improve scores. |

## What was tried

The first bounded P0 used PR #46's generated network and default-driver,
unsigned-speed demand, seed 2026, 07:25–10:35 horizon, `_0` closure at 08:55,
both lanes at 09:36, reopening at 10:02. The initial launch **failed before
time zero** because loops referenced the pre-split AID01107 edge. The existing
loop relocation fixed that input-path issue without changing observations.
The corrected run completed 11,400 seconds: **87.15% GEH < 5 / 607 count
bins, 47.33% speed MAPE / 790 bins, 72 teleports, 840 pending departures and
1,881 unfinished**. Its early AID01104 total was 547 versus 17 observed over
six eligible bins. [Full P0 diagnostic](p0-diagnostic-2026-10-07.md).

A bounded 09:15 all-lane timing sensitivity also completed. That time is a
**diagnostic assumption**, not an observed physical transition. It matched
more zero-flow bins but scored **83.86% GEH**, produced **130 teleports** and
still missed downstream flow and recovery. The same-input no-closure control
had **964 waiting** and **56.90% unsigned-speed MAPE**. No corrective rerun has
been made from these findings, because none of them establishes a new entry
rate, diversion share, physical closure extent or ramp control.

## Joint can/can't gate for 9 October

**Can attempt one bounded rerun** if Data supplies independent provenance for
surface-road entry/diversion or a reviewed physical correction to detector or
road connections. Simulation should change one supported item, retain seed
and matching observation bins, and report closure flow, upstream speeds and
queue proxy, AID01106/AID01107 flow, reopening through 10:35, teleports,
unfinished vehicles and pending departures. If AID01106 is used to derive a
new input, remove it from held-out validation and state the remaining check.

**Cannot accept P0 now.** Count GEH alone conceals the key flow failure; the
missing surface demand, provisional AID01106 location, uncertain physical
phase times and ramp backlog prevent a credible incident baseline. Without
new independent evidence by the checkpoint, Simulation recommends a **no-go
for P0/P1/P2 benefit claims**, with the observed incident playback, Reader
and operator workflow as the main demonstration. A simplified illustration
may be shown only with a clear unvalidated label. Lead owns the 9 October
scope decision; Data/E owns comparable `result.json` files and original
provenance sidecars if the model later passes.

## Single artifact list for the thread

- [Simulation demo handoff: assumptions, network identity, ordered road edges](simulation-demo-handoff-2026-10-07.md)
- [P0 setup and input source ledger](p0-setup-proposal-2026-10-06.md)
- [Portable P0 input packet](../results/twin/oct07-p0-replay-inputs.zip) and [SHA-256 manifest](../results/twin/oct07-p0-replay-inputs.manifest.json)
- [First P0 evaluation](../results/twin/oct06-p0-assumed-evaluation.json), [run summary](../results/twin/oct06-p0-assumed-run-summary.json) and [queue audit](../results/twin/oct06-p0-assumed-diagnostic.json)
- [Same-input timing and no-closure comparison](../results/twin/oct07-p0-followup-comparison.json)
- [Surface-route and detector cut audit](../results/twin/oct07-p0-cut-audit.json)

The Data/E plan results, independent surface-road evidence and agreed joint
sign-off are **not included** in this Simulation artifact list.
