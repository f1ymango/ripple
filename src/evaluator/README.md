# E — Evaluator

Runs one validated plan through the twin and writes the contracted
`result.json` with its provenance sidecar
([contract](../../docs/03-architecture.md#resultjson--output-of-e)).

**Status, 7 Oct:** P0 only. Diversions and signal changes are not modelled
yet, so E refuses P1 and P2 rather than save the do-nothing case under their
names. No P0 meets the validation targets yet; the current baseline and how
it was reached are in [the note](../../docs/evaluator-p0-2026-10-07.md).

## Run it

Needs SUMO 1.27.1 and `pip install -r requirements.txt`.

```bash
# once: Simulation's P0 input packet (unmerged), extracted to sim/work/p0-replay/
git fetch origin sim/e1-evaluation-correctness
git checkout 4ec5afe -- results/twin/oct07-p0-replay-inputs.zip
python -c "import zipfile; zipfile.ZipFile('results/twin/oct07-p0-replay-inputs.zip').extractall('.')"
git restore --staged results/twin/oct07-p0-replay-inputs.zip   # keep Simulation's file out of your commit

python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-p0-only --plan P0 \
    --scenario sim/scenarios/evaluator_IN-26-03365_detector-timing-rerouted.json \
    --compliance 0.5 --clearance 66
```

`--plans` is the folder D wrote (`P0.json`, `generation-inputs.json`).
`--clearance` is minutes from closure onset to reopening; 66 is 08:54 to
10:00, when AID01104 carried traffic again. `--results-dir` sends a diagnostic
somewhere other than `results/`, so it does not sit beside the baseline. The run takes about two minutes and prints SUMO's teleport
warnings as it goes; they are also kept in the run's `sumo.log`.

It writes three files and never overwrites one:

| File | What |
|---|---|
| `results/runs/<run_id>.json` | the contracted result |
| `results/runs/<run_id>.provenance.json` | hashes of the plan, generation inputs, result and every simulation input |
| `results/evaluator/<run_id>.report.json` | run health, score by phase, assumptions, how each metric was measured |

Nothing is written if the run does not reach its end time.

## How it works

1. [run.py](run.py) loads the plan and checks it is exactly what D's
   constraint validator returns for its saved inputs.
2. It hashes every simulation input **before** SUMO starts: network, demand,
   loops, observations, the scenario file and E's own code.
3. [simulate.py](simulate.py) runs SUMO and closes the scenario's lanes the
   way `src/twin/run_scenario.py` does. A run is void if an input changes
   under it.
4. [metrics.py](metrics.py) reads the metrics from SUMO's output files.
   `DEFINITIONS` there states each one in a sentence, and the run report
   repeats them. The detector score is `src/twin/evaluate.py`, unchanged.

## The scenario file

A scenario file in `sim/scenarios/` holds what E assumes: inputs, seed, the
closure, and where each metric is measured. Every assumption carries its
status and source, and they are copied into each run report.

| Scenario | Closure | Drivers |
|---|---|---|
| [evaluator_IN-26-03365.json](../../sim/scenarios/evaluator_IN-26-03365.json) | TD-message timing: 08:55, all lanes 09:36, reopen 10:02 | keep their routes |
| [..._detector-timing.json](../../sim/scenarios/evaluator_IN-26-03365_detector-timing.json) | AID01104 readings: 08:54:00, all lanes 09:00:30, reopen 10:00:00 | keep their routes |
| [..._detector-timing-rerouted.json](../../sim/scenarios/evaluator_IN-26-03365_detector-timing-rerouted.json), **current baseline** | the same | go round while every lane is closed |

- **Lanes travel as names.** [scenario.py](scenario.py) converts them to SUMO
  indices once (`slow` is index 0 in our left-hand network).
- **`unspecified` is never simulated as it stands.** The scenario must name
  the lanes and say why. For IN-26-03365 that is the slow lane, inferred from
  AID01104.
- **Rerouting is optional.** With `closure.reroute_at_edges`, a driver
  entering one of those edges while every lane is closed takes another route,
  chosen by SUMO. Nobody reroutes while a lane is open.
- A different closure assumption is a new scenario file with a new
  `run_label`, so its results get their own `run_id`.

## What the numbers do and do not include

- Vehicles count from the end of the warm-up, **including** those still
  driving or still waiting to enter when the run ends.
- `total_vehicle_hours_delay` includes time waiting to enter. In the P0 runs so
  far a third to a half of it is ramp flow `f22` waiting to enter, a queue
  Simulation also found with no closure at all.
- `max_queue_m` cannot exceed its path. `queue_share_of_path_pct` in the run
  report shows how much of the path it filled; near 100 means the queue ran
  off the path and the real figure is "at least".
- `emergency_tt_min` is general traffic on a candidate route that mostly
  carries no modelled traffic. Treat it as a placeholder until the route is
  reviewed.

## Tests

```bash
python -m pytest tests/test_evaluator.py
```

No SUMO needed: the simulator is replaced by mock output in
`tests/fixtures/mock_evaluator/`.
