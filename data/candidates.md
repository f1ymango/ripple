# Candidate demo incidents

Generated 2026-09-26 by `python -m src.loaders.fetch candidates`. Regenerate rather than edit; the reasoned pick is in `data/demo_shortlist.md`.

Screened: corridor incidents of type Traffic Accident, with a clear NEW and CLOSED 20-240 min apart, from all three STN files.

Each incident is compared with two ordinary days: the same weekday and clock time 1-6 weeks earlier with no corridor incident in the window. A detector is **credited** when it ran at least 20 km/h below the first ordinary day for 10+ minutes, longer than the two ordinary days ever differed that way. **No traffic** is a detector carrying no vehicles for 15+ minutes with every lane reporting: a closure seen directly.

| # | Incident | When | Where | TD's lane wording | Duration | Credited | Strongest (mean below ordinary, longest run) | No traffic | Onset vs report | Coverage | Other corridor incident | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `IN-26-03365` | 2026-05-15 09:01 | Wong Chuk Hang Road (Aberdeen Tunnel); Traffic Accident | part of the lanes -> all lanes | 61 min | 5 | AID01103 (main eastbound) -39.7 km/h, 75 min | AID01104 25 min | -6 min | 38% | — | 4.38 |
| 2 | `IN-26-03030` | 2026-05-02 12:15 | Shek Pai Wan Road (Aberdeen Praya Road); Traffic Accident | part of the lanes | 55 min | 3 | TDSSPWR10001 (western alternative) -25.4 km/h, 50 min | TDSSPWR10001 15 min | -20 min | 42% | — | 4.27 |
| 3 | `IN-26-05951` | 2026-08-18 02:53 | Wong Chuk Hang Road (Aberdeen Tunnel); Traffic Accident | part of the lanes -> all lanes | 63 min | 4 | AID01107 (main eastbound) -16.6 km/h, 10 min | AID01106 20 min, AID01107 55 min | -23 min | 34% | — | 3.34 |
| 4 | `IN-26-05992` | 2026-08-19 11:31 | Pok Fu Lam Road (Aberdeen); Traffic Accident | part of the lanes -> one-lane-two-way | 112 min | 4 | TDSSPWR10001 (western alternative) -32.4 km/h, 65 min | — | -31 min | 38% | — | 2.88 |
| 5 | `IN-26-03744` | 2026-05-29 13:05 | Wong Nai Chung Gap Flyover (Aberdeen Tunnel); Traffic Accident | fast lane | 32 min | 4 | AID01108 (main eastbound) -26.4 km/h, 30 min | — | -30 min | 31% | — | 2.86 |
| 6 | `IN-26-06874` | 2026-09-18 17:34 | Pok Fu Lam Road (Central); Traffic Accident | part of the lanes | 43 min | 6 | TDSSPWR20003 (western alternative) -53.2 km/h, 70 min | — | -34 min | 36% | — | 2.86 |
| 7 | `IN-26-06391` | 2026-09-01 12:41 | Aberdeen Tunnel (Wan Chai); Traffic Accident | tunnel tube slow lane | 26 min | 6 | AID01107 (main eastbound) -36.8 km/h, 45 min | — | -31 min | 32% | — | 2.82 |
| 8 | `IN-26-03254` | 2026-05-11 16:29 | Pok Fu Lam Road (no direction); Traffic Accident | one-lane-two-way -> part of the lanes | 62 min | 1 | AID01107 (main eastbound) -31.7 km/h, 55 min | — | -19 min | 48% | — | 2.81 |
| 9 | `IN-26-03652` | 2026-05-26 15:41 | Wong Nai Chung Gap Flyover (Cross Harbour Tunnel); Traffic Accident | part of the lanes | 20 min | 1 | AID01108 (main eastbound) -38.6 km/h, 50 min | — | -11 min | 45% | — | 2.78 |
| 10 | `IN-26-02105` | 2026-03-23 08:23 | Wong Chuk Hang Road (Aberdeen); Traffic Accident | slow lane | 48 min | 1 | AID01219 (main westbound) -24.4 km/h, 45 min | — | -13 min | 40% | — | 2.55 |
| 11 | `IN-26-02398` | 2026-04-02 17:01 | Wong Nai Chung Gap Flyover (Cross Harbour Tunnel); Traffic Accident | fast lane | 44 min | 2 | AID01108 (main eastbound) -11.2 km/h, 45 min | — | -1 min | 41% | — | 2.45 |
| 12 | `IN-26-05576` | 2026-08-03 06:03 | Aberdeen Tunnel (Aberdeen); Traffic Accident | tunnel tube fast lane | 59 min | 5 | AID01108 (main eastbound) -15.2 km/h, 25 min | — | -18 min | 39% | — | 2.45 |
| 13 | `IN-26-02316` | 2026-03-30 18:37 | Pok Fu Lam Road (Central); Traffic Accident | part of the lanes | 37 min | 2 | TDSSPWR20003 (western alternative) -29.5 km/h, 15 min | — | -12 min | 30% | — | 2.28 |
| 14 | `IN-26-02637` | 2026-04-16 12:56 | Wong Chuk Hang Road (Aberdeen Tunnel); Traffic Accident | part of the lanes | 57 min | 4 | AID01103 (main eastbound) -18.9 km/h, 35 min | — | -31 min | 28% | — | 2.19 |
| 15 | `IN-26-06195` | 2026-08-25 17:03 | Pok Fu Lam Road (Central); Traffic Accident | part of the lanes | 35 min | 3 | AID01108 (main eastbound) -17.9 km/h, 30 min | — | -33 min | 39% | — | 2.15 |
| 16 | `IN-26-03212` | 2026-05-09 09:29 | Wong Chuk Hang Road (Aberdeen Tunnel); Traffic Accident | part of the lanes | 63 min | 2 | AID01104 (main eastbound) -55.6 km/h, 55 min | — | -19 min | 44% | IN-26-03214 | 2.11 |
| 17 | `IN-26-05931` | 2026-08-17 16:16 | Wong Nai Chung Gap Flyover (Cross Harbour Tunnel); Traffic Accident | part of the lanes | 20 min | 1 | AID01108 (main eastbound) -29.6 km/h, 20 min | — | -1 min | 32% | — | 2.08 |
| 18 | `IN-26-03214` | 2026-05-09 10:31 | Pok Fu Lam Road (Aberdeen); Traffic Accident | part of the lanes | 85 min | 3 | AID01104 (main eastbound) -32.0 km/h, 70 min | — | -31 min | 49% | IN-26-03212, IN-26-03217 | 1.99 |
| 19 | `IN-26-02614` | 2026-04-15 17:57 | Wong Chuk Hang Road (Aberdeen); Traffic Accident | part of the lanes | 49 min | 2 | AID01109 (main eastbound) -16.7 km/h, 20 min | — | -17 min | 31% | — | 1.98 |
| 20 | `IN-26-06117` | 2026-08-22 14:06 | Pok Fu Lam Road (no direction); Traffic Accident | one-lane-two-way | 191 min | 2 | AID01108 (main eastbound) -8.9 km/h, 25 min | — | 74 min | 38% | — | 1.9 |
| 21 | `IN-26-04010` | 2026-06-09 08:23 | Pok Fu Lam Road (Central); Traffic Accident | part of the lanes | 20 min | 2 | AID01216 (main westbound) -22.5 km/h, 25 min | — | -33 min | 41% | — | 1.88 |
| 22 | `IN-26-04067` | 2026-06-11 17:07 | Leighton Road (Wan Chai); Traffic Accident | part of the lanes | 25 min | 2 | AID01108 (main eastbound) -10.5 km/h, 40 min | — | -32 min | 40% | — | 1.81 |
| 23 | `IN-26-06240` | 2026-08-26 21:54 | Canal Road Flyover (Aberdeen Tunnel); Traffic Accident | part of the lanes | 28 min | 2 | AID01214 (main westbound) -12.4 km/h, 15 min | — | -29 min | 40% | — | 1.81 |
| 24 | `IN-26-05636` | 2026-08-05 17:23 | Canal Road Flyover (Cross Harbour Tunnel); Traffic Accident | part of the lanes | 28 min | 1 | AID01108 (main eastbound) -19.2 km/h, 20 min | — | -8 min | 37% | — | 1.79 |
| 25 | `IN-26-04482` | 2026-06-26 08:18 | Canal Road Flyover (Aberdeen Tunnel); Traffic Accident | part of the lanes | 33 min | 2 | AID01214 (main westbound) -21.6 km/h, 40 min | — | -23 min | 40% | IN-26-04479 | 1.68 |
| 26 | `IN-26-02923` | 2026-04-28 17:32 | Wong Chuk Hang Road (Pok Fu Lam); Traffic Accident | only lane of a slip road | 24 min | 1 | AID01221 (main westbound) -12.7 km/h, 25 min | — | -2 min | 34% | — | 1.65 |
| 27 | `IN-26-04326` | 2026-06-20 06:54 | Wong Nai Chung Gap Flyover (Aberdeen Tunnel); Traffic Accident | all lanes -> part of the lanes | 38 min | 1 | AID01215 (main westbound) -5.0 km/h, 25 min | — | 1 min | 44% | — | 1.5 |
| 28 | `IN-26-03217` | 2026-05-09 12:25 | Wong Nai Chung Gap Flyover (Cross Harbour Tunnel); Traffic Accident | fast lane | 73 min | 2 | AID01108 (main eastbound) -20.7 km/h, 15 min | — | -30 min | 43% | IN-26-03214 | 1.34 |
| 29 | `IN-26-04705` | 2026-07-04 17:25 | Wong Nai Chung Gap Flyover (Cross Harbour Tunnel); Traffic Accident | part of the lanes | 229 min | 2 | AID01107 (main eastbound) -19.6 km/h, 20 min | — | 25 min | 24% | IN-26-04706 | 1.34 |
| 30 | `IN-26-05720` | 2026-08-08 13:07 | Wah Fu Road (no direction); Traffic Accident | part of the lanes | 227 min | 1 | AID01107 (main eastbound) 0.8 km/h, 15 min | — | 68 min | 40% | — | 1.04 |
| 31 | `IN-26-02266` | 2026-03-28 13:59 | Canal Road Flyover (Cross Harbour Tunnel); Traffic Accident | part of the lanes | 23 min | 1 | AID01108 (main eastbound) -22.5 km/h, 20 min | — | -29 min | 39% | IN-26-02262 | 0.92 |
| 32 | `IN-26-06063` | 2026-08-21 08:52 | Pok Fu Lam Road (Aberdeen); Traffic Accident | part of the lanes | 34 min | 3 | AID01107 (main eastbound) -2.9 km/h, 15 min | — | -27 min | 38% | IN-26-06062 | 0.81 |
| 33 | `IN-26-02349` | 2026-03-31 19:12 | Pok Fu Lam Road (Central); Traffic Accident | part of the lanes | 30 min | 1 | TDSSPWR10001 (western alternative) -6.4 km/h, 10 min | — | 18 min | 35% | IN-26-02343 | 0.12 |
| 34 | `IN-26-03430` | 2026-05-17 10:15 | Pok Fu Lam Road (Central); Traffic Accident | only lane of a slip road | 81 min | 0 | none | — | — | 35% | — | 0.0 |
| 35 | `IN-26-03639` | 2026-05-25 15:09 | Canal Road Flyover (Cross Harbour Tunnel); Traffic Accident | fast lane | 29 min | 0 | none | — | — | 41% | — | 0.0 |

## Reading the table

- **Onset vs report** — the first credited slowdown against TD's NEW message; negative means before it. Queues usually build 5-25 minutes before the report; more than 30 minutes before may be something else.
- **Coverage** — mean share of each 5-minute bin the archive delivered during the incident (docs/02-data.md section 3).
- **Other corridor incident** — another incident on the corridor overlaps the detector window, so part of the slowdown may be its doing.
- **Score** — one point each for depth, duration, spread, a closure seen as no traffic, and coverage; minus one for an overlapping incident, minus a half for an early onset. It orders the table; it does not pick the demo.
- An incident with fewer than two clean ordinary days is listed with no evidence rather than judged against a contaminated one.
