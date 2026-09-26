# Aberdeen SUMO diagnostic

![Animated clip rendered from SUMO FCD trajectories](aberdeen-diagnostic.gif)

The animated GIF renders actual vehicle positions recorded by SUMO 1.27.1 on the Aberdeen corridor network. It samples completed FCD snapshots every 60 simulation seconds and spans simulation time 0–6,360 seconds. The red segment marks the incident edge. This is the earlier IN-26-06481 (3–4 Sep) diagnostic, not a replay of Data's newer IN-26-03365 shortlist pick.

This is an **incomplete diagnostic excerpt**, not a validated baseline. The intended run horizon was 30,900 seconds, but the run was stopped at approximately 6,410 seconds after repeated jam and teleport warnings. The interrupted run did not produce complete E1 detector intervals: the attached partial evaluation has zero scoreable count or speed bins. Do not quote it as a calibration result. The run summary records that the exact teleport and dropped-vehicle totals were unavailable for this interrupted run; future runs record those counters and the estimated departure-delay drops.

The calibration input is [`sim/scenarios/calibration.json`](../../sim/scenarios/calibration.json), derived from available 15-minute bins in the pre-incident hour for IN-26-06481. It must not be used to claim calibration of IN-26-03365. Candidate screening is in [`data/candidates.md`](../../data/candidates.md), with the demo shortlist in [`data/demo_shortlist.md`](../../data/demo_shortlist.md).

## Network decision

The old run emitted jam, yield and wrong-lane teleports after fitting 52,296
vehicles over the 30,900-second horizon. That run cannot separate demand
pressure from OSM turn/lane topology. The registry-based direction match places
AID01104 on a northeast-aligned edge 6.3 m from its coordinate, but AID01217
has no nearby edge meeting the stricter bearing check and must be map-reviewed
or hand-mapped. The OSM network and generated loops are therefore not ready to
commit as a shared reviewed network. Keep the ~15-link fallback active while
time-boxing a topology review; do not attribute the previous teleports to OSM
alone.
