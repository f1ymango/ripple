# src/

One package per component. The JSON contracts between them are in
[docs/03-architecture.md](../docs/03-architecture.md).

| | Package | What it does | Owner |
|---|---|---|---|
| A | [`loaders/`](loaders/) | Detector and incident (Special Traffic News) archives from DATA.GOV.HK, corridor table, candidate screen, live poller | Data |
| B | [`reader/`](reader/) | **GenAI #1** — incident notice → `incident.json` with a local Qwen3:8b model; labelling and scoring tools | Lead |
| C | [`twin/`](twin/) | SUMO network, demand fitting, incident injection and audits ([README](twin/README.md)) | Simulation |
| D | [`plans/`](plans/) | **GenAI #2** — drafts response plans; deterministic validator and capacity bound | Lead |
| E | [`evaluator/`](evaluator/) | Runs every plan in SUMO and writes metrics and rankings to `results/` ([README](evaluator/README.md)) | Data |
| F | [`briefing/`](briefing/) | **GenAI #3** — operator briefing and bilingual sign-text drafts, checked against `results/` | Lead |
| G | [`console/`](console/) | Streamlit operator console: playback, plan comparison, approve/hold, audit log ([workflow](console/OPERATOR_WORKFLOW.md)) | Visuals |

Prompts live in each GenAI package's `prompts/` folder, never inline.
