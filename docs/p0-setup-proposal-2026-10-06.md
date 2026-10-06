# IN-26-03365 P0 setup for Data and Simulation agreement — 6 October HKT

**Status: proposed, not yet agreed.** Simulation can reproduce the revised
PR #46 no-closure baseline, but Data has not confirmed the incident lane and
phase times. This is the single candidate setup to decide today. P0 means the
physical incident with **no operator intervention**. Any P1/P2 advice must
start no earlier than the 09:01 TD report and must respect when the message was
actually available to an operator.

## Frozen inputs proposed for the first bounded diagnostic

| Item | Exact choice | Evidence and status |
|---|---|---|
| Source revision | PR #46 head `647b13c` ([Data handoff](https://github.com/f1ymango/ripple/blob/647b13c/docs/flow-balance-replay-handoff-2026-10-05.md)) for the two revised files; flow-balance builder/runner from main `4875a85` | **Proposed.** PR #46 is not merged in the fetched main as of this review. Data recommends the revision; Simulation independently reproduced its stated no-closure result. |
| Base road and detectors | `sim/work/aberdeen.net.xml` from [Simulation's provisional input archive](../results/twin/oct04-provisional-replay-inputs.zip), SHA-256 `e3bcd9ed2bc1acfc72b5c72ba8a421fc85c51f3a87ef8138aa450fbe984ed90e`; loop file in that archive, SHA-256 `d0ac843e8ef99b431db28444d2131e4c7e1602aa7683f5ad69c8e7a40742ad6e` | **Source-backed but provisional physical map.** [Network audit](../results/twin/osm-network-audit.md) checks the AID01104 placement/lane scope. The archived network is not a committed reviewed standalone `sim/aberdeen.net.xml`. |
| Network conversion | `netconvert` 1.27.1, `--lefthand true`, original net plus PR #46 [`aberdeen-flow-balance-buslane.con.xml`](https://github.com/f1ymango/ripple/blob/647b13c/sim/scenarios/aberdeen-flow-balance-buslane.con.xml) (SHA-256 `d259c1ab989bf7ed37dfe38beccdf20a6ebe10c8642fe9e78d65fb6979e3a676`) and main `aberdeen-flow-balance.edg.xml`. Normalised generated-network SHA-256 `c11501968dc3d15235f23c6802f0be9551b03743ef0a81eecf6f28ed26c23937`. | **Model choice.** Keeps the OSM-tagged bus lane disconnected and splits one edge into two speed zones. Raw network byte hashes include a generated timestamp/path; use the documented header-stripped check. Tunnel connections still need physical review. |
| Demand input | PR #46 [`twin-inputs_20260515_no-mainline-join.json`](https://github.com/f1ymango/ripple/blob/647b13c/sim/scenarios/twin-inputs_20260515_no-mainline-join.json), SHA-256 `fbc71ca5696238006dd42403d0f4783cab1ad50664d34f5087c56eed6fbe8e1f`. Four first-detector counts from 15 May set entry demand; four earlier Fridays set internal joins/exits and later entry rates. | **Measured aggregates plus inferred allocation.** This revision removes an unsupported +201 veh/h main-line join. It still assumes a 32.7% westbound entry-to-exit split and independent chains. Demand after the pre-incident hour uses ordinary-day rates, not observed incident-window downstream counts. [Data's handoff](https://github.com/f1ymango/ripple/blob/647b13c/docs/flow-balance-replay-handoff-2026-10-05.md) lists the remaining omissions. |
| Observation export | `sim/scenarios/detectors.json` from the same archive, SHA-256 `a1d842a25ff872091b47fb3e7bcad566fe9932af0bc5452be3f79fc1462a4605` | **Observed**, 07:55–10:35. Never use incident-window downstream detector counts or speeds to set P0 demand or speed controls. Apply the existing coverage/validity filters. |
| Seed and horizon | SUMO seed `2026`, 1 s step; 07:25–10:35 HKT (11,400 simulated seconds), first 30 minutes warm-up; `--max-depart-delay -1`; 180 s wall timeout for the first attempt | **Reproducibility choice.** Matches PR #46's 07:25 warm-up and extends the builder's explicit 14 entry steps through the incident window. A timeout is an incomplete diagnostic, not a score. |
| Speed control | For the first P0 **queue diagnostic**, build with `--no-speeds` so no variable speed sign prescribes the incident-chain queue. This disables signs on all chains; keep that limitation in the comparison. | **Simulation proposal.** The revised no-sign no-closure control has 41.2% speed MAPE, so the first P0 cannot claim the 15.8% signed-speed baseline. Selective non-incident signs would require an explicit builder change and separate replay. |

The revised **no-closure** baseline independently reproduced on Windows SUMO
1.27.1: 231/242 count bins (95.5%) GEH < 5, 15.8% speed MAPE over 299 bins,
222 of 16,299 waiting to enter, zero teleports. The generated
[result](../results/twin/oct06-pr46-reviewed-independent.json) exactly matches
Data's published aggregates. This does not validate an incident queue.

## Physical incident and clocks

| Event | HKT / seconds from 07:25 | Choice for P0 | Source and epistemic status |
|---|---:|---|---|
| Physical first restriction | 08:55 / 5,400 s | Close only `44419212_0` (index `[0]`, slow/driver-left). | **Assumption pending Data and Lead review.** AID01104 drops to 7 km/h by 08:55, with persistent slow-lane zero readings around 08:54–09:00. This supports disruption, not the physical lane or exact crash onset. [Shortlist](../data/demo_shortlist.md), [raw lane review](../results/twin/may15-AID01104-lane-readings.md). |
| TD first report | 09:01 / 5,760 s | Message has `lanes_closed: ["unspecified"]`; P0 makes no operator move. | **Observed report timestamp**, not physical onset. [Shortlist](../data/demo_shortlist.md). An intervention cannot precede report availability. |
| All-lane phase | 09:36 / 7,860 s (offset 2,460 s) | Close both `44419212_0` and `44419212_1` (phase `"all"`). | **Observed TD update says all lanes at 09:36; physical transition time is assumed.** AID01104's earlier near-zero flow may contradict this as a physical onset. Compare flow from 09:00–09:36 before accepting. [Shortlist](../data/demo_shortlist.md). |
| Reopening | 10:02 / 9,420 s | Restore both lanes' original permissions. Closure duration from 08:55: 4,020 s. | **Observed TD clearance report; physical reopening instant is assumed.** Check detector flow/speed recovery through 10:35 rather than equating a message with recovery. [Shortlist](../data/demo_shortlist.md). |
| End | 10:35 / 11,400 s | Stop without draining an unbounded queue. | **Observation-window choice** in [shortlist](../data/demo_shortlist.md). Report unfinished, waiting and teleports. |

The edge and index mapping comes from [Simulation's source audit](simulation-handoff-2026-10-01.md):
two lanes on edge `44419212`, AID01104 at 136.31 m, SUMO `_0` is slow and
`_1` fast. I confirmed both IDs exist in the PR #46 rebuilt network. The exact
crash location on that 543.17 m edge is **not observed**; closing the whole
edge lane is a spatial approximation.

## Reproduction and decision gate

From an isolated checkout at PR #46 head, extract the Simulation archive at
the checkout root, then run:

```powershell
netconvert -s sim/work/aberdeen.net.xml `
  -x sim/scenarios/aberdeen-flow-balance-buslane.con.xml `
  -e sim/scenarios/aberdeen-flow-balance.edg.xml `
  -o sim/work/aberdeen.flow-balance-buslane.net.xml `
  --lefthand true --output.street-names true
python -m src.twin.flow_balance_demand `
  --inputs sim/scenarios/twin-inputs_20260515_no-mainline-join.json `
  --network sim/work/aberdeen.flow-balance-buslane.net.xml `
  --out sim/work/p0-demand --begin 07:25 --end 10:35 --no-speeds
```

The demand build has been checked locally: 287 flows and about 33,509 expected
vehicles over 07:25–10:35. **This is a generated model output, not an observed
incident count.** The P0 closure has not been run. After Data confirms the
choices, configure the existing `src/twin/run_scenario.py` with network and
routes above, the archived all-lane loop file, `seed=2026`, `begin=0`,
`end=11400`, incident `edge_id="44419212"`, `start=5400`,
`duration_seconds=4020`, and phases at offsets 0 `[0]` and 2460 `"all"`.
Use the archived loop file as `detector_additional`; the generated no-sign
additional file is empty and is not needed by `run_scenario.py`. Record exact
hashes in the run sidecar. The runner's `--max-seconds` limits simulated time,
not wall time, so launch it under an external 180-second wall guard and retain
incomplete output rather than publishing a truncated score.

The first comparison must cover AID01104 closure flow, both neighbouring
upstream/downstream detector bins, queue onset/length or a declared proxy,
and reopening/recovery through 10:35. Include the pre-incident no-sign
control, per-detector count and speed coverage, the ramp `46766432` entry
backlog, dropped/unfinished vehicles, teleports and source hashes. The
independent chain and immediate off-ramp exit assumptions could suppress
spillback or diversion, so a good GEH score alone cannot accept P0.

**Decisions still required today:** Data/E owns the initial unspecified-lane
policy and must confirm or revise `[0]`, including what detector evidence may
override it and what happens when evidence is insufficient. Data and Simulation
must agree the physical onset and all-lane transition as scenario assumptions;
the Lead resolves any remaining disagreement and approves the exact baseline
input version. Data/E owns reviewed plan context and provenance-bound P0
`result.json`; none is claimed here. Simulation will attempt the bounded P0
diagnostic by **7 October HKT after these choices are recorded**, and will
publish failure/timeout evidence if the run cannot complete.
