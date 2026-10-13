# Component C diagnostic of the saved Lead plans — 13 October 2026

**Disposition: completed diagnostic, joint P0 NO-GO unchanged.** We ran the
three actual Qwen3-generated plans in
`data/generated-plans/IN-26-03365-lead-draft-20261013-b/`, each with its
original `generation-inputs.json`. This is the retrospective draft described
in `docs/lead-genai-handoff-2026-10-13.md`. The plans pass the implemented
constraints and E's action mapping. The run demonstrates a working handoff
from D to E; its delay differences are simulated diagnostic output and do not
establish a real-world recommendation or saving.

## Common setup and input identity

- Base: main `9053d13`, SUMO 1.27.1, Python 3.14.3, seed 2026.
- Scenario: `sim/scenarios/evaluator_IN-26-03365_replay.json`, 07:25–10:35,
  30-minute warm-up, 66-minute clearance from modelled 08:54 onset.
- Plan set: `lead-draft-20261013-b`; compliance 0.5 for all three.
- Network SHA-256 `eb006b4ea09f01246ea53f163d68854e47b1be0410943f587d846388ef053e9d`.
  Speed signs SHA-256 `a8734743f90363ef9a7eedbb0f99e3ed2f9cac0c0411d15818f9087f1c9b8792`.
  Corrected demand SHA-256 `8caed7394039f64155dc7605458366507481ca8abd494193ff6c606130ad0f43`.
- Inputs were reconstructed from Simulation's committed 7 October packet with
  the commands in `src/evaluator/README.md`. The demand file had its generated
  line endings normalized to LF; its final hash matches E's documented input.
- `load_plan` validated each saved plan against its generation inputs;
  `PlanActions` placed each named route and signal. Each result was verified
  against the exact saved plan, generation inputs and all 13 captured simulator
  input/code identities in its original provenance sidecar.
- An outer 300-second wall guard included SUMO startup. P0, P1 and P2
  completed the full 11,400 simulation seconds in 216.55, 188.18 and 182.08
  wall seconds. See generated `execution.json` and original logs below.

Run one plan at a time, starting with P0:

```powershell
.\.venv\Scripts\python.exe -m src.evaluator.run --plans data/generated-plans/IN-26-03365-lead-draft-20261013-b --plan-set lead-draft-20261013-b --plan P0 --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --compliance 0.5 --clearance 66 --results-dir results/lead-draft-diagnostic-oct13
```

Repeat with `--plan P1`, then `--plan P2`, using the same arguments and an
external five-minute wall guard for each. The generated results, reports,
sidecars and logs are in `results/lead-draft-diagnostic-oct13/`. This folder
is kept separate from accepted `results/runs/` and the older rehearsal set.

## Results generated from the exact plans

| Plan | Total delay, veh-h | Against P0 in this run | Completed vehicles | Waiting to enter at end | Wrong-lane teleports |
|---|---:|---:|---:|---:|---:|
| P0 | 870.6 | reference | 26,633 | 0 | 3 |
| P1 | 961.3 | +10.4% | 26,594 | 0 | 7 |
| P2 | 952.2 | +9.4% | 26,596 | 0 | 6 |

P0 independently reproduces Data's corrected whole-run count result:
**89.45% GEH < 5 over 607 eligible bins** and **14.44% speed MAPE over 787
bins**. During the closure its count score is **83.15% over 267 bins**, below
the 85% target; after reopening speed MAPE is 15.82%. These P0 validation
figures are copied by E as a baseline reference for P1/P2, not measurements
of a real P1/P2 morning.

The P1 actions advise both supplied OD groups on Wong Chuk Hang Road despite
the original model title saying “Single OD Group Detour.” At compliance 0.5,
E modelled a 0.5 following probability in each group and recorded 411 vehicles
taking the advised route. P2 modelled 0.4 and 0.35 following probabilities,
350 advised-route vehicles, and an extra 20 seconds of green at the Tong Bin
Lane junction. Those shares, route choices and signal authority are candidate
or model assumptions, not observed operator actions. The advice window in E
starts at 09:01, while the context also contains later-known incident details;
the plans are a retrospective demonstration.

## Scientific decision and next handoff

The joint Data/Simulation NO-GO in
`docs/evaluator-p0-go-no-go-2026-10-09.md` still applies. The model has a
tunnel-side flow deficit; its incident-day speed signs constrain 20 detector
roads, while ordinary-morning signs miss the speed target; its northern join
was moved from a queuing ramp to the main line without independent physical
entry evidence; and its fitted driver-exit rule affects the comparison. The
three completed runs retain wrong-lane teleports. A single seed on these
exact AI plans also cannot establish a stable ranking. We did not retune
demand, add diversion flow, change road connections or rerun a broad sweep to
make a candidate appear better.

Data can inspect these new original result and provenance files, and Lead can
use them as an internal demonstration of the D→E handoff. An accepted
P0/P1/P2 comparison would require a new joint P0 behaviour review, source
evidence for the entry/turning and closure assumptions, common defensible
speed inputs, and paired-seed results for the exact plans. The proposed
16 October results/claims freeze does not itself change this gate. The
15 October presentation package should keep the observed playback and
recorded B/D inference as its supported material.
