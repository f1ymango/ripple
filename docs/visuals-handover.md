# Visuals handover — 29 Sep 2026

Rorath owns component G: the Streamlit operator console and the roughly
90-second demo video. The working arrangement is for the coding assistant to
write and explain readable code, with Rorath guiding visual decisions and video
work.

## Saved work

Branch: `visuals/console-framing-theme`, based on the latest fetched `main`
(`7927f92`). The earlier incident playback work is already merged in PR #29.

[PR #31](https://github.com/f1ymango/ripple/pull/31) is open for review against
`main`. The branch and this handover are pushed to GitHub; the Lead owns merging.

- The map now uses the detector bounds to frame the whole corridor. All 28
  detector circles fit at the checked 1280px and 1500px browser widths.
- `.streamlit/config.toml` pins a light theme with blue controls. The page and
  browser tab both say “Ripple — Aberdeen corridor”.
- Playback controls update session state before the page renders. Pausing,
  stepping, rewinding and scrubbing restore the Play button immediately.
- Scrubbing updates the selected bin before drawing the controls, keeping
  stepping, the map and the timeline cursor aligned.
- The README tracker records the work. The README rebase conflict was resolved
  by retaining the latest Lead and Impact updates alongside the Visuals entry.

Implementation commit: `f010165` — Console: frame corridor, pin theme and
synchronize playback.

## Validation and evidence

`python -m pytest tests/test_console.py -q`: **38 passed**, including five new
regression cases for stopping playback and stepping after scrubbing.

Playwright CLI checked the two browser widths, the light theme under dark and
light browser preferences, scrubbing to the real IN-26-03365 09:15 bin, stepping
to 09:20 and back, and playback advancing and pausing.

[Console screenshot at 09:15](img/console-framing-theme.png).

Run the console from the repo root with
`streamlit run src/console/app.py`. Restart an existing Streamlit server after
code or theme changes if it continues displaying the old version.

## Where to resume

1. Build three-column plan comparison and headline metrics against the existing
   `result.json` contract in `docs/03-architecture.md`. The evaluator and briefing
   components are still scheduled work; present missing outputs explicitly.
2. Coordinate road geometry with the Simulation owner before drawing diversion
   routes. Routes should follow real road shapes.
3. Add the operator approval action and audit log, then prepare the demo video.

Metrics must come from simulator outputs in `results/`. Test mocks must be
clearly named `mock_*` and kept in `tests/fixtures/`.

## Local operator workflow — 3 Oct 2026

Integration branch: `visuals/operator-workflow-oct03`, based on fetched main
`1f17b4f`. The working checkout is `/tmp/ripple-operator-workflow-oct03`; if
that temporary directory is cleared, recreate a worktree from the saved branch.
The original checkout and its earlier replay draft remain separate.

- Plan comparison now reuses D/F validation and requires E's original
  provenance sidecars and saved generation inputs. Mixed or changed inputs
  withhold the recommendation.
- The operator panel reads the matching saved bilingual briefing, checks
  result/sidecar sources and sign limits, and records identified views and
  approvals/rejections with the existing audit fields. Inputs are re-read at
  each decision; a changed draft requires another review. Delivery is manual.
- The replay renderer uses the same provenance checks. Integration commands
  and environment variables are in `src/console/REPLAY.md`.
- Verification: 112 focused console, recommendation, operator-workflow and
  D/F tests passed; `git diff --check` and compile checks passed. The live
  1500px preview rendered its waiting state with disabled decisions and no
  browser errors. Fixtures remain clearly named `mock_*`; there are no real
  accepted plan runs or May rerouting evidence in this checkpoint.

Preview: `http://127.0.0.1:8502`. It uses the original checkout's recorded
detector bins via `RIPPLE_DATA_DIR`. The 2 Oct report contribution is already
pushed in PR #40 and was still open when checked today. This console
integration is local until Rorath approves its own push and PR.
