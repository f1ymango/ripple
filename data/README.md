# data/

Inputs and generated drafts. Raw downloads are cached in `data/raw/`, which is
not committed; see [docs/02-data.md](../docs/02-data.md) for every feed and its gotchas.

| Path | What it holds |
|---|---|
| [`detectors.csv`](detectors.csv) | The 28 Aberdeen corridor detectors drawn on the console map |
| [`candidates.md`](candidates.md), [`demo_shortlist.md`](demo_shortlist.md) | Incident screen and the shortlist that picked the demo cases |
| [`demo_incident_messages.jsonl`](demo_incident_messages.jsonl) | Archived TD messages for the Aberdeen demo incident (IN-26-03365) |
| [`hk_holidays.csv`](hk_holidays.csv) | Public holidays, used to pick ordinary comparison days |
| [`labelled_incidents/`](labelled_incidents/README.md) | 100 hand-labelled messages and the Reader scoring history |
| [`generated-plans/`](generated-plans/) | Model-drafted P0/P1/P2 plan sets, with the inputs that produced them |
| [`generated-briefings/`](generated-briefings/) | Briefing drafts (pending human review; not approved advice) |
| `lead-inputs/`, `plan-context/`, `plan-experiments/` | Context and experiments behind the plan drafts ([Lead P2 diagnostic](../docs/lead-p2-diagnostic-2026-10-13.md)) |
| [`tuen-mun/`](tuen-mun/) | Tuen Mun case inputs ([Tuen Mun replay](../docs/tuen-mun-2026-10-14.md)) |
