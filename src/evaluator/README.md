# E — Evaluator

Runs one validated plan through the twin and writes the contracted
`result.json` with its provenance sidecar
([contract](../../docs/03-architecture.md#resultjson--output-of-e)).

**Status, 13 Oct:** version 3 of the replay
([scenario](../../sim/scenarios/evaluator_IN-26-03365_replay-v3.json),
[note](../../docs/evaluator-replay-v3-2026-10-13.md)) sets no speed at a scored
detector, shows ordinary-morning speeds on every sign, opens both lanes at
10:00, and does not score counts measured under 30 km/h, which these detectors
undercount. Its P0 meets the count target in every phase and every seed and
still misses the speed target (24.8%), almost all of it on the queue at
AID01102 and AID01103. The earlier replay and its notes
([10 Oct](../../docs/evaluator-replay-fixes-2026-10-10.md),
[8 Oct](../../docs/evaluator-replay-2026-10-08.md)) stay as dated history. The
plans run so far are stand-ins written by `rehearsal_plans.py`, not D's. The
go/no-go is in [the review](../../docs/evaluator-p0-go-no-go-2026-10-09.md),
section 6.

## Run it

Needs SUMO 1.27.1 and `pip install -r requirements.txt`.

```bash
# once: Simulation's P0 input packet (unmerged), extracted to sim/work/p0-replay/
git fetch origin sim/e1-evaluation-correctness
git checkout 4ec5afe -- results/twin/oct07-p0-replay-inputs.zip
python -c "import zipfile; zipfile.ZipFile('results/twin/oct07-p0-replay-inputs.zip').extractall('.')"
git restore --staged results/twin/oct07-p0-replay-inputs.zip   # keep Simulation's file out of your commit

# once: the replay's demand and speed signs, into sim/work/p0-replay-build/
python -m src.twin.flow_balance_demand --inputs sim/work/p0-replay/twin-inputs_20260515_no-mainline-join.json \
    --network sim/work/p0-replay/network.net.xml --out sim/work/p0-replay-build --begin 07:25 --end 10:35
python -m src.evaluator.speed_signs --build sim/work/p0-replay-build \
    --inputs sim/work/p0-replay/twin-inputs_20260515_no-mainline-join.json \
    --observations sim/work/p0-replay/detectors.json \
    --ordinary-only AID01101 AID01102 AID01103 AID01104 \
    --drop-edge 44419212 "814979901#0" 1198059118 1198059119 1198059120 \
    --out sim/work/p0-replay-build/speeds-replay.add.xml
python -m src.evaluator.main_line_join --routes sim/work/p0-replay-build/demand.rou.xml \
    --flow f22 --from-edge 1194711693 --out sim/work/p0-replay-build/demand-main-line-join.rou.xml

# P0, P1 and P2 of the rehearsal plans at 30%, 50% and 70% compliance
python -m src.evaluator.batch --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal \
    --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --clearance 66 \
    --results-dir results/evaluator-rehearsal

# or one run; P0 first, because P1 and P2 are compared with it
python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal \
    --plan P0 --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --compliance 0.5 --clearance 66 \
    --results-dir results/evaluator-rehearsal

# replay version 3 (13 Oct): two more inputs first, commands in docs/evaluator-replay-v3-2026-10-13.md section 10
python -m src.evaluator.batch --plans data/generated-plans/IN-26-03365-rehearsal --plan-set rehearsal \
    --scenario sim/scenarios/evaluator_IN-26-03365_replay-v3.json --clearance 66 \
    --results-dir results/evaluator-rehearsal-v3

# the Lead's plan set, once it exists and P0 is accepted: its own name, into results/runs/
python -m src.evaluator.batch --plans <the Lead's plans folder> --plan-set <its name, e.g. lead-v1> \
    --scenario sim/scenarios/evaluator_IN-26-03365_replay.json --clearance 66
```

The replay runs on `demand-main-line-join.rou.xml`: the same demand with the
join north of the tunnel on the main line. The built files must have these
SHA-256 values, which the scenario also states: `demand.rou.xml`
`5cbf6f6c…b955e`, `demand-main-line-join.rou.xml` `8caed739…f0ad0f43`,
`speeds-replay.add.xml` `a8734743…b8792`. A different file gives a different
result and a different provenance sidecar.

`--plans` is the folder D wrote (`P0.json`, `P1.json`, `P2.json`,
`generation-inputs.json`). `--plan-set` names that folder in the `run_id`
(lower-case letters, digits and hyphens), so results of two plan sets never
share an ID: `2026-05-15_ABD_P1_c50_t66_replay_rehearsal` is P1 of the
rehearsal plans at 50% compliance and 66 minutes' clearance on the replay
scenario. Use one name per plans folder. `--compliance` is a share from 0 to 1.
`--clearance` is minutes from closure onset to the first lane reopening; 66 is
08:54 to 10:00, when AID01104 carried traffic again. With the replay's
20-minute second stage the longest clearance that fits the run is 80.
`--results-dir` is the folder the run writes into (default `results/`). A run
takes about two minutes and prints SUMO's warnings as it goes; they are also
kept in the run's `sumo.log`.

**Where results go.** Each folder holds one plan set on one scenario: the
console groups runs by compliance, clearance and seed only, and withholds a
comparison when two P0 results share them.

| Folder | What |
|---|---|
| `results/runs/` | the plan set the briefing and console compare; F reads only this folder. Empty until the Lead's plans are evaluated |
| `results/evaluator-rehearsal/` | the stand-in rehearsal plans on the 10 October replay. Not for the briefing |
| `results/evaluator-rehearsal-v3/` | the stand-in rehearsal plans on replay version 3. Not for the briefing |
| `results/evaluator-diagnostics/` | other seeds, one-change scenarios (version 3's labels start `v3-`), and the 7 October P0 records |

Before E keeps an existing result, `batch` checks that it binds these plans,
their generation inputs and today's simulation inputs, and stops if not.

To see the rehearsal results in the console:

```bash
RIPPLE_RESULTS_DIR=results/evaluator-rehearsal/runs RIPPLE_PLANS_DIR=data/generated-plans/IN-26-03365-rehearsal \
    streamlit run src/console/app.py
```

Each run writes three files and never overwrites one:

| File | What |
|---|---|
| `<results-dir>/runs/<run_id>.json` | the contracted result |
| `<results-dir>/runs/<run_id>.provenance.json` | hashes of the plan, generation inputs, result and every simulation input |
| `<results-dir>/evaluator/<run_id>.report.json` | run health, score by phase, assumptions, what the plan did, how each metric was measured |

Nothing is written if the run does not reach its end time.

E refuses, before SUMO starts and without writing anything:

- a compliance outside 0 to 1, or a clearance that is not a positive number
  of minutes;
- a clearance with which some lane would still be closed when the run ends;
- a compliance or clearance with more decimals than the `run_id` shows
  (`c12.3457` cannot tell 0.1234567 from 0.1234571), or a plan-set name with
  anything but lower-case letters, digits and hyphens;
- a plan that is not exactly what D's validator returns for the saved inputs;
- a plan whose od group, route or junction the scenario does not place, a
  route that does not start on the road it avoids, or two junctions that are
  one traffic light in the network;
- for P1 or P2: a missing P0, a P0 without its sidecar or run report, a P0
  that no longer matches its sidecar, `P0.json` or `generation-inputs.json`,
  or a P0 made from other simulation inputs;
- a `run_id` that already has a result.

## How it works

1. [run.py](run.py) loads the plan and checks it is exactly what D's
   constraint validator returns for its saved inputs.
2. It hashes every simulation input **before** SUMO starts: network, demand,
   loops, observations, speed signs, the scenario file and E's own code. For
   P1 or P2 it then finds the P0 result of the same scenario, compliance and
   clearance, and refuses to go on if that was made from other inputs.
3. [simulate.py](simulate.py) runs SUMO and applies the closure each second.
   A run is void if an input changes under it.
4. Two things may also act each second.
   [behaviour.py](behaviour.py) is what drivers do by themselves when they
   meet the queue; it is in every run, P0 included.
   [actions.py](actions.py) is the plan: nothing for P0.
5. [metrics.py](metrics.py) reads the metrics from SUMO's output files.
   `DEFINITIONS` there states each one in a sentence, and the run report
   repeats them. The detector score is `src/twin/evaluate.py`, unchanged, and
   only P0 has one: a plan that did not happen cannot be compared with the
   morning that did.

## What E models of a plan

Between the plan context's `active_from` and `active_until`, or until the
first lane reopens if that is earlier. If the road reopens before
`active_from`, the plan does nothing and its run report says so:

| In the plan | In the twin |
|---|---|
| `diversions` | A driver of the od group follows the advice with probability share × compliance, takes the advised route from wherever they are, and does not leave the corridor at an exit. With two routes for one od group, one draw per driver splits the group by the shares. When the advice stops, drivers still short of the detour go back to the reopened road. |
| `signals` | The junction's green for the advised route runs `green_extend_s` longer; the cycle grows by as much. |
| `vms` | Nothing of their own: a sign is one way the advice reaches drivers. |
| `pt_nudge` | Not modelled. E refuses the plan. |

E also refuses a plan that names an od group, route or junction the
scenario's `plan_actions` block does not place in the network.

## The scenario file

A scenario file in `sim/scenarios/` holds what E assumes: inputs, seed, the
closure, how drivers behave, where plan actions act, and where each metric is
measured. Every assumption carries its status and source, and they are copied
into each run report. [scenario.py](scenario.py) lists every field.

| Scenario | Closure | Drivers | Plans |
|---|---|---|---|
| [evaluator_IN-26-03365.json](../../sim/scenarios/evaluator_IN-26-03365.json) | TD-message timing: 08:55, all lanes 09:36, reopen 10:02 | keep their routes | P0 only |
| [..._detector-timing.json](../../sim/scenarios/evaluator_IN-26-03365_detector-timing.json) | AID01104 readings: 08:54:00, all lanes 09:00:30, reopen 10:00:00 | keep their routes | P0 only |
| [..._detector-timing-rerouted.json](../../sim/scenarios/evaluator_IN-26-03365_detector-timing-rerouted.json) | the same | go round while every lane is closed | P0 only |
| [..._replay.json](../../sim/scenarios/evaluator_IN-26-03365_replay.json), **current** | the same, with the speeds around the crash and a two-stage reopening | go round by Wong Chuk Hang Road and keep their route (`closure.detour`, since 10 Oct), and some leave at the Aberdeen exits when they meet the queue | P0, P1, P2 |

[evaluator-diagnostics/](../../sim/scenarios/evaluator-diagnostics/) holds
copies of the replay with one thing changed each, named for the change. Their
results are in `results/evaluator-diagnostics/`.

- **Lanes travel as names.** [scenario.py](scenario.py) converts them to SUMO
  indices once (`slow` is index 0 in our left-hand network).
- **`unspecified` is never simulated as it stands.** The scenario must name
  the lanes and say why. For IN-26-03365 that is the slow lane, inferred from
  AID01104.
- **The first three scenarios run exactly as they did on 7 October.** The
  blocks the replay adds (`closure.scene`, `vehicles`, `drivers_leave`,
  `plan_actions`) are optional.
- A different assumption is a new scenario file with a new `run_label`, so
  its results get their own `run_id`.

## Two tools for inputs

- [speed_signs.py](speed_signs.py) writes the speed signs. It decides which
  detectors' speeds go in from the morning itself and which the model must
  produce. Read its first lines before quoting a speed error.
- [main_line_join.py](main_line_join.py) copies a demand file so that named
  flows join on the main line instead of by their on-ramp. The replay uses it
  for the join north of the tunnel, whose ramp merge held vehicles back
  ([10 October note](../../docs/evaluator-replay-fixes-2026-10-10.md)).
- `speed_signs.py --hold-from HH:MM` writes signs that show nothing measured
  after that time; [the 10 October note](../../docs/evaluator-replay-fixes-2026-10-10.md)
  compares it with the other sign files.
- [rehearsal_plans.py](rehearsal_plans.py) writes a P0, P1 and P2 from the
  reviewed context without a model, checked by D's validator.
  [do_nothing_plan.py](do_nothing_plan.py) writes P0 alone. When D generates
  its own plans, evaluate those: a result is bound to one exact plan file.

## What the numbers do and do not include

- Vehicles count from the end of the warm-up, **including** those still
  driving or still waiting to enter when the run ends.
- `total_vehicle_hours_delay` has three parts, and the run report gives each:
  time lost in the network, time waiting to enter, and an assumed 20 minutes
  for each vehicle that left the corridor because of the queue. A large,
  steady share of the waiting is a tunnel on-ramp (entry edge `46766432`)
  that also queues with no closure at all.
- `delay_vs_do_nothing_pct` compares one seed with one seed. Runs of the same
  plan with other seeds differ by a few percent, so a difference that small
  does not rank two plans. The note gives the spread.
- `max_queue_m` cannot exceed its path. `queue_share_of_path_pct` in the run
  report shows how much of the path it filled; near 100 means the queue ran
  off the path and the real figure is "at least".
- `emergency_tt_min` is general traffic on a candidate route that mostly
  carries no modelled traffic. Treat it as a placeholder until the route is
  reviewed.
- `validation` is empty for P1 and P2. Their run reports name the P0 they
  were compared with and repeat its validation.

## Tests

```bash
python -m pytest tests/test_evaluator.py
```

No SUMO needed: the simulator is replaced by mock output and a stand-in for
TraCI in the test file.
