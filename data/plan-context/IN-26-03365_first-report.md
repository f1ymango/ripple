# Plan context for IN-26-03365, first report (09:01) — where each value comes from

[IN-26-03365_first-report.json](IN-26-03365_first-report.json) is the context
D needs ([handoff](../../docs/lead-pipeline-handoff.md)). Prepared by Data on
7 October.

**Data marked it reviewed on 7 October**, accepting the rows marked **check**
below as working assumptions. They are judgement calls, not sourced facts.

| Field | Value | Source | Status |
|---|---|---|---|
| `active_from` | 09:01 | TD's first message ([messages](../demo_incident_messages.jsonl)) | Observed report time. No action can start earlier. |
| `active_until` | 10:02 | TD's incident end ([shortlist](../demo_shortlist.md)) | **check.** Advice stops when TD reports the road clear. The run itself continues to 10:35. |
| `od_demand_vehicles` | 1,060.1 to Canal Road Flyover; 66.0 to Wong Nai Chung Road | `python -m src.evaluator.od_demand` on the P0 demand file | Modelled, not observed: vehicles the flow-balance demand schedules to enter 09:01–10:02 on a route over the closed edge. |
| `routes` | one detour, "Wong Chuk Hang Road", for both groups | TD's 09:36 message advises "alternative routes such as Wong Chuk Hang Road" | **check.** In the network this is the road under the flyover: off at edge `1198059138`, back on at `714996652`. It is the only detour the network can carry; there is no path to Canal Road that avoids the tunnel. |
| `routes[].residential` | `false` | OSM tags of the detour's edges (secondary, trunk) | OSM tags, not a land-use survey. |
| `routes[].school` | `true` | AID01103 is "Wong Chuk Hang Road near Aberdeen Technical School" ([detectors](../detectors.csv)) | Set conservatively. No effect on this window: it misses both school peaks. |
| `blocked_roads` | none | — | D adds the incident road itself. |
| `signals` | none | — | No sourced junction IDs or timings. Simulation found the ramp signal's real timing is unsourced. |
| `sign_ids` | none | — | No sign inventory in the repository. |
| `pt_modes` | none | — | [02-data.md](../../docs/02-data.md) §5 names the MTR South Island Line, but E cannot model a mode shift, so a plan using it could not be evaluated. |
| `priority_corridor` | Aberdeen → Queen Mary Hospital; keep clear Pok Fu Lam Road and Shek Pai Wan Road | [00-brief.md](../../docs/00-brief.md) and 02-data.md §5 put the hospital on the western alternative | **check.** The roads are those of E's candidate emergency route. The hospital's position is not from a repository source. |

With one detour, P1 sends everyone under the flyover and P2 can only differ
in how much of each group it sends there.

Passing D's check (`python -m src.plans.run ... --check-only`) shows the file
is well formed. It does not show the routes are right.
