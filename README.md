# Ripple

An AI incident co-pilot for Hong Kong traffic operators. When an incident is
reported, Ripple reads the Transport Department's message, tests a handful of
response plans in a simulation of the road network, recommends the plan with
the least total delay, and drafts messages that split traffic across the
alternatives instead of sending everyone down the same detour.

**Ripple recommends; it never controls.** Nothing reaches a sign or a signal
until a human operator approves it, and every approval is logged.

Built for the Hong Kong Inter-University GenAI Hackathon for the SDGs 2026
(hack4sdg), Track 1: Green Transport & Smart Mobility. Pilot corridor:
Aberdeen Tunnel and its alternatives. Submission: 18 Oct 2026.

## Tracker

**Last updated: Thu 24 Sep 2026, 18:00** · Week 1 of 5 (21–27 Sep: setup and pick
the incident) · Stand-ups: Sunday and Wednesday

✅ done · 🟡 in progress · ⚪ not started, or nothing in the repo yet

**Critical path:** 🟡 demo incident chosen → ⚪ baseline matches reality →
⚪ three plans compared → ⚪ video. If anything slips, cut features and protect
this chain.

> **Keeping this current.** In the same pull request as your work, update your
> rows and add a line to the [update log](#update-log). A status only counts if
> the repo shows it, so link the file that proves it. After each stand-up,
> refresh the date and **This week**. Full timeline:
> [docs/04-plan.md](docs/04-plan.md).

### Milestones

| Date | Milestone | Status |
|---|---|---|
| Sun 27 Sep | 🔒 Team picks **the** demo incident | ⚪ |
| Sat 3 Oct | 📤 Submit interim report (official deadline Sun 4 Oct) | ⚪ |
| Sun 4 Oct | 🚦 Go / no-go: if the baseline does not roughly match the detectors, switch to the ~15-link network that day | ⚪ |
| Mon 12 Oct | Pitching workshop, everyone (HKU Innovation Wing 2, 14:00–17:30) | ⚪ |
| Wed 14 Oct | 🔒 **Results freeze**: bug fixes only after this, every number locked | ⚪ |
| Sat 17 Oct | 📤 Submit deck + prototype (official deadline Sun 18 Oct) | ⚪ |
| Thu 22 Oct | Finalists announced | ⚪ |
| Sat 24 Oct | Final pitch, CityU Kowloon Tong | ⚪ |

### Components

| | Component | Owner | Status |
|---|---|---|---|
| A | Loaders: detector and incident archives, live poller | Data | 🟡 Archive client, incident timelines, detector bins with coverage, corridor table, candidate screener and live poller ([src/loaders/](src/loaders/)). Committed output: the 28-detector [data/detectors.csv](data/detectors.csv); shortlist still to generate |
| B | Incident Reader (GenAI #1): STN message → `incident.json` | Lead | 🟡 Parses all 20 dev messages ([src/reader/](src/reader/)). Accuracy: 100 gold messages drawn ([gold_messages.jsonl](data/labelled_incidents/gold_messages.jsonl)), labelling app and scorer ready, labels not started ([LABELLING.md](data/labelled_incidents/LABELLING.md)) |
| C | Twin: SUMO model of the corridor, calibrated to detectors | Simulation | 🟡 Starter scripts and a draft Aberdeen network workflow are in [simulation_validation/](simulation_validation/SIMULATION_README.md). Candidate traffic runs; route teleports, detector calibration, and incident validation still need work. |
| D | Plan Generator (GenAI #2): 3–5 plans + constraint validator | Lead | ⚪ Planned for week 3 |
| E | Evaluator: runs every plan, writes metrics to `results/` | Data | ⚪ Planned for week 3 |
| F | Briefing Writer (GenAI #3): briefing + bilingual sign text | Lead | ⚪ Planned for week 3 |
| G | Operator console: map, plan comparison, Approve + audit log | Visuals | 🟡 Streamlit console with the corridor detector map, coloured by speed, with headline stats and a bin slider ([src/console/app.py](src/console/app.py), [screenshot](docs/img/week1-corridor-map.png)). Plan comparison, Approve and audit log still to build |
| H | Evidence pack: validation, accuracy, interviews, deck | Impact | 🟡 Problem evidence drafted in [docs/05-pitch.md](docs/05-pitch.md) §3; workspaces and their definitions of done are in [evidence/interviews/](evidence/interviews/) and [deck/](deck/) |

The JSON contracts between modules are in
[docs/03-architecture.md](docs/03-architecture.md). Build to them.

### This week: Week 1 (21–27 Sep)

| Owner | Task | Done when | Status |
|---|---|---|---|
| Lead | Freeze scope; write `CLAUDE.md`; create repo; test the Incident Reader on 20 real messages | repo exists, 20 messages parsed | ✅ 22 Sep |
| Data | Pull Aberdeen detector + incident archives; shortlist 3–5 corridor incidents with good detector coverage | shortlist in `data/candidates.md` | 🟡 loaders and screener built ([src/loaders/candidates.py](src/loaders/candidates.py)); 3-month STN pull and `fetch candidates` still to run |
| Visuals | Map of corridor detectors coloured by speed, from a static file | screenshot posted | ✅ 24 Sep — [screenshot](docs/img/week1-corridor-map.png) of the 21 Sep 08:20 bin ([src/console/app.py](src/console/app.py)) |
| Simulation | Install SUMO; build the Aberdeen network from OSM; get vehicles moving | a video of cars moving | 🟡 SUMO and a draft network run locally; record/share evidence and improve route coverage ([guide](simulation_validation/SIMULATION_README.md)) |
| Impact | Line up 2–3 user interviews; fact-check the evidence claims; start the interim report | `evidence/interviews/plan.md` exists with one interview scheduled; every claim in `05-pitch.md` §3 carries a source and the date it was checked | 🟡 evidence drafted; interviews and fact-check outstanding |

### In review

Work that exists but is not on `main` yet, as of Thu 24 Sep, 18:00. Everything
merged shows in the rows above; pull requests #1–#10 are all merged.

| What | Who | Branch |
|---|---|---|
| [#11](https://github.com/f1ymango/ripple/pull/11) Console: headline stats, legend, street basemap, clock-time bin slider, and the week-1 screenshot | Visuals | `visuals/map-improvements` |

Six branches whose pull request is already merged are still on the remote
(`data/loaders`, `docs/impact-workspace`, `docs/readme-tracker`,
`docs/tracker-data-layer`, `visuals/detector-map`,
`visuals/tracker-role-label`). Deleting them keeps the branch list readable.

### Open decisions

- **The demo incident** (🔒 Sun 27 Sep), from Data's shortlist. Corridor
  incidents are rare: 15–21 Sep had only two (IN-26-06874, IN-26-06904), so
  search a longer window. Only about a quarter of incidents have a captured
  CLOSED message, so three months should give roughly 5–7 usable candidates.
  The screener ranks them on archive coverage as well as the speed drop, and
  the run takes an afternoon, so it has to start before Sunday:
  `python -m src.loaders.fetch candidates --start 2026-06-22 --end 2026-09-21`
  writes `data/candidates.md`.
- **One corridor-road list.** The Reader ([src/reader/reader.py](src/reader/reader.py))
  and the loaders ([src/loaders/corridor.py](src/loaders/corridor.py)) each
  keep their own, and they differ: Stubbs Road and the Chinese road names are
  only in the Reader's. Pick one and share it.
- **Who runs the live poller, and on which machine.** Its data has no gaps,
  but it only records while it runs (`python -m src.loaders.fetch live`).
- **What the Evaluator (E) simulates for `lanes_closed: ["unspecified"]`**
  (Data, before E's first run). The Reader now says "some lanes are closed, the
  message does not say which" instead of "none"; E picks the closure to
  simulate and states that assumption with the results
  ([docs/03-architecture.md](docs/03-architecture.md) §3). 7 of the 20 dev
  messages are this case.
- **Calibration thresholds** (Data + Simulation): a bin is used for GEH only at
  ≥ 40% archive coverage and ≥ 90% of lane readings valid
  ([docs/02-data.md](docs/02-data.md) §7). Relax them deliberately if too few
  bins survive, and state the values on the validation slide.
- **`network_state.json` vs component A's CSV output**: the contract promises a
  shape A does not emit yet. Raised in the PR #2 review; the Lead is taking it to
  Simulation.
- **Enter the Best WorkBuddy Award?** If yes, assign one person in week 3
  ([docs/01-hackathon.md](docs/01-hackathon.md) §5).

### Known issues

- Incident Reader accuracy is not measured yet. The 100 gold messages still
  need labelling ([data/labelled_incidents/LABELLING.md](data/labelled_incidents/LABELLING.md)).
- `requirements.txt` pins `pandas==2.2.3`, which has no build for Python 3.14,
  so `pip install -r requirements.txt` fails on a 3.14 venv. `pip install
  streamlit==1.40.2` on its own works there (it brings pandas 2.3.3).
- Lane totals are wrong on 2 of the 20 dev messages.
- No Aberdeen-corridor message has been through a live model run yet. Scope
  detection is tested on two real corridor messages, with the model mocked.
- The historical archive serves only about half the raw detector snapshots it
  lists (39% were a persistent 404 on 21 Sep), so a 5-minute bin usually holds
  1–3 observed minutes. Summing raw volume into a bin would understate flow by
  about half, so the loader reports a flow rate and a `coverage_pct` instead.
  The missing minutes cannot be recovered
  ([docs/02-data.md](docs/02-data.md) §3, §7).
- For [C]: the processed segment-speed feed is fully retrievable. It has no
  volume, so it cannot support GEH, but it is the better series for the speed
  side of validation ([docs/02-data.md](docs/02-data.md) §3).

### Definition of done

- [ ] One real archived incident replayed end to end
- [ ] Validation chart: simulated vs observed, with a stated error
- [ ] Three plans compared on ≥ 4 metrics
- [ ] Sensitivity: plan still wins across compliance and clearance ranges
- [ ] Incident Reader accuracy measured on ~100 labelled messages
- [ ] One on-screen moment where a real bilingual message goes in and a ranked
      plan + briefing + sign text come out
- [ ] Operator console with an Approve action and an audit log
- [ ] 2–3 user interviews recorded in `evidence/interviews/`
- [ ] ~90-second video
- [ ] Deck covering all five criteria
- [ ] Every number traceable to a file in `results/`

### Update log

Newest first. One line per change that matters, with a link to the proof.

**Thu 24 Sep**
- Week-1 Visuals task done: the corridor map, coloured by speed, screenshot
  posted ([docs/img/week1-corridor-map.png](docs/img/week1-corridor-map.png)).
  The frame is the 21 Sep 08:20 bin — mean 55 km/h, 5 of 28 detectors at or
  below 30 km/h, slowest AID01106 at 14 km/h. The morning peak clears by 08:45,
  so the later bins show nothing.
- Console: the bin slider showed a full ISO timestamp
  (`2026-09-21T08:20:00+08:00`) on every tick; it now shows clock time. Also
  landed: headline stats, colour legend, street basemap, a readable snapshot
  picker, and fixes for a blank-speed snapshot crashing the page, a bin width
  labelled 5 minutes whatever the data said, and the coverage-filtered exports
  being indistinguishable from full windows
  ([src/console/app.py](src/console/app.py), 17 tests in
  [tests/test_console.py](tests/test_console.py)).
- Data layer: a truncated archive snapshot no longer crashes `fetch incidents`,
  `candidates` or `detectors`. Any snapshot that does not parse is skipped, and
  each run prints how many snapshots were listed, read, not served and
  unparseable, naming the unparseable ones. Across 22 Jun–21 Sep only one of
  9,690 STN snapshots is affected, 3 Aug 08:15. The archive returns the same
  cut-off file on every request, so refetching cannot fix it
  ([src/loaders/incidents.py](src/loaders/incidents.py),
  [tests/test_loaders_edges.py](tests/test_loaders_edges.py),
  [docs/02-data.md](docs/02-data.md) §3).
- Contract change agreed by the team: `lanes_closed` gains `unspecified` for
  "part of the lanes is closed", which had come out the same as "no lane
  closed". The Evaluator (E) decides what to simulate for it
  ([docs/03-architecture.md](docs/03-architecture.md) §3,
  [src/reader/incident.schema.json](src/reader/incident.schema.json),
  [src/reader/prompts/system.md](src/reader/prompts/system.md)).
- Incident Reader accuracy, set up: the sampler draws a gold set of 80
  citywide + 20 corridor messages from 22 Jun–21 Sep, leaving out the dev set
  and the prompt's worked examples; a Streamlit app to label them; a scorer
  with per-field accuracy and 95% intervals, its matching rules fixed before
  any score is seen ([LABELLING.md](data/labelled_incidents/LABELLING.md),
  [src/reader/label.py](src/reader/label.py), [src/reader/score.py](src/reader/score.py)).
  The sampler now reads the data layer's cache and still rebuilds the dev set
  byte for byte.
- Gold set drawn: 80 citywide + 20 corridor messages from 2,519 incidents,
  with no dev-set incident or worked example among them. 47 of the 100 say
  "part of the lanes"
  ([data/labelled_incidents/gold_messages.jsonl](data/labelled_incidents/gold_messages.jsonl)).
- Reader prompt and labelling guide aligned on four rules found by labelling
  the dev set twice: a closure that also mentions buses takes the closure's
  cause, not `public_transport_notice` (otherwise code marks a corridor
  closure out of scope); "road incident" alone is `other`; a bracketed
  section name stays in `road_name`; English wins over Chinese. On the dev
  set the Reader parses 20/20 and gives `unspecified` for all 7 "part of the
  lanes" closures, but still types "road incident" as `road_works`
  ([results/reader/2026-09-24T1504_qwen3-8b.jsonl](results/reader/2026-09-24T1504_qwen3-8b.jsonl)).
- One archived STN snapshot (3 Aug 08:15) is truncated. The gold sampler skips
  and reports it. The data layer's incident loader crashed on it, which
  blocked the candidate screen over 22 Jun–21 Sep; fixed in the entry above.

**Wed 23 Sep**
- Evidence pack (component H): workspaces for the interviews and the deck, each
  with its own definition of done ([evidence/interviews/](evidence/interviews/),
  [deck/](deck/)).
- Operator console (component G) started: Streamlit app with the 28-detector
  corridor map coloured by speed, greying detectors when no speed snapshot is
  loaded rather than inventing one ([src/console/app.py](src/console/app.py)).
- All 15 items from the PR #2 review of the data layer fixed, each with a test
  that fails on the previous code. The ones that changed numbers: an offline
  lane halved a detector's count, and sensor outages were reported as archive
  gaps. Also fixed: a 15-minute request returned 20 minutes, and censored
  incidents showed a duration of 0. 153 tests
  ([tests/test_loaders.py](tests/test_loaders.py),
  [tests/test_loaders_edges.py](tests/test_loaders_edges.py)).
- Found in the detector feed: when no vehicle passes, the speed is the road's
  speed limit (about 19% of lane readings) and occupancy is often -1. Such a lane
  now has no speed and 0% occupancy. At night 77 of 975 corridor bins had been
  showing the limit as a measured speed ([docs/02-data.md](docs/02-data.md) §1).
- Lane convention agreed: offside to nearside Fast, Middle Lane 2, Middle
  Lane 1, Slow ([docs/03-architecture.md](docs/03-architecture.md) §3). The
  Incident Reader prompt already matches.
- Ways around the archive's missing minutes: the candidate screener scores
  coverage, `--bin-minutes 15` for calibration, and a live poller
  ([src/loaders/candidates.py](src/loaders/candidates.py),
  [src/loaders/live.py](src/loaders/live.py)).
- Tracker and `CLAUDE.md` brought up to date with the data layer
  ([#3](https://github.com/f1ymango/ripple/pull/3)).

**Tue 22 Sep**
- Data layer (component A): archive client, incident timelines from archived
  STN snapshots, detector readings in 5-minute bins with coverage, and the 28
  corridor detectors ([data/detectors.csv](data/detectors.csv), for the map).
  Merged in PR #2.
- Measured against the live feed: `lane_id` and `direction` are text, the
  archive timestamp runs about 9 minutes behind the data, and about half of the
  listed detector snapshots are a persistent 404
  ([docs/02-data.md](docs/02-data.md)).
- Incident Reader pinned to `qwen3:8b`. After the fix below, both models
  parse 20/20 dev messages and none is wrongly marked in scope; `qwen3:8b`
  takes about 4.6 s per message on an 8 GB laptop GPU.
  ([results/reader/](results/reader/))
- Reader fix: code, not the model, decides whether a message is on the
  corridor; the district is copied from the feed, never guessed; the prompt
  gained five worked examples from real messages.
- First Reader runs on the dev set: `qwen3:4b` flagged 7 of 20; `qwen3:8b`
  parsed all 20 but marked 17 off-corridor messages as in scope.
- Reader runs on local models through Ollama; every call is logged to
  [evidence/ai-log/](evidence/ai-log/).
- 20 real Special Traffic News messages from 15–21 Sep added as the Reader dev
  set ([data/labelled_incidents/](data/labelled_incidents/)).
- Incident Reader (component B): contract schema, validation, retry once then
  flag, 17 tests that need no LLM.
- Python environment: pinned requirements, pytest config.

**Mon 21 Sep**
- Repo created: `CLAUDE.md` and the brief, hackathon, data, architecture, plan
  and pitch docs.

## Quick start

Python 3.11 or newer.

```bash
git clone https://github.com/f1ymango/ripple.git
cd ripple
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest                   # 153 tests, no LLM needed
```

### Run the data layer

```bash
python -m src.loaders.fetch corridor     # writes data/detectors.csv
python -m src.loaders.fetch candidates --start 2026-06-22 --end 2026-09-21
python -m src.loaders.fetch detectors --start 2026-09-21T07:00 --end 2026-09-21T10:00
python -m src.loaders.fetch live         # polls the live feeds until stopped
```

Downloads are cached in `data/raw/`, so each machine fills its own cache the
first time. Read [docs/02-data.md](docs/02-data.md) §7 before calibrating on
the detector bins.

### Run the Incident Reader

The model (`qwen3:8b`, run locally through Ollama) only reads what the message
says: road, direction, landmark, lanes closed, incident type. Code copies what
the feed already carries (IDs, text, times, coordinates) and decides whether
the message is about our corridor. Every reply is checked against the
contract, retried once if it fails, then flagged, never used.

Install [Ollama](https://ollama.com), then:

```bash
ollama pull qwen3:8b               # 5.2 GB, once
python -m src.reader.run           # parses data/labelled_incidents/messages.jsonl
python -m src.reader.run --model qwen3:4b   # same messages, another model
```

Each run writes `results/reader/<time>_<model>.jsonl`. Without a GPU it runs
on the CPU, much more slowly.

To collect real messages from the DATA.GOV.HK archive:

```bash
python -m src.reader.sample --start 2026-09-15 --end 2026-09-21 --n 20 --out dev.jsonl
```

It never overwrites an existing file. Downloads go through the data layer's
cache in `data/raw/` (not committed); run `python -m src.loaders.fetch prefetch
--feed stn ...` first to download a long window in parallel. The gold set
behind the accuracy number is made and labelled as described in
[data/labelled_incidents/LABELLING.md](data/labelled_incidents/LABELLING.md).

### Run the operator console

```bash
streamlit run src/console/app.py
```

![The corridor console at the 21 Sep 08:20 bin: five detectors at or below 30
km/h along the Aberdeen Tunnel approach](docs/img/week1-corridor-map.png)

The map draws all 28 corridor detectors from [data/detectors.csv](data/detectors.csv).
Colour comes from a `data/detector_5min_*.csv` window written by the data
layer; without one, every detector stays grey rather than being given an
invented speed. Pick the window in the sidebar and the bin on the slider —
prefer a full window over a `_cov` export, which is a filtered subset meant for
count calibration ([docs/02-data.md](docs/02-data.md) §7).

## Rules everyone follows

The full list is in [CLAUDE.md](CLAUDE.md). The ones that bite:

- **The LLM never produces a number the simulator can compute.** Every number
  we present comes from `results/`, and nobody edits `results/` by hand.
- **Build to the contracts.** Changing one is a team decision, said out loud
  and written into [docs/03-architecture.md](docs/03-architecture.md) the same day.
- **Never invent data.** If a source is missing, say so. Test stand-ins are
  named `mock_*` and live in `tests/fixtures/`.
- **Log every LLM call** to `evidence/ai-log/`. Prompts live in files under
  `src/*/prompts/`, never inline.
- **Runs are seeded and reproducible.**

## Working in the repo

- One branch per piece of work (e.g. `data/archive-loader`), then a pull
  request to `main`. The Lead merges.
- Add your packages, pinned, under your component's heading in
  [requirements.txt](requirements.txt).
- On Windows, open text files with `encoding="utf-8"`: Python still defaults
  to cp1252 there, and our data is in English and Chinese.

## Docs

| File | What's in it |
|---|---|
| [00-brief.md](docs/00-brief.md) | The product, the components, what is out of scope |
| [01-hackathon.md](docs/01-hackathon.md) | Rules, dates, judging criteria |
| [02-data.md](docs/02-data.md) | Data feeds, schemas and their gotchas |
| [03-architecture.md](docs/03-architecture.md) | JSON contracts between modules |
| [04-plan.md](docs/04-plan.md) | Timeline, roles, critical path |
| [05-pitch.md](docs/05-pitch.md) | Narrative, evidence, Q&A, ethics |

## Data

Traffic detector data and Special Traffic News from
[DATA.GOV.HK](https://data.gov.hk) and the Transport Department. Attribute both
wherever the data is shown. Everything we use is aggregate and open: no
personal data, no vehicle identifiers.
