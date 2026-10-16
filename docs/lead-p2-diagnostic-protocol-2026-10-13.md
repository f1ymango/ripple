# Lead P2 diagnostics (PR #67): screen, confirmation and claim rule, fixed before any run

Data, 13 October 2026, 21:45 HKT. Committed before any run of these plan sets.
Data's earlier rebuild of the same two P2 variants was stopped after eight
runs; none of its outputs were read, and they were deleted, because the
labels in the Lead's files make their provenance hashes differ.
**Everything here is diagnostic: the incident P0 is not accepted**
(`docs/incident-p0-verdict-2026-10-14.md`).

## Plan sets

The Lead's PR #67, `data/plan-experiments/IN-26-03365-lead-p2-20261013/`. In
both, P0.json, P1.json and generation-inputs.json are byte-identical to
`lead-draft-20261013-b`, and the P2 hashes match the manifest (checked
13 October). Each variant has its own `--plan-set` and results folder.

| Plan set | P2 |
|---|---|
| `lead-p2-nosignal-oct13` | shares 0.8 and 0.7, no signal action |
| `lead-p2-half-nosignal-oct13` | shares 0.4 and 0.35, no signal action |

## 1. Screen

The same 33 cells as `lead-draft-20261013-b`
(`sim/scenarios/rankings/IN-26-03365_<plan set>_screen.json`). Each variant is
ranked with `src.evaluator.ranking`: the 95% interval of the paired difference,
ties allowed, and no order if more than 10% of cells do not count. The 33
cells are sensitivity cases, not independent traffic samples, so the interval
is a decision rule, not a population confidence interval.

## 2. Confirmation, reserved

`sim/scenarios/rankings/IN-26-03365_<plan set>_confirm.json`: seeds 6 to 11,
never run before, under the one-stage reopening at 10:00, the clearing stage,
both lanes at 10:04 and the ramp as built (24 cells;
`sim/scenarios/evaluator-diagnostics/v3-1-confirm/`). It is run only for a
variant the screen puts before both P0 and P1, and judged by the same rule.

## 3. Claim rule

A variant **beats both** only if the screen and the confirmation each put it
before P0 and before P1, and both verdicts hold when the outside-network delay
is recomputed at 0 and at 40 minutes instead of 20. A verdict that changes with
that assumption is reported as driven by it. Even then, **no plan benefit is
claimed** while the incident P0 fails the checks in the verdict doc (closure
flow after the flyover, queue recovery). The result is a diagnostic finding
about this replay.

## 4. Reported for every plan set

Per plan and cell:
- vehicles that took the advised route, and how many were still on it after the reopening
- drivers sent round at the closure
- drivers who left the corridor
- delay in the network, waiting to enter, and assumed outside
- total delay
- teleports by kind

Per set:
- the ranking
- the outside-delay recomputation at 0 to 40 minutes
- `p0_checks` (closure flow after the flyover, queues, waiting)

Also, an audit of whether a driver *selected* for advice but not actually
rerouted is shielded from the leave-the-corridor rule (the Lead's question).
