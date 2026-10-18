# sim/

SUMO inputs for the two corridors. How the twin is built and validated:
[src/twin/README.md](../src/twin/README.md).

| Path | What it holds |
|---|---|
| [`scenarios/`](scenarios/) | Aberdeen network edits, calibration, twin inputs and evaluator scenario files (`evaluator_IN-26-03365_*.json`); `*.example.json` show the format |
| [`scenarios/rankings/`](scenarios/rankings/) | Grid definitions used for each ranking |
| [`scenarios/evaluator-diagnostics/`](scenarios/evaluator-diagnostics/) | Diagnostic scenario variants ([replay, 8 Oct](../docs/evaluator-replay-2026-10-08.md)) |
| [`scenarios/tuen-mun/`](scenarios/tuen-mun/) | Tuen Mun scenario files ([matched-comparison protocol](../docs/tuen-mun-p1-p2-protocol-2026-10-14.md)) |
| [`tuen-mun/`](tuen-mun/) | Tuen Mun network, signals and observations ([two-incident pack](../docs/demo-two-incidents-2026-10-16.md)) |
