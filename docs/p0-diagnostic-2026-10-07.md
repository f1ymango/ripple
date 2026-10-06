# IN-26-03365 — first bounded SUMO P0 diagnostic

Run on 6–7 October HKT by Simulation, after Data confirmed PR #46 inputs for
this diagnostic. This is **an attempted incident replay, not acceptance of the
baseline, physical closure reconstruction, rerouting or plan benefits**.

## Agreed-for-diagnostic assumptions and sources

Use the PR #46 revised flow-balance input and bus-lane-safe connection patch
at `647b13c`; the provisional base network and original detector observations
are from [Simulation's archived inputs](../results/twin/oct04-provisional-replay-inputs.zip).
The detailed source and SHA-256 ledger is in the
[P0 setup](p0-setup-proposal-2026-10-06.md). SUMO/netconvert 1.27.1,
seed 2026, 1-second step, 07:25–10:35 HKT, first 30 minutes warm-up.
`--no-speeds` and SUMO's default vehicle-type driver attributes allow queue
behaviour to emerge in the simulation; they forgo the 15.8% speed score from
the *different* no-closure run that imposed ordinary-day speed signs.

For this first diagnostic, the model closes `44419212_0` (slow lane) at
**08:55**, both `44419212_0` and `_1` at **09:36**, and reopens them at
**10:02**. The AID01104 lane readings support the initial slow-lane *inference*,
not a known physical lane closure. TD's 09:01 report says only “part of the
lanes”; its 09:36 all-lanes and 10:02 clearance messages are **observed report
times**, not observations of the exact physical transition seconds. P0 applies
no operator action; any plan intervention must wait for report availability.

The generated demand has 287 flows, about 33,509 expected vehicles. Its
measured entries at four first detectors and ordinary-Friday join/exit rates
are [Data's PR #46 handover](https://github.com/f1ymango/ripple/blob/647b13c/docs/flow-balance-replay-handoff-2026-10-05.md),
not incident-window downstream fitting. The Canal Road entry split and
independent chains remain model inferences.

## Execution and failed launch

The first launch **failed before time zero**. The archived AID01107 loops
still referenced lane `1198101443` beyond the PR #46 edge cut, and SUMO could
not create their output paths. I used the existing
`src/twin/run_flow_balance.py::move_loops` transformation, which relocates
those loops onto `1198101443.40` at their original physical position and
writes loop outputs to the diagnostic work directory. No observation or
detector count was altered. The failed launch is not a scored run.

The corrected TraCI replay completed all **11,400 seconds** within the
180-second wall guard. It did not silently discard delayed departures
(`max_depart_delay=-1`). Generated evidence:

- [Run summary](../results/twin/oct06-p0-assumed-run-summary.json): 33,505
  loaded, 32,665 inserted, **840 waiting to enter**, 1,881 unfinished at
  10:35, **72 teleports** (63 jam, 9 wrong-lane, 0 yield).
- [Detector comparison](../results/twin/oct06-p0-assumed-evaluation.json):
  87.15% GEH < 5 over 607 eligible count bins, but **47.33% speed MAPE** over
  790 speed bins. Seven observed zero-count bins were scoreable; only four
  had simulated zero count. No detector or count interval was unmatched.
- [Phase and FCD queue audit](../results/twin/oct06-p0-assumed-diagnostic.json):
  audited upstream slow-vehicle proxy, ramp proxy, source hashes and phase
  score breakdown. FCD is sampled at 10 seconds; the full 139 MB trajectory
  remains in ignored `sim/work/` and is not claimed as a committed artifact.

### Portable replay packet

The [3.2 MB input packet](../results/twin/oct07-p0-replay-inputs.zip) and
[SHA-256 manifest](../results/twin/oct07-p0-replay-inputs.manifest.json)
carry the generated network, default-driver demand, relocated detector loops,
observation export, PR #46 input and patches, and the exact scenario config.
Packet SHA-256:
`52b298aa73eb7e8621fce28223fc6b798100979f5735d0605ee62c2198b68505`.
The packet rewrites only each loop's output `file` path to a relative path;
lane IDs and positions are unchanged. SUMO successfully loaded the extracted
packet for a one-second input check. A second full 11,400-second packet replay
has **not** been run. From a fresh checkout of this Simulation branch with
SUMO 1.27.1 and its Python dependencies installed:

```powershell
Expand-Archive results/twin/oct07-p0-replay-inputs.zip -DestinationPath .
# Apply an external 180-second wall guard to this command.
python -m src.twin.run_scenario --config sim/work/p0-replay/p0.json --label p0-replay
python -m src.twin.evaluate `
  --observations sim/work/p0-replay/detectors.json `
  --sim sim/work/p0-replay/results `
  --config sim/work/p0-replay/evaluate.json `
  --out results/twin/p0-replay-evaluation.json
```

The overall 87.15% count-bin figure **does not pass the incident validation
gate**: the key detector and temporal pattern fail, and 72 teleports can
artificially clear queues.

## Closure flow and upstream queue timing

Counts below sum **only eligible five-minute bins**. The 09:35 bin mixes the
09:36 transition and has no eligible count; the 10:00 bin mixes the 10:02
reopening and is shown separately. These totals are not complete continuous
traffic counts.

| Interval / scoreable bins | AID01104 observed / SUMO | AID01103 upstream observed / SUMO | AID01102 upstream observed / SUMO |
|---|---:|---:|---:|
| Before 08:55 (10 each) | 1,041 / 1,149 | 1,596 / 1,747 | 1,311 / 1,402 |
| Assumed partial, 08:55–09:35 (6 each) | **17 / 547** | **280 / 826** | 318 / 619 |
| Assumed full, 09:40–10:00 (4 each) | **0 / 0** | 153 / 46 | 64 / 124 |
| Reopening bin 10:00 (1 each) | 72 / 165 | 75 / 147 | 43 / 4 |
| Recovery 10:05–10:35 (4 each) | 405 / 643 | 545 / 956 | 383 / 675 |

At AID01104, the first assumed one-lane closure passes about 91 vehicles per
scored five-minute bin while the detector mostly sees none. The upstream
AID01103 count is already substantially depressed in observation from 09:05;
SUMO still passes roughly 135–140 vehicles per scoreable bin until near the
09:36 all-lane phase. Thus the assumed one-lane restriction does **not**
reproduce the early closure flow or upstream queue onset. The full-lane phase
does reproduce four zero-flow bins at AID01104, but AID01106 downstream has
**310 observed versus 59 simulated** in the same four bins. That is a second
physical-location/timing or inflow-path discrepancy, not validation of the
full closure.

For a separate queue proxy, the [audit script](../src/twin/summarize_p0.py)
counts FCD vehicles below 5 km/h on the audited AID01102→AID01104 upstream
path, plus the incident edge before AID01104 at 136.31 m. It is an inserted-
vehicle proxy, **not a measured queue length**. The average is zero before
08:55, about **9.9** during the assumed partial phase, and **224.5** during
the all-lane phase (peak **303**). It peaks near 09:55; the five-minute sample
averages fall to zero by 10:20. The observed upstream flow collapse starts
earlier than this simulated large queue.

## Recovery and ramp backlog

Reopening at the reported 10:02 clearance causes an immediate simulated
release: AID01104 has 165 simulated versus 72 observed in the mixed 10:00
bin, then 643 versus 405 over four eligible recovery bins. AID01103 has
956 versus 545 over those bins. The FCD upstream slow-vehicle proxy clears
by 10:20, but the high simulated recovery flows and **1,881 unfinished** at
10:35 prevent a claim that recovery matches observation. Teleports further
confound that reading.

The pre-incident ramp queue also persists. FCD shows a mean **14.0 slow
vehicles on ramp `46766432`** before 08:55 (peak 23). Its sole demand flow
`f22` schedules 2,481 vehicles; FCD contains sequential IDs `f22.0` through
`f22.1640` (1,641 inserted), leaving a difference of **840**, equal to the
run's total pending departures. This strongly points to the same ramp as the
entry backlog, while the FCD alone cannot prove the exact location of every
outside-network vehicle. The ramp's actual signal timing is not sourced.

## Decision for the next diagnostic

This run supplies the requested bounded P0 attempt but **fails incident
validation**. Do not quote the overall GEH pass as a validated P0, use it to
rank plans, or infer a diversion benefit. The next decision is whether the
physical all-lane loss began before TD's 09:36 message, whether edge
`44419212` is the right spatial extent, and how upstream/downstream traffic
reaches the detectors. Data and Simulation should review the 09:00–09:36
lane-by-lane evidence and the downstream AID01106 flow, while the Lead decides
whether to continue SUMO or narrow the demonstration. Any alternative phase
timing is a new labelled sensitivity run, never a retrospective “observed”
fact. Data/E can build its first provenance-bound P0 result in parallel, but
this Component C diagnostic is not that result contract.
