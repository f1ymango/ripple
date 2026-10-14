# IN-26-02615: Simulation P0 start and evidence inventory

**Status:** isolated Tuen Mun improvement bet. Aberdeen remains the submission
fallback. This is source inspection and observed-data preparation, **not** an
accepted P0 or an estimated plan benefit. The 16 October HKT go/no-go remains
open with Data and Lead.

## Original incident timeline

The Transport Department's historical [Special Traffic News archive](https://data.gov.hk/en-data/dataset/hk-td-tis_19-special-traffic-news-v2)
contains `IN-26-02615` on **Wednesday 15 April 2026**. The four English XML
snapshots at `20260415-1809`, `-1820`, `-1857`, and `-2029` are cached locally
under `data/raw/stn/`; their SHA-256 hashes are in the generated
[15 April evidence](../results/twin/tuen-mun-02615-observed.json). TD's
message announcement times, which differ from archive capture times, say:

| Announcement | Observed source statement | What remains unknown |
| --- | --- | --- |
| 17:59 NEW | Traffic accident, Tuen Mun Road **Tuen Mun bound**, near Hong Kong Garden; part of the lanes closed, only one lane remaining; traffic busy. | Exact lane(s), physical onset and edge. |
| 18:16 UPDATED | Same partial closure; queue tail reported near Tsing Long Highway / Ting Kau Bridge. | Tail's exact distance and preceding onset. |
| 18:46 UPDATED | Closed lanes reopened; queue will take time to disperse. | Physical reopening and full recovery time. |
| 18:46 message later marked CLOSED (captured 20:29) | The same reopening statement. | The 20:29 capture is **not** a new reopening time. |

No archived wording in these messages specifies a diversion route or share.
P0 must include drivers' ordinary route choices and any independently
supported spontaneous incident diversion, with both labelled and checked by
Data. It must not set an extra share merely to make a plan win.

## Observed detector diagnostic

The original [TD detector-location CSV](https://static.data.gov.hk/td/traffic-data-strategic-major-roads/info/traffic_speed_volume_occ_info.csv)
(SHA-256 `f30818ec94984c024f0188e2e45139ac684c4636aae7906561e227f01407423d`)
puts westbound `TDS90030` just before Hong Kong Garden, `TDS90031–32` near it,
and `TDS90033–34` near Ka Loon Tsuen farther west. The archive was queried for
16:30–21:00, then binned from *reading* timestamps. Of 188 listed snapshots,
122 were served and 66 were not. The generated JSON preserves per-snapshot
hashes, all five-minute bins including gaps, lane completeness and location
rows. Count summaries below use only bins with at least 40% archive coverage
and 90% valid lane readings; they are sampled-flow estimates, not direct full
five-minute totals.

| Detector | 17:00–17:55 mean flow, veh/h | 18:00–18:45 mean flow, veh/h | Mean speed, km/h before → during | Eligible bins before / during |
| --- | ---: | ---: | ---: | ---: |
| TDS90029, upstream Sham Tseng | 4,392 | 2,728 | 75 → 14 | 9 / 5 |
| TDS90031, near Hong Kong Garden | 4,085 | 3,140 | 70 → 17 | 9 / 3 |
| TDS90032, near Hong Kong Garden | 3,940 | 2,680 | 84 → 18 | 9 / 3 |
| TDS90033, downstream Ka Loon Tsuen | 4,050 | 2,312 | 72 → 68 | 9 / 5 |

This is consistent with an upstream queue and lower discharge through the
incident. It does not locate the closure to one edge, establish which lane was
closed, or measure drivers who left the corridor. `TDS90026` has no eligible
closure bins, so it cannot be used as a continuity constraint there.

Two Tsing Long Highway northbound probes, `AID03115–16`, are present in the
location CSV. Their 15 April flows rise from 1,494 to 1,880 and 1,440 to
1,774 veh/h between the same windows. But on the separate 8 April Wednesday
[comparison series](../results/twin/tuen-mun-ordinary-2026-04-08.json), they
also rise, 1,253 → 1,495 and 1,247 → 1,526 veh/h. The 8 April series has
84/120 served snapshots and has **not** been certified incident-free. These
probes alone do not quantify Tuen Mun-bound diversion or prove the turn is
reachable from the affected upstream traffic. No Castle Peak Road detector is
identified in this local location table near the scene.

## Network and P0 gates

The [draft network config](../sim/scenarios/tuen-mun-network-draft.json) uses
the westbound detector envelope with surrounding roads in a separate
`sim/work/tuen-mun/` directory. SUMO's three configured OSM mirrors failed,
so the same bounding box was fetched from the [official read-only OSM map
API](https://wiki.openstreetmap.org/wiki/Api06#Retrieving_map_data_by_bounding_box:_GET_/api/0.6/map)
and cached as `sim/work/tuen-mun/tuen-mun_bbox.osm.xml` (SHA-256
`5e5ebbdb9ac218e0416df06369057bf8e800a18776f8a9d662cfbc3af73d206d`).
The builder then converted that unedited source with `--lefthand` and
`--geometry.split true` into a **provisional** network (SHA-256
`516e79e45770f4cb88f2ec5d13f4a5542b98594649d98c15bb30fc193bbc97e2`).
The bounding box is an extraction extent, not a claim about where motorists
went. The ignored OSM and network files must be regenerated and hash-checked
before another person uses this exact draft.

The split is necessary: normal geometry removal combines the westbound scene
and multiple detectors into a single 5.36 km SUMO edge. The generated
[network audit](../results/twin/tuen-mun-network-audit.json) lists source
bearing, observed lane names and nearby directed SUMO edges for TDS90028–36.
Near the reported scene, TDS90031 has two plausible westbound three-lane edges
`158584355#2.228` / `#2.210`, and TDS90032 has `1212548387.379` /
`1212548387.459`. Both detectors show the speed collapse, while downstream
TDS90033 is faster. This brackets an affected road stretch but **does not
identify a unique closure edge**. TDS90036 has four feed lanes against nearby
three-lane network candidates, another unresolved mapping. SUMO also reports
ignored OSM restriction relations, so lane and turn connections need review.
No closure edge or lane has been injected yet.

Simulation and Data still need to jointly establish:

1. The correct Tuen Mun-bound incident edge and lane scope from road geometry,
   location and lane observations; the STN gives only one lane remaining.
2. A lawful, upstream-reachable route inventory, and observed entry/turning
   evidence or an explicitly bounded uncertainty range for spontaneous P0
   diversion. Queue accumulation must not be counted as diverted traffic.
3. An ordinary-period demand fit with independent held-out detectors, then a
   bounded 15 April P0 replay that checks detector count and speed, queue-tail
   onset, downstream discharge, reopening/recovery, entry backlog and
   teleports. Keep physical onset separate from the 17:59 report time.
4. Only after P0 is credible, freeze network, demand, evaluator version,
   seeds, compliance and comparator semantics before matched P1/P2 runs.

The generated data can be reproduced after caching the public STN and detector
snapshots and downloading the location CSV:

```powershell
python -m src.twin.tuen_mun_evidence --day 2026-04-15 --locations sim/work/td-detector-locations.csv --out results/twin/tuen-mun-02615-observed.json
python -m src.twin.tuen_mun_evidence --day 2026-04-08 --end 19:30 --locations sim/work/td-detector-locations.csv --out results/twin/tuen-mun-ordinary-2026-04-08.json
```

**Early blocker for the 16 October decision:** no reviewed network or source
backed P0 diversion share exists yet. The observed slowdown is real; a plan
benefit is unmeasured. Data owns demand/evaluator review, Simulation owns the
physical network and replay review, and Lead owns the scope decision.
