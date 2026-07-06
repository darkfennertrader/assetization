---
title: "Aegon AI Lighthouses — Effort Estimates & Recommendation"
classoption: landscape
header-includes:
  - \setlength{\parskip}{3pt}
  - \setlength{\parindent}{0pt}
---

\footnotesize
*PwC roles — **SA**: Solution Architect · **Eng**: Backend engineer (Python/agent) · **FE**: Frontend engineer (React/Teams) · **Data**: Data engineer (Databricks) · **UX**: UX & change*

*Aegon roles — **IR SME**: IR director/senior manager (~1 day/wk; validates Q&A accuracy) · **Reporting SME**: Group Reporting lead · **Gov owner**: Document governance owner (LH2)*

***PoC** = static data, dev tenant, demo only — not shippable. **MVP** = real data, 5-15 pilot users, production Azure with auth + observability.*
\normalsize

## Per-Lighthouse Estimates

\footnotesize

| Lighthouse | PoC | PoC team | MVP | MVP team | Key blocker |
|---|---|---|---|---|---|
| **LH1 - IR Agent** | 4-6 wks | SA / 2 Eng / 1 FE | 12-14 wks | SA / 2 Eng / 1 FE / 0.5 UX / IR SME | Teams Live Transcription API; CEO/CFO test availability |
| **LH2 - Knowledge Base** | 3-4 wks | SA / 1 Eng / 1 FE | 10-12 wks (+Aegon pre-work) | SA / 2 Eng / 1 Data / 1 FE / Gov owner | **Doc governance must be resolved by Aegon first (4-8 wks Aegon-side)** |
| **LH3 - Anomaly Detection** | 3-4 wks | SA / 1 Data / 1 FE | 10-12 wks | SA / 2 Data / 1 Eng / 0.5 UX / Reporting SME | Tagetik data access; threshold sign-off with country units |

\normalsize

**Shared Substrate** (Entra / APIM / LLM / observability / CI gate): **4-5 weeks** — 1 SA + 1 platform Eng + 1 DevOps + 0.5 InfoSec. Runs **in parallel with PoCs** — zero extra elapsed time.

## Recommendation: Start with LH3, Scenario B

Start with **LH3 (Anomaly Detection)** for three reasons:

1. **Clearest KPI** — replaces a daily manual Tagetik scan with an automated briefing; measurable from day one.
2. **No live-user risk** — unlike LH1, no CEO/CFO availability dependency or real-time transcription API approval needed.
3. **No document governance blocker** — unlike LH2, no document classification or approval workflow pre-work required from Aegon. (LH3 does require a Tagetik data access agreement, but this typically resolves in 2-4 weeks vs 4-8 weeks for LH2 document governance.)

**Recommended sequence:**

- **W1-4** — Shared Substrate + LH3 PoC (SA / 1 Data / 1 FE)
- **W5-14** — LH3 MVP to pilot (SA / 2 Data / 1 Eng / 0.5 UX / Reporting SME)
- **W6-10** — LH1 PoC runs in parallel (SA shared / 2 Eng / 1 FE)
- **W8+** — Aegon completes LH2 doc governance (Aegon-side)
- **W12-24** — LH1 MVP + LH2 MVP staggered builds
- **W24-28** — All 3 MVPs in pilot

\footnotesize
*Figures are indicative; revised on detailed requirements confirmation. LH2 Aegon governance pre-work not included in PwC elapsed time.*
