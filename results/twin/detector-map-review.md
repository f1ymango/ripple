# Draft OSM detector map review

This is a review record for the ten detectors Data flagged. The candidate
`edge_id` and `position_m` values were applied to the local ignored
`sim/scenarios/detectors.json`, then the per-lane E1 loops were regenerated.
They refer only to the local draft network below; the network itself is not in
Git and has not been approved for validation.

- Draft network SHA-256: `d8a99ca49b50e34da72fdf86c13b897703b6913fe9c7a65951ec262bb49f7465`
- Evidence checked: detector coordinate and sequence in `data/detectors.csv`,
  local OSM way tags, and edge direction/continuity in the generated SUMO net.
- The distance column is the lateral distance from the detector coordinate to
  the selected edge. `position_delta_m` compares the manually entered position
  with the nearest projection along that edge.

| Detector | Registry road / direction | Candidate edge (OSM way) | Position (m) | Offset (m) | Position delta (m) | Review note |
|---|---|---:|---:|---:|---:|---|
| AID01104 | Wong Chuk Hang Road Flyover / North East | `44419212` (Wong Chuk Hang Road flyover) | 136.31 | 7.75 | 0.00 | Eastbound carriageway confirmed against paired opposite edge `44419249`. |
| AID01216 | Wong Nai Chung Gap Flyover / South East | `673961732` (Canal Road Flyover) | 476.58 | 5.89 | 0.00 | Provisional: OSM way name differs from registry; confirm at the flyover junction. |
| AID01217 | Aberdeen Tunnel / North West | `1420680571` (Aberdeen Tunnel) | 82.78 | 1.93 | 0.00 | Tunnel edge follows the westbound corridor sequence. |
| AID01218 | Wong Chuk Hang Road / North West | `1198101430` (Aberdeen Tunnel) | 265.82 | 6.69 | 0.00 | Provisional: OSM way name differs from registry; confirm the tunnel exit versus WCH Road approach. |
| AID01219 | Wong Chuk Hang Road / South West | `44419249` (Wong Chuk Hang Road flyover) | 0.10 | 7.64 | 0.10 | Provisional: registry omits “Flyover”; check vertical level against the map. |
| AID01220 | Wong Chuk Hang Road Flyover / North West | `44419249` (Wong Chuk Hang Road flyover) | 497.32 | 7.33 | 0.00 | Westbound flyover edge. |
| AID01221 | Wong Chuk Hang Road / South West | `1205891500` (Wong Chuk Hang Road) | 21.26 | 18.99 | 0.10 | Near edge endpoint; confirm the position in the map before scoring. |
| AID01222 | Aberdeen Praya Road / South West | `956602968` (Aberdeen Praya Road) | 52.56 | 13.03 | 0.00 | Westbound road edge. |
| TDSSPWR10002 | Shek Pai Wan Road / South East | `26560129` (Shek Pai Wan Road) | 92.08 | 13.86 | 0.00 | Eastbound alternative leg; continues into the next detector. |
| TDSSPWR10003 | Shek Pai Wan Road / North East | `26560129` (Shek Pai Wan Road) | 539.06 | 3.39 | 0.00 | Same eastbound edge; position is near its downstream end. |

Do not use this draft mapping to claim a validated baseline. The name conflicts
and offsets marked above still need review on the corridor map. The OSM build,
lane count, tunnel/flyover connections, and incident lane selection also remain
unreviewed.
