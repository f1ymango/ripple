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

## How it works, and what exists today

Status as of 22 Sep 2026.

| | Component | What it does | Status |
|---|---|---|---|
| A | Loaders | Turn TD's detector and incident archives into tidy data | not in the repo yet |
| B | Incident Reader (GenAI #1) | TD's bilingual incident message → `incident.json` | **working prototype** |
| C | Twin | SUMO simulation of the corridor, calibrated to detector data | not in the repo yet |
| D | Plan Generator (GenAI #2) | Proposes 3–5 response plans; a validator rejects unsafe ones before simulation | not in the repo yet |
| E | Evaluator | Runs every plan in the twin and writes the metrics to `results/` | not in the repo yet |
| F | Briefing Writer (GenAI #3) | Plan + metrics → operator briefing and bilingual sign text | not in the repo yet |
| G | Operator console | Shows all of it; nothing goes out until an operator approves | not in the repo yet |

The JSON contracts between these modules are in
[docs/03-architecture.md](docs/03-architecture.md). Build to them.

### Incident Reader

The model (`qwen3:8b`, run locally through Ollama) only reads what the message
says: road, direction, landmark, lanes closed, incident type. Code copies what
the feed already carries (IDs, text, times, coordinates) and decides whether
the message is about our corridor. Every reply is checked against the
contract, retried once if it fails, then flagged, never used.

On the 20 real messages in [data/labelled_incidents/](data/labelled_incidents/)
it gets every one accepted, in about 4.6 s per message on an 8 GB laptop GPU.
Known gaps:

- Accuracy is not measured yet. That needs ~100 hand-labelled messages.
- "Part of the lanes is closed" comes out as no lanes, until the team decides
  on an `unspecified` lane value in the contract.
- Lane totals are wrong on 2 of the 20 messages.

Runs live in [results/reader/](results/reader/); every model call is logged in
[evidence/ai-log/](evidence/ai-log/).

## Quick start

Python 3.11 or newer.

```bash
git clone https://github.com/f1ymango/ripple.git
cd ripple
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest                   # 17 tests, no LLM needed
```

### Run the Incident Reader

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
