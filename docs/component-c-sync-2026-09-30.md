# Component C handoff for 30 September

Checked 29 September against fetched main `7927f92` and the local source audit.
E's initial `unspecified` closure assumption remains open in main's tracker.

## Edge and direction

On the exact network SHA-256
`e3bcd9ed2bc1acfc72b5c72ba8a421fc85c51f3a87ef8138aa450fbe984ed90e`,
SUMO edge **44419212** is named **Wong Chuk Hang Road flyover**. Its direction
is east/northeast towards the Aberdeen Tunnel, consistent with AID01104's
North East registry bearing and the incident's named carriageway near Yip Kan
Street. This confirms the model carriageway association, not an exact crash
coordinate or the initially closed lane; the incident description supplies neither.

The directed path to the AID01106/07 tunnel approach is:
`44419212 -> 44419216 -> 714996652 -> 1198101500 -> 1198101498 -> 86289334 -> 1198101497 -> 1198101443`.

AID01104 is at 136.31 m on this 543.17 m, two-lane edge; AID01105 is at
461.21 m on the same edge. Local lane geometry at AID01104 places `_0` to
the driver's left of `_1`. Under the adopted TD convention this maps
**Slow Lane to index 0, Fast Lane to index 1** on this network. Neither this
mapping nor sampled zero volumes selects the initially closed lane.

## Source and placement check

The current network, OSM, registry, observations, mapping and overrides match
the hashes in [the audit](../results/twin/osm-network-audit.md). The local
scenario config differs from its recorded hash; do not present that audit as
a manifest for a new run. All 70 XML loops across 28 detectors match the CSV's
edge lanes and positions. This establishes internal consistency, not surveyed
physical placement. The network and loop files remain local and provisional.

Remaining physical/scope review:

- AID01221 and AID01222: TD three lanes versus SUMO four.
- TDSAPR10001: TD three versus SUMO two.
- AID01105, AID01220 and TDSSPWR20002: missing usable May-window lane scope.
- AID01106: 20.73 m lane-0 offset and an endpoint projection; inspect the
  approach/junction placement. Other endpoint placements remain review items.
- AID01218's reviewed two-lane tunnel-exit override is source-hash pinned;
  re-review it if the network changes.

The May 14 lane-count check corroborates feed labels only. It does not prove
physical placement or validate May 15 traffic. The separate
[May 15 raw lane report](../results/twin/may15-AID01104-lane-readings.md)
retains sparse readings and source hashes without filling archive gaps.

## Validation blockers and next steps

1. Data/E records its initial partial-closure assumption, including the lane
   index on this network and its status as an assumption. C then checks that
   mapping together with Data before freezing the incident config. No choice
   has been made on E's behalf and no coordination message has been sent yet.
2. Review the physical placements above with Visuals/Data; publish the reviewed
   network and loop files with a reproducible source manifest. Do not change
   OSM lane counts just to make them match detector labels.
3. Regenerate fitted demand after the departure-order fix. Recent local
   lane-0/lane-1 runs logged `Route file should be sorted by departure time,
   ignoring ...`: those runs are invalid validation evidence. The fitter now
   stably sorts flows by begin time. Check generated versus loaded vehicles
   and route-loader warnings before accepting any rerun.
4. Review the existing suspension of routes originating on the incident edge:
   it removes demand during closure and must be explicitly reported/agreed,
   not silently treated as observed traffic. Keep identical documented demand
   assumptions across compared runs.
5. Run a bounded pre-incident calibration diagnostic, then the full incident
   P0 (incident present, no response plan) against observed May 15 bins.
   Use 07:55–10:35 observations, 900 s warm-up, end 10,500 s; closure onset
   08:55, all-lanes phase 09:36, reopening 10:02. Record the configured
   wall-time limit, completion status, waiting, teleports, discarded vehicles,
   source hashes and seed. A no-incident replay is not incident P0 validation.
6. Match bins by time and sum all lanes. Include valid zero-count bins even
   when speed is null; leave unmeasured speeds unscored. Report coverage and
   denominators for pre-incident, closure and recovery separately, plus the
   full-window result. Publish E's result contract only after the accepted run.

## 4 October decision

The saved May 15 pre-incident diagnostic is still below target (66.5% of
242 count bins with GEH < 5; 36.9% speed MAPE over 296 bins, with 68 teleports).
The architecture requires at least 85% GEH < 5 and approximately 15% or lower
speed MAPE. There is no accepted full incident P0 validation.

Keep Data's simplified-network fallback active now. SUMO remains a conditional
option: by 4 October it needs a shared reviewed network, an explicit E closure
assumption, correct demand loading and a reproducible baseline meeting the
agreed thresholds. If these remain unmet, use the simplified network for the
demo path and label its assumptions and validation limits. The present evidence
does not justify promising that OSM topology or calibration will be fixed by then.
