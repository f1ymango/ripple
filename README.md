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

**Last updated: Wed 23 Sep 2026** · Week 1 of 5 (21–27 Sep: setup and pick
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
| B | Incident Reader (GenAI #1): STN message → `incident.json` | Lead | 🟡 Parses all 20 dev messages; accuracy not measured yet ([src/reader/](src/reader/)) |
| C | Twin: SUMO model of the corridor, calibrated to detectors | Simulation | ⚪ Nothing in the repo yet |
| D | Plan Generator (GenAI #2): 3–5 plans + constraint validator | Lead | ⚪ Planned for week 3 |
| E | Evaluator: runs every plan, writes metrics to `results/` | Data | ⚪ Planned for week 3 |
| F | Briefing Writer (GenAI #3): briefing + bilingual sign text | Lead | ⚪ Planned for week 3 |
| G | Operator console: map, plan comparison, Approve + audit log | Visuals | 🟡 Streamlit console with the corridor detector map, coloured by speed ([src/console/app.py](src/console/app.py)) |
| H | Evidence pack: validation, accuracy, interviews | Impact | 🟡 Problem evidence drafted in [docs/05-pitch.md](docs/05-pitch.md) §3 |

The JSON contracts between modules are in
[docs/03-architecture.md](docs/03-architecture.md). Build to them.

### This week: Week 1 (21–27 Sep)

| Owner | Task | Done when | Status |
|---|---|---|---|
| Lead | Freeze scope; write `CLAUDE.md`; create repo; test the Incident Reader on 20 real messages | repo exists, 20 messages parsed | ✅ 22 Sep |
| Data | Pull Aberdeen detector + incident archives; shortlist 3–5 corridor incidents with good detector coverage | shortlist in `data/candidates.md` | 🟡 loaders and screener built ([src/loaders/candidates.py](src/loaders/candidates.py)); 3-month STN pull and `fetch candidates` still to run |
| Visuals | Map of corridor detectors coloured by speed, from a static file | screenshot posted | 🟡 map built ([src/console/app.py](src/console/app.py)); screenshot to post |
| Simulation | Install SUMO; build the Aberdeen network from OSM; get vehicles moving | a video of cars moving | ⚪ |
| Impact | Gather problem evidence; line up 2–3 user interviews | `05-pitch.md` evidence section filled | 🟡 evidence drafted |

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
- **An `unspecified` lane value in `incident.json`**, so "part of the lanes is
  closed" stops coming out as "no lanes closed". A contract change: decide as a
  team, then update [docs/03-architecture.md](docs/03-architecture.md) the same day.
  12 of the 20 dev messages are this case. Without it, the Evaluator (E) would
  inject such an incident as no closure at all.
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

- Incident Reader accuracy is not measured yet. That needs ~100 hand-labelled
  messages, none of them from the dev set or the prompt's worked examples
  (see [data/labelled_incidents/README.md](data/labelled_incidents/README.md)).
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

**Wed 23 Sep**
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
python -m src.reader.sample --start 2026-09-15 --end 2026-09-21 --n 20
```

This **overwrites** `data/labelled_incidents/messages.jsonl`, the committed
dev set. Downloads are cached in `data/raw/` (not committed); a week of archive
takes about 20 minutes the first time.

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
