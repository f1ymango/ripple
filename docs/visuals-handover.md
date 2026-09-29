# Visuals handover — 29 Sep 2026

Rorath owns component G: the Streamlit operator console and the roughly
90-second demo video. The working arrangement is for the coding assistant to
write and explain readable code, with Rorath guiding visual decisions and video
work.

## Saved work

Branch: `visuals/console-framing-theme`, based on the latest fetched `main`
(`7927f92`). The earlier incident playback work is already merged in PR #29.

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
