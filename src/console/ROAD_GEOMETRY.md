# Corridor road graph

An optional road graph on the existing CARTO street basemap. The default
**Corridor network** view draws the main corridor in blue and the alternative
roads named in `docs/02-data.md` section 5 in purple. **Full supplied network**
adds other passenger-accessible roads in thin grey. **Single road** retains
the detailed alignment preview, initially selecting Shek Pai Wan Road when
present. Detector colours remain recorded observations.

This is not a route recommendation, vehicle replay or validation of the model.
It changes no D/E/F contracts and does not affect recommendation eligibility.

## Run

With repository requirements installed and a georeferenced SUMO network:

```bash
RIPPLE_SUMO_NETWORK=/absolute/path/to/network.net.xml \
  streamlit run src/console/app.py
```

`RIPPLE_DATA_DIR` optionally points to existing recorded detector exports.
Without `RIPPLE_SUMO_NETWORK`, the console retains its normal detector map.
Malformed/missing/unprojected networks show a warning while the console remains
usable. Both the network overlay and automatic map fitting can be turned off.

## Geometry and limitations

- `sumolib` reads passenger-accessible external edges. `getShape()` supplies
  the average lane shape for each carriageway; `convertXY2LonLat()` applies the
  network's projection and offset. Every returned vertex is preserved.
- Each directed edge is a separate path. Corridor grouping matches full English
  road names; it does not include Old Pok Fu Lam Road merely because its name
  contains Pok Fu Lam Road. These groups are visual filters, not approved plans.
- Junction curves use the actual internal lane shapes referenced by SUMO
  connections, including multiple internal lanes where a turn has them. They
  are included only when both external edges are displayed and the connection
  and its lanes allow passenger vehicles. No inferred straight connectors.
- `route_geometry()` can take an ordered list of SUMO edge IDs and this
  network's hash. It rejects missing edges, mismatched networks and disconnected
  turns, then returns only the network's real edge and junction shapes. It is a
  renderer input check, not proof that an evaluated run used those edges. The
  current console does not call it until C/E provide reviewed route and producer
  identities under an agreed handoff.
- A named-road subset can still have gaps where a linking street has another
  name, the source lacks geometry, or carriageway centres meet individual lane
  connections. Full supplied network exposes surrounding coverage. This does
  not certify that a selected collection is a continuous feasible diversion.
- The content hash identifies the supplied geometry and invalidates the cache.
  It does not establish a relationship to any evaluated plan or FCD output.
- Basemap and SUMO data can differ in lane offsets, simplification and age.
  Visual alignment is not a survey or an incident-model acceptance test.
- Road shapes originate from the supplied network; for the current OSM-derived
  preview, preserve OpenStreetMap attribution alongside CARTO's basemap credit.

## Observed incident playback

See [the playback guide](../../docs/console-observed-playback.md) for archived
messages, the small incident arrow, source limits and review steps.
