# Component C review for the 5 October model decision

## Independent reproduction

I rebuilt Data's network from the provisional May network in
`results/twin/oct04-provisional-replay-inputs.zip` and the committed
`aberdeen-flow-balance.con.xml` and `.edg.xml` on main (`4875a85`). I ran the
committed flow-balance builder and `run_flow_balance` with seed 2026, SUMO and
netconvert 1.27.1, and a 180-second wall timeout. No closure was applied. The
run starts at **07:25 HKT**, warms up until **07:55**, and scores the 12
five-minute slots ending at **08:55**. Its observation and loop hashes equal
Data's saved run. See [the generated replay](../results/twin/oct05-flow-balance-independent.json).

| 15 May no-closure run | Count bins with GEH < 5 | Speed MAPE | Waiting to enter | Teleports |
|---|---:|---:|---:|---:|
| Data's saved ordinary-morning run | 96.7% / 242 | 15.7% / 299 | 238 / 16,601 | 0 |
| Independent replay, same settings | 96.7% / 242 | 15.7% / 299 | 238 / 16,601 | 0 |
| Same replay, **without speed signs** | 96.7% / 242 | 41.2% / 299 | 523 / 16,601 | 0 |

All `per_detector`, `evaluation`, `score`, `vehicles`, `teleports`, and
`build_notes` fields in the independent replay match Data's saved result.
The no-sign control is [a separate generated run](../results/twin/oct05-flow-balance-no-speeds.json);
it retains the network, demand, seed, driver settings, warm-up, and scoring
window. The rebuilt network and generated route/speed files have different
**byte hashes** from Data's Linux files, despite matching scored rows and
vehicle statistics. The network hash here is
`920e8df22737dd5cac44a7cbfa004ba1f2b2f63bcff8f7abfffe4cc6ed299d4d`,
versus Data's
`9e23e7de17a5a2e351a59cb6e21031136854c36da9036589694a240597d724cb`.
The reason for the byte difference has not been established; do not claim a
byte-identical network. Both runs use the same observation SHA-256
`a1d842a25ff872091b47fb3e7bcad566fe9932af0bc5452be3f79fc1462a4605`
and loops SHA-256
`d0ac843e8ef99b431db28444d2131e4c7e1602aa7683f5ad69c8e7a40742ad6e`.

### Reproduce from the Simulation branch

Use the isolated main worktree and commands in Simulation's
[reproduction handout at `e17ab73`](https://github.com/f1ymango/ripple/blob/e17ab736033ea09a92219d73ccd6e61802ff3f18/docs/sumo-upgrade-reproduction-2026-10-05.md).
The provisional input archive and its manifest are included beside the generated
reports in `results/twin/`. The handout's `--out` paths can be renamed to
`sim/work/repro-flow-balance-oct05` and
`results/twin/repro-flow-balance-oct05.json`. For the control, repeat the
builder with `--no-speeds` and a fresh work directory, then run the same
`run_flow_balance` command with that directory. Both output JSON files above
were copied from those generated runs without editing their metrics.

## Assumption disposition

| Assumption | Component C review |
|---|---|
| Four entry detectors set 15 May demand; four clean prior Fridays set internal joins/exits | **Accept for a no-closure count propagation diagnostic.** The 21 other detectors are assessment sites: 96.6% / 205 count bins. They are not a held-out incident test. |
| Joins/exits allocated by lane count and eligible ramps | **Change before physical incident claims.** Net counts do not identify turning movements. The builder omits +58 and +44 veh/h changes without ramps, sends 32.7% of a westbound entry to its only mapped exit, and injects +201 veh/h on the western main line where no ramp is mapped. Keep these explicit; obtain a map or turning-flow check where incident queues/diversions rely on them. |
| Toll plaza connection patch | **Provisional.** It removes an apparent dead end, and the count replay improves, but cached OSM tags mark `1198101424` lane 0 `motor_vehicle=no`. The added lane-0 connection and lane-to-tube mappings need a physical/legal lane review before this becomes a reviewed network. The 40 m edge split only separates speed-sign zones; it is not a new junction. |
| Ordinary-day 15-minute speeds imposed through variable speed signs | **Accept as a measured input for a limited no-closure speed forecast, not as evidence of queue physics.** Removing signs raises MAPE from 15.7% to 41.2% and waiting from 238 to 523. Closure flow, spillback and recovery must be checked without using incident-day observed speeds to force the answer. |
| `speedFactor=1`, `speedDev=0.05`, `sigma=0`, `departSpeed=max` | **Provisional.** They are documented modelling choices, not estimated driver behaviour. Keep fixed for the first P0 comparison and report a sensitivity run before using plan travel-time benefits. |
| 30-minute warm-up and 07:55–08:55 scored hour | **Accept for comparable no-closure runs.** Retain the same warm-up when testing incident P0; score the incident separately from the pre-incident hour. |
| Ramp edge `46766432` queue | **Unresolved.** 238 waiting (1.4% loaded) remains on 15 May, and Data reports up to 952 (6.1%) on another day. Zero teleports does not clear this flow problem. Signal timing is unavailable in the repository; an arbitrary timing fix is not acceptable. |

The ordinary-morning speed result is **15.7%**, just above the team's
approximately 15% target. It supports a narrowly described, partly externally
speed-controlled **no-closure count baseline** for the 15 May hour, with the
ramp and network caveats above. It does not justify a blanket “acceptable SUMO
baseline” claim. The **13.2% refreshed-speed** result uses each detector's own
previous-quarter-hour speed from 15 May, leaving no detector held out for speed.
It supports a separate short-horizon nowcast claim only; it cannot replace the
ordinary-morning independent-input test or validate incident response.

## Incident P0 handoff and tonight's decision

The proposed incident is IN-26-03365 on the Wong Chuk Hang Road flyover towards
Aberdeen Tunnel near Yip Kan Street. Data's [shortlist](../data/demo_shortlist.md)
shows a queue by **08:55**, the first TD message at **09:01**, an all-lanes
message at **09:36**, and clearance at **10:02**. The slow lane at AID01104 is
an evidence-backed **initial-lane proposal**, not an observed closure identity.
The severe detector starvation before 09:36 means using that report time as
the physical all-lanes onset may miss the observed closure. Data and Simulation
need to agree on the initial lane, phase transition rule and exact SUMO edge/lane
mapping, with each inference labelled. I have not injected an unagreed closure.

Once those inputs are fixed, run P0 with the same four entry count sources and
ordinary-day profiles, without feeding incident-window downstream counts or
speeds into the model. Compare five-minute AID01104 closure flow, upstream
detector queues and onset, and downstream flow and recovery through 10:35;
report missing bins and the ramp backlog alongside count/speed scores. A
bounded first replay is realistic **by 7 October HKT if Data and Simulation
agree the edge, lane, and onset on 6 October**. It would be a diagnostic, not
an automatically validated P0; a source review or failed queue comparison
will extend that date.

**Recommendation for the Lead tonight:** retain flow-balance SUMO as a
promising, reproducible *limited no-closure count baseline*, while keeping
Data's simplified model available for Week 3. Do not yet use this SUMO setup
to rank P0/P1/P2 or claim credible incident queues, recovery or diversion.
The unresolved toll-plaza lane legality, inferred joins, imposed speeds and
ramp entry queue make count GEH alone insufficient. A P0 observation comparison
and a reviewed network decision should gate any stronger claim.
