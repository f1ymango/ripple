# results/

Every number Ripple presents comes from this folder. Files here are written by
the code (seeded runs, scoring scripts) and are **never edited by hand**. Each
simulation run sits next to a `*.provenance.json` that records its inputs.

## Start here

| Folder | What it holds | Explained in |
|---|---|---|
| [`demo-oct16/`](demo-oct16/) | **Frozen two-case pack** used in the pitch: plans, P0/P1/P2 runs with provenance, rankings and console verdicts for Aberdeen and Tuen Mun | [two-incident pack](../docs/demo-two-incidents-2026-10-16.md) |
| [`rankings/`](rankings/) | Ranking outputs under the team's paired comparison rule | [architecture §4](../docs/03-architecture.md) |
| [`reader/`](reader/) | Incident Reader runs (`<time>_<model>.jsonl`) and accuracy scores | [labelling and scores](../data/labelled_incidents/LABELLING.md) |

## Evidence behind the cases

| Folder | What it holds | Explained in |
|---|---|---|
| [`data/`](data/) | Data's detector checks: bin survival, lane evidence, flow balance, free-flow speeds | [observed vs modelled](../deck/real-vs-simulated.md) |
| [`twin/`](twin/) | SUMO twin replays and validation summaries | [twin README](twin/README.md) |
| [`tuen-mun-lead-grid-oct15-p0x-merge-at-site/`](tuen-mun-lead-grid-oct15-p0x-merge-at-site/) | The frozen Tuen Mun 18-cell grid behind the −4.3% comparison | [two-case handoff](../docs/2026-10-15-two-case-demo-handoff.md) |
| [`evaluator-lead-draft-20261013-b/`](evaluator-lead-draft-20261013-b/) | The Aberdeen grid behind the P0/P2 tie | [Lead plans on replay 3.1](../docs/evaluator-lead-plans-2026-10-13.md) |

## Diagnostics and earlier runs

Kept so every dated note in [`docs/`](../docs/README.md) still points at its evidence.

| Folder | Explained in |
|---|---|
| `evaluator-diagnostics/` | [first P0 result](../docs/evaluator-p0-2026-10-07.md) |
| `evaluator-rehearsal/`, `evaluator-rehearsal-v3/` | [replay v3](../docs/evaluator-replay-v3-2026-10-13.md) |
| `evaluator-lead-p2-nosignal-oct13/`, `evaluator-lead-p2-half-nosignal-oct13/` | [Lead P2 diagnostic](../docs/lead-p2-diagnostic-2026-10-13.md) |
| `simulation-review-oct10-control/`, `simulation-review-oct10-move-over/` | [Simulation review](../docs/simulation-evaluator-review-2026-10-09.md) |
| `diagnostic-whatif-slow-lane/` | [slow-lane what-if](../docs/whatif-slow-lane-2026-10-14.md) |
| `tuen-mun-diagnostic-oct14/` | [Tuen Mun replay](../docs/tuen-mun-2026-10-14.md) |
| `tuen-mun-p0-variants-oct15/`, `tuen-mun-share-sweep-oct15/`, `tuen-mun-share-020-fresh-oct15/`, `tuen-mun-lead-grid-oct15/` | [Tuen Mun evidence, 15 Oct](../docs/tuen-mun-go-no-go-evidence-2026-10-15.md) |
