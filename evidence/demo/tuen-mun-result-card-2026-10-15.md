# Tuen Mun result card — 15 October 2026

`tuen-mun-result-card-2026-10-15.html` is a single-file, offline capture aid for
the Lead's frozen Tuen Mun P0/P1/P2 grid. It does not run SUMO, the evaluator or
an LLM. Keep the amber status banner visible in any screenshot or video crop.

Open the saved page from the repository root:

```powershell
Invoke-Item -LiteralPath evidence/demo/tuen-mun-result-card-2026-10-15.html
```

To rebuild into a **new** file (the builder refuses to overwrite an existing
capture):

```powershell
.\.venv\Scripts\python.exe -m scripts.build_tuen_mun_result_card --out evidence/demo/tuen-mun-result-card-rebuild.html
```

The card reads the saved team ranking, matched detour-inclusive comparison, and
P0/P1/P2 plan JSON. It checks that all 18 ranking cells match the comparison's
E delays and that the frozen plan actions remain unchanged. The source table
inside the HTML gives full raw-byte SHA-256 hashes for those files and the
predeclared Tuen Mun protocol and Data's P0 review.

The displayed −4.3% is the mean paired difference in E's modelled delay; E's
ranking does not charge the longer Castle Peak Road drive. The −3.7% line is
the mean paired difference from Data's corrected delay with that drive included
and a 4-minute outside-network assumption. Neither is a measured road saving.
The team's 13 October interval rule ranks P2 first; the stricter Tuen Mun
every-cell rule fails one cell. Simulation's P0 queue/recovery concern remains
visible on the card. This is a candidate result, not an operator-ready
recommendation.
