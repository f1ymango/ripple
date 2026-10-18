# scripts/

One-off builders that turn saved results into presentable artifacts. They read
from `results/` and `data/`; they do not change frozen results.

| Script | What it builds |
|---|---|
| [`demo_pack.py`](demo_pack.py) | Packages each demo incident's main cell, plans, ranking and console verdict into [`results/demo-oct16/`](../results/demo-oct16/) |
| [`build_genai_evidence.py`](build_genai_evidence.py) | The offline recorded Reader page in [`evidence/demo/`](../evidence/demo/README.md) |
| [`build_tuen_mun_result_card.py`](build_tuen_mun_result_card.py) | The Tuen Mun result card |
| [`tuen_mun/`](tuen_mun/) | Tuen Mun network, demand, detector and report builders ([Tuen Mun replay](../docs/tuen-mun-2026-10-14.md)) |
