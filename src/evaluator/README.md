# E — Evaluator

Runs one validated plan through the twin and writes the contracted
`result.json` with its provenance sidecar
([contract](../../docs/03-architecture.md#resultjson--output-of-e)).

**Status, 7 Oct:** P0 only. Diversions and signal changes are not modelled
yet, so E refuses P1 and P2 rather than save the do-nothing case under their
names. The first P0 does not meet the validation targets; see
[the note](../../docs/evaluator-p0-2026-10-07.md).

## Run it

Needs SUMO 1.27.1 and `pip install -r requirements.txt`.

```bash
# once: Simulation's P0 input packet (unmerged), extracted to sim/work/p0-replay/
git fetch origin sim/e1-evaluation-correctness
git checkout 4ec5afe -- results/twin/oct07-p0-replay-inputs.zip
python -c "import zipfile; zipfile.ZipFile('results/twin/oct07-p0-replay-inputs.zip').extractall('.')"
git restore --staged results/twin/oct07-p0-replay-inputs.zip   # keep Simulation's file out of your commit

python -m src.evaluator.run --plans data/generated-plans/IN-26-03365-first --plan P0 \
    --scenario sim/scenarios/evaluator_IN-26-03365.json --compliance 0.5 --clearance 67
```

`--plans` is the folder D wrote (`P0.json`, `generation-inputs.json`).
`--clearance` is minutes from closure onset to reopening; 67 is 08:55 to TD's
10:02 incident end. The run takes about two minutes and prints SUMO's teleport
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

[sim/scenarios/evaluator_IN-26-03365.json](../../sim/scenarios/evaluator_IN-26-03365.json)
holds what E assumes: inputs, seed, the closure, and where each metric is
measured. Every assumption carries its status and source, and they are copied
into each run report.

- **Lanes travel as names.** [scenario.py](scenario.py) converts them to SUMO
  indices once (`slow` is index 0 in our left-hand network).
- **`unspecified` is never simulated as it stands.** The scenario must name
  the lanes and say why. For IN-26-03365 that is the slow lane, inferred from
  AID01104.
- A different closure assumption is a new scenario file with a new
  `run_label`, so its results get their own `run_id`.

## What the numbers do and do not include

- Vehicles count from the end of the warm-up, **including** those still
  driving or still waiting to enter when the run ends.
- `total_vehicle_hours_delay` includes time waiting to enter. In the first P0
  1,388 of the 2,584 vehicle-hours is ramp flow `f22` waiting to enter, a
  queue Simulation also found with no closure at all.
- `max_queue_m` cannot exceed its path. In the first P0 it is 1,961 m of a
  1,971 m path (`queue_share_of_path_pct` 99.5 in the run report): the queue
  reached the network entry, so the real figure is "at least".
- `emergency_tt_min` is general traffic on a candidate route that mostly
  carries no modelled traffic. Treat it as a placeholder until the route is
  reviewed.

## Tests

```bash
python -m pytest tests/test_evaluator.py
```

No SUMO needed: the simulator is replaced by mock output in
`tests/fixtures/mock_evaluator/`.
