# Why IN-26-03365 P0 is not ready for plan comparison

Simulation reviewed the first P0, its 09:15 timing sensitivity, the matched
no-closure control, the PR #46 generated demand and the provisional OSM network
on 7 October HKT. The new [generated route and detector audit](../results/twin/oct07-p0-cut-audit.json)
can be reproduced from the PR #46 review worktree with:

```powershell
python -m src.twin.audit_p0_cut `
  --network sim/work/oct06-pr46-review/sim/work/aberdeen.flow-balance-buslane.net.xml `
  --routes sim/work/oct06-pr46-review/sim/work/p0-demand-draft-oct06/demand-default-drivers.rou.xml `
  --build sim/work/oct06-pr46-review/sim/work/p0-demand-draft-oct06/build.json `
  --evaluation results/twin/oct06-p0-assumed-evaluation.json `
  --out results/twin/oct07-p0-cut-audit.json
```

The network and route file are also in the
[portable P0 packet](../results/twin/oct07-p0-replay-inputs.zip). The generated
`build.json` comes from PR #46 revision `647b13c` and is not in that packet;
its generation commands are in the [P0 setup](p0-setup-proposal-2026-10-06.md).
The audit records SHA-256 hashes for its four inputs. It changes no network,
demand, observations or result numbers.

## Core failure: the model cannot represent the observed downstream path

In the three eligible five-minute bins **09:45–10:00**, AID01104 on the flyover
reported **0** vehicles, but AID01106 at the tunnel approach reported **228**
and AID01107 inside the tunnel **204**. The P0 sim reported **0**, **33** and
**34**, respectively. The downstream flow is sustained after the 09:36 report;
it is not explained by one batch of cars already downstream at closure onset.

The OSM network does contain a **694 m passenger-car path** from the surface
fork `1198059138` around closed flyover edge `44419212` to tunnel entrance
`1198101443`. It also has passenger connections from Nam Long Shan Road,
Tong Bin Lane, Ocean Park Road and other nearby edges. Network reachability is
therefore present in this provisional map; it does not prove that those
connections carried the measured volume on 15 May.

The **generated demand cannot use this surface path to reach the tunnel**:
of 68 flow definitions through upstream edge `1198059120`, 51 take the flyover,
17 terminate on the surface exit edge, and **zero** go from that fork to the
downstream tunnel entrance. These are flow definitions, not vehicle counts.
The two ordinary-day joins between AID01104 and AID01106 total **125 veh/h**,
about 31 vehicles over this 15-minute interval, consistent with the P0's 33.
They do not represent the observed 228. Fixed P0 routes have no incident
diversion rule. Closing the flyover therefore strands the upstream stream and
starves the tunnel even though the real detectors saw traffic reaching it.

This is a **demand and route-topology mismatch**. Moving the assumed all-lane
closure to 09:15 did not solve it: [the same-input sensitivity](p0-followup-2026-10-07.md)
scored 83.86% count GEH < 5, had 130 teleports, and still produced only 42
vehicles at AID01106 across 09:40–10:00 against 310 observed. Its 09:15
physical transition remains unobserved. The first P0's headline 87.15% count
GEH < 5 also conceals its key-detector miss, 47.33% speed error, 72 teleports
and 840 vehicles waiting to enter at 10:35. The matched no-closure control
already has 964 waiting and 56.90% speed error without imposed signs.

## Why a direct numerical patch would be misleading

The current repo has detector readings at the flyover and tunnel but no
incident-window counts on those intermediate surface entries. Deriving a
diversion fraction or a new side-road flow from AID01106 would use that
detector to **set** P0 demand; it could no longer serve as independent
validation. Likewise, the recorded 09:36 all-lanes and 10:02 clearance are TD
message times, not observed seconds when traffic physically changed.
AID01106's physical mapping is still provisional: the source audit projects it
20.73 m from lane 0 at the start of a short tunnel edge. Its similar counts
to AID01107 support real tunnel throughput, but do not independently certify
the exact cross-section or source road.

The separate ramp backlog also remains: the P0 scheduled 2,481 vehicles on
the `46766432` ramp flow and inserted 1,641 by 10:35, leaving 840 pending,
with the signal and merge priority not checked against a primary physical
source. Changing those parameters to remove the queue would be unsupported.

## Readiness decision and smallest defensible next step

**P0 is still a diagnostic, not a validated plan-comparison baseline.** The
model needs a source-backed account of (1) surface-road entry and diversion
during the incident, (2) the physical AID01106 cross-section and flyover
closure extent, and (3) ramp control/priority. Data/E should first check its
original May 15 lane feed and any independent evidence for the surface entries
or driver diversion. Simulation can then implement one explicit route choice
or entry correction and rerun with fixed seed, the same 607 eligible count
bins, closure flow, upstream speed/queue, downstream flow, recovery, pending
departures and teleports. If AID01106 is used to set demand, remove it from
the held-out score and declare that limitation.

Until those inputs are available, adding a percentage of rerouted traffic or
changing the ramp signal would be a guess. The Lead should keep the simplified
model decision active and narrow any P0 claim rather than rank P1/P2 with this
SUMO run. No plan benefit is certified by this audit.
