# Interim Report Skeleton — Project Ripple

> **Internal Submission Target:** Saturday 3 October 2026  
> **Official Deadline:** Sunday 4 October 2026

---

## 1. Executive Summary & Social Problem Statement
- **Owner:** Impact
- **Primary Source Alignment:** `docs/00-brief.md` (Section 2), `docs/05-pitch.md` (Sections 1 & 3)
- **Content:**
  - Clear statement of Hong Kong's non-recurring congestion problem, focusing on critical corridors like Aberdeen.
  - Limits of individual user-equilibrium routing apps vs. system-optimum corridor management.
  - Social and economic impacts (delays to emergency services, public transit, freight).

## 2. Preliminary Idea & System Architecture
- **Owner:** Lead
- **Primary Source Alignment:** `docs/03-architecture.md` (Section 1), `docs/00-brief.md` (Section 4)
- **Content:**
  - Overview of Ripple’s architecture, ingestion pipelines (TD open feeds, detector loops), and incident processing.
  - Human-in-the-loop workflow and real-time candidate plan generation.

## 3. Feasibility, Preliminary Results & Cost-Benefit Framework
- **Owner:** Impact
- **Primary Source Alignment:** `docs/05-pitch.md` (Section 6)
- **Content:**
  - Costing structure and Benefit-Cost Ratio (BCR) framework using HK Value of Time benchmarks.
  - Note: Unmeasured simulation numbers flagged explicitly as *[not measured yet]* per evaluation guidance.

## 4. Sustainability, Ethics & User Validation
- **Owner:** Impact (with Simulation reviewing validation wording)
- **Primary Source Alignment:** `docs/05-pitch.md` (Section 5), `evidence/interviews/2026-09-26-minibus-driver.md`
- **Content:**
  - Distributional fairness, privacy compliance, and system sustainability.
  - Empirical qualitative evidence from primary research interviews (e.g., minibus driver insights on official alert delays and peer verification).
- **Owner:** Teammate 4 (Ethics & Evidence Lead)
- **Content:**
  - Summary of real user interview insights (`evidence/interviews/`).
  - Distributional fairness metrics (preventing traffic spillover into residential streets).
  - Privacy compliance (zero personal data tracking) and per-corridor confidence score rules.
