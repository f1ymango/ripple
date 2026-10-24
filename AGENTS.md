# AGENTS.md — repository guidance

> This file is read automatically by Codex at the start of every session
> in this repo. Keep it short; point at the context files rather than repeating
> them.

## Project

**Ripple** — an AI incident co-pilot for Hong Kong traffic operators.
The current implementation is the UST Ripple Team 1075 competition alpha for
Hack4SDG 2026, Track 1 (Green Transport & Smart Mobility). The competition
phase is over. Read [PROJECT_STATUS.md](PROJECT_STATUS.md) before treating any
dated plan or deadline as current. A future Ripple phase may use a new design.

Before doing anything substantial, read:
- `docs/00-brief.md` — the product, the components, and what is out of scope
- `docs/02-data.md` — data feeds, schemas and their gotchas
- `docs/03-architecture.md` — the JSON contracts between modules

## Non-negotiable rules

1. **The LLM never produces a number that the simulator can compute.** It reads
   messages, proposes candidate plans, and writes explanations. Every metric
   comes from the simulator and lands in `results/`.
2. **For alpha fixes, preserve the contracts in `docs/03-architecture.md`.**
   If a future phase changes them, document the new phase and migrate its
   callers and evidence together.
3. **Label the phase.** The scope in `docs/00-brief.md` describes the 2026
   competition entry. A future project can choose a different scope without
   retroactively changing the alpha's claims.
4. **Never invent data.** If a data source is unavailable, say so; do not
   fabricate plausible values, even for a placeholder. Mock files must be
   clearly named `mock_*` and live in `tests/fixtures/`.
5. **Log every LLM call** (prompt, response, model, timestamp) to
   `evidence/ai-log/`.
6. **Prompts live in files** under `src/*/prompts/`, never as inline strings.
7. **Runs are seeded and reproducible.** Never hand-edit anything in `results/`.
8. **Small, readable code.** A teammate should be able to understand the
   alpha's behavior and how its saved results were produced.
9. **Preserve the competition record.** Do not move or rewrite the
   `judge-facing-2026-10-18` tag or final deck and media. Keep new results
   separate from the saved 2026 evidence.

## Commands

```bash
# setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# data layer (cached in data/raw/): corridor table, incident shortlist, detector bins
python -m src.loaders.fetch corridor
python -m src.loaders.fetch candidates --start 2026-03-22 --end 2026-09-21
python -m src.loaders.fetch detectors --start 2026-09-21T07:00 --end 2026-09-21T10:00
python -m src.loaders.fetch twin-detectors --start 2026-05-15T07:55 --end 2026-05-15T10:35

# Incident Reader: sample real STN messages, then parse them with a local model
# (needs Ollama running, https://ollama.com, and `ollama pull qwen3:8b`)
python -m src.reader.sample --start 2026-09-15 --end 2026-09-21 --n 20 --out dev.jsonl
python -m src.reader.run --messages data/labelled_incidents/messages.jsonl

# Reader accuracy: label the gold set, then score a run (data/labelled_incidents/LABELLING.md)
streamlit run src/reader/label.py
python -m src.reader.score --run results/reader/<run_id>.jsonl

# twin (needs SUMO installed; step by step in src/twin/README.md)
python -m src.twin.check_sumo

# tests (no LLM needed)
python -m pytest

# run one scenario
python -m src.evaluator.run --incident IN-26-01234 --plan P2 \
    --compliance 0.5 --clearance 60

# batch: all plans x compliance x clearance
python -m src.evaluator.batch --incident IN-26-01234

# console
streamlit run src/console/app.py
```

## Layout

```
src/loaders/   A — detector + incident archives, live poller
src/reader/    B — GenAI #1: incident message -> incident.json
src/twin/      C — SUMO network, demand, incident injection
src/plans/     D — GenAI #2 + constraint validator + optimiser
src/evaluator/ E — scenario runner -> results/runs/<run_id>.json
src/briefing/  F — GenAI #3: plan + metrics -> briefing.json
src/console/   G — Streamlit operator console
results/       ⭐ single source of truth for every number we present
evidence/      ai-log/, interviews/, audit_log.jsonl
```

## 2026 competition ownership (historical)

| Area | Owner |
|---|---|
| B, D, F + integration + merges to main | Lead |
| A, E | Data |
| C + calibration | Simulation |
| G + video | Visuals |
| Deck, evidence pack | Impact |
