# Interim Report Skeleton — Project Ripple

> **Internal Submission Target:** Saturday 3 October 2026
> **Official Deadline:** Sunday 4 October 2026

---

## 1. Executive Summary & Social Problem Statement
- **Owner:** Project Lead
- **Content:**
  - Clear statement of Hong Kong's non-recurring congestion problem, focusing on critical corridors like Aberdeen.
  - The limits of individual user-equilibrium routing apps vs. system-optimum corridor management.
  - Key social and economic impacts (delays to emergency services, public transit, and freight).

## 2. Data Ingestion & Real-Time Incident Parsing
- **Owner:** Data Lead
- **Content:**
  - Overview of Ripple’s data ingestion pipeline (TD open feeds, detector loops, incident reader).
  - Processing bilingual (Chinese/English) Transport Department incident reports into structured feeds.

## 3. Simulation & Digital Twin Validation
- **Owner:** Simulation Lead
- **Content:**
  - The SUMO digital twin setup and LLM-driven candidate response plan generator.
  - Baseline vs. plan simulation comparison methodology and validation metrics.

## 4. Human-in-the-Loop Operator UI & Visuals
- **Owner:** Visuals Lead
- **Content:**
  - Operator console interface design for reviewing and approving candidate response plans.
  - Visualisation of real-time corridor status, confidence levels, and bilingual VMS message previews.

## 5. Feasibility, Sustainability, Ethics & Impact Framework
- **Owner:** Impact Lead
- **Content:**
  - Costing structure for a single corridor rollout (compute, storage, maintenance hours).
  - Framework for Benefit-Cost Ratio (BCR) using HK Value of Time benchmarks.
  - Distributional fairness metrics, privacy compliance, and user validation evidence (`evidence/interviews/`).
- **Owner:** Teammate 4 (Ethics & Evidence Lead)
- **Content:**
  - Summary of real user interview insights (`evidence/interviews/`).
  - Distributional fairness metrics (preventing traffic spillover into residential streets).
  - Privacy compliance (zero personal data tracking) and per-corridor confidence score rules.
