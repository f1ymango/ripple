# May 15 OSM pre-incident replay: diagnostic, not a validated baseline

**Status on 27 Sep 2026:** SUMO 1.27.1 completed a bounded replay to the
08:55 observed queue onset for proposed demo incident IN-26-03365. No incident
closure was injected. The current model scored **66.5% of 242 usable count bins
with GEH < 5** (target: 85%) and **36.9% speed MAPE** over 296 speed bins.
All usable count bins matched a simulated time interval. The [machine-readable
result](may15-preincident-diagnostic.json) records each detector's totals, the
SUMO statistics, the exact input hashes, and the 25% demand sensitivity.

## What ran

- Observations: first twelve five-minute slots (07:55-08:55 HKT) from the
  committed [May calibration grid](../../sim/scenarios/calibration.json).
  Simulation seconds 0-900 were warm-up; the observed slots map to seconds
  900-4,500. The run stopped at 4,500 seconds with a 360-second wall timeout.
- Inputs: the local left-hand OSM/SUMO network from the [mapping audit](osm-network-audit.md),
  28 lane-wide E1 detectors, 97 directed corridor candidate routes, and demand
  fitted only from the pre-incident hour. The fitter generated 41,756 vehicles
  across the full 10,500-second intended horizon; only the first 4,500 seconds
  ran here. No counts, speeds, OSM tags, geometry, or lane counts were edited.
- Plain `sumo` used seed 2026, one-second steps, `--max-depart-delay -1`,
  `--duration-log.statistics true`, and `--statistic-output`. This avoids
  discarding uninserted vehicles while exposing the queue. The run completed
  in 37.45 wall seconds. The local network and loops remain uncommitted and
  unreviewed, so teammates cannot yet reproduce this run from Git alone.

| Checkpoint | Result |
|---|---:|
| Count bins with GEH < 5 | 161 / 242 = **66.5%** |
| Speed MAPE | **36.9%** over 296 bins |
| Vehicles loaded / inserted / waiting at 4,500 s | 17,922 / 15,517 / **2,405** |
| Teleports | **68**: 57 jam, 6 yield, 5 wrong lane |
| AID01214 observed / simulated count, usable bins | 2,494 / 1,519 |
| AID01107 observed / simulated count, usable bins | 1,276 / 421 |
| AID01217 observed / simulated count, usable bins | 1,887 / 836 |

The 25% route-volume diagnostic used the same network and route shapes, with
10,441 vehicles over the full horizon, and disabled departure dropping. At
4,500 seconds it still had 172 waiting vehicles and **9 teleports** (8 jam,
1 yield). This is evidence that the remaining trouble is not solely total
demand volume. The reduced-volume run is a topology diagnostic, not a
validation score against actual traffic.

## Corrections made during this replay

1. Missing pre-incident count bins no longer become zero targets in
   `fit_demand`. Three detectors lacked usable calibration counts. The old
   objective suppressed traffic on their shared edges.
2. The western alternative now has two directional candidate chains based on
   the registry coordinates and road directions. The old route builder joined
   opposing carriageways and reversed the westbound station order.
3. Fitted flows depart at position 0 and on SUMO's `best` lane. SUMO's default
   `base` position starts a vehicle about one length into its origin edge,
   which bypasses E1 loops near position 0. At quarter volume, selecting the
   route-compatible lane changed wrong-lane teleports from 27 to 0 and the
   insertion backlog from 373 to 172. These are model insertion settings,
   not changes to source observations.
4. `place_detectors` now creates its E1 output directory. The first attempt
   failed at startup because the XML named a directory that did not exist.
5. The TraCI runner now reads SUMO's cumulative statistics file for loaded,
   inserted, waiting, and teleported totals. Its previous summary mistakenly
   labeled last-step TraCI values as whole-run totals.

[SUMO departure positions](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#departpos),
[vehicle insertion](https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html),
[wrong-lane teleports](https://sumo.dlr.de/docs/Simulation/Why_Vehicles_are_teleporting.html),
[statistics fields](https://sumo.dlr.de/docs/Simulation/Output/StatisticOutput.html).

## What remains before incident validation

- **AID01214 is a boundary detector:** its loop is 0.55 m into a three-lane
  edge reached by two separate OSM approaches (two lanes plus one lane).
  The registry and May feed establish its three-lane scope; they do not
  establish how the 2,494 observed vehicles divide between those incoming
  roads. Even with boundary insertion, it remains undercounted. Inventing an
  approach split would hide this model limitation.
- The audit now checks all 24 directed links across the two main chains and both western-alternative chains. Every link is reachable; modeled path distance is 0.959?1.120? direct distance on the main chains and 1.002?1.093? on the western alternative. This supports local route continuity in the current OSM extract, but it is not a review of the road geometry or turns.

The audit still shows TD/SUMO lane-count conflicts at AID01221, AID01222,
  and TDSAPR10001. AID01105, AID01220, and TDSSPWR20002 have no usable lane
  records in the cached May window. AID01106 remains projected to an edge
  endpoint with a 20.73 m lane-0 offset. The network is not reviewed.
- The initial May message says only "part of the lanes." AID01104 raw lane
  readings show Slow Lane at zero at 08:55 and 09:00, but Fast Lane at zero
  at 09:05 while Slow Lane carried two vehicles. These data do not identify
  one physical closed lane or the incident edge. The
  [scenario example](../../sim/scenarios/scenario.example.json) records the
  known 08:55 onset, 09:36 TD escalation, and 10:02 clearance while leaving
  the edge and first-phase lane choice explicitly unresolved.

The OSM baseline does **not** meet the go/no-go validation threshold yet. Data's
~15-link fallback should stay active for the 4 Oct decision. A reviewed
incident edge and a stated `unspecified`-lane scenario choice are needed
before a full incident replay can support plan comparisons or a demo video.
