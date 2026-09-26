# Draft OSM network and detector map review

This review uses only the repository's `data/detectors.csv`, cached May 15 raw
Transport Department XML snapshots, the local cached OSM extract, and the SUMO
network built from that extract. It does not add or infer road geometry, lane
counts, or traffic observations. The output is a provisional map review, not a
validated network.

## Reproducibility

- Cached OSM extract: `sim/work/osm/aberdeen_bbox.osm.xml`
- OSM extract SHA-256: `c6d3333d803ef19db9707ae1ac9dc958121d7bd19941a555a8db0ec50e62b09f`
- Draft SUMO network: `sim/work/aberdeen.net.xml`
- Draft network SHA-256: `e3bcd9ed2bc1acfc72b5c72ba8a421fc85c51f3a87ef8138aa450fbe984ed90e`
- Conversion includes `--lefthand`, passenger-edge filtering, and street-name
  output. Street names are used only to choose among nearby, correctly directed
  OSM edges; they are not used to create or rename roads.
- Detector matching uses the ordered chains in `src/loaders/corridor.py`, the
  coordinates and road names in `data/detectors.csv`, and the local OSM edge
  direction/name. The ten detectors Data flagged were rechecked against these
  sources. The resulting per-lane loops are in ignored local work files.

## Rechecked detector candidates

Offsets are the distance from the registry coordinate to the selected OSM edge.
They are evidence about placement, not proof of the carriageway. Positions are
projected from the source coordinate by the matcher.

| Detector | Registry road / direction | Draft edge | OSM name | Position (m) | Offset (m) | Finding |
|---|---|---:|---|---:|---:|---|
| AID01104 | Wong Chuk Hang Road Flyover / North East | `44419212` | Wong Chuk Hang Road flyover | 136.31 | 6.25 | Direction and road name select the eastbound flyover, opposite edge is `44419249`. |
| AID01216 | Wong Nai Chung Gap Flyover / South East | `88718922` | Wong Nai Chung Gap Flyover | 412.69 | 4.29 | Road-name match replaces the former Canal Road Flyover candidate. |
| AID01217 | Aberdeen Tunnel / North West | `1420680571` | Aberdeen Tunnel | 82.78 | 2.87 | Tunnel edge follows the westbound chain direction. |
| AID01218 | Wong Chuk Hang Road / North West | `46766843` | Wong Chuk Hang Road | 42.66 | 18.77 | Road name agrees; offset remains high and needs map review. |
| AID01219 | Wong Chuk Hang Road / South West | `1198059110` | Wong Chuk Hang Road | 25.50 | 6.46 | Road-name match replaces the former flyover candidate. |
| AID01220 | Wong Chuk Hang Road Flyover / North West | `44419249` | Wong Chuk Hang Road flyover | 497.32 | 5.73 | Westbound flyover candidate. |
| AID01221 | Wong Chuk Hang Road / South West | `1205891500` | Wong Chuk Hang Road | 21.26 | 12.57 | Near edge endpoint; offset needs map review. |
| AID01222 | Aberdeen Praya Road / South West | `956602968` | Aberdeen Praya Road | 52.56 | 8.23 | Direction and road name agree. |
| TDSSPWR10002 | Shek Pai Wan Road / South East | `26560129` | Shek Pai Wan Road | 92.08 | 12.25 | Direction and road name agree; offset needs map review. |
| TDSSPWR10003 | Shek Pai Wan Road / North East | `26560129` | Shek Pai Wan Road | 539.06 | 4.99 | Same directed OSM edge, downstream of the preceding detector. |

## Network issues still evidenced by source conflicts

- The cached raw detector feed and draft OSM network disagree on lane counts at
  AID01106, AID01214, AID01218, AID01219, AID01221, AID01222, and TDSAPR10001.
  The raw feed is authoritative for detector lanes; OSM is the source for road
  geometry. These observations do not justify changing OSM lane counts, so no
  lane count was edited to force agreement.
- In the current passenger network, the shortest network path from AID01106's
  selected edge to AID01107's selected edge is about 1.64 km, while their
  detector coordinates are about 0.46 km apart. That 3.6x ratio flags a likely
  tunnel/approach connectivity problem in this extract. The data establishes
  that the route is implausible, but does not identify which OSM nodes or links
  should be changed. Do not use this network for tunnel incident validation.
- Other chain pairs also have path/direct-distance ratios above 2. They require
  corridor map inspection before the network can be called reviewed.
- Netconvert emitted OSM conversion warnings. The generated network and E1
  loops remain uncommitted because the cached extract has not passed topology,
  lane-count, and detector-offset review.

The automated matcher fixes direction/name selection where repository evidence
distinguishes the candidates. It deliberately leaves the remaining OSM topology
conflicts visible rather than synthesizing a repaired network.
