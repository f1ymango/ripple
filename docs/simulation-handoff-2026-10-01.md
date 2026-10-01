# Simulation handoff — 1 October

Read against main `1f17b4f`. Data's Slow Lane proposal is recorded in main,
but the default, detector override rule, insufficient-data behaviour and full
P0 timing are not yet agreed. This document records C's proposal, not a team decision.

## Physical mapping supplied to Data/E

For network SHA-256
`e3bcd9ed2bc1acfc72b5c72ba8a421fc85c51f3a87ef8138aa450fbe984ed90e`,
the affected model carriageway is `44419212`, Wong Chuk Hang Road flyover,
east/northeast towards Aberdeen Tunnel near Yip Kan Street. At AID01104,
136.31 m along the edge, SUMO `44419212_0` is driver-left (Slow Lane) and
`44419212_1` driver-right (Fast Lane). Both lanes are included in the detector
measurement. This mapping is specific to this network; exact crash position
and initial physical lane closure are not established by the source text.

Data's proposed Slow Lane case would therefore select `[0]`; all lanes would
select `[0, 1]`. Keep the first choice labelled an assumption. Sparse zero
counts cannot establish a physical lane closure. Data/E should publish:

- Its default and number of lanes assumed closed.
- Its evidence rule, including coverage, validity and persistence requirements,
  and whether evidence means raw period time or actual archive availability.
- Its insufficient-data behaviour and how uncertainty reaches the result.

No numerical evidence threshold is invented here. An operator decision must
only use observations actually available by that decision time; an earlier
XML measurement timestamp does not by itself establish availability.

## P0 timing proposed for agreement

P0 includes the incident and no response intervention. The replay begins at
07:40 HKT on 15 May 2026, with 900 seconds of warm-up.

| Event | HKT | Simulation seconds | Status |
|---|---|---:|---|
| Observation window starts | 07:55 | 900 | Source window |
| Initial closure onset | 08:55 | 4500 | Queue-based modelling proposal |
| TD first partial-closure message | 09:01 | 4860 | Message time; not replay onset |
| All-lanes phase | 09:36 | 6960 | Proposed use of TD update time |
| Reopening | 10:02 | 8520 | Proposed use of reported clearance |
| Observation/replay end | 10:35 | 10500 | Source window |

The initial phase lasts 2460 seconds and the full closure interval 4020 seconds.
The detector evidence may indicate earlier severe blockage; using 09:36 for the
all-lanes phase remains a disclosed timing assumption. Data must acknowledge or
revise this table before we freeze the full P0 config. Operator interventions
must respect message availability; physical replay onset is a separate clock.

## Next no-closure calibration run

The 66.94% GEH pass rate covers 07:55–08:55 only. No closure was applied and
the unspecified lane choice cannot explain that failure.

1. Freeze the current network, loops, candidate routes, observations and seed
   2026. Use unchanged coverage rules (40% archive coverage, 90% valid lane
   readings), 900-second warm-up and end 4500. Record hashes and versions.
2. Review the tunnel approach `1198101443` and its downstream connections,
   where 64 of 123 teleport starts occurred. Trace contributing route origins
   and lane connections; check AID01106's endpoint placement. Review the three
   lane-count conflicts and three missing scopes without changing TD values.
3. Generate a dedicated no-closure demand configuration so incident-origin
   suspension cannot alter its demand. Fit only the pre-incident observations.
   Preserve the existing full-rate reference; report any rounding differences
   and generated/loaded/inserted/waiting counts.
4. Run a reference replay, then only a source-supported correction justified by
   step 2. Keep inputs and seed fixed across comparisons except the documented
   correction. Use fresh output directories and a 180-second wall limit per run;
   stop on loader errors/timeouts and retain partial diagnostics. Do not silently
   scale demand, delete lanes or discard waiting vehicles to raise the score.
5. Publish per-detector and overall count GEH, speed MAPE, coverage, unmatched
   bins, waiting vehicles and teleports. Count target: at least 85% GEH < 5;
   speed target: approximately 15% MAPE or lower. Treat comparisons against the
   fitted hour as calibration, not independent validation.

No new simulation was run for this handoff. The latest recorded result remains
66.94% over 242 count bins and 36.84% speed MAPE over 296 bins. Keep Data's
simplified-network fallback active for the 4 October gate.

Evidence: [diagnosis](component-c-diagnosis-2026-09-30.md),
[run report](../results/twin/sept30-preincident-diagnosis.json),
[source audit](../results/twin/osm-network-audit.md),
[lane readings](../results/twin/may15-AID01104-lane-readings.md).
