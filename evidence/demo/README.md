# Recorded B/D evidence page — 13 October 2026 HKT

`recorded-genai-bd-2026-10-13.html` is a single-file, offline capture aid for
the archived bilingual incident messages, saved Reader extractions and saved
P0/P1/P2 model candidates. It contains inline CSS, no external assets and no
live inference. Keep its visible status banner in screenshots. The joint
incident P0 decision is NO-GO; these plans have no accepted benefit result.

Open on Windows from the repository root:

```powershell
Invoke-Item -LiteralPath evidence/demo/recorded-genai-bd-2026-10-13.html
```

Rebuild into a **new** path from the repository root (the exporter refuses to
overwrite an earlier capture):

```powershell
.\.venv\Scripts\python.exe -m scripts.build_genai_evidence --capture-date 2026-10-13 --out evidence/demo/recorded-genai-bd-2026-10-13-rebuild.html
```

The exporter selects one record for each specified message/call ID and fails
if a record is missing or duplicated. It compares the saved Reader output to
the corresponding logged response and revalidates the D response with the
existing constraint code before comparing it to the saved candidate files.
Only code-added `constraints_checked` fields may differ. Source text is HTML
escaped. No original evidence is rewritten.

Raw-byte SHA-256 at page creation:

| Repository-relative source | SHA-256 |
| --- | --- |
| `data/demo_incident_messages.jsonl` | `b76366fc278f08ed81a3d8dbfe2d3007792236130ae56d386e5cce108e2750fe` |
| `results/reader/2026-09-29T1608_qwen3-8b.jsonl` | `3b015de2169bdc5de034bbce6b1c7b76ea212a59b4f0a8f6e178aeae86be4464` |
| `evidence/ai-log/2026-09-29.jsonl` | `87fc40388dcc6ad9a120b6f277dd71e14f9baa8baa890d3eb8f6a19678cea56d` |
| `data/plan-context/IN-26-03365_first-report-v2.json` | `fe6c708905d9b2e29f2da603a290762142199ec94ff5e95a7573ec785e0f8d18` |
| `data/plan-context/IN-26-03365_first-report-v2.md` | `25f19269644104286f4ad16288fefda2810d20f75d0625c53273b7056a5dab91` |
| `data/generated-plans/IN-26-03365-lead-draft-20261013-b/generation-inputs.json` | `8726acd9be7023a9483f3e46128fa172abb6bebf5f1361970194144d904f33a1` |
| `data/generated-plans/IN-26-03365-lead-draft-20261013-b/P0.json` | `4198ec674296e0a1413b3ef3d0758fdf3e60124afbe9d51728b912b69ed898ff` |
| `data/generated-plans/IN-26-03365-lead-draft-20261013-b/P1.json` | `dae8a9c06f0e7d34b77407193ff36eb1d814311b8a8d0739fe508190da27dade` |
| `data/generated-plans/IN-26-03365-lead-draft-20261013-b/P2.json` | `3afc8b638a7abd2d9a290541d07032ab9a9f269fa4196c14f479ef7284eea20c` |
| `evidence/ai-log/2026-10-13.jsonl` | `49dc7e73209d56de1987d904253e8c5f8646200f2726162cccc92ad6203572d6` |
| `docs/lead-genai-handoff-2026-10-13.md` | `bf18ea4dada8d5197aa478f99e7d1e27229d7650ff251054664d9e7d72083704` |

Generated HTML SHA-256:
`46b4d6d4cbe65f3c5a1b54a9ada18ab5db394df38b24c9e86bc49f4f53e7a195`.
The full source table is also embedded in the page. These checksums show file
identity; they do not validate the incident simulation or the proposal's
effectiveness. The [current Lead status](../../docs/lead-genai-follow-up-2026-10-13.md)
records F separately. This page is neither recorded video nor a finished deck.
