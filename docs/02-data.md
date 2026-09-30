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


#### ⚠️ Two markers in the readings (measured across all of Hong Kong, 21 Sep)

- **When no vehicle crosses a loop, the feed reports the road's speed limit as
  the speed** — 70, 80, 100, 50, 110 km/h. That is 441,064 readings a day, about
  19% of all lane readings. It is not a measurement.
- **`<occupancy>-1</occupancy>` means "not measured"**, and appeared 2,143
  times, every one of them with `volume` 0.

The loader treats a lane with `volume` 0 as having **no speed** and **0%
occupancy** (an empty loop is unoccupied), and treats any negative value as
missing. The raw cache keeps what the feed sent. Before this was handled, a bin
with no vehicles reported the speed limit as its speed — at night, 77 of 975
five-minute bins on the corridor.

#### Lane position on 4-lane roads — adopted convention

**Team decision, 23 Sep.** Offside (median) to nearside (kerb) — Hong Kong drives
on the left, so the Fast Lane is the driver's right-hand lane:

```
Fast Lane  →  Middle Lane 2  →  Middle Lane 1  →  Slow Lane
```

So **`Middle Lane 1` is next to the Slow Lane** and `Middle Lane 2` is next to
the Fast Lane. This matches the data-dictionary PDF's coding table and
`src/reader/prompts/system.md` (`middle2` next to `fast`), so the Reader's
vocabulary and the detector names line up with no translation. For 1-, 2- and
3-lane carriageways the names are unambiguous; a 3-lane road's single middle
lane is `Middle Lane` in the feed and `middle1` in `incident.json`.

**The XML does not list lanes in carriageway order.** It sends
`Fast Lane, Middle Lane 1, Middle Lane 2, Slow Lane`. Never infer a lane's
position from its place in the file — match by name.

**One recorded disagreement, not acted on.** At AID01217 (Aberdeen Tunnel near
Toll Plaza) over a full day (1,102 periods), `(occupancy ÷ vehicles) × speed`
— a proxy for vehicle length — is 96.7 for `Middle Lane 2` against 70.1 for
`Middle Lane 1` (~38% higher), in all five time bands. The usual pattern of heavy vehicles keeping left would put
`Middle Lane 2` nearer the kerb, which contradicts the convention. The
convention stands: that proxy assumes keep-left behaviour, and lane use on a
toll-plaza approach can be set by booth assignment instead. We do not know which
explains it. `python -m src.loaders.fetch lanes` reproduces the numbers; it
reports agreement or disagreement and never changes the mapping.

AID01217 is our only 4-lane detector, so this affects one detector and one
function ([E]'s name → SUMO-index mapping, week 3).

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
- **`CLOSED` is usually not a new message.** TD closes an incident by switching
  a message already in the feed, normally the last one (*"...is re-opened to
  all traffic"*), from `UPDATED` to `CLOSED`. Its `ID`, text and
  `ANNOUNCEMENT_DATE` stay the same, so the clearance time is that message's
  announcement time, not the time the flip was seen. A loader that keeps each
  message ID only as first seen never sees the `CLOSED`; ours did, and that is
  why only about a quarter of incidents first looked complete.
- When the flip falls in an archive gap, a captured *"re-opened to all
  traffic"* (or *"...has been cleared"*, *"...now cancelled"*) message gives the
  same clearance time. *"...remain closed"* is a partial reopening and does not
  count. `incidents.csv` says which source was used in `clearance_source`.
- **TD also switches the NEW message to CLOSED**, sometimes half an hour before
  the incident ends (IN-26-06887: NEW 10:02 shown CLOSED by 11:06, arrangement
  cancelled 11:32), and an incident number can carry on after one of its
  messages is closed (IN-26-02351: a lane re-opened at 06:04, closed again at
  23:00). So the **start** is the message published as NEW, even once it shows
  CLOSED, and the **clearance** is read only from the incident's latest
  message, never from the NEW one. A CLOSED on the NEW message alone says the
  incident is over, not when: that row stays `right_censored`. No row has a
  zero or negative duration.
- **Each archived copy holds exactly one message, and the feed is three
  files.** Every readable archived copy of the three files above for 22 Mar–21
  Sep (54,117; 27 more are truncated) holds one `<message>`, so a message is
  only archived if it is the one
  on display when the archive saves a copy. The three files carry the same
  records — same `ID`, `INCIDENT_NUMBER`, times, status and English text; the
  `/sc/` file's Chinese text is the same text in simplified script — but the
  archive saves them at different moments, so `incidents.load` reads all three
  and merges by message ID (`archive.FEEDS`: `stn`, `stn_tc`, `stn_sc`). Rules:
  - the English copy is kept; `/sc/` Chinese text is never used;
  - a `CLOSED` is never undone: the feed serves out-of-date copies still saying
    `UPDATED` for a few minutes after the switch (954 of 3,933 closed
    messages; median 3 min, one case 3 h);
  - a copy with a different `INCIDENT_NUMBER` or `ANNOUNCEMENT_DATE` is not the
    same message and is not merged (none found); a copy whose text TD edited in
    place still counts as a sighting, first text kept, and is reported (3
    copies of 2 messages, all location fields).

  Measured over 22 Mar–21 Sep:

  | | English file alone | All three files |
  |---|---|---|
  | Distinct messages | 9,119 | 10,410 |
  | Incidents | 4,681 | 4,784 |
  | With a complete timeline | 3,176 (68%) | 4,067 (85%) |
  | Corridor traffic accidents, complete | 35 of 53 | 49 of 55 |
  | …and lasting ≥ 20 min | 22 | 35 |

  Nothing the English file gave is contradicted: no start time changes, no
  incident loses its timeline, and all 22 earlier usable corridor accidents
  keep the same start and end. 11 clearances move later, all off-corridor
  notices ("heavy traffic", car parks, MTR) whose final message only the
  Chinese files caught. `seen_in` in `incidents.csv` names the files each
  incident was seen in. For the English file alone:
  `incidents.load(start, end, feeds=("stn",))`.

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
> **(b) Coverage is partial: only about half of the listed detector versions can
> actually be retrieved.** `list-file-versions` returns timestamps that
> `get-file` then 404s on. The 404 is persistent, not transient — retrying is
> wasted effort — and it is **specific to the raw detector feed**:
>
> | Feed (sampled 40 versions, 21 Sep) | listed/day | retrievable | avg size |
> |---|---|---|---|
> | Special Traffic News | 127 | **40/40** | ~1.5 KB |
> | Segment speeds (`irnAvgSpeed-all.xml`) | 619 | **40/40** | ~373 KB |
> | Raw detectors (`rawSpeedVol-all.xml`) | 901 | **17/40** | ~694 KB |
>
> Across time-of-day bands on two days, detector retrievability ran 36–71% with
> no pattern we can establish at this sample size — treat it as roughly half,
> scattered, with early indications that night windows are worse than daytime
> ones (33% at 04:00 against 47% at 08:00). It is not a timestamp-rounding
> problem: neighbouring minutes usually serve fine. **Nor is it
> de-duplication** — inspecting the data periods either side of a 404 shows
> genuine holes, e.g. a jump from 03:56 straight to 04:05 with five 404s in
> between, 26 minutes lost in one 40-minute stretch. The minutes are gone, not
> stored elsewhere.
>
> Update frequency is not the cause either: the processed feed refreshes every
> 2 minutes (less often than the raw feed's 1 minute) and loses nothing. What
> tracks the failures is storage load — 0.2 MB/day for STN and 231 MB/day for
> the processed feed, both intact, against 625 MB/day for the raw feed. The cause is unverified; the raw detector feed is by far
> the heaviest thing the archive stores (~625 MB/day against ~231 MB for
> segments), so retention or storage pressure is the leading guess. Asking the
> Transport Department is the only way to know.
>
> **How the loader handles it.** A 404 is permanent, so it is recorded as a
> zero-byte `<timestamp>.404` beside the cache and never requested again
> (delete those files to force a recheck). A 5xx, a network failure, or a 200
> whose body is not the feed's XML is transient: not recorded, not cached, and
> retried on the next run. `prefetch` reports the two separately. A snapshot
> the archive serves **cut off part-way** is a third case: STN `20260803-0815`
> stops mid-`<LONGITUDE>`, and the archive returns the same 1,583 bytes on
> every request, so it is cached as served. The loaders skip any snapshot that
> does not parse, and every run prints one line per feed: snapshots listed,
> read, not served, and unparseable, naming the unparseable ones.
>
> Net effect: for the hour 08:00-09:00, 41 versions listed, 28 served, holding
> **28 distinct data minutes out of 60 (about 47%)**, with gaps of up to five
> minutes.
>
> **Note for [C]:** the processed segment-speed feed is fully retrievable and
> twice as dense. It carries no volume, so it cannot support GEH — but for the
> *speed* side of validation, where sparse coverage hurts least anyway, it is a
> better series than the raw feed. Worth using alongside it.
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
`archive.list_versions` asks for one calendar month at a time: a month of raw
detector versions is about 27,000 rows (~900 a day), so any request longer
than about 11 days would hit the cap.
⚠️ **A few archived snapshots are malformed.** Of 18,381 STN snapshots for
22 Mar–21 Sep, 8 would not parse. 4 are a complete document followed by NUL
bytes; `common.parse_xml` strips them and reads the file. The other 4
(`20260419-2002`, `20260608-1446`, `20260608-1449`, `20260803-0815`) stop
mid-document and come back byte-identical on every request, so they are skipped
and named in each run's summary line (§3 above).
⚠️ The dataset pages also offer **packaged daily / monthly archives**, which are
much faster than pulling thousands of 1-minute snapshots. Prefer those for a
whole-day pull; use the API for precise timestamps.

**Practical recipe for one incident day:**
1. Pull the STN archive for the day, dedupe by `INCIDENT_NUMBER`, find incidents
   whose `LOCATION_EN` matches our corridor.
2. Note `NEW` and `CLOSED` timestamps (`CLOSED` is a status change on an
   existing message, see §2).
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

`src/loaders/detectors.py` emits one row per detector per five minutes —
**every** five minutes of the window, for every corridor detector, since 26 Sep.
A slot the archive delivered nothing for is a row with `periods_observed` 0 and
blank speed and counts, never a missing row. So is every slot of a detector
that is missing from the snapshots the archive did deliver (15 May 07:55-10:35:
AID01105, AID01220 and TDSSPWR20002) -- that is a feed outage, not
an archive gap, though both read `coverage_pct` 0. The twin matches observations
by timestamp, so a missing simulated interval remains unmatched without
shifting later slots. The full grid keeps archive gaps visible. Because of the
partial coverage in section 3, every row carries how much of the window was
actually observed:

| Column | Meaning |
|---|---|
| `speed_kmh` | volume-weighted mean over valid lanes. Blank when no vehicle crossed — never the speed limit the feed reports then |
| `flow_veh_h` | vehicles per hour: each lane's rate over its own valid seconds, summed. Blank if any lane never reported — the total is unknown, not smaller |
| `count_bin` | the count this bin width implies — **this is the number for GEH** |
| `volume_observed` | vehicles actually counted (usually far fewer than `count_bin`) |
| `periods_observed` | how many 30-second periods the bin is built from |
| `bin_minutes` | the bin width these numbers were computed at |
| `coverage_pct` | seconds the **archive** delivered ÷ bin seconds — archive gaps only |
| `lane_completeness_pct` | share of delivered lane readings the **sensors** marked valid — detector outages only |
| `lanes_valid` / `lanes_offline` | offline lane readings are counted, never treated as zero traffic |

**`coverage_pct` is a precision label, not a correctness label.** A bin at 10%
is not wrong, it is uncertain — the same five minutes estimated from one sample
can come out at 200 vehicles when the truth is 90.

**Rules:**

- **Speed survives low coverage. Counts do not.** A 30-second reading of
  26 km/h is a fair estimate of the speed at that moment; a 30-second count
  scaled ×10 is a gamble. Use every bin for the speed chart; use only
  high-coverage bins for GEH.
- **Calibrate on `coverage_pct >= 40` *and* `lane_completeness_pct >= 90`**
  (the loader's defaults, exported as a separate `_cov40.csv`). The two are
  different failures and must not be merged: archive gaps are unrelated to
  traffic, detector outages are not — sensors fail in exactly the conditions an
  incident creates. Before 23 Sep an offline lane was counted as an empty one,
  halving a two-lane road's count while coverage still read 100%. If that leaves too few points, relax the threshold
  deliberately and **state the threshold on the validation slide**. What each
  choice leaves for the demo morning, before and after the incident, with the
  bias check below:

      python -m src.loaders.fetch bin-survival --start 2026-05-15T07:55 --end 2026-05-15T10:35 --split 2026-05-15T08:55

  (`results/data/bin-survival_20260515-0755_1035.md`). A bin holds whole
  archived minutes, so coverage comes in steps -- mostly 20%, 40% and 60% --
  and a threshold between two steps changes nothing.
- **Never quote a count from a bin without quoting its coverage.** Every number
  in the deck traces to `results/`; a count whose sampling fraction is unknown
  cannot be defended in the Q&A.
- **`_cov40.csv` is a subset, not a series.** It drops the bins below the
  thresholds, so it must never be lined up by position with anything. For a
  series with unusable counts blanked but every row kept, use
  `detectors.calibration_series()` — or, for the twin, the file below.
- Run the loader's coverage-versus-speed check before filtering. If low- and
  high-coverage bins show similar mean speeds, the filter is a precision filter
  and nothing more. If they differ, filtering would bias the calibration and
  that has to be said out loud.


### Handing the bins to the twin

    python -m src.loaders.fetch twin-detectors --start 2026-05-15T07:55 --end 2026-05-15T10:35

writes `sim/scenarios/detectors.json` in the twin's own format
(`sim/scenarios/detectors.example.json`): one observation per detector per
5-minute slot, starting at `--start`, which is the simulation's time 0. `count`
is `count_bin` where the bin passes both thresholds above and `null` otherwise;
`speed_kmh` is the measured speed, `null` where no vehicle was measured; a slot
with no vehicles and every lane reporting is `count: 0`, a real measurement.
`coverage_pct` rides along on each observation. Nothing is interpolated. An
`edge_id` / `position_m` already filled in by hand is kept when the file is
rewritten. Both ends must sit on 5-minute boundaries.

Two more inputs for the twin (30 Sep), both into `results/data/`:

    python -m src.loaders.fetch flow-balance --start 2026-05-15T07:55 --end 2026-05-15T08:55 --ordinary-day 2026-05-08 2026-04-24
    python -m src.loaders.fetch free-flow --day 2026-05-08 2026-04-24 --start 07:30 --end 11:00

`flow-balance` gives each detector's hourly flow and the change between
neighbouring detectors: where traffic joins or leaves the corridor, with a 95%
sampling margin, checked against ordinary days. `free-flow` gives each
detector's speeds in light traffic (occupancy at or below 10%), the desired
speeds a model should reproduce before any queue forms.

### Four ways we offset the missing minutes

The gaps cannot be filled — the files do not exist, on either archive host, at
any timestamp (checked 22 Sep). So the loader offsets them instead, cheapest
first:

**1. Choose an incident the detectors plainly saw.** `data/candidates.md`
compares every corridor traffic accident with two ordinary days (same weekday
and clock time, not a public holiday, no corridor incident in the window) and
credits a detector only when it ran 20+ km/h below the ordinary day for longer
than the two ordinary days ever differed; it also reports archive coverage per
incident. The team picks from that table, and `data/demo_shortlist.md` gives
Data's reasoned pick:

    python -m src.loaders.fetch candidates --start 2026-03-22 --end 2026-09-21

Three detector windows per incident; about ten minutes on a filled cache, over
an hour on a fresh one, because STN is read from six weeks before `--start`.

Two rules were added on 29 Sep, after the table was generated: public holidays
(`data/hk_holidays.csv`, the government's 1823 list) are never ordinary days,
and incidents are loaded from six weeks before `--start` so that a control day
before the range is checked too (before, it always looked clean). The demo
incident was re-screened under both rules on its own, without replacing the
full table:

    python -m src.loaders.fetch candidates --start 2026-05-15 --end 2026-05-15 \
        --out results/data/candidates_2026-05-15.md

**2. Widen the bin where precision matters more than timing.** Demand
calibration for the pre-incident hour wants a stable count, not fine timing:

    python -m src.loaders.fetch detectors --start ... --end ... --bin-minutes 15

Three times the samples behind each count. Keep 5-minute bins for the incident
itself, where timing is the whole point. Two resolutions, two jobs.

**3. Poll the live feed from now on (component A4).** The live feed has no gap —
the Transport Department republishes every minute and we can take all of them:

    python -m src.loaders.fetch live

It cannot help a past incident, but every corridor incident from the moment it
starts is captured at 100% coverage, and corridor incidents run about two a
week. Needs a machine that stays awake; files are named by the data's own
timestamp, so a sleep costs only the minutes slept.

> This is also the honest Q&A answer: **our coverage limit is an artefact of
> replaying history, not of the system.** Deployed, Ripple reads the live feed.

**4. (Deferred) The processed segment-speed feed** is 100% retrievable and twice
as dense, and would strengthen the speed side of validation. But it keys on IRN
`segment_id`, and `speed_segments_info.csv` carries only `irn_id` and `route` —
no road names — so mapping segments to our corridor needs the separate Road
Network (2nd Generation) GML and a geospatial join against detector lat/lon.
Worth doing if week 2 has room; not a quick win.
