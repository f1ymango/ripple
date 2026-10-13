# Lead P2 diagnostic — predeclared candidate and comparison handoff

**Status (13 Oct HKT): candidate preparation only.** The two new derivatives
have not been simulated or ranked. [Data's unmerged v3 branch](https://github.com/f1ymango/ripple/blob/ee404167/docs/evaluator-lead-plans-2026-10-13.md)
contains diagnostic runs of the saved model proposal, but no plan is accepted
or approved for operator use. The joint incident-P0 NO-GO remains. This is a
bounded attempt to learn whether a
supported intervention can outperform P0 and the fixed P1 broadcast comparator
before the provisional 16 October claims freeze; it is not a promise of a
positive result. The 15 October deck/video pack proceeds independently.

## Why this small search

The [reviewed D context](../data/plan-context/IN-26-03365_first-report-v2.md)
contains one modelled diversion (Wong Chuk Hang Road), two OD groups and an
**assumed, unverified** Tong Bin Lane signal extension. It contains no sign
inventory or modelled public-transport shift. The [replay scenario](../sim/scenarios/evaluator_IN-26-03365_replay.json)
already diverts drivers around the full closure through the same surface road
in P0, from approximately 09:00:30; a plan can act no earlier than the 09:01
report. Thus P2 can mainly change when and how many drivers take a road P0
already uses. A second real route or effective signal control would require
new, independent Data/Simulation evidence and a reviewed context; neither is
silently added here. P1 is fixed by [D's validator](../src/plans/validator.py)
as one broadcast detour with advice share 1 for both groups. It is a comparator,
not a plan whose improvement is guaranteed.

The original model-generated [Lead plan set](../data/generated-plans/IN-26-03365-lead-draft-20261013-b/README.md)
was retrospectively informed by the 09:36 TD route advice and known clearance;
its 09:01 proposal is **not** a real-time reconstruction of what an operator
knew at 09:01. Its generated JSON files remain unchanged. These variants are
deterministic Lead parameter-search derivatives, **not new LLM outputs**.

| P2 case | Canal Road OD advice share | Wong Nai Chung OD advice share | Tong Bin signal | Question |
| --- | ---: | ---: | --- | --- |
| Saved model P2 | 0.8 | 0.7 | Assumed +20 s | Existing diagnostic reference; not an accepted recommendation |
| `lead-p2-nosignal-oct13` | 0.8 | 0.7 | None | Did the unverified signal drive the result? |
| `lead-p2-half-nosignal-oct13` | 0.4 | 0.35 | None | Does less early advice avoid loading/retaining too many vehicles on the sole detour? |

The second variant's shares are exactly half the saved proposal, selected
before its outcome is observed. Compliance remains a separate E scenario
parameter: the chance of following advice is `share × compliance`. Neither
share is an observed traffic fraction or an optimum. Both variants keep the
same OD-to-road mapping and omit unsupported VMS/PT actions.

There is an important scoring confounder: E's advice selection prevents an
advised driver from taking its modelled leave-corridor exit. The delay metric
charges each vehicle that leaves an **assumed 20 minutes outside** the network
in this scenario. A change in reported delay can therefore reflect that
assumption or the number leaving, not only better road throughput. The [metric
detail](../src/evaluator/metrics.py) separates in-network delay, entry wait
and assumed outside delay; every comparison must show those components and
the counts of actual advised routes and exits.

## Prepared artifacts and local checks

Run this only with a **new** output directory; the command refuses overwrite:

```powershell
python -m src.plans.diagnostic --source data/generated-plans/IN-26-03365-lead-draft-20261013-b --out data/plan-experiments/IN-26-03365-lead-p2-20261013
```

The prepared [candidate pack](../data/plan-experiments/IN-26-03365-lead-p2-20261013/manifest.json)
contains one complete folder per case. In each, `P0.json`, `P1.json` and
`generation-inputs.json` are byte-for-byte copies of the original. `P2.json`
alone is derived and constraint-validated. The manifest records original and
derived SHA-256 hashes, and the generator refuses if any original source file's
bytes change. No model, SUMO run or `results/` write occurs during
preparation. `tests/test_plan_diagnostic.py` checks source drift, unchanged
comparators, validation, E action construction and no-overwrite behaviour.

## Data/Simulation run and decision protocol

1. **Acceptance gate first.** Agree what P0 represents: no *additional plan
   actions*, but automatic full-closure detouring and modelled exits. Verify
   detector cross-sections, independently supported side-road entry/turning
   flow, ramp operation, closure throughput, queue/recovery, waiting and
   teleports. Set the incident-specific acceptance checks **before** choosing
   a candidate. Data's proposed validation v2 aggregate pass is not by itself
   an accepted incident replay. Simulation has not yet accepted Data's newer
   v3 run.
2. **Small diagnostic screen if inputs are available.** Use the same frozen
   scenario, network, demand, speed inputs and matched seed/compliance/
   clearance settings for each P0/P1/P2 triplet. Each variant needs its own
   `--plan-set` and `--results-dir`; run P0 first and retain E's original
   result, sidecar and report. Check the report's actual reroute count and
   signal actions. Do not reuse a result from another plan set or relabel an
   earlier run. On Data's v3 branch, after rebuilding its missing input bundle
   as documented there, an example main-cell command is:

   ```powershell
   python -m src.evaluator.batch --plans data/plan-experiments/IN-26-03365-lead-p2-20261013/lead-p2-nosignal-oct13 --plan-set lead-p2-nosignal-oct13 --scenario sim/scenarios/evaluator_IN-26-03365_replay-v3-1.json --clearance 66 --compliance 0.5 --results-dir results/evaluator-lead-p2-nosignal-oct13
   ```

   The `replay-v3-1.json` scenario and rebuilt inputs are **not on main** as of
   this handoff; the command is a handoff for Data's branch, not a claim that
   it has run locally. Repeat with the other variant's matching directory,
   plan-set and results directory.
3. **Confirm, do not cherry-pick.** Before looking at screening outcomes,
   Data and Simulation should reserve untouched paired seeds and plausible
   reopening/ramp/compliance cases for confirmation, with the same P0
   acceptance checks. If none can be reserved, results remain exploratory.
   Report *all* matched delay **and its in-network, entry-wait and
   assumed-outside components**,
   downstream flow, queues, waiting-to-enter, teleports, actual advised-route
   takes and leave-corridor counts. Predeclare a sensitivity check for the
   assumed outside-network penalty if it materially drives a winner; changing
   that penalty creates a new simulation-input set and needs new original
   provenance. Data's 33 sensitivity cells are not independent traffic samples;
   a nominal paired interval over them is diagnostic, not a population-level
   confidence interval. A result that reverses under a plausible ramp or
   reopening case is not a robust recommendation.
4. **Claim decision.** Only a jointly accepted P0 plus a provenance-bound P2
   that consistently beats both P0 and P1 without an unacceptable queue,
   safety or recovery trade-off can support a plan-benefit claim. A saving
   created only by the assumed outside-delay penalty is not measured benefit.
   Otherwise keep the console's refusal and the observed/recorded GenAI
   submission cut.
   Neither the screening outcome nor a green software test changes that rule.

**Owners:** Lead supplies these unchanged-source candidate sets and reviews any
new D context; Data owns E runs, ranking and original provenance; Simulation
owns physical replay acceptance with Data. Visuals and Impact should continue
the 15 October deliverables without waiting for a positive P2.
