# Component C: bounded calibration experiments and 4 October handoff

## Summary

- Add opt-in route construction from Data's observed net-flow stretches and
  existing passenger-legal entry/exit connections, with source audits.
- Make demand fitting respect deterministic route start/end positions, retain
  endpoint attributes/types, and expose explicit `--no-closure` demand conservation.
- Add comparisons on identical count bins and common speed bins, including
  queues, teleports, per-detector failures and source hashes.
- Publish the completed 4,500-second bounded experiment and portable provisional
  input archive; update Simulation's status and Visuals handoff.
- Review Data's newer main results and record source/network, imposed-speed
  and incident-readiness questions for the 5 October decision.
- Add a reproduction/assumption handout for the reporter's upgraded case and
  a source-hashed hourly-equivalent GEH audit on matched eligible bins.

## Evidence and limits

The new boundary experiment scores **73.55% (178/242) GEH<5**, against
66.94% (162/242). It does not reach 80% or the agreed 85% target. Speed MAPE
worsens to 45.42% on 298 common bins (45.98% on all 299). 2,016/13,622
vehicles wait to enter (14.80%); 14 wrong-lane teleports remain. The candidate
is **not adopted** as an accepted baseline.

No observations, network geometry, lane connections, speeds, filters or teleport
thresholds changed in this controlled experiment. Inferred route weights are
not measured OD flows. The network remains provisional. Data's separately
merged 96.7% count result uses a different method and still needs assumptions
review; no full incident or diversion/compliance validation is claimed.

Evidence and reproduction:

- `docs/calibration-boundaries-2026-10-04.md`
- `docs/simulation-handoff-2026-10-04.md`
- `docs/sumo-upgrade-reproduction-2026-10-05.md`
- `results/twin/oct03-boundaries-comparison.json`
- `results/twin/oct05-hourly-geh.json`
- `results/twin/oct04-boundary-experiment-inputs.zip` and manifest

## Checks

- 51 Component C tests passed, including 15 boundary/position tests and
  no-closure conservation coverage in the existing demand regression.
- Complete no-closure SUMO run under a 180-second wall limit.
- Trip trace reconciles inserted and waiting totals exactly.
- Input archive integrity checked; no independent fresh-checkout replay.
- The saved count rows reproduce 11/25 original and 19/25 upgrade hourly-
  equivalent detector passes. A new Windows SUMO run was blocked by the local
  executables exiting before startup (`0xC0E90002`).

## Invalid historical artifacts

`results/twin/invalid/partial-lane-index-0-evaluation.json` and
`results/twin/invalid/partial-lane-index-1-evaluation.json` are preserved unchanged
for audit history only. SUMO ignored routes because their departure times were
unsorted. Their scores MUST NOT be used for validation, comparisons or claims.
These files do not represent an accepted initial-lane choice.

The branch also contains earlier demand-ordering, source-audit and diagnostic
video work. The saved traffic-only MP4 is not a validated incident replay.
Main was fetched/read at `4875a85`; it was not merged or overwritten in this
update. Lead owns integration and any conflicts with the updated tracker.
No accepted real P0/P1/P2 set or original evaluator sidecars were found on main.
