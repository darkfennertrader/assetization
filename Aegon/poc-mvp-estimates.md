---
title: "Aegon AI Lighthouses — PoC & MVP Effort Estimates"
classoption: landscape
header-includes:
  - \setlength{\parskip}{2pt}
  - \setlength{\parindent}{0pt}
---

**PoC** = static data, dev tenant, demo only — not shippable. **MVP** = real data, 5-15 pilot users, production Azure with auth + observability.

\footnotesize
*PwC roles — **SA**: Solution Architect · **Eng**: Backend engineer (Python/agent) · **FE**: Frontend engineer (React/Teams) · **Data**: Data engineer (Databricks) · **UX**: UX & change · **FTE**: Full-Time Equivalent*

*Aegon roles — **IR SME**: IR director/senior manager (~1 day/wk; validates Q&A accuracy) · **Reporting SME**: Group Reporting lead · **Gov owner**: Document governance owner (LH2)*
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

## Delivery Scenarios

\footnotesize

| Scenario | Scope | Elapsed | Peak team | Best for |
|---|---|---|---|---|
| **A - All 3 PoCs in parallel** | 3 PoCs, dev-only, no substrate | **6 wks** | 8 FTE | Quick go/no-go decision |
| **B - Substrate + 1 MVP** *(recommended)* | Substrate + LH3 PoC to pilot | **14-16 wks** | 7 FTE | First real value on real users before year-end |
| **C - All 3 MVPs staggered** | Substrate + all 3 in pilot | **24-28 wks** | 12 FTE | Full programme; change-management from week 1 |

\normalsize

## Recommendation: Scenario B, lead with LH3

Start with **LH3 (Anomaly Detection)** — clearest KPI (manual Tagetik scanning -> automated daily briefing), no live-user risk (unlike LH1), no document governance blocker (unlike LH2; LH3 still requires a Tagetik data access agreement, typically 2-4 wks). While LH3 MVP runs (W5-14), Aegon completes LH2 governance and LH1 PoC starts (W6-10). All 3 MVPs in pilot by W24-28.

\footnotesize
*Assumes 2 Eng + 1 FE per pod. LH2 Aegon governance pre-work not in PwC elapsed time. Figures indicative; revised on requirements confirmation.*

\newpage

## How Peak Team Is Calculated

**Peak team** = the maximum number of full-time-equivalent (FTE) people working *concurrently in any single week* of the scenario. It is **not** cumulative person-weeks (cost); it is the number you need to staff the programme at its busiest point.

### Scenario A — All 3 PoCs in parallel (peak week 1-6)

\footnotesize

| Pod | Roles active at the same time | FTE |
|---|---|---|
| LH1 PoC | 1 SA (shared) + 2 Eng + 1 FE | 4.0 |
| LH2 PoC | *(SA shared from LH1)* + 1 Eng + 1 FE | 2.0 |
| LH3 PoC | *(SA shared)* + 1 Data + 1 FE | 2.0 |
| **Peak** | | **8 FTE** |

\normalsize

The SA is counted once (shared across pods), not three times.

### Scenario B — Substrate + LH3 MVP (peak weeks 8-12)

\footnotesize

| Team | Roles at peak | FTE |
|---|---|---|
| LH3 MVP build | 1 SA + 2 Data + 1 Eng + 0.5 UX | 4.5 |
| Substrate tail | 1 Platform Eng + 0.5 DevOps + 0.2 InfoSec | 1.7 |
| PM / delivery overhead | | 0.5 |
| Aegon Reporting SME (~1 day/wk) | | 0.2 |
| **Peak** | | **~7 FTE** |

\normalsize

Aegon SMEs are included for completeness but are not PwC-billable headcount.

### Scenario C — All 3 MVPs staggered (peak weeks 14-20)

\footnotesize

| Team | Roles at peak | FTE |
|---|---|---|
| LH3 pilot maintenance | 0.5 SA + 1 Data + 0.5 DevOps | 2.0 |
| LH1 MVP full build | 1 SA + 2 Eng + 1 FE + 0.5 UX | 4.5 |
| LH2 MVP starting | 1 Eng + 1 Data + 1 FE | 3.0 |
| Shared substrate / obs | 0.5 Platform + 0.3 InfoSec | 0.8 |
| PM / delivery overhead | | 1.0 |
| Aegon SMEs (~1 day/wk each) | | 0.4 |
| **Peak** | | **~12 FTE** |

\normalsize

### Staffing caveats

- **Real bodies on roster** = approx. peak FTE / 0.8 (PwC standard 80% chargeable utilisation). 12 FTE peak -> ~15 people rostered.
- **SA is shared** across active lighthouse pods in all scenarios; if Aegon requires dedicated per-pod SA, add 1-2 FTE.
- **Ramp-up**: team grows from ~3 FTE in week 1 to peak, then tapers in the pilot/hypercare phase. Peak is for staffing feasibility checks; use a week-by-week burn for cost modelling.
- **Aegon-side effort** (SMEs, governance owner, IT ops, IR director) is excluded from PwC cost but must be planned separately by Aegon.
