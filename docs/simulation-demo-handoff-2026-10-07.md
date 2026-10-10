# Simulation handoff for the 9 October demo checkpoint

> **10 October update:** use the [completed Data/Simulation review at cfb4d04](https://github.com/f1ymango/ripple/blob/cfb4d04/docs/evaluator-p0-go-no-go-2026-10-09.md)
> for the current evaluator P0 decision. It records NO-GO for public plan
> comparison before 14 October. The 7 October assumptions and scores below
> describe the older Simulation diagnostic, not the newer E replay.
> The independent 10 October control reproduced E's P0; earlier move-over
> awareness did not resolve the wrong-lane teleport or closure count gap.

**Status on 7 October HKT: P0 no-go for plan comparison.** The
[8 October assessment for Data review](p0-assessment-for-data-2026-10-08.md)
tracks the joint evidence gate. This is Simulation's
evidence-labelled input to a shared demo bundle, not an accepted P0/P1/P2
result. The Lead owns the 9 October scope decision.

## Incident definition and input identity

| Item | Choice for the bounded P0 diagnostic | Status |
|---|---|---|
| Incident | IN-26-03365, Wong Chuk Hang Road flyover towards Aberdeen Tunnel near Yip Kan Street | TD incident and corridor detector evidence; exact crash point on the edge is unknown. |
| Network | PR #46 `647b13c` flow-balance conversion on Simulation's provisional OSM base; SUMO/netconvert 1.27.1, left-hand traffic, bus-lane-safe connection patch | Generated network has a header-stripped SHA-256 `c11501968dc3d15235f23c6802f0be9551b03743ef0a81eecf6f28ed26c23937`. Base-network SHA-256 `e3bcd9ed2bc1acfc72b5c72ba8a421fc85c51f3a87ef8138aa450fbe984ed90e`. Still provisional, not a physically reviewed network. |
| Portable inputs | [P0 packet](../results/twin/oct07-p0-replay-inputs.zip), SHA-256 `52b298aa73eb7e8621fce28223fc6b798100979f5735d0605ee62c2198b68505`; [manifest](../results/twin/oct07-p0-replay-inputs.manifest.json) | Contains generated network, demand, detector loops, observations and scenario config. The generated `build.json` is separately produced by PR #46. |
| Closure edge | `44419212`, two lanes, AID01104 at 136.31 m and AID01105 at 461.21 m | OSM road identity and lane scope match AID01104; exact physical closure length is not observed. |
| Initial restriction | At **08:55**, close `44419212_0` (slow/driver-left) | Detector-inferred diagnostic assumption. TD's 09:01 message says only “part of the lanes”; it does not identify the lane. No operator response begins before that report. |
| All-lane phase | At **09:36**, close `_0` and `_1` | TD all-lanes **report time**. Physical transition second is unobserved. A 09:15 sensitivity matched some zero bins but worsened teleports and is not accepted. |
| Reopening | At **10:02**, restore both lanes | TD clearance **report time**; physical reopening and queue recovery must be checked separately. |
| Run horizon | 07:25–10:35 HKT, first 30 minutes warm-up; 1 s steps, seed 2026; no departure dropping | Reproducibility choice. The P0 completed the bounded horizon. |

The exact assumptions and source ledger are in the [P0 setup](p0-setup-proposal-2026-10-06.md).

## Surface route for a map highlight

The provisional OSM network provides a passenger-car path from the surface
fork around the flyover to the tunnel entrance. **Ordered SUMO road-edge IDs:**

```text
1198059120 -> 1198059138 -> 1470218115 -> 770629127#0 ->
1470218117 -> 92245534 -> 1198059130 -> 1198059131 ->
1198059126 -> 1198059128 -> 714996652 -> 1198101500 ->
1198101498 -> 86289334 -> 1198101497 -> 1198101443
```

The portion beginning with `1198059138` is the 694 m shortest passenger path in this
generated network. The OSM network connects it to named roads including Nam
Long Shan Road and Ocean Park Road. This establishes **graph reachability**,
not real-world permission, capacity, travel time, or observed use during the
incident. It has not been physically reviewed as a recommended route. Visuals
may highlight it as a **provisional network path** with that label, but should
not call it a recommended diversion or animate vehicles on it as P0 results.
The [route-cut audit](../results/twin/oct07-p0-cut-audit.json) records the path,
other connections, source hashes and generated-flow assignments.

## P0 go/no-go evidence

**No-go for a validated incident baseline or plan-benefit comparison.** During
09:45–10:00, AID01104 observed/simulated flow was **0/0**, but AID01106 was
**228/33** and AID01107 **204/34**. Of 68 generated flow definitions reaching
the fork, 51 take the flyover, 17 end on the surface exit edge, and **none**
continues along the surface path to the tunnel. The two ordinary-day joins
after the flyover total 125 veh/h and cannot explain the sustained observed
tunnel flow. The [core diagnosis](p0-core-blocker-2026-10-07.md) details this.

The first P0 scored **87.15% GEH < 5 over 607 eligible count bins**, yet speed
MAPE was **47.33% over 790 bins**; it ended with **72 teleports**, **840 waiting
to enter** and **1,881 unfinished**. Its early AID01104 flow was 547 versus 17
observed in six eligible bins. The 09:15 all-lane timing sensitivity reduced
that flow but scored 83.86% GEH, produced **130 teleports**, and still missed
downstream flow and recovery. Reopening at the assumed 10:02 time gave 643
simulated versus 405 observed vehicles at AID01104 across eligible recovery
bins. The ramp entry backlog also occurs without a closure. Count GEH alone
does not accept P0.

One more bounded replay is technically feasible **only after** independent
evidence or a reviewed modelling rule resolves the intermediate surface
entries/diversion and the physical detector placement. Simulation can then
change one sourced assumption and retain the same comparison windows and
queue, recovery, teleport and pending-departure checks. AID01106 cannot both
set a new demand input and remain an independent validation target. Without
that evidence by the 9 October checkpoint, Simulation recommends a narrower
observed-playback/diagnostic demo and no delay, CO₂, travel-time or plan-ranking
claim. The simplified model has its own validation gate.

## Artifact handoff boundary

Visuals can use the real incident and detector playback, provisional road
graph, and clearly labelled P0 diagnostic evidence now. There is **no accepted
provenance-bound P0/P1/P2 result bundle** from Simulation to animate or rank.
Data/E owns those `result.json` files and original provenance sidecars; the
Lead owns reviewed plans, start/destination, bilingual briefing and the final
scope decision. Simulation will confirm any later network/route identity
against this handoff before it is shown as an evaluated run.
