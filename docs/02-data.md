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

> ⚠️ **Checked against the live feed on 22 Sep 2026.** The values below are what
> the XML actually carries. `lane_id` and `direction` arrive as **text**, not as
> the numeric codes an earlier version of this section implied; the PDF itself
> types `lane_id` as `string` and lists the exact strings. The **numbering in
> the PDF's coding table may be the lane's position on the carriageway, or may
> just enumerate the possible strings — see the open question below.

```
date                              yyyy-mm-dd
└── periods (two 30-second intervals per file)
    ├── period_from               HH:mm:ss
    ├── period_to                 HH:mm:ss
    └── detectors
        ├── detector_id           string, e.g. AID01107
        ├── direction             TEXT, 8-point compass: "North", "North East",
        │                         "East", "South East", "South", "South West",
        │                         "West", "North West"  (not 1-8)
        └── lanes
            ├── lane_id           TEXT (PDF data type: string). Values, in
            │                     CARRIAGEWAY ORDER, fast -> slow:
            │                       4-lane: Fast Lane, Middle Lane 2,
            │                               Middle Lane 1, Slow Lane
            │                       3-lane: Fast Lane, Middle Lane, Slow Lane
            │                       2-lane: Fast Lane, Slow Lane
            │                       1-lane: Fast Lane
            ├── speed             int, km/h
            ├── occupancy         int, % of time the zone is occupied
            ├── volume            int, vehicles in the interval
            ├── s.d.              decimal, standard deviation of speed (1 dp)
            │                     (the tag name really does contain dots)
            └── valid             "Y" = detector online, "N" = offline
```

#### ⚠️ Lane position on 4-lane roads — OPEN QUESTION

Positions run fast → slow: from the offside (median) lane across to the
nearside (kerb) lane. Hong Kong drives on the left, so the Fast Lane is the
driver's right-hand lane. For 1-, 2- and 3-lane carriageways the names map
unambiguously. **For 4-lane carriageways, which physical lane `Middle Lane 1`
is has not been established.**

Two sources, and they may or may not agree:

```
Data-dictionary PDF, "Coding" column      XML serialisation order
  1. Fast Lane                              Fast Lane
  2. Middle Lane 2                          Middle Lane 1
  3. Middle Lane 1                          Middle Lane 2
  4. Slow Lane                              Slow Lane
```

The PDF's numbering may be carriageway positions, or may simply enumerate the
possible output strings — its wording ("different output will be generated
depends on the number of lanes") does not say which.

**Evidence so far, from AID01217 over 40 30-second periods (21 Sep, 08:15–08:30):**

| lane, in file order | mean speed | total veh | mean occupancy |
|---|---|---|---|
| Fast Lane | 82.7 km/h | 401 | 7.6% |
| Middle Lane 1 | 80.0 km/h | 181 | 3.4% |
| Middle Lane 2 | 75.2 km/h | 195 | 6.2% |
| Slow Lane | 73.1 km/h | 16 | 0.3% |

Speed falls monotonically in file order, and `Middle Lane 2` shows higher
occupancy than `Middle Lane 1` at similar volume — both consistent with
`Middle Lane 2` being the lane nearer the kerb, i.e. file order = carriageway
order. **This is 20 minutes of one morning at one detector and is not
conclusive.**

**To settle it** (week 2, before [E] needs a lane mapping): rerun the table
above over the full cached window. If `Middle Lane 1` consistently sits between
`Fast Lane` and `Middle Lane 2` on speed and occupancy across weeks and across
times of day, file order is carriageway order. Otherwise ask the Transport
Department through the data.gov.hk enquiry channel.

**Until then, the rule that is safe either way:** map lanes by **name**, never
by position in the file, and keep the single name→SUMO-index conversion in one
function in [E] so that flipping it later is a one-line change. Nothing in the
loaders depends on the answer; only incident injection does, and only on this
one detector — AID01217, the Aberdeen Tunnel toll-plaza approach, the only
4-lane detector on the corridor.

Lane counts across our 28 corridor detectors: **16 two-lane, 11 three-lane,
1 four-lane**. Nothing may assume a fixed number of lanes per detector.

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

> ⚠️ **Two things the archive does that will silently corrupt your results if
> you do not handle them.** Both measured on 21 Sep 2026; see
> `src/loaders/detectors.py`.
>
> **(a) The archive timestamp is not the data timestamp.** The file archived at
> `20260921-0830` contains the periods `08:21:00-08:22:00` — a publish lag of
> about nine minutes. Always take the time from `date` + `period_from` *inside*
> the file, and widen any wanted window by ~15 minutes before asking the archive
> for versions.
>
> **(b) Coverage is partial, and roughly a third of listed versions are dead.**
> For the hour 08:00-09:00, `list-file-versions` returned 41 timestamps, only 28
> of which `get-file` would serve — the other 13 are a persistent 404, not a
> transient error, so do not waste retries on them. Those 28 files held **28
> distinct data minutes out of 60 (about 47%)**, with gaps of up to five minutes.
>
> **The consequence of (b):** a five-minute bin typically contains one to three
> sampled minutes, not five. **Summing raw volume into a bin understates flow by
> roughly half**, and since GEH compares counts, a twin calibrated on those sums
> would be fitted to half of Hong Kong's real traffic — and would still appear to
> validate. Bins must therefore report a flow *rate* over the seconds actually
> observed, together with the coverage behind it. See section 7.


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

---

## 7. Using the 5-minute bins — read this before calibrating

`src/loaders/detectors.py` emits one row per detector per five minutes. Because
of the partial coverage in section 3, every row carries how much of the window
was actually observed:

| Column | Meaning |
|---|---|
| `speed_kmh` | volume-weighted mean over valid lanes |
| `flow_veh_h` | vehicles per hour, over the seconds actually observed |
| `count_5min` | the count a full five-minute bin implies — **this is the number for GEH** |
| `volume_observed` | vehicles actually counted (usually far fewer than `count_5min`) |
| `periods_observed` | how many 30-second periods the bin is built from |
| `coverage_pct` | `periods_observed × 30 / 300` — the sampling fraction |
| `lanes_valid` / `lanes_offline` | offline lanes are counted, never treated as zero traffic |

**`coverage_pct` is a precision label, not a correctness label.** A bin at 10%
is not wrong, it is uncertain — the same five minutes estimated from one sample
can come out at 200 vehicles when the truth is 90.

**Rules:**

- **Speed survives low coverage. Counts do not.** A 30-second reading of
  26 km/h is a fair estimate of the speed at that moment; a 30-second count
  scaled ×10 is a gamble. Use every bin for the speed chart; use only
  high-coverage bins for GEH.
- **Calibrate on `coverage_pct >= 40`** (the loader's default, exported as a
  separate `_cov40.csv`). If that leaves too few points, relax the threshold
  deliberately and **state the threshold on the validation slide**.
- **Never quote a count from a bin without quoting its coverage.** Every number
  in the deck traces to `results/`; a count whose sampling fraction is unknown
  cannot be defended in the Q&A.
- Run the loader's coverage-versus-speed check before filtering. If low- and
  high-coverage bins show similar mean speeds, the filter is a precision filter
  and nothing more. If they differ, filtering would bias the calibration and
  that has to be said out loud.
