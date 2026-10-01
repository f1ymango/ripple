# Calibration and teleport investigation — 2 October

Two completed no-closure replays used the same May 15 observations, network,
loops, route edges, departure counts, seed 2026 and 0–4500 s horizon. Both used
the original unsuspended full-horizon demand. Each had a 180 s wall-time limit
and completed without loader errors. Only the second run's vehicle maximum
speed attribute changed: the unsupported global 16.7 m/s cap was removed.
SUMO's vehicle defaults and network speed limits then govern speeds; this is
not a measured driver-speed distribution or an approved calibration.

| Metric | Reference | Network speed limits |
|---|---:|---:|
| GEH < 5, 242 count bins | 66.53% | 66.94% |
| Speed MAPE on 296 common bins | 36.94% | 41.36% |
| Speed MAPE on all scored bins | 36.94% (296) | 41.42% (298) |
| Teleports | 68 | 53 |
| Jam / yield / wrong-lane teleports | 57 / 6 / 5 | 41 / 7 / 5 |
| Vehicles loaded | 17,922 | 17,922 |
| Vehicles inserted | 15,517 | 15,532 |
| Vehicles waiting to enter | 2,405 | 2,390 |
| Wall seconds | 38.37 | 34.32 |

This reduced teleports but worsened speed error. The small count improvement
does not meet the 85% requirement, and both speed scores miss approximately
15%. Removing the ungrounded speed ceiling is a model correction, not a claim
of a better overall baseline. Existing generated routes retain their old cap
until explicitly regenerated. No detector data, OSM geometry, lane counts or
teleport thresholds were changed.

## Tunnel evidence

The [connection audit](../results/twin/oct02-tunnel-bottleneck.json) records
the exact network and OSM hashes, full tags, permissions and outgoing lanes.
Edge `251366297` is 10.67 m long with two model lanes and OSM `lanes=2`, but
OSM `motor_vehicle:lanes=no|yes|yes|yes` contains four values. It feeds four-lane
`1198101424`; that edge's lane 0 allows passengers in SUMO but has no outgoing
connection. Its OSM lane-access tag also excludes one lane.

These inconsistencies merit source/map review. A missing lane connection can
also represent a legitimate lane drop; the evidence does not authorize adding
a connection or assuming which source tag is correct. We did not make that edit.

The earlier split-flow run had 123 teleports, including 64 on `1198101443`.
Today's unsuspended reference has 68, including 16 there. Different flow IDs
and schedules affect trajectories even at the same seed, so the 123-to-53
difference is not a controlled improvement attributable to this speed change.
The valid paired comparison is 68-to-53.

The previous 242-bin count audit also identifies AID01110 and AID01217 with
zero passing bins, and AID01107, AID01214, AID01218 and AID01221 with only one
passing bin each. Prioritise those demand/placement checks rather than assume
the tunnel bottleneck explains every count failure.

## Project impact and next action

Severity is high for quantitative SUMO claims. Teleports interrupt physical
queue progression; insertion backlogs withhold traffic from the network;
incorrect counts and speeds undermine delay estimates and could change plan
rankings. They do not prove a particular ranking is wrong, but prevent us
claiming reliable plan benefits before validation.

Reader, plan validation, briefing and observed-data playback work remain useful.
Data's simplified model is still a viable integration path, subject to its own
assumptions and checks. With the 4 October gate two days away, keep it active
and do not rely on the current SUMO model as a validated baseline.

Next: review the recorded tunnel lane-access inconsistencies with source/map
evidence, trace route contributions at the worst count detectors, and repeat
the paired no-closure comparison for a justified correction. Full incident
timing and E's unspecified-lane choice remain separate from this calibration.

## Evidence and reproduction

- [Reference run](../results/twin/oct02-reference.json)
- [Speed-cap correction run](../results/twin/oct02-network-speed.json)
- [Matched speed-bin comparison](../results/twin/oct02-comparison.json)
- [Tunnel and detector audit](../results/twin/oct02-tunnel-bottleneck.json)

The local `sim/work/oct02-calibration/reference.json` and `network-speed.json`
configs point to copies of `sim/work/may-diagnostic/fitted.rou.xml`, with only
the latter copy's vType `maxSpeed` removed. Replays were produced by
`python -m src.twin.diagnose_preincident --config <config> --observations
sim/scenarios/detectors.json --work <new-directory> --out <report> --timeout 180`.
All output reports include source hashes and command lines. The provisional
network and raw cache are still local; these reports alone are not a portable
network release.

Checks: three existing route, demand and lane-audit tests passed. The two
bounded SUMO replays above completed; no full incident or policy comparison
was run in this update.
