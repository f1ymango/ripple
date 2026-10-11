# Costing & Financial Feasibility Analysis

## 1. Resource questions for a deployment estimate

| Component | Prototype choice | Evidence needed for a monthly estimate |
| :--- | :--- | :--- |
| **Reader (LLM)** | Local Qwen3-8B | Hardware price, power/hosting, model-call volume and support time |
| **Digital twin (SUMO)** | Local batch runs | Validated run frequency, CPU time, hosting price and storage |
| **Data storage and pipeline** | Archive/cache plus logs | Retention period, data volume, hosting and maintenance |

No deployed configuration or measured operating cost is available. The earlier
USD 300–600/month range lacked a price or usage source and is withdrawn.

---

## 2. Benefit-Cost Ratio (BCR) Summary

| Metric | Status / Value | Source / Traceability |
| :--- | :--- | :--- |
| **Operational infrastructure cost** | Not measured | Requires a priced deployment configuration |
| **Delay savings ($ value)** | No accepted benefit claim | Incident P0 and plan comparison remain unaccepted |
| **CO₂ reduction benefits ($ value)** | No accepted benefit claim | Incident P0 and plan comparison remain unaccepted |
| **Benefit-cost ratio (BCR)** | Not calculated | Requires sourced costs and accepted benefits |

---

## 3. Financial Feasibility Governance Rules

1. **No Speculative Benefit Calculations**: Benefit-Cost Ratio must **not** be calculated using partial, pre-incident, or unvalidated simulation metrics.
2. **Freeze Boundary Alignment**: The 14 Oct freeze locks supported figures. If the incident comparison remains unaccepted, financial return claims stay out of the submission.
