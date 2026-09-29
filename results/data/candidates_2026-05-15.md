# Candidate demo incidents

Generated 2026-09-29 by `python -m src.loaders.fetch candidates`. Regenerate rather than edit; the reasoned pick is in `data/demo_shortlist.md`.

Screened: corridor incidents of type Traffic Accident, with a clear NEW and CLOSED 20-240 min apart, from all three STN files.

Each incident is compared with two ordinary days: the same weekday and clock time 1-6 weeks earlier that is not a public holiday and has no corridor incident in the window. A detector is **credited** when it ran at least 20 km/h below the first ordinary day for 10+ minutes, longer than the two ordinary days ever differed that way. **No traffic** is a detector carrying no vehicles for 15+ minutes with every lane reporting: a closure seen directly.

| # | Incident | When | Ordinary days | Where | TD's lane wording | Duration | Credited | Strongest (mean below ordinary, longest run) | No traffic | Onset vs report | Coverage | Other corridor incident | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `IN-26-03365` | 2026-05-15 09:01 | 8 May, 24 Apr | Wong Chuk Hang Road (Aberdeen Tunnel); Traffic Accident | part of the lanes -> all lanes | 61 min | 5 | AID01103 (main eastbound) -39.7 km/h, 75 min | AID01104 25 min | -6 min | 38% | — | 4.38 |

## Reading the table

- **Ordinary days** — the two days the incident was compared with. Public holidays (`data/hk_holidays.csv`) are never used. **(public holiday)** after the time means the incident itself fell on one, so it is compared with working days and may look milder than it was.
- **Onset vs report** — the first credited slowdown against TD's NEW message; negative means before it. Queues usually build 5-25 minutes before the report; more than 30 minutes before may be something else.
- **Coverage** — mean share of each 5-minute bin the archive delivered during the incident (docs/02-data.md section 3).
- **Other corridor incident** — another incident on the corridor overlaps the detector window, so part of the slowdown may be its doing.
- **Score** — one point each for depth, duration, spread, a closure seen as no traffic, and coverage; minus one for an overlapping incident, minus a half for an early onset. It orders the table; it does not pick the demo.
- An incident with fewer than two clean ordinary days is listed with no evidence rather than judged against a contaminated one.
