# Simulation Gate 1 audit — IN-26-03365 route-choice spike

**Decision: stop the new-road experiment at Gate 1.** This is Simulation's
graph and source audit, not a joint acceptance decision. The existing network
has a late branch, but no independent route at the upstream choice point for
the two tested Aberdeen-origin OD groups. Independent 15 May turning and entry
counts for the late branch have not been supplied. Its real-world turn legality
and capacity have not been reviewed. No new geometry, demand, signal action or
matched P0/P1/P2 runs were made for this spike.

## Fixed inputs and reproduction

The machine-readable [audit](../results/twin/route-choice-gate1-2026-10-14.json)
records every directed edge for both OD groups, OSM tags, and SHA-256 hashes.
It used the local evaluator replay network `sim/work/p0-replay/network.net.xml`
(`eb006b4ea09f01246ea53f163d68854e47b1be0410943f587d846388ef053e9d`),
`sim/scenarios/evaluator_IN-26-03365_replay-v3-1.json`
(`35d1665ae682c563cd99c5092927667cd574132929c1d045bab8902237a3c7da`),
and original cached OSM `sim/work/osm/aberdeen_bbox.osm.xml`
(`c6d3333d803ef19db9707ae1ac9dc958121d7bd19941a555a8db0ec50e62b09f`).
The network and OSM files are ignored local source artifacts; obtain the
matching P0 replay packet as described in `src/evaluator/README.md` and
verify hashes before reproducing. From the repository root:

```powershell
python -m src.twin.audit_route_choice --network sim/work/p0-replay/network.net.xml --scenario sim/scenarios/evaluator_IN-26-03365_replay-v3-1.json --osm sim/work/osm/aberdeen_bbox.osm.xml --out results/twin/route-choice-gate1-2026-10-14.json
```

The audit starts at scenario edge `1197689855`, tests destinations `485146382`
(Canal Road) and `1194711688` (Wong Nai Chung), blocks closure edges
`44419212` and `44419216`, and traverses only existing SUMO connections whose
from and to lanes permit passenger vehicles. The protected hospital corridor
uses the scenario's emergency edges plus named Pok Fu Lam and Shek Pai Wan
edges. This is a permissive graph screen: a path proves model connectivity,
not lawful real-world turns or available capacity. A negative result on this
permissive graph is stronger evidence of a missing model route.

## What the graph establishes

The existing surface detour has these directed edges, in order:

`1198059138 1470218115 770629127#0 1470218117 92245534 1198059130 1198059131 1198059126 1198059128`

With the closure and hospital corridor excluded, that route reaches both
destinations. If its first edge `1198059138` is excluded too, neither
destination is reachable; the same holds even when the hospital exclusion is
removed. Blocking each of the first six later surface segments also leaves no
path. Thus the graph supplies no distinct route choice before the shared
surface-road entry and early bottleneck.

Blocking the seventh surface segment instead exposes a **late** branch. It
shares the upstream entry and the first seven surface edges, then uses this
directed suffix through Nam Long Shan Road, Heung Yip Road and Ocean Park Road
before rejoining at `86289334`:

`412761209#0 814923162#0 1470047312#1 1470218114 412761205#1 1079029074 1079029071 648423567#0 648423567#1 648423567#3 302998781#0 155997148#1 1198101445 492610841 1198101461 1198101471 1198101465 1198101463 1198101464 1198101479 365888442#1 26560290#0`

The cached OSM has road names, direction and lane tags for these ways (saved
per edge in the audit JSON). SUMO has passenger lane connections. Those inputs
do not independently establish every turn's legal status on 15 May, background
flow, turning share, entry capacity, or whether diversion instructions could
reach vehicles before the common queue. The late branch is therefore an
unvalidated model path, not a defensible upstream alternative.

## Independent evidence and disposition

The repo's `data/detectors.csv` and `docs/02-data.md` provide no detector
entry or turn series for Nam Long Shan, Heung Yip or Ocean Park Road. Data's
`docs/incident-p0-verdict-2026-10-14.md` likewise flags missing independent
entry/turning evidence. The Transport Department's [strategic-road detector
dataset](https://data.gov.hk/en-data/dataset/hk-td-sm_4-traffic-data-strategic-major-roads)
describes detector speed, volume and occupancy, while its [annual traffic
census](https://data.gov.hk/en-data/dataset/hk-td-sm_5-annual-traffic-census-survey-data)
describes hourly volumes at selected routes. Neither dataset description alone
supplies the incident-specific turning and entry split needed here. The census
location CSV could not be retrieved in this environment; we make no claim
that no relevant public station exists.

Gate 1 therefore fails the requested evidence standard. We did not freeze
experimental inputs or inspect new-network outcomes, and there is no new
P0/P1/P2 comparison to report. The 15 October submission pack is unchanged.
The incident P0 remains scientifically **NO-GO** under the existing joint
verdict; no route recommendation or measured savings follow from this audit.
Data and Lead can review the exact edges and source gap if independent turn
counts or a distinct upstream road source becomes available before freeze.
