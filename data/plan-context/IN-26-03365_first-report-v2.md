# Plan context for IN-26-03365, first report (09:01), version 2 — where each value comes from

[IN-26-03365_first-report-v2.json](IN-26-03365_first-report-v2.json) replaces
[the first version](IN-26-03365_first-report.md) for D. Prepared by Data on
8 October. One thing changed: it now offers D a junction, so that a P2 can
differ from P1 by more than a share. The first version stays, because the
7 October P0 results are bound to it.

**9 October correction:** `sources` named
`sim/scenarios/evaluator_IN-26-03365_signals.add.xml`, a file that was never
committed (a calibrated signal program that was tried and dropped). The entry
is removed. Where the junction is in the network is the `plan_actions` block
of [the replay scenario](../../sim/scenarios/evaluator_IN-26-03365_replay.json),
already in `sources`. No other value changed.

**Data marked it reviewed on 8 October**, accepting the rows marked **check**
as working assumptions. They are judgement calls, not sourced facts.

| Field | Value | Source | Status |
|---|---|---|---|
| `active_from` | 09:01 | TD's first message ([messages](../demo_incident_messages.jsonl)) | Observed report time. No action can start earlier. |
| `active_until` | 10:02 | TD's incident end ([shortlist](../demo_shortlist.md)) | **check.** E also stops a plan's actions when the first lane reopens, if that is earlier. |
| `od_demand_vehicles` | 1,060.1 to Canal Road Flyover; 66.0 to Wong Nai Chung Road | `python -m src.evaluator.od_demand` on the replay's demand file | Modelled, not observed. Unchanged from version 1: the replay's demand has the same flows. |
| `routes` | one detour, "Wong Chuk Hang Road", for both groups | TD's 09:36 message advises "alternative routes such as Wong Chuk Hang Road" | **check.** The road under the flyover. It is the only detour the network contains. |
| `routes[].residential` | `false` | OSM tags of the detour's edges (secondary, trunk) | OSM tags, not a land-use survey. |
| `routes[].school` | `true` | AID01103 is "Wong Chuk Hang Road near Aberdeen Technical School" ([detectors](../detectors.csv)) | Set conservatively. No effect on this window: it misses both school peaks. |
| `blocked_roads` | none | — | D adds the incident road itself. |
| `signals` | **"Wong Chuk Hang Road / Tong Bin Lane": up to 20 s more green** | The second signal on the detour, at 22.24926 N 114.16742 E in the network | **ASSUMED NETWORK CONTROL, not a sourced TD control.** Neither the junction's real timing nor whether TD can extend it is in any source we have. The 20 s limit is assumed, and the program it extends is netconvert's guess (24 s of green for Wong Chuk Hang Road eastbound in a 90 s cycle). |
| `sign_ids` | none | — | No sign inventory in the repository. |
| `pt_modes` | none | — | E does not model a shift to public transport and refuses a plan that uses one. |
| `priority_corridor` | Aberdeen → Queen Mary Hospital; keep clear Pok Fu Lam Road and Shek Pai Wan Road | [00-brief.md](../../docs/00-brief.md) and 02-data.md §5 | **check.** The hospital's position is not from a repository source. |

The other signal on the detour, Wong Chuk Hang Road / Nam Long Shan Road, is
not offered: in the network it already gives the detour 39 s of green in 90.

How E applies each of these in the twin is in
[src/evaluator/actions.py](../../src/evaluator/actions.py), and where each
name is in the network is in the `plan_actions` block of
[the replay scenario](../../sim/scenarios/evaluator_IN-26-03365_replay.json).

Passing D's check (`python -m src.plans.run ... --check-only`) shows the file
is well formed. It does not show the routes are right.
