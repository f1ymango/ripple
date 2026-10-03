# Recorded simulation replay for the demo video

The console reads the unchanged `plan.json` and `result.json` contracts from
`results/plans/*.json` and `results/runs/*.json`. Set `RIPPLE_PLANS_DIR` and
`RIPPLE_RESULTS_DIR` if the producing modules write elsewhere. It compares only
runs with the same incident, compliance, clearance and seed. A recommendation
appears only when P0, P1 and a coordinated plan have simulator delay metrics,
the plan files exist, and P0 meets the project's GEH and speed validation
targets. If P0 wins, the console says to do nothing.

To make a paired animation after Simulation and Data provide completed May 15
run files, use their reviewed network, incident edge and matching FCD outputs:

```bash
python -m src.console.render_replay \
  --incident-id IN-26-03365 \
  --network sim/aberdeen.net.xml \
  --incident-edge REVIEWED_SUMO_EDGE_ID \
  --baseline-fcd sim/work/results/BASELINE.fcd.xml \
  --plan-fcd sim/work/results/RECOMMENDED_PLAN.fcd.xml \
  --compliance 0.5 --clearance-min 60 \
  --start-seconds 4200 --end-seconds 7200 \
  --clock-start 2026-05-15T07:40:00+08:00
```

The example's simulation second zero is 07:40 because its 07:55 observation
begins at second 900. Check the completed scenario before using that clock or
the sample frame range. Use `--bbox XMIN YMIN XMAX YMAX` in SUMO map metres to
crop both panels to the reviewed corridor. `--every-seconds` controls sampling
(default 30); each GIF frame lasts 250 ms.

The renderer selects the winning plan from the result files, pairs only exact
timestamps present in both complete FCD files, and writes a GIF plus a JSON
manifest containing run IDs, scenario, time span and input SHA-256 hashes under
`results/replays/`. The console displays the GIF only when that manifest
matches its selected runs. `RIPPLE_REPLAYS_DIR` can point the console at another
output directory.

## Saved plans, briefing and operator decisions

The console and replay renderer now require the Lead's approved result
provenance sidecars. Each run needs its original `<run_id>.provenance.json`,
and the plans directory needs D's saved `generation-inputs.json` alongside
P0/P1/P2. Sidecars are checked against the plans, results and generation inputs;
compared runs must identify the same shared simulation inputs. The console
reuses D's constraint validator and F's result checks. Missing or changed
artifacts withhold the recommendation. Hashes identify inputs; model acceptance
still requires Simulation/Data review.

Point the console at the plan bundle actually written by D and F's saved drafts:

```bash
RIPPLE_PLANS_DIR=data/generated-plans/IN-26-03365-first \
RIPPLE_BRIEFINGS_DIR=data/generated-briefings \
streamlit run src/console/app.py
```

The briefing panel offers English and Traditional Chinese. It requires the
winning run/plan, the comparison's result and sidecar sources, and matching
sign IDs and character limits. A missing or mismatched briefing cannot be
approved. The operator enters their name, reviews the saved messages, and
records approval or rejection with a note. Message delivery is manual.

The console appends `viewed`, `approved` and `rejected` records to
`evidence/audit_log.jsonl` using the existing G contract. The note retains an
evidence fingerprint. Identified views are recorded once per displayed draft
and operator in the session. Inputs are re-read when recording a decision;
changes require reviewing the updated draft. Set `RIPPLE_AUDIT_LOG` to select
another audit file. Tests use only mock artifacts and temporary audit files.

Current checkpoint: the committed May run is a pre-incident diagnostic below
validation targets, the policy hook is still a no-op, and this checkout has no
May FCD outputs. The older September GIF is from another incident. Neither is
an evidenced route recommendation for the final video. When the policy and
validated runs arrive, verify on screen that vehicles actually take different
paths before recording the paired animation.
