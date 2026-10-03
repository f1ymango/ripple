# Lead pipeline handoff — 30 September 2026

## Status

The initial D/F command-line path implements the existing plan and briefing
field shapes in [the architecture](03-architecture.md), with exactly P0/P1/P2.
Tests use mocked responses and named fixtures. Real model quality, evaluated
benefits, an optimiser and console integration remain outstanding.
The [interim report](interim-report.md) now contains the Lead's Reader evidence.

## Required C/E context

Supply a reviewed context matching `CONTEXT_SCHEMA` in
[schema.py](../src/plans/schema.py). This is internal configuration, not a
replacement for a shared module contract.

| Field | Required input |
|---|---|
| `incident_id`, `reviewed`, `sources` | Matching incident, explicit review and supporting paths |
| `active_from`, `active_until` | Time-zone-qualified action window, starting at or after the report |
| `od_demand_vehicles` | Demand by OD for that window |
| `routes` | Each OD/via pair's full road list and residential/school exposure |
| `blocked_roads` | Additional unavailable roads |
| `signals` | Supported junction IDs and maximum green extensions in seconds |
| `sign_ids`, `pt_modes` | Supported signs and modes; empty lists if unavailable |
| `priority_corridor` | Reviewed emergency OD and roads to keep clear |

[mock_plan_context.json](../tests/fixtures/mock_plan_context.json) illustrates
structure only. Never use its synthetic metadata for real runs. Road names
must be canonical across inputs; code normalises case and spacing but cannot
infer aliases or missing route segments. The incident road is also excluded
from diversions when lanes are closed.

The proposed 08:55 physical onset, TD's 09:01 report and unresolved physical
lane choice remain separate. D preserves `unspecified`; Data/E still owns
the lane evidence/default policy. Operator actions cannot precede the report.
A new incident update needs another reviewed context; D does not schedule phases.

## Generate plans

Before starting the model, C/E can check their incident/context handoff locally:

```bash
python -m src.plans.run --incident results/reader/2026-09-29T1608_qwen3-8b.jsonl --message-id 138270 --context PATH_TO_REVIEWED_CONTEXT.json --check-only
```

This runs the same incident/context checks as generation. It does not call a
model, create outputs, verify source documents, or prove route feasibility. The
context must already have been reviewed; `reviewed: true` is a caller assertion.
Candidate constraints are checked once actual plans exist. `--check-only` cannot
be combined with `--out-dir`.

With Ollama and `qwen3:8b` available, supply an actual reviewed context:

```bash
python -m src.plans.run --incident results/reader/2026-09-29T1608_qwen3-8b.jsonl --message-id 138270 --context PATH_TO_REVIEWED_CONTEXT.json --out-dir data/generated-plans/IN-26-03365-first
```

The new directory receives `P0.json`, `P1.json`, `P2.json` and
`generation-inputs.json`. No simulation or approval occurs.

Code checks all five documented constraints. Residential exposure conservatively
counts the entire marked route, weighted by OD vehicles, against 15% of diverted
demand. School checks cover the full action window in Hong Kong time. Unknown
routes, unsupported controls and altered emergency corridors fail validation.

P0 uses empty action arrays and empty `pt_nudge` strings. P1 advises every
supplied OD to take one detour with share 1; compliance is a separate evaluator
parameter. P2 must differ in its intervention. Code supplies `constraints_checked`.

## Evaluate and draft

E must evaluate the exact plans and save one contracted result per plan under
`results/runs/`, with matching incident, compliance, clearance and seed. P0 must
report GEH >=85% and speed MAPE <=15%. The approved
[provenance sidecar](03-architecture.md#result-provenance-sidecar--e--f-approved-by-lead-30-sep)
is now required. E calls `capture_inputs` from `src/evaluation_provenance.py`
before simulation and `write_result` afterwards. This binds each result to
the exact validated plan, saved generation inputs and shared simulator input
files. Old results without provenance fail closed; never backfill unknown
input identities. Acceptance of a full incident replay still needs C/E review.

Replace these result placeholders with actual artifacts:

```bash
python -m src.briefing.run --plans data/generated-plans/IN-26-03365-first --results results/runs/P0_RUN.json results/runs/P1_RUN.json results/runs/P2_RUN.json --out data/generated-briefings/IN-26-03365-first.json
```

Do not manufacture results to unblock this step. The current unvalidated
baseline cannot pass. Code selects the lowest total vehicle-hours delay,
including P0; ties prefer the lower plan ID. This is a single-scenario comparison,
not evidence of robustness across compliance or clearance assumptions.

Use the same briefing command with `--check-only` instead of `--out` to check
the saved handoff without generating prose:

```bash
python -m src.briefing.run --plans data/generated-plans/IN-26-03365-first --results results/runs/P0_RUN.json results/runs/P1_RUN.json results/runs/P2_RUN.json --check-only
```

This revalidates plans against their saved incident/context, checks result
comparability and baseline targets, and verifies every provenance sidecar and
shared input hash. It reports the lowest-delay candidate without writing files
or calling the model. The direct `write_briefing` API now uses this same gate;
copying `constraints_checked` into an unsafe plan cannot bypass revalidation.
Python integrations can call `src.briefing.writer.prepare_comparison` for the
validated plan, selected result, baseline and source paths. Passing this gate
does not establish full incident validation or operator approval.

The model drafts bilingual prose using named evidence tokens. Code inserts
saved metrics, source paths and character counts. Literal numeric claims and
unknown tokens fail. Common worded quantities (English number words, fractions,
multipliers and Chinese numerals) also fail, including Unicode-obfuscated forms.
This conservative guard can reject legitimate names containing number words;
such drafts need revision. VMS limits are checked after rendering: three lines maximum,
60 characters per line in each language. Operator text requires 3–5 sentences.
Token checks do not establish semantic correctness or catch every unsupported
claim written in words. Human review remains required before publication.

## Checks and reproducibility

Prompts live in `src/plans/prompts/` and `src/briefing/prompts/`. Calls use the
seeded adapter and log prompts, responses and transport failures in
`evidence/ai-log/`. Invalid responses get one retry, then fail visibly.
Existing output files are not overwritten. No signs or signals are controlled.

```bash
python -m pytest tests/test_plans_briefing.py
```

Fabricated traffic inputs live only in `tests/fixtures/mock_*`. CLI tests use
temporary artifacts; they never save synthetic project results and need no model
or SUMO service.
