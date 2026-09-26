# Provisional OSM detector map review

This review uses the committed detector registry, the cached May 15 Transport
Department feed, the cached OSM extract, and the SUMO network built from that
extract. The full generated evidence, including hashes, lane labels, offsets,
network positions and consecutive chain paths, is in
[osm-network-audit.md](osm-network-audit.md) and
[osm-network-audit.json](osm-network-audit.json).

The network geometry and OSM lane tags were not edited. `place_detectors` now
reads the cached OSM name aliases. It uses an alias only if the TD lane count
for the same replay window agrees with the candidate. If two equally named
candidates are within one SUMO lane width of each other, the measured lane
count breaks the tie. The observed count and SUMO lanes are never altered.

| Detector | Previous candidate | Current candidate | Evidence |
|---|---|---|---|
| AID01106 | Wong Chuk Hang surface edge `1198101444` | Aberdeen Tunnel entrance `1198101443` | OSM street-name alias says Wong Chuk Hang Road; the measured TD lane count is 2, matching the tunnel edge. This changes the position-aware route to AID01107 from 1,771.83 m to 441.79 m. The projected detector still sits at the edge endpoint, 20.73 m from lane 0, and needs map inspection. |
| AID01214 | Canal Road Flyover `46108739` (2 lanes) | Canal Road Flyover `136461565` (3 lanes) | The raw feed reports Fast, Middle, and Slow lanes; the latter edge direction better matches the source bearing. Its projection is close to the edge start, so confirm on the map. |
| AID01218 | Wong Chuk Hang surface edge `46766843` (3 lanes) | Tunnel exit `1198101430` (2 lanes) | AID01218's coordinates and westbound bearing align with the tunnel edge, the TD feed records two lanes, and it continues from AID01217. This exception is pinned to the exact local network and registry hashes in `sim/scenarios/aberdeen-detector-overrides.json`. |
| AID01219 | Wong Chuk Hang surface edge `1198059110` | Flyover edge `44419249` | The OSM flyover way also tags Wong Chuk Hang Road as its English street name; its two lanes match the raw TD lane labels. |

Three lane scopes still differ: AID01221 and AID01222 each have 3 lanes in
TD but 4 in OSM/SUMO; TDSAPR10001 has 3 in TD but 2 in OSM/SUMO. The cached
window contains no lane readings for AID01105, AID01220, or TDSSPWR20002, so
their lane scope cannot be confirmed from these files. Those observations do
not authorize editing OSM lane counts. The full May 15 interval covers 07:55
to 10:35; 66 cached snapshots contributed readings.

This is not a reviewed or shared network. The SUMO network and raw cache are
ignored local files; the source hashes make the audit reproducible only with
those exact local inputs. No new baseline simulation was run, and the earlier
teleport result does not validate the updated detector map.
