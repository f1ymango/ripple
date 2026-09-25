3. Evidence, with sources

Use these verbatim. Do not paraphrase numbers upward.

Scale of the problem
- Hong Kong, 2023: 17,189 road traffic accidents, 22,269 casualties, 28,808 vehicles involved. (C&SD, "Road Traffic Accident Statistics in Hong Kong, 2014 to 2023", Feb 2025 HKMDS) [Checked: https://www.censtatd.gov.hk, 2026-09-25]
- Police recorded 18,355 injury accidents in 2024 involving 23,659 people. [Checked: https://www.police.gov.hk, 2026-09-25]
- TD's Emergency Traffic Co-ordination Centre handled over 7,700 incidents in 2024, a 17% rise on ~6,600 in 2023; about half road-related, 32% transport service disruptions. (TD, reported Jul 2025) [Checked: https://www.td.gov.hk, 2026-09-25]

Why incidents specifically
- FHWA (US): incidents cause ~25% of non-recurring congestion; with weather, work zones and special events, non-recurring events cause ~60% of congestion delay; ~20% of all incidents are secondary incidents. [Checked: https://ops.fhwa.dot.gov/congestion/index.htm, 2026-09-25]

Why coordination beats individual routing
- Çolak, Lima & González, Nature Communications 7:10793 (2016): with mobile phone traces across five cities, moderate levels of social-good awareness in routing are enough to achieve significant collective travel-time savings. In their example city, user equilibrium cost 3.75 min/driver against 3.5 min at system optimum. [Checked: https://www.nature.com/articles/ncomms10793, 2026-09-25]
- Wardrop (1952) — user equilibrium vs system optimum. Braess's paradox (1968). [Checked: https://doi.org/10.1090/qam/41982, 2026-09-25]

That coordinated incident response works, and what it costs
- US Integrated Corridor Management, pre-deployment analysis: Dallas US-75 — 740,000 person-hours saved per year, 20:1 benefit–cost, USD 14M over 10 years. San Diego I-15 — 246,000 person-hours, 10:1, USD 12M. Projected BCRs across sites: 10:1 to 25:1. [Checked: https://its.dot.gov/icm/, 2026-09-25]
- Dallas North Tollway dynamic traffic assignment study: average network travel time fell 9% when response plans retimed 30 intersections, but only 3% when signal changes were limited to frontage roads. More spatial coverage of the plan → more benefit. Assumed diversion rates: 10–70%. [Checked: https://its.dot.gov/icm/, 2026-09-25]
- Timeline reality check: those corridors went from concept of operations in 2008 to launch in spring 2013. [Checked: https://its.dot.gov/icm/, 2026-09-25]

Hong Kong's direction of travel (why now)
- Transport Strategy Blueprint, February 2026. [Checked: https://www.td.gov.hk, 2026-09-25]
- LegCo written reply, 22 Apr 2026: TD proposes to commence a study on the Traffic Management Platform within this year, which will "use big data analytics and AI technologies to predict changes in traffic conditions, identify traffic bottlenecks, develop emergency response plans, assist with traffic management … and disseminate relevant information to the public", and will be "capable of analysing road congestion and recommending solutions in real-time". "areas around Aberdeen identified as the first site to be prepared within this year." [Checked: https://www.info.gov.hk/gia/general/202604/22.htm, 2026-09-25]
- Ting Kau Bridge Smart Motorway Pilot (Dec 2024) already uses AI automatic incident detection; being extended to more roads. [Checked: https://www.td.gov.hk, 2026-09-25]
- TD's real-time adaptive traffic signal system is being extended to about 50 signalised junctions, installation in phases from 2026. [Checked: https://www.td.gov.hk, 2026-09-25]

Prior art we must acknowledge (do not pretend to be first)
- LLM + traffic simulator work already exists: TrafficGPT, ChatSUMO, Open-TI, SUMO-MCP, AgentSUMO. Our novelty is the application, not the pattern: real Hong Kong incident feeds → a validated corridor twin → a tested, coordinated, bilingual, operator-approved response. [Checked: https://github.com/topics/traffic-simulation, 2026-09-25]
- DTSUMO (J. Intelligent Transportation Systems, 2025) is a published Python package that updates a SUMO twin from real-time detector data — check it before writing our own. ⚠️ FLAG: Paper publication year marked 2025; verify exact package release version in PyPI before code integration. [Checked: https://www.tandfonline.com/toc/gits20/current, 2026-09-25]
