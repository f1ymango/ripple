# Route-choice spike — isolated 14–16 October experiment

**Status:** exploratory branch `codex/route-choice-spike-oct14`, based on Data's
E 3.2 branch at `9552cd4`. This is not a submission claim, a replacement for
the 15 October evidence pack, or an approval to merge E 3.2's shared-contract
changes. Lead owns the decision to include a result; Data owns evaluator runs;
Simulation owns network and physical-validation review.

## Question and fixed boundaries

Can a source-supported alternative road path, reachable by the affected OD
groups *upstream of* the flyover closure, let a no-signal P2 reduce total delay
against **both** the no-extra-action P0 and fixed P1 broadcast comparator?
The real 15 May operator action still starts no earlier than the 09:01 TD
report. The emergency-priority corridor, residential/school constraints and
the prohibition on an unsourced Tong Bin Lane signal change remain in force.
The observed 15 May replay remains a joint scientific P0 **NO-GO** until its
closure-flow and queue-recovery failures are resolved independently.

The branch is disposable. A numerical win is necessary but not sufficient to
merge or claim a measured benefit; source support, healthy matched runs and
the physical P0 gate are separate requirements. Do not compare a new-network
P2 with a P0 from the existing network.

## Gate 1 — route feasibility, by 15 October HKT

Simulation and Data identify the exact directed edge sequence from each
affected origin to its destination. A candidate must avoid closure edge
`44419212`, be reachable from the relevant upstream fork, avoid the protected
Pok Fu Lam Road / Shek Pai Wan Road hospital corridor, respect lawful lane and
turn connections, and not rely on the unsourced Tong Bin signal. Record the
road/turn sources and a reviewer for the proposed network change. Also name
independent evidence for demand, background traffic and turning or entry flow
on any newly modelled link. Missing evidence must be labelled, not fitted to
make P2 win.

First-pass evidence is unfavourable: Nam Fung Road, Shouson Hill Road and
Island Road already occur in the generated network, while Data's
`docs/incident-p0-verdict-2026-10-14.md` reports that every modelled path
around the flyover still uses Wong Chuk Hang Road. The currently reviewed
`generation-inputs.json` supplies only that surface-road diversion and protects
the hospital corridor. A larger Central–Wan Chai bypass is not a one- or
two-road edit and would need independently checked background traffic.

**Stop the new-road experiment at Gate 1** if no source-backed, lawful,
meaningfully distinct path exists by the checkpoint. Do not invent geometry,
turning demand, signs or capacity to keep it alive. A separate partial-closure
what-if may be explored only as a clearly hypothetical model-world test; the
existing three-seed slow-lane result has disqualifying teleport flags and no
matching detector validation. Simulation must also verify the travel direction
of its 23 March analogue before that comparison is used.

## Gate 2 — predeclare and run a fair comparison

Before inspecting any P2 outcome, freeze the candidate route, source inventory,
scenario inputs, no-signal P2 plan, success threshold and hashes. Change only
the declared experimental road/route inputs; keep P0 and P1 plan semantics
fixed. On the **same expanded network and demand**, run matched P0/P1/P2 with
the same evaluator commit, closure, reopening/ramp/compliance/leave-share
settings and seeds. Save original results and provenance sidecars under a new
`results/` experiment namespace; never relabel or hand-edit them.

Use the existing 33-cell diagnostic screen and untouched confirmation seeds
only if the screen is promising. Report every cell, not just the best one:
actual advised-route takes, forced detours, exits, total delay split into
in-network / entry-wait / assumed outside delay, downstream closure flow,
queue onset and recovery, waiting-to-enter and teleport types. Check the
outside-delay assumption at 0, 20 and 40 minutes. Sensitivity cells are not
independent traffic samples; do not market a nominal paired interval as
population confidence. Fix a simulation bug only with a new run set and
provenance, never by editing saved results.

## Gate 3 — result disposition by the provisional 16 October claims freeze

| Outcome | Disposition |
| --- | --- |
| No feasible distinct route, or P2 does not robustly beat both matched P0 and P1 | Stop and leave the submission cut unchanged; do not merge this branch. |
| P2 wins in a model world, but road/demand evidence or incident-P0 closure flow and recovery remain unaccepted | Keep as explicitly hypothetical diagnostic only. No measured 15 May saving, route recommendation or merged benefit claim. |
| Independently supported inputs, Simulation-accepted P0 checks, healthy provenance-bound confirmation runs and a robust P2 win without unacceptable queue/safety trade-offs | Lead may review a narrowly scoped PR and matching deck/video changes before freeze. This branch is not automatically merged. |

Keep the 15 October observed-playback / recorded-GenAI / refusal pack moving in
parallel. After claims freeze, polish and test the repo and media; any fix that
changes a claimed result needs fresh matched runs, provenance and review.

## References

- `docs/lead-p2-diagnostic-2026-10-13.md` — predeclared matched comparison and
  confirmation rules.
- `docs/lead-p2-diagnostic-protocol-2026-10-13.md` — Data's 33-cell and reserved
  confirmation protocol on the E 3.2 branch.
- `docs/incident-p0-verdict-2026-10-14.md` — current flow/recovery failures and
  proposed checks, pending Simulation review.
- `docs/whatif-slow-lane-2026-10-14.md` — labelled hypothetical, not a validated
  incident result.
