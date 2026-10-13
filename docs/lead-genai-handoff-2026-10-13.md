# Lead GenAI evidence and owner handoff — 13 October 2026

## Delivered and remaining

A real local Qwen3:8b call produced a constraint-validated P0/P1/P2 set for
IN-26-03365. This is a retrospective draft using Data's reviewed working
assumptions. No simulator run or public incident recommendation was produced.
The [joint P0 review](evaluator-p0-go-no-go-2026-10-09.md) remains NO-GO.

Base code: `8a62382341464ea067ad344699b364f48496364d`. D's prompt clarifies
literal empty strings, P0's comparison role and retaining a distinct P2
intervention on retry. F's prompt clarifies metric tokens and concise output.
The shared adapter now bounds responses at 2,048 output tokens and records
that setting in the call log; a repeating F request exposed the missing bound.
This applies to subsequent B/D/F calls, not the earlier D evidence below.
The fixture-only F helper is separate from the real recommendation CLI.
No validator, shared contract, scenario or saved simulator result was changed.
Implementation and immutable artifact commit:
`03c096389a7f624e52a028b771540a9782d6a8d9`. This commit contains the prompt
revisions and adapter fix made between attempts; the log is authoritative for
which prompt/settings each historical call actually used.

## D — actual model-generated plans

Directory: [IN-26-03365-lead-draft-20261013-b](../data/generated-plans/IN-26-03365-lead-draft-20261013-b/).
Evaluator plan-set ID: `lead-draft-20261013-b`.
Input Reader message: `138270` in
[`2026-09-29T1608_qwen3-8b.jsonl`](../results/reader/2026-09-29T1608_qwen3-8b.jsonl).
Context: [v2 JSON](../data/plan-context/IN-26-03365_first-report-v2.json) and
[Data's assumption review](../data/plan-context/IN-26-03365_first-report-v2.md).

| Plan | Saved action | Review |
| --- | --- | --- |
| P0 | No intervention | Correct comparison baseline; no signal, VMS or PT action |
| P1 | Advise both supplied OD groups via Wong Chuk Hang Road, share 1 each | Passes constraints; title incorrectly says "Single OD Group" although the actions cover both groups. Original model text is preserved. |
| P2 | Advise Canal Road group at share 0.8 and Wong Nai Chung Road group at 0.7; extend Tong Bin Lane junction green by 20 s | Distinct proposal; route and signal identifiers match supplied context. Shares and timing are candidate settings, not optimized or measured outcomes. |

The five validator checks passed for all three plans. A separate read-only
check reloaded the saved JSON and constructed E's `PlanActions` for each plan
at compliance 0.5 / clearance 66. This checks action mapping, not simulated
effectiveness. Compliance is distinct from the plan's advised diversion share.

The context was reviewed by Data as working assumptions, not accepted as an
operational network. Signal availability/timing, modelled OD demand, route
classifications and emergency-route evidence retain their stated limitations.
The route justification uses the later 09:36 message and the horizon ends at
the known 10:02 clearance. Label this **retrospective model demonstration**;
do not claim all context was available to an operator at 09:01.

### Integrity and model identity

These are SHA-256 hashes of raw file bytes, distinct from the canonical JSON
hashes E computes for its provenance sidecars.

| File within plan directory | SHA-256 |
| --- | --- |
| `P0.json` | `4198ec674296e0a1413b3ef3d0758fdf3e60124afbe9d51728b912b69ed898ff` |
| `P1.json` | `dae8a9c06f0e7d34b77407193ff36eb1d814311b8a8d0739fe508190da27dade` |
| `P2.json` | `3afc8b638a7abd2d9a290541d07032ab9a9f269fa4196c14f479ef7284eea20c` |
| `generation-inputs.json` | `8726acd9be7023a9483f3e46128fa172abb6bebf5f1361970194144d904f33a1` |

Local runtime: Python 3.13.16, Ollama 0.40.3, `qwen3:8b` (Q4_K_M), model
digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
Adapter settings: seed 42, context 8192, thinking disabled; D temperature 0.3.
Recorded identity supports reproduction; model/runtime changes may change text.
The initial host API outage cleared as Ollama completed its startup/upgrade;
no dependency installation or model download was performed by this execution.

All calls, including failures, are retained in
[`evidence/ai-log/2026-10-13.jsonl`](../evidence/ai-log/2026-10-13.jsonl).

| D call timestamp (HKT) | Logged duration | Outcome |
| --- | --- | --- |
| 12:17:58 | 74.66 s | Rejected: literal "empty" strings used for unsupported PT nudge |
| 12:19:13 | 12.37 s | Rejected: P2 actions identical to P1; first invocation failed |
| 12:20:00 | 12.18 s | Clarified prompt; rejected P1 policy violation |
| 12:20:13 | 12.78 s | Passed on retry; saved set above |

Successful D prompt SHA-256:
`7c93bba08a46efe169c7eeb1768662ededc306bc8a995138010bb6cf026d8404`.
The log records each exact prompt and raw response. Code adds
`constraints_checked`; generated actions and text were not hand-edited.
One successful example after retries is not a reliability benchmark.

## F — bounded real-model attempt failed; no accepted output

The synthetic comparison passed provenance/plan preflight and selected fixture
P2 using the unchanged `tests/fixtures/mock_recommendation/` bundle. This is
not an evaluation of the new D plans or of the real incident.

The new helper can preflight without any model call:

```powershell
.\.venv\Scripts\python.exe -m src.briefing.demo --check-only
```

Two invocations were attempted with `qwen3:8b`, temperature 0, seed 42,
context 8192 and thinking disabled. Neither saved an accepted briefing:

| F call timestamp (HKT) | Duration | Outcome |
| --- | --- | --- |
| 12:20:49 | 602.09 s | Initial request timed out; response unavailable. Local Ollama log showed repetitive generation exceeding 13,000 tokens. |
| 12:31:05 | 10.91 s | With the new 2,048-token bound and clarified prompt: rejected duplicate `MOCK-VMS` entries. |
| 12:31:16 | 8.41 s | Retry removed the duplicate but omitted required uncertainty tokens; invocation failed. |

The retry responses also contain literal numbers and present advice as already
in effect. Those statements are unsuitable even for an approved fixture
briefing. The validator stopped at the errors above; semantic inspection
identified these additional limitations. No validation was weakened, no JSON
was repaired, and no further model invocation was made. Human bilingual review
is pending; rejected text must not be presented as a finished F deliverable.

Requested output names `tests/fixtures/mock_genai_briefing_20261013_a.json`
and `tests/fixtures/mock_genai_briefing_20261013_b.json` do **not** exist. The
three failed call records remain in `evidence/ai-log/2026-10-13.jsonl`.
Initial F prompt SHA-256 was
`f5608ae5c70fd3931606045266c182d85f37f877b16ca5aa3ab3d59263837cf6`;
the retry prompt is
`a10a8c6fc451e6472ebea4ec68d8f1ae21e2e198ca011879552c895c8f594cae`.
The exact prompt text is in each call record. The helper and tests are
repeatable, but this execution does not demonstrate successful model F output.

The helper uses existing `mock_p0.json`, `mock_p1.json`, `mock_p2.json`,
`mock_generation-inputs.json`, `mock_p0_result.json`, `mock_p1_result.json`,
`mock_p2_result.json` and the original matching `.provenance.json` sidecars,
all under `tests/fixtures/mock_recommendation/`. The existing writer's source
aliases `results/runs/mock_p{0,1,2}_result.json` and
`results/runs/mock_p{0,1,2}_result.provenance.json` map to those fixture files,
not real runs. Do not show these aliases as real simulation evidence.

### Software verification

- Full suite after the runtime/helper changes: **582 passed, 1 skipped**
  (Windows), with the existing Streamlit/Altair deprecation warning.
- Final focused plans/briefing/helper/adapter/repository checks: **65 passed**.
  `git diff --check` passed.
- The new helper tests check original fixture provenance, logged generation,
  exclusive output preservation and rejection of non-fixture destinations.
- The adapter regression checks that the sent output-token limit matches the
  logged setting. Earlier D calls were unbounded; later calls use the cap.
- No SUMO run, accepted real E comparison, human bilingual sign-off, new
  Reader benchmark or media/export review was performed.

## Capture sequence — instructions, not completed footage

1. **B, recorded extraction:** show `data/demo_incident_messages.jsonl` beside
   `results/reader/2026-09-29T1608_qwen3-8b.jsonl` for message IDs `138270`
   and `138272`. The log is `evidence/ai-log/2026-09-29.jsonl`. Label
   **Recorded Qwen3:8b inference — not a live model call**. Show unspecified
   versus all lanes; retain or visibly flag the first output's imperfect
   free-text direction note. This proves a recorded extraction example, not
   an accuracy benchmark.
2. **D, saved candidates:** show the v2 context qualifications, then
   `data/generated-plans/IN-26-03365-lead-draft-20261013-b/P1.json` and
   `P2.json` beside the successful call in `evidence/ai-log/2026-10-13.jsonl`.
   Label **Recorded GenAI draft — retrospective working assumptions; not
   evaluated**. Flag the P1 title mismatch and assumed signal action. This
   proves generation and constraint checking, not recommended-route validity.
3. **F, current limitation:** no accepted real-model output is available from
   this execution. Omit a successful F-generation shot. An existing synthetic
   operator-workflow screen may demonstrate tested UI capability with an
   explicit fixture label, but must not be attributed to these failed calls.
   Keep B/D as the recorded GenAI capture material. Future accepted F output
   still needs language review and code-supplied numeric tokens.

Visuals owns capture/editing; Impact owns final slide export. Neither footage,
audio, revised SRT timings nor a rendered deck was produced by this execution.

## Consolidated owner note — draft, not sent

Lead is targeting a provisional 16 October freeze (hour unconfirmed), with
17 October internal submission unchanged. Please continue the 15 October
delivery; use the 16th for a reviewed final delta, not a delayed first package.

- **Data/Simulation:** the exact new candidates and `generation-inputs.json`
  are in `data/generated-plans/IN-26-03365-lead-draft-20261013-b/`; raw hashes
  and assumptions are recorded above. Use distinct evaluator plan-set ID
  `lead-draft-20261013-b`. Confirm whether diagnostic evaluation is feasible
  and flag unsupported actions, especially the assumed Tong Bin Lane green
  extension. Bind new results and original sidecars to these exact files and
  captured inputs; do not reuse rehearsal results. Keep the joint P0 NO-GO
  unless a new joint evidence review explicitly supersedes it. Supply a
  bounded artifact or an explicit unavailable status; no broad tuning sweep
  is requested.
- **Visuals:** use the B/D capture sequence above and only the F evidence
  status above, preserving every retrospective/synthetic label. There is no
  accepted new F output; use B/D and the explicitly synthetic workflow.
  Deliver an accessible cut, captions and source manifest. The observed-only
  public demo remains the minimum; do not wait for accepted benefit figures.
- **Impact:** use `deck/slides.md`, `deck/qa-sheet.md` and
  `deck/submission-manifest.md`; provide editable slides plus a reviewable
  export and claim-to-source mapping. Leave real traffic benefits unmeasured.
- **Lead + Impact:** confirm named uploader, prototype/deck/video access and
  submission format. Record receipt after actual submission. These remain
  unconfirmed; repository deadline information was not freshly checked
  against organizer material during this execution.

## Schedule and claims

On 13 October the Lead rejected the original 14 October freeze and proposed
**16 October** as the working freeze; an exact hour remains unconfirmed.
Keep the 15 October evidence/deck/video checkpoint and 17 October internal
submission target. The repository records the official deadline as 18 October.
The extra time does not supersede the joint scientific NO-GO or guarantee an
accepted incident comparison. The 15th should deliver a usable package, with
a reviewed final delta on the 16th.
