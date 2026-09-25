# Candidate demo incidents

Generated 2026-09-25 by `python -m src.loaders.fetch candidates`. Regenerate rather than edit.

**Coverage is a selection criterion, not a defect.** The historical archive keeps under half the detector minutes and which minutes survive is effectively random, so rather than fight the gaps we pick an incident that falls where they are smallest. See `docs/02-data.md` section 3.

| # | Incident | Date | Road | Duration | Retrievable | Coverage | Usable bins | Lanes valid | Speed drop | Score |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `IN-26-06481` | 2026-09-04 00:15 | Aberdeen Tunnel Wan Chai | 350 min | 75% | 45% | 77% | 99% | -11.5 km/h (AID01107) | 3.307 |
| 2 | `IN-26-06904` | 2026-09-19 17:37 | Busy Road Sections  | 126 min | 67% | — | — | — | — | 2.34 |
| 3 | `IN-26-05931` | 2026-08-17 16:16 | Wong Nai Chung Gap Flyover Cross Harbour Tunnel | 20 min | 83% | — | — | — | — | 1.993 |
| 4 | `IN-26-04390` | 2026-06-23 14:44 | Gloucester Road Central | 32 min | 67% | — | — | — | — | 1.873 |
| 5 | `IN-26-05992` | 2026-08-19 11:31 | Pok Fu Lam Road Aberdeen | 112 min | 25% | — | — | — | — | 1.5 |

Columns are blank below the top 1: those were screened on a 12-version sample only, not pulled in full.

## What the columns mean

- **Retrievable** — of the archive versions listed for this window, the share that actually serve rather than returning a persistent 404. Sampled.
- **Coverage** — mean share of each bin we actually observed, from the full pull. Higher means counts are closer to measurements than to estimates.
- **Usable bins** — share at or above the calibration threshold (40%). This is what Simulation has to fit demand against.
- **Lanes valid** — share of lane readings with `valid="Y"`. Low means detectors were offline, which is a different problem from archive gaps.
- **Speed drop** — slowest bin during the incident against the pre-incident mean, per tunnel detector (named in brackets), largest drop kept. An incident that does not move these is not worth simulating.
- **Order** — fully measured candidates come first, ranked on measured usable bins; the rest are ranked on a 12-file sample and are not comparable with them.

## Decision

🔒 The team picks one incident from this table. Record the choice in the README and in `docs/04-plan.md`, then everything downstream replays that one incident.
