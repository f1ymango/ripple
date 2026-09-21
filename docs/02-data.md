# 02 — Data sources, schemas and gotchas

All feeds are free and open, from DATA.GOV.HK / Transport Department. Verified
21 Sep 2026. Attribute DATA.GOV.HK and the Transport Department in the deck.

---

## 1. Traffic detectors — speed, volume, occupancy

Dataset: *Traffic Data of Strategic / Major Roads*
`https://data.gov.hk/en-data/dataset/hk-td-sm_4-traffic-data-strategic-major-roads`
Update frequency: **raw every 1 minute**, processed every 2 minutes.
Data dictionary:
`https://static.data.gov.hk/td/traffic-data-strategic-major-roads/dataspec/dataspec-traffic-data-strategic-major-roads.pdf`

| Resource | Format | URL |
|---|---|---|
| Raw speed/volume/occupancy (live) | XML | `https://resource.data.one.gov.hk/td/traffic-detectors/rawSpeedVol-all.xml` |
| Processed segment speeds (live) | XML | `https://resource.data.one.gov.hk/td/traffic-detectors/irnAvgSpeed-all.xml` |
| Detector locations | CSV | `https://static.data.gov.hk/td/traffic-data-strategic-major-roads/info/traffic_speed_volume_occ_info.csv` |
| Road network segments | CSV | `https://static.data.gov.hk/td/traffic-data-strategic-major-roads/info/speed_segments_info.csv` |

### Raw XML structure

```
date                              yyyy-mm-dd
└── periods (two 30-second intervals per file)
    ├── period_from               HH:mm:ss
    ├── period_to                 HH:mm:ss
    └── detectors
        ├── detector_id           string, e.g. AID01107
        ├── direction             1=N 2=E 3=S 4=W 5=NE 6=SE 7=NW 8=SW
        └── lanes
            ├── lane_id           4-lane: 1 Fast, 2 Middle2, 3 Middle1, 4 Slow
            │                     3-lane: 1 Fast, 2 Middle, 3 Slow
            │                     2-lane: 1 Fast, 2 Slow
            │                     1-lane: 1 Fast
            ├── speed             int, km/h
            ├── occupancy         int, % of time the zone is occupied
            ├── volume            int, vehicles in the interval
            ├── sd                decimal, standard deviation of speed (1 dp)
            └── valid             "Y" = detector online, "N" = offline
```

### Detector locations CSV columns

`AID_ID_Number, District, Road_EN, Road_TC, Road_SC, Easting, Northing,
Latitude, Longitude, Direction, Rotation`

- Easting/Northing are **HK1980 Grid**; Latitude/Longitude are WGS-84 — use the
  lat/lon columns and skip the projection work.
- `Rotation` is the detector's bearing in degrees; useful for snapping a
  detector to the correct **direction** of a two-way road in SUMO.
- IDs come in families: `AIDxxxxx` (older), `TDSxxxxx` and named prefixes like
  `TDSAPR…` (Aberdeen Praya Road), `TDSSPWR…` (Shek Pai Wan Road). Do not assume
  a single ID format.

### Processed segment XML (optional, easier)

`date, time, irn_version` then per segment: `segment_id` (= `ROUTE_ID` in the
Intelligent Road Network centreline), `speed` (km/h), `valid` (Y/N).
Useful for a quick corridor speed map without lane-level detail.

---

## 2. Incidents — Special Traffic News (2nd generation)

Dataset: `https://data.gov.hk/en-data/dataset/hk-td-tis_19-special-traffic-news-v2`
Update frequency: **real time**.
Schema: `https://www.td.gov.hk/en/special_news/trafficnews.xsd`
Data dictionary (v4.0):
`https://static.data.gov.hk/td/special-traffic-news/en/Data_Specification_for_STN_Eng_v4.0.pdf`

| Language | URL |
|---|---|
| English | `https://www.td.gov.hk/en/special_news/trafficnews.xml` |
| Traditional Chinese | `https://www.td.gov.hk/tc/special_news/trafficnews.xml` |
| Simplified Chinese | `https://www.td.gov.hk/sc/special_news/trafficnews.xml` |

### Fields

`INCIDENT_NUMBER` (e.g. `IN-19-09408`) · `INCIDENT_HEADING_EN/CN` (e.g. "Road
Incident") · `INCIDENT_DETAIL_EN/CN` (e.g. "Traffic Accident") · `LOCATION_EN/CN`
· `DISTRICT_EN/CN` (one of the 18 districts) · `DIRECTION_EN/CN` (bound) ·
`ANNOUNCEMENT_DATE` (`YYYY-MM-DDTHH:MM:SS`) · `INCIDENT_STATUS_EN/CN`
(**NEW / UPDATED / CLOSED**) · `NEAR_LANDMARK_EN/CN` · `BETWEEN_LANDMARK_EN/CN`
· `ID` (numeric) · `CONTENT_EN/CN` (the full prose message) · `LATITUDE` ·
`LONGITUDE` (WGS-84).

### ⚠️ Gotchas — this is why the Incident Reader is a GenAI job

- **`LATITUDE` / `LONGITUDE` are frequently empty.** Both worked examples in the
  official data dictionary have them blank. You cannot rely on coordinates.
- **`DISTRICT_EN` is often empty too** (blank in both official examples).
- The real information — which lanes, which direction, how bad — lives in
  `CONTENT_EN` as free prose: *"Due to traffic accident, the fast lane of San
  Tin Highway Yuen Long bound near Fairview Park Roundabout is closed to all
  traffic. Only remaining lane(s) is still available to motorists. Traffic is
  busy now."*
- Messages containing tables are replaced by a link to the TD website.
- The feed carries **all** kinds of "special traffic news", including public
  processions, road works and public-transport arrangements — not just crashes.
  The Reader must output an `in_scope` flag.
- Status transitions are how you get duration: first `NEW`, then zero or more
  `UPDATED`, then `CLOSED`. **Clearance time = CLOSED time − NEW time.**

---

## 3. Historical archive API (how we replay a past incident)

Both feeds are snapshotted by DATA.GOV.HK. All times are GMT+8. The latest
available historical data is from **yesterday** — you cannot archive today.

**List available versions of a file**
```
https://api.data.gov.hk/v1/historical-archive/list-file-versions
    ?url=<url-encoded file url>
    &start=YYYYMMDD
    &end=YYYYMMDD
```

**Fetch one version** (returns 302, follow the redirect)
```
https://api.data.gov.hk/v1/historical-archive/get-file
    ?url=<url-encoded file url>
    &time=YYYYMMDD-HHmm
```

Response codes: 200 success · 302 redirect (file downloads) · 400 syntax error
(missing parameter) · 404 that version does not exist.

⚠️ Historical queries return at most **10,000 rows** for a date range — page it.
⚠️ The dataset pages also offer **packaged daily / monthly archives**, which are
much faster than pulling thousands of 1-minute snapshots. Prefer those for a
whole-day pull; use the API for precise timestamps.

**Practical recipe for one incident day:**
1. Pull the STN archive for the day, dedupe by `INCIDENT_NUMBER`, find incidents
   whose `LOCATION_EN` matches our corridor.
2. Note `NEW` and `CLOSED` timestamps.
3. Pull raw detector snapshots for `NEW − 90 min` to `CLOSED + 60 min`.
4. Aggregate detector data to 5-minute bins per detector per lane.

---

## 4. Road network (turn restrictions)

Dataset: *Road Network (2nd Generation)*
`https://data.gov.hk/en-data/dataset/hk-td-tis_15-road-network-v2`
Formats: FGDB, KML, **GML** (GML is plain XML — easiest to parse).
Contains traffic directions, **turning restrictions at road junctions**,
stopping restrictions, on-street parking.

Three layers matter for a graph model:
- **Road Centerline** → edges
- **Intersection point of two centrelines** → nodes
- **Restricted turn movement** → forbidden turns (roads being connected does not
  mean vehicles may turn between them)

> Decision: for the SUMO twin we build the network from **OpenStreetMap**
> (faster, SUMO-native). Use the TD Road Network only if OSM turn restrictions
> look wrong on the corridor, or as a credibility slide ("our network is
> consistent with TD's Intelligent Road Network").

Related: *Intelligent Road Network Package* (TD) also publishes Traffic Aids
Drawings (signs and signals) and the Annual Traffic Flow Census.

---

## 5. Our corridor — Aberdeen detector inventory

Verified present in the locations CSV. Two full directional chains form the
main corridor; Pok Fu Lam Road / Shek Pai Wan Road form the western alternative.

### Chain 1 — Aberdeen → Wan Chai / Causeway Bay (eastbound / northbound)
| ID | Road | District |
|---|---|---|
| AID01101 | Aberdeen Praya Road near Abba House — EB | Southern |
| AID01102 | Aberdeen Praya Road near Hoi Fai Mansion — EB | Southern |
| AID01103 | Wong Chuk Hang Road near Aberdeen Technical School — EB | Southern |
| AID01104 | Wong Chuk Hang Road Flyover near AXA Southside — EB | Southern |
| AID01105 | Wong Chuk Hang Road Flyover near Benefit Ind. Bldg — EB | Southern |
| AID01106 | Wong Chuk Hang Road near HK Academy of Medicine — EB | Southern |
| **AID01107** | **Aberdeen Tunnel near Wong Chuk Hang Hospital — EB** | Southern |
| AID01108 | Wong Nai Chung Gap Flyover near Racecourse — NB | Wan Chai |
| AID01109 | Canal Road Flyover near Cricket Club — NB | Wan Chai |
| AID01110 | Canal Road Flyover near Wan Chai Fire Station — NB | Wan Chai |

### Chain 2 — Causeway Bay / Wan Chai → Aberdeen (southbound / westbound)
| ID | Road | District |
|---|---|---|
| AID01214 | Canal Road Flyover near Elizabeth House — SB | Wan Chai |
| AID01215 | Canal Road Flyover near Wing Tak Building — SB | Wan Chai |
| AID01216 | Wong Nai Chung Gap Flyover near Racecourse — SB | Wan Chai |
| **AID01217** | **Aberdeen Tunnel near Toll Plaza — WB** | Southern |
| AID01218 | Wong Chuk Hang Road near WCH Sports Centre — WB | Southern |
| AID01219 | Wong Chuk Hang Road near WCH Recreation Ground — WB | Southern |
| AID01220 | Wong Chuk Hang Road Flyover near Cheung Tak Ind. Bldg — WB | Southern |
| AID01221 | Wong Chuk Hang Road near Aberdeen Police Station — WB | Southern |
| AID01222 | Aberdeen Praya Road near Ocean Court — WB | Southern |
| AID01223 | Aberdeen Praya Road near Aberdeen Bus Terminus — WB | Southern |

### Western alternative (via Pok Fu Lam Road — past Queen Mary Hospital)
| ID | Road |
|---|---|
| TDSSPWR10001 | Pok Fu Lam Road near St. Paul's College Primary School — EB |
| TDSSPWR10002 | Shek Pai Wan Road near Wah Kwai Estate — EB |
| TDSSPWR10003 | Shek Pai Wan Road near Shek Pai Wan Road Playground — EB |
| TDSSPWR20001 | Shek Pai Wan Road near Wah Fu Road — WB |
| TDSSPWR20002 | Shek Pai Wan Road near Wah Kwai Estate — WB |
| TDSSPWR20003 | Shek Pai Wan Road near Shek Pai Wan Road Playground — WB |
| TDSAPR10001 | Aberdeen Praya Road near Wholesale Fish Market — EB |
| TDSAPR20001 | Aberdeen Praya Road near Wholesale Fish Market — WB |

**Alternatives to model:** Pok Fu Lam Road (west, past Queen Mary Hospital) ·
Wong Nai Chung Gap Road / Stubbs Road (over the hill) · Shek Pai Wan Road →
Wah Fu → Pok Fu Lam Road · **MTR South Island Line** as a mode shift.

> ❗ Cheung Tsing Highway and Nam Wan Tunnel (the 29 Jul 2026 incident) have
> **no detectors in this feed**. Use that incident as narrative only.

---

## 6. Data ethics — for the ethics slide

- Everything we use is **aggregate and open**. No personal data, no vehicle
  identifiers, no tracking of individuals. Say this explicitly.
- **Coverage bias is real and must be named:** detectors sit on strategic and
  major roads. Districts and back streets with no detectors get worse forecasts,
  so a naive rollout would serve well-instrumented (often wealthier or
  higher-traffic) corridors first. Our mitigation: report a confidence level per
  corridor based on detector density, and refuse to recommend where coverage is
  below a threshold.
- `valid = "N"` means the detector was offline. Never silently treat missing
  data as zero traffic — count and report it.
