"""Build an offline Tuen Mun result card from the saved Lead grid.

This is a presentation aid, not a new evaluator run. Its figures come from the
saved ranking and comparison JSON; it makes no model, SUMO or network call.
"""

import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from statistics import mean
from string import Template


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "evidence/demo/tuen-mun-result-card-2026-10-15.html"
PLAN_DIR = "data/generated-plans/IN-26-02615-lead-capacity-oct15"
SOURCES = {
    "Team ranking": "results/rankings/lead-capacity-oct15-p0x-merge-at-site.json",
    "Detour-inclusive comparison": (
        "results/tuen-mun-lead-grid-oct15-p0x-merge-at-site/"
        "comparison_p0x-merge-at-site.json"
    ),
    "P0 plan": f"{PLAN_DIR}/P0.json",
    "P1 plan": f"{PLAN_DIR}/P1.json",
    "P2 plan": f"{PLAN_DIR}/P2.json",
    "Predeclared Tuen Mun protocol": "docs/tuen-mun-p1-p2-protocol-2026-10-14.md",
    "Data's 15 Oct P0 review": "docs/tuen-mun-go-no-go-evidence-2026-10-15.md",
}


def read_bundle(root=ROOT):
    """Load raw sources, retaining hashes so a capture identifies its inputs."""
    raw = {label: (root / relative).read_bytes()
           for label, relative in SOURCES.items()}
    documents = {label: json.loads(data)
                 for label, data in raw.items() if label not in (
                     "Predeclared Tuen Mun protocol", "Data's 15 Oct P0 review")}
    hashes = {label: sha256(data).hexdigest() for label, data in raw.items()}
    return validate_bundle(documents, hashes)


def validate_bundle(documents, hashes):
    """Reject a mixed grid or changed plan action before showing a ranking."""
    ranking = documents["Team ranking"]
    comparisons = documents["Detour-inclusive comparison"]
    plans = {pid: documents[f"{pid} plan"] for pid in ("P0", "P1", "P2")}
    if ranking["incident_id"] != "IN-26-02615" or ranking["plan_set"] != "lead-capacity-oct15":
        raise ValueError("Not the frozen Tuen Mun Lead grid")
    if ranking["first"] != "P2" or len(ranking["cells"]) != 18:
        raise ValueError("The saved team ranking changed; review the card before rebuilding")
    if not all(cell["counts"] for cell in ranking["cells"]):
        raise ValueError("The ranking contains a cell that does not count")
    if any(plans[pid]["plan_id"] != pid or plans[pid]["signals"]
           for pid in plans):
        raise ValueError("The frozen plan IDs or no-signal assumption changed")
    if plans["P0"]["diversions"] or len(plans["P1"]["diversions"]) != 1 or len(plans["P2"]["diversions"]) != 1:
        raise ValueError("The frozen plan actions changed")
    p1_diversion = plans["P1"]["diversions"][0]
    p2_diversion = plans["P2"]["diversions"][0]
    if (p1_diversion["share"] != 1 or p2_diversion["share"] != 0.11
            or p1_diversion["via"] != "Castle Peak Road"
            or p2_diversion["via"] != "Castle Peak Road"
            or p1_diversion["od_group"] != p2_diversion["od_group"]):
        raise ValueError("The frozen Castle Peak Road advice changed")

    pairs = {(row["a"], row["b"]): row for row in ranking["pairs"]}
    if set(pairs) != {("P0", "P1"), ("P0", "P2"), ("P1", "P2")}:
        raise ValueError("The saved ranking lacks a P0/P1/P2 comparison")
    if [pairs[key]["before"] for key in (("P0", "P1"), ("P0", "P2"), ("P1", "P2"))] != ["P0", "P2", "P2"]:
        raise ValueError("The saved pair verdicts changed")

    compared = {row["cell"]: row for row in comparisons}
    cells = {row["name"]: row for row in ranking["cells"]}
    if len(compared) != 18 or set(compared) != set(cells):
        raise ValueError("The detour comparison does not match the ranking cells")
    charged_differences = []
    for name, cell in cells.items():
        row = compared[name]
        if not row["p0_validation_met"]:
            raise ValueError(f"{name}: P0 validation differs from the ranking")
        for pid in plans:
            if abs(row["plans"][pid]["delay_E"] - cell["total_vehicle_hours_delay"][pid]) > 0.01:
                raise ValueError(f"{name}: E delay differs between the two saved outputs")
        p0 = row["plans"]["P0"]["corrected"]["4 min outside"]
        p2 = row["plans"]["P2"]["corrected"]["4 min outside"]
        if p0 <= 0:
            raise ValueError(f"{name}: nonpositive corrected P0 delay")
        charged_differences.append(100 * (p2 - p0) / p0)

    p0_p1 = pairs[("P0", "P1")]
    p0_p2 = pairs[("P0", "P2")]
    lower_cells = p0_p2["cells_b_lower"]
    if lower_cells != sum(c["total_vehicle_hours_delay"]["P2"] < c["total_vehicle_hours_delay"]["P0"]
                          for c in ranking["cells"]):
        raise ValueError("P2 cell count differs from the saved delays")
    return {
        "ranking": ranking,
        "plans": plans,
        "hashes": hashes,
        "p1_vs_p0_pct": -p0_p1["mean_difference_pct"],
        "p1_vs_p0_interval": [-p0_p1["interval_pct"][1], -p0_p1["interval_pct"][0]],
        "p2_vs_p0_pct": -p0_p2["mean_difference_pct"],
        "p2_vs_p0_interval": [-p0_p2["interval_pct"][1], -p0_p2["interval_pct"][0]],
        "p2_lower_cells": lower_cells,
        "detour_charged_pct": mean(charged_differences),
    }


def h(value):
    return escape(str(value), quote=True)


HTML = Template("""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>Ripple · Tuen Mun simulated plan comparison</title>
  <style>
    :root { font-family: system-ui, "Segoe UI", sans-serif; color: #eff7f8; background: #071b27; }
    * { box-sizing: border-box; }
    body { margin: 0; line-height: 1.45; }
    .banner { background: #f7bd60; color: #2a1b08; padding: .7rem 1.4rem; font-size: 1rem; font-weight: 850; letter-spacing: .055em; text-align: center; }
    main { max-width: 1260px; margin: auto; padding: 1.1rem 1.4rem 2rem; }
    .topline { color: #8de1dd; font-size: .86rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 800; }
    h1 { margin: .24rem 0 .35rem; font-size: clamp(2rem, 4vw, 3.3rem); line-height: 1.1; }
    .lede { color: #c9d8df; margin: 0 0 1.25rem; font-size: 1.08rem; }
    .cards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .9rem; }
    .card { border: 1px solid #42606d; border-radius: 14px; padding: 1.05rem 1.15rem; background: #102e3c; min-width: 0; }
    .card.best { border: 2px solid #73d5b3; background: #123b3d; }
    .planid { color: #8de1dd; font-weight: 850; letter-spacing: .12em; font-size: .9rem; }
    .card h2 { font-size: 1.25rem; margin: .28rem 0 .55rem; }
    .number { font-weight: 850; font-size: clamp(2.2rem, 4.5vw, 3.75rem); line-height: 1.05; font-variant-numeric: tabular-nums; margin: .18rem 0; }
    .neutral { color: #e3eef1; } .bad { color: #ff9d91; } .good { color: #81e4bc; }
    .metric { color: #d1e1e4; font-size: .94rem; margin: .2rem 0 .6rem; }
    .small { color: #bfd2d8; font-size: .9rem; margin: .48rem 0 0; }
    .rule { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .9rem; margin-top: .9rem; }
    .rule article { padding: .9rem 1rem; border-radius: 12px; background: #173547; border-left: 4px solid #78c8e2; }
    .rule article:nth-child(2) { border-color: #f7bd60; }
    .rule h2 { margin: 0 0 .26rem; font-size: 1.05rem; }
    .rule p { margin: 0; font-size: .94rem; }
    .limit { margin-top: .9rem; padding: .78rem 1rem; border-radius: 10px; border-left: 4px solid #f7bd60; background: #493424; font-size: .95rem; }
    .meta { margin-top: 1.2rem; border-top: 1px solid #45606b; padding-top: .8rem; color: #bfd2d8; font-size: .86rem; }
    details { margin-top: .45rem; } summary { cursor: pointer; }
    table { border-collapse: collapse; width: 100%; margin-top: .45rem; }
    td, th { border-bottom: 1px solid #45606b; padding: .42rem .3rem; text-align: left; vertical-align: top; }
    code { overflow-wrap: anywhere; }
    a { color: #8de1dd; }
    @media (max-width: 800px) { .cards, .rule { grid-template-columns: 1fr; } }
    @media print { :root { color: #142b35; background: white; } .banner { print-color-adjust: exact; } .card, .rule article, .limit { print-color-adjust: exact; } }
  </style>
</head>
<body>
  <div class="banner">SIMULATED CANDIDATE — P0 QUEUE UNDER REVIEW</div>
  <main>
    <div class="topline">Ripple / Tuen Mun / IN-26-02615 / 15 April 2026</div>
    <h1>Target the detour. Don’t broadcast it.</h1>
    <p class="lede">Frozen Lead plans compared on the same Tuen Mun incident replay: 3 fresh seeds × 3 compliance settings × 2 signal designs = 18 matched cells.</p>
    <section class="cards" aria-label="Three simulated plans">
      <article class="card">
        <div class="planid">P0 · REFERENCE</div><h2>Do nothing</h2>
        <p class="number neutral">0%</p>
        <p class="metric">Reference for modelled vehicle-hours of delay</p>
        <p class="small">No added route advice. The incident replay retains its saved demand and route assumptions.</p>
      </article>
      <article class="card">
        <div class="planid">P1 · BROADCAST</div><h2>Advise everyone</h2>
        <p class="number bad">$p1_delta</p>
        <p class="metric">Mean E delay difference vs P0 · worse in $p1_worse of $cell_count cells</p>
        <p class="small">One Castle Peak Road alternative advised to 100% of the eligible group. 95% paired interval: $p1_interval.</p>
      </article>
      <article class="card best">
        <div class="planid">P2 · TARGETED CANDIDATE</div><h2>Advise 11%</h2>
        <p class="number good">$p2_delta</p>
        <p class="metric">Mean E delay difference vs P0 · lower in $p2_lower of $cell_count cells</p>
        <p class="small">Same route, limited advice. 95% paired interval: $p2_interval. With the longer drive charged and a 4-minute outside-network assumption: $charged_delta.</p>
      </article>
    </section>
    <section class="rule" aria-label="Decision rule comparison">
      <article><h2>Team ranking rule</h2><p>The saved 13 Oct rule ranks P2 before both P0 and P1: its paired 95% interval is below zero across all 18 counting cells. This is a <strong>model ranking</strong>, not a road-validated benefit.</p></article>
      <article><h2>Stricter Tuen Mun protocol</h2><p>The predeclared every-cell rule does <strong>not</strong> pass: P2 is higher than P0 in one of 18 cells. The team rule was applied to this grid after the runs; both readings must stay visible.</p></article>
    </section>
    <p class="limit"><strong>Baseline limit:</strong> P0 passes headline validation v2 on these seeds, but its queue moves too fast, clears early and discharges too much after reopening. Simulation has not accepted it for a measured saving or an operator-ready recommendation.</p>
    <footer class="meta">
      Saved grid: <code>$grid</code>. Percentages compare paired modelled delays, not simulation against observed road delay. The E-delay ranking does not include the longer Castle Peak Road drive; the separate 4-minute sensitivity above does. No live inference or evaluator run was used to build this page.
      <details><summary>Source files and raw-byte SHA-256</summary><table><thead><tr><th>Source</th><th>SHA-256</th></tr></thead><tbody>$source_rows</tbody></table></details>
    </footer>
  </main>
</body>
</html>
""")


def render(bundle):
    rows = "".join(
        f'<tr><td><a href="../../{h(relative)}">{h(label)}</a><br><code>{h(relative)}</code></td>'
        f'<td><code>{h(bundle["hashes"][label])}</code></td></tr>'
        for label, relative in SOURCES.items()
    )
    ranking = bundle["ranking"]
    p1_low, p1_high = bundle["p1_vs_p0_interval"]
    p2_low, p2_high = bundle["p2_vs_p0_interval"]
    return HTML.substitute(
        p1_delta=f'+{bundle["p1_vs_p0_pct"]:.1f}%',
        p1_worse=next(p["cells_a_lower"] for p in ranking["pairs"] if (p["a"], p["b"]) == ("P0", "P1")),
        p1_interval=f'+{p1_low:.1f}% to +{p1_high:.1f}%',
        p2_delta=f'{bundle["p2_vs_p0_pct"]:.1f}%',
        p2_lower=bundle["p2_lower_cells"],
        p2_interval=f'{p2_low:.1f}% to {p2_high:.1f}%',
        charged_delta=f'{bundle["detour_charged_pct"]:.1f}%',
        cell_count=len(ranking["cells"]),
        grid=h(ranking["grid"]),
        source_rows=rows,
    )


def build(out=DEFAULT_OUT, root=ROOT):
    """Write a new capture; never silently replace a reviewed frame."""
    page = render(read_bundle(root))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as target:
        target.write(page)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="New HTML path; existing captures are never overwritten")
    args = parser.parse_args()
    print(build(args.out))


if __name__ == "__main__":
    main()
