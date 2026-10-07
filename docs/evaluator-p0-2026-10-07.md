# E — P0 for IN-26-03365: first result, the detector evidence, and a better baseline (7 October)

Prepared by Data. **No P0 here is accurate enough to compare plans against
yet.** Timing the closure from the detectors and letting drivers go round it
brings the counts closer to the morning; the speed error stays near 40%, and
that part is not caused by the closure.

## 1. What the detectors say (Simulation's three questions)

| Question | Answer | Source |
|---|---|---|
| When did each lane at AID01104 stop carrying traffic? | Slow lane from **08:54:00**. **Every lane from 09:00:30**, about 35 minutes before TD's "all lanes" message. Traffic again at 10:00:00. | [AID01104 lane readings](../results/data/closed-lanes_AID01104_20260515-0840_1010.md) |
| When did the queue reach AID01103? | Between 09:00 and 09:05: speed 51 km/h in the 09:00 bin, 14 in the 09:05 bin, 6 by 09:10. Its middle lane stood still from 09:09:30 to 10:02:30, **but 350–550 veh/h kept passing in the other lanes**. | [AID01103 lane readings](../results/data/closed-lanes_AID01103_20260515-0840_1035.md), five-minute export |
| Did traffic still reach AID01106? | Yes, almost as usual. **No lane was ever blocked.** It counted 895 vehicles in the ten valid bins 09:05–09:55 (89.5 a bin; 95.1 a bin before the incident) while AID01104 counted 17. | [AID01106 lane readings](../results/data/closed-lanes_AID01106_20260515-0840_1035.md), five-minute export |

Read together: the flyover was fully blocked from about 09:00, and drivers
went round it. The only road in the network between AID01103 and AID01106 that avoids the
flyover is Wong Chuk Hang Road underneath it, which is also what TD advised at
09:36.

**Two clocks.** The detectors time the physical closure. TD's messages
(09:01, 09:36, 10:02) time what an operator could know, so no plan may act
before 09:01.

## 2. Three runs, one change at a time

Same network, demand, seed and scorer in all three
([how E runs](../src/evaluator/README.md)).

| | First P0 | Detector timing | Detector timing, drivers reroute |
|---|---|---|---|
| Slow lane closes | 08:55 (assumed) | 08:54:00 | 08:54:00 |
| Both lanes close | 09:36 (TD message) | 09:00:30 | 09:00:30 |
| Reopens | 10:02 (TD message) | 10:00:00 | 10:00:00 |
| Drivers go round a full closure | no | no | yes, from the last 330 m before the fork |
| **GEH < 5, all 607 count bins** (target 85%) | 87.14% | 81.71% | **89.95%** |
| **Speed MAPE, 786–790 bins** (target 15%) | 47.34% | 37.49% | 42.69% |
| GEH < 5 during the closure | 80.90% | 74.16% | 88.39% |
| Still waiting to enter at 10:35 | 840 (2.5%) | 642 (1.9%) | 447 (1.3%) |
| Teleports (wrong-lane) | 72 (9) | 170 (25) | 35 (0) |
| Scenario file | [first](../sim/scenarios/evaluator_IN-26-03365.json) | [timing](../sim/scenarios/evaluator_IN-26-03365_detector-timing.json) | [rerouted](../sim/scenarios/evaluator_IN-26-03365_detector-timing-rerouted.json) |
| Result | [results/runs](../results/runs/2026-05-15_ABD_P0_c50_t67_assumed-0855-0936.json) | [diagnostic](../results/evaluator-diagnostics/runs/2026-05-15_ABD_P0_c50_t66_detector-0854-0900.json) | [results/runs](../results/runs/2026-05-15_ABD_P0_c50_t66_detector-0854-0900-rerouted.json) |

Vehicles counted in the ten valid bins 09:05–09:55:

| Detector | Observed | First P0 | Detector timing | Rerouted |
|---|---|---|---|---|
| AID01102, upstream | 382 | 743 | 127 | 559 |
| AID01103, before the fork | 433 | 872 | 56 | 603 |
| AID01104, on the flyover | 17 | 547 | 0 | 0 |
| AID01106, past the flyover | 895 | 675 | 151 | 524 |
| AID01107, tunnel | 824 | 669 | 151 | 532 |

- **Timing alone makes the counts worse.** The flyover is right (0 against
  17), but with nowhere to go the model's traffic stops dead: 151 vehicles
  reach AID01106 against 895.
- **With rerouting the flyover and the road before it are close**, and the
  run is healthier. 547 vehicles took the road under the flyover.
- **The first P0 looks better past the flyover (675) only because it left the
  road half open until 09:36.**

The rerouted run is the baseline to build on. It is in `results/runs/` beside
the first P0, which stays as the record of what the TD-message timing gave.

## 3. What is still wrong

1. **Too little traffic past the flyover: 524 against 895 at AID01106.** The
   road underneath carries about 50 vehicles a bin in the model. The rest
   reached AID01106 some other way, or the real road carries more than the
   model's. Which drivers turned off further upstream is not observed, and
   fitting it to AID01106 would be tuning the baseline to the incident.
2. **The queue is too mild and clears too suddenly.** AID01103 was at 6–14
   km/h; the model has 23–34. After reopening the model releases a surge:
   731 vehicles at AID01104 in the four valid bins 10:05–10:30 against 405.
3. **The speed error starts before the incident: 40.83% in 07:55–08:50.**
   This setup has no speed signs, so no closure change can bring 42.69% to
   15%. The signed setup scored 15.8% with no closure, but signs dictate the
   speeds that a queue should produce.
4. **Run health.** 447 vehicles (1.3%) never entered, 427 of them ramp flow `f22`.
   35 jam teleports, 17 of them stuck vehicles lifted off the closed flyover.
5. **Not modelled.** The few vehicles AID01104 saw at 09:09, 09:14 and
   09:30:30, and the exact crash position on the 543 m edge.

## 4. The rerouted baseline's result

| Metric | Value | Read it as |
|---|---|---|
| Total delay | 2,628.6 vehicle-hours | 1,397.5 in the network; 1,231.0 waiting to enter, 883.1 of it ramp flow `f22` |
| Longest queue behind the closure | 1,341 m | 68% of the 1,971 m path, so no longer cut off by it |
| Corridor travel time, 95th percentile | 39.0 min | 149 of 2,284 vehicles had not finished |
| Emergency route travel time | 2.8 min | Placeholder: candidate route, 8 of 40 edges carry modelled traffic |
| CO₂ | 18,639 kg | One default emission class for every vehicle |
| Delay on residential streets | 0.0% | The demand barely uses them |
| Vehicles completed | 26,499 of 28,023 in scope | 1,077 still driving, 447 never entered |

Do not quote these as incident impacts.

Each run was made twice on Linux (Python 3.13.16, SUMO 1.27.1) with identical
result files; the first P0 three times. Not run on Windows. The first P0
matches Simulation's [diagnostic](https://github.com/f1ymango/ripple/blob/4ec5afe/docs/p0-diagnostic-2026-10-07.md)
to every digit.

## 5. Open

1. **Lead — what P0 means.** Once drivers go round a full closure by
   themselves, P0 already contains the detour that TD advised and that the
   plan context offers P1. With one detour in the network, a plan can only
   differ in when and how much traffic it moves.
2. **Lead — which window the validation targets apply to.**
   [03-architecture.md](03-architecture.md) §4 states them for the
   pre-incident hour. E reports the whole run, which is stricter.
3. **Lead — contract.** `emergency_tt_min` is required, but the twin has no
   traffic on most of any route to Queen Mary Hospital.
4. **Simulation — the road under the flyover.** Its two signals and one-lane
   ends set how much traffic gets round. Their timing is netconvert's guess.
5. **Data — plans.** E still refuses P1 and P2. D's own P0 will replace
   [the validator-built one](../data/generated-plans/IN-26-03365-p0-only/P0.json),
   and P0 must then be run again.
