# Lead integration review — evaluator PR #55, 11 October 2026

Reviewed head: `a8d04aa19fa1b2bbaf161ed674aa52a65add3a96`.
PR: <https://github.com/f1ymango/ripple/pull/55>.

**Disposition: request changes; do not merge this head.** This review concerns
E's software integration. Separately, [Data and Simulation's corrected P0
review](https://github.com/f1ymango/ripple/blob/a8d04aa/docs/evaluator-p0-go-no-go-2026-10-09.md)
retains NO-GO for public incident plan comparison by the 14 October freeze.
Passing unit tests and provenance checks do not change that scientific verdict.

## Blocking findings

1. **Constrain and contain the evaluator scratch path.**
   `src/evaluator/scenario.py` line 65 accepts `run_prefix` as any nonempty
   string. `run_id` at line 244 includes that prefix, and
   `src/evaluator/run.py` lines 135–137 construct `work_root / run_id` then
   recursively delete it if it exists. A read-only probe changed the replay
   prefix to `../outside`; scenario loading accepted it and the resolved work
   path escaped `sim/work/evaluator`. Restrict the prefix to an explicit safe
   filename pattern and verify the resolved scratch path remains beneath the
   resolved work root before deletion. Test separators and dot segments.

2. **Make the reopening check reachable.**
   In `src/evaluator/scenario.py` lines 141–147, the `reopening` validation
   sits under the `if` block that raises for an invalid detour, so it cannot
   execute. A read-only probe changed the replay's first reopening stage to
   `lanes: ["all"]`; `load()` accepted the scenario and `closure_steps()` kept
   both lanes closed at that stage. Move the check to the intended scene branch
   and test that an all-lanes-still-closed reopening is rejected.

3. **Check cached result identity and completeness before reuse.**
   `src/evaluator/run.py` lines 87–98 and `src/evaluator/batch.py` lines 36–39
   recheck plan and simulation-input hashes, but `kept_result()` does not
   require the matching run report or compare the result's `run_id` and
   scenario settings with the requested run. `run.py` writes result/sidecar
   before report at lines 191–192, so an interrupted three-file write is
   possible. A read-only probe showed that an internally consistent,
   misfiled result/sidecar can pass these checks. Require the report and
   expected identity/settings; add regression tests for missing report and
   misfiled result.

These are failures of validation and filesystem safety at the current head;
do not depend on the disputed traffic assumptions.

## Checks and good changes

- Isolated detached checkout at the reviewed head: focused evaluator,
  Lead-pipeline and console tests **180 passed**; full suite **519 passed**,
  with one Altair deprecation warning. The first restricted-shell full run
  had 12 localhost-stub failures because Windows denied test sockets;
  rerunning with normal access passed. The temporary checkout was removed.
- Prior handoff issues appear corrected: v2 context no longer cites the
  nonexistent signal file; plan-set IDs separate result names; batch checks
  saved hashes before keeping a result; rehearsal output is under
  `results/evaluator-rehearsal/`, with `results/runs/` reserved for actual
  Lead-generated plans. These improvements need to remain through the fixes.
- The current PR also conflicts with main's `README.md` after the observed
  playback merge. Resolve both sides' current status text without discarding
  the 9 October public-scope decision.

## Older PR #46

PR #46 is **partly superseded**, not safe to close as a duplicate or merge as
written. It uniquely carries `docs/flow-balance-replay-handoff-2026-10-05.md`
and two revised inputs,
`sim/scenarios/aberdeen-flow-balance-buslane.con.xml` and
`sim/scenarios/twin-inputs_20260515_no-mainline-join.json`. The input files
also exist byte-identically inside Simulation's Oct 7 replay ZIP, on which
PR #55's reconstruction instructions depend; neither the standalone files
nor PR #46's ledger are in PR #55 or main. PR #46 still calls a provisional
score a “reviewed baseline” without committing its generated run result or
manifest, and its changes-requested review remains unresolved. Preserve the
unique historical evidence in a small corrected evidence change, with a dated
superseded/provisional label and cited outputs if scores are retained. Only
then decide whether to close the older PR with that replacement link.

## Acceptance for a revised head

Fix the three findings, add targeted regression coverage, run focused and full
tests, resolve the README conflict and obtain current-head CI. Keep rehearsal
results labelled as diagnostics. Software merge approval would still leave
the incident P0 and public plan-comparison decision at NO-GO unless Data,
Simulation and Lead explicitly accept new evidence under the existing gates.
