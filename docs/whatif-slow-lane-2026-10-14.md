# What if only the slow lane had closed? A hypothetical test (14 October)

Data, 14 October 2026. **HYPOTHETICAL. Not a replay of 15 May, and not validated
against any detector.** The incident P0 is not accepted
(`docs/incident-p0-verdict-2026-10-14.md`), and this test adds no measured claim.

## Why

On 15 May, both lanes shut at 09:00:30, before any plan could act (09:01), so
every driver was already forced onto Wong Chuk Hang Road and no route advice
could help. This test asks whether the same plans help when drivers have a real
choice. It uses the same morning's traffic and the same seeds (2026, 1, 2), but
only the slow lane closes, from 08:54 to 10:00
(`sim/scenarios/evaluator-diagnostics/whatif-slow-lane/`). It runs the Lead's
two no-signal plan sets from PR #67, 36 runs, in `results/diagnostic-whatif-slow-lane/`.

The open lane's speed is unknown, so two bounds are run:
- **4.7 km/h:** as measured on 15 May in the 6.5 minutes while one lane was open (crash-scene conditions).
- **66 km/h:** as on 23 March, when a slow-lane closure of this flyover (IN-26-02105) did not slow AID01104 or AID01105 (64 to 78 km/h, 08:25 to 09:10).

## Results (mean of 3 seeds, change in total delay against P0 of the same world)

| Open lane | P1 broadcast | P2 0.8/0.7, no signal | P2 0.4/0.35, no signal |
|---|---|---|---|
| 66 km/h | +11.9% | +6.2% | +2.3% |
| 4.7 km/h | −31.9% (−52, −30, −13) | −25.7% (−33, −28, −16) | −8.6% |
| 4.7 km/h, no outside-delay penalty | −13.7% | −8.5% | −1.0% |

- **When the lane flows, advice only sends drivers onto the slower surface road.** There is no queue (P0's delay is 115 to 122 vehicle-hours), and doing nothing is best, as on 23 March.
- **When the lane crawls, P0's queue fills the 1.1 km path** and 837 drivers leave the corridor. Advising the detour cuts that to 329 (P1) to 675, and lowers delay in the network too. About three-quarters of the headline saving is the assumed 20 minutes charged to each driver who leaves; without it, P1 saves 13.7%.
- **One crawling lane against the real full closure, with no advice:** the full closure had 2 to 11% less delay over the three seeds (779.5 against 873.9, 815.9 against 831.3, 810.3 against 860.5 vehicle-hours). Closing fully and sending everyone round was better for traffic than leaving a 4.7 km/h lane and saying nothing.

## Limits

- No detector data exists for this world. The 4.7 km/h is 6.5 minutes of 15 May.
- The crawling-lane cells have 4 to 10 wrong-lane teleports per cell outside a lane shutting or a jam, so they would not count under validation version 2.
- Three seeds and no grid: no interval and no ranking.
- Closing lanes at a scene is the police's safety decision, and no plan in the format can do it.

**Use for the demo: the pattern, not the numbers.** Whether advising a detour
helps depends on how the remaining lane is moving. If it crawls, divert; if it
flows, don't. Ripple can read that live from AID01104.
