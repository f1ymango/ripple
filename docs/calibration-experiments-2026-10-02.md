# Continued calibration investigation — 2 October

Two additional no-closure experiments were compared with the recorded
network-speed run. Demand, routes, seed 2026 and 0–4500 s horizon were fixed;
each experiment changed one setting. Neither is adopted in the working
baseline. Both completed within their 180-second wall limits without loader
errors; neither establishes full incident P0 validation.

| Measure | Network-speed reference | Adaptive insertion | Passenger restriction |
|---|---:|---:|---:|
| Count GEH pass, 242 bins | 66.94% | 66.12% | 66.53% |
| Speed MAPE, all available bins | 41.42% | 43.09% | 40.96% |
| Scored speed bins | 298 | 298 | 294 |
| Teleports | 53 | 71 | 73 |
| Waiting vehicles | 2,390 | 2,391 | 2,397 |
| Vehicles loaded | 17,922 | 17,922 | 17,922 |
| Wall seconds | 34.32 | 33.02 | 31.24 |

The restriction case has fewer scored speed bins, so its lower aggregate
speed error is not evidence of improved speed accuracy on identical bins.
Both variants worsen count agreement and teleport totals relative to the
controlled reference. The targets remain at least 85% GEH pass and approximately
15% speed MAPE or lower.

## What was tested

**Adaptive insertion:** changed only `departSpeed="desired"` to `"max"` in a
derived copy of the fitted routes. SUMO documents that `desired` waits until
desired-speed insertion is safe, while `max` may reduce entry speed to fit
traffic ahead. No safety checks were disabled, demand reduced or waiting
vehicles discarded. This plausible insertion constraint did not explain the
main failure in this experiment.
[SUMO reference](https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html#departspeed).

**Passenger restriction:** the exact local OSM way `1198101424` has
`oneway=yes`, `lanes=4` and `motor_vehicle:lanes=no|yes|yes|yes`. Its four
lane shapes were checked: SUMO index 0 is driver-left, matching OSM's lane
value ordering. Only `passenger` was added to that lane's disallowed classes
in a derived network copy; geometry, connections and other classes were
preserved. This translates an existing tag, but is still experimental: OSM's
historical applicability and adjacent inconsistent tags require review.
The ambiguous two-lane/four-value edge `251366297` was left untouched.
[OSM lane ordering](https://wiki.openstreetmap.org/wiki/Lanes).

`src.twin.replay_permission_review` reproduces the experimental network only
from the exact recorded source hashes and lane attributes, checks that the
sole change is the documented permission, refuses existing output paths and
checks the resulting hash. Reproduction succeeded against the real sources.
It is not connected to the default build workflow or detector overrides.

## Where the count discrepancy occurs

The [flow-delivery audit](../results/twin/oct02-flow-delivery-audit.json)
compares the original linear route fit with the original no-closure reference.
Examples, expressed as hourly equivalents over scoreable five-minute slots:

| Detector | Fitted hourly target | Linear prediction | Simulated hourly equivalent |
|---|---:|---:|---:|
| AID01110 | 3004 | 3004 | 1787 |
| AID01214 | 2993 | 2993 | 1823 |
| AID01217 | 2264 | 2264 | 1003 |

These equivalents are calculated diagnostics, not extra observations. Close
linear fit does not account for insertion delays, travel-time lag, queues,
teleports or misplaced detectors. Raising fitted demand to cover the deficit
could aggravate queues. AID01106/07 also share one mapped edge but have different
targets; an edge-membership fit cannot distinguish those detector positions.

Next work should trace per-route delivery and boundary placement at these
locations and review shared-edge detector constraints. These experiments rule
out two simple fixes; they do not resolve the source of the calibration gap.
The 4 October SUMO decision remains at risk and the simplified fallback should
continue. Quantitative delay and plan-benefit claims remain unsupported by
this unvalidated baseline.

## Artifacts

- [Reference](../results/twin/oct02-network-speed.json)
- [Adaptive insertion run](../results/twin/oct02-adaptive-insertion.json)
- [Permission run](../results/twin/oct02-permission-replay.json)
- [Permission source manifest](../results/twin/oct02-permission-source.json)
- [Flow delivery audit](../results/twin/oct02-flow-delivery-audit.json)

Reproduce the permission network with:

```powershell
python -m src.twin.replay_permission_review --review results/twin/oct02-permission-source.json --network sim/work/aberdeen.net.xml --osm sim/work/osm/aberdeen_bbox.osm.xml --out sim/work/permission-review/new.net.xml
```

The local experiment configs and command lines are recorded in the run
manifests. Raw cache/network inputs remain local. No test suite was rerun;
checks were the bounded SUMO replays and exact source/output hash reproduction.
