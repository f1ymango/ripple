# Component C diagnosis — 30 September

## Findings from a fresh run

Fetched main remains at `7927f92`; no new E initial-lane decision was found.
The [source-hashed replay](../results/twin/sept30-preincident-diagnosis.json)
completed 0–4,500 simulation seconds in 60.15 wall seconds, within its 180 s
limit. It uses the real May 15 export, existing network and regenerated fitted
routes; no closure lane was selected and no observations were fabricated.

| Check | Fresh evidence | Diagnosis |
|---|---|---|
| Departure ordering | No route-loading warnings | Earlier ignored-route failure corrected |
| Count accuracy | 66.94% of 242 bins with GEH < 5 | Below required 85% |
| Speed accuracy | 36.84% MAPE, 296 bins | Above approximately 15% target |
| Alignment | No unmatched observation intervals | Timestamp alignment is not the current blocker |
| Missing simulated speeds | 3 intervals | Remain unscored, not filled |
| Vehicles | 17,921 loaded; 15,543 inserted; 2,378 waiting | Insertion congestion remains |
| Teleports | 123: 110 jam, 10 yield, 3 wrong-lane | Network/demand diagnosis still required |
| Safety counters | Zero collisions and emergency stops | Does not establish calibration |

The [raw SUMO log](../results/twin/sept30-preincident-sumo.log) records
58 teleport starts on `1198101443_0` and six on `1198101443_1`. This tunnel
approach is the next priority for lane connections, route origins and queue
inspection. Jam teleports alone cannot distinguish bad topology from excess
demand or lane-changing behaviour. Do not remove teleports by disabling the
warning or shortening departure patience and claim a fix.

The earlier diagnostic had 68 teleports. This rerun is not an improvement in
that measure, and its changed route IDs/split flows mean the difference cannot
be attributed solely to a physical network change. No geometry changed here.

## Work completed

- Regenerated demand with sorted flow begins. The
  [fit report](../results/twin/sept30-demand-fit.json) records 41,756 vehicles
  before origin suspension and 41,347 emitted: 409 removed, including rounding.
  This existing modelling assumption is now explicit. It is not measured
  demand disappearance and still needs agreement before full P0 comparisons.
- Fixed the lane audit to read and hash the same selected cache file. A custom
  cache can no longer silently read component A's default cache. Fetching into
  an unsupported custom cache is rejected explicitly.
- Conflicting readings for a detector/lane/time now stop the raw lane audit
  rather than silently choosing the last value. Reprocessing the recorded
  May 15 snapshot selection produced unchanged detector readings.
- Added `src.twin.diagnose_preincident`: refuses an existing run directory,
  checks flow ordering, uses a subprocess wall-time limit, preserves logs and
  source hashes, and evaluates only the pre-incident observation slots.
  `run_usable` means completed without detected loader errors, not calibrated.

## Remaining work and ownership

1. C: inspect `1198101443` connections and incident-edge candidate origins;
   compare demand contribution to the queues without altering real observations.
2. C with Visuals/Data: finish three lane-count conflicts, three missing May
   lane scopes and endpoint placement reviews listed in the
   [sync handoff](component-c-sync-2026-09-30.md). Equal lane counts do not prove
   physical placement. Publish the network/loops only with the review status clear.
3. Data/E: state the initial partial-closure assumption. C maps it to the
   confirmed carriageway and checks phases before full incident P0 runs.
4. C/E: agree demand-origin treatment, freeze source/config hashes, then run
   bounded full P0 with closure and recovery coverage. These pre-incident
   results provide no evidence about closure zero-count reproduction.
5. Data: continue the simplified-network fallback. The 4 October SUMO gate is
   still at risk; today's corrected run does not meet either calibration target.

No test suite was run in this update. Checks used the actual cached sources,
demand generation and a bounded SUMO replay. The earlier invalid partial-lane
evaluation files remain local and were not published as validation results.
