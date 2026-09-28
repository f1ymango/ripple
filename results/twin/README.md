# Component C results and diagnostics

The [15 May pre-incident diagnostic](may15-preincident-diagnostic.md) compares
SUMO's 07:55-08:55 simulated detector bins with the committed May observations.
It reports the demand, E1 counts, speed error, teleports, and insertion backlog
for the local draft OSM network. This interval ends at the observed queue onset;
it does not score the incident closure. The network and raw OSM cache remain
local and provisional. The [source and route audit](osm-network-audit.md) checks all 24 directed
corridor links and keeps the six lane-scope conflicts or missing feed scopes
visible.

## Earlier September diagnostic

![Animated clip rendered from SUMO FCD trajectories](aberdeen-diagnostic.gif)

The GIF renders vehicle positions from an earlier IN-26-06481 (3-4 Sep)
diagnostic using SUMO 1.27.1. It spans simulation time 0-6,360 seconds of an
intended 30,900-second run. The run stopped around 6,410 seconds after repeated
teleport warnings and had zero scoreable detector bins. It is a real simulation
excerpt, but it is not a validated baseline or footage of the May demo incident.

The committed [calibration input](../../sim/scenarios/calibration.json) now
covers the May 15 demo window; it superseded the old September input. The May
candidate evidence is in [Data's demo shortlist](../../data/demo_shortlist.md).
