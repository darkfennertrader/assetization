---
title: "Aegon AI Lighthouses — Use Case Summary"
subtitle: "Investor Relations Agent · Historical Knowledge Base · Data Anomaly Detection"
author: "Raimondo Marino, Solution AI Architect"
date: "2026-07-01"
source: "PwC / Strategy& — Aegon AI Acceleration Proposal, 17 June 2026"
---

# Aegon AI Lighthouses — Use Case Summary

> **Client:** Aegon (Finance function)
> **Context:** PwC / Strategy& is proposing five AI Lighthouses for Aegon's Finance function as the foundation of a broader AI-enabled operating model. Three have working demos. This document summarises the three use cases relevant to the assetization and architecture work: Investor Relations Agent (LH 1), Historical Knowledge Base (LH 2), and Data Anomaly Detection (LH 3).

---

## Lighthouse 1 — Investor Relations Agent

**Pages 8–9 | Primary users:** IR team NL, CEO, CFO (potential scale to TA IR team)

### Problem being solved

- Preparing for investor calls is manual and time-consuming — collecting prior questions, drafting answers, anticipating shareholder focus areas all happen ad-hoc.
- During live calls, responding to unexpected questions is slow; there is a gap between the prepared Q&A deck and the reality of what gets asked.
- Institutional knowledge of the IR team (what specific analysts care about, what was said in prior calls) is not systematically captured and is lost when people leave.

### What the agent does

| Capability | Description |
|---|---|
| **Call preparation** | Collects previously asked questions, organises them by investor/analyst, flags when a specific party frequently asks on a specific topic, surfaces all relevant materials in one portal workspace |
| **Sentiment profiling** | Analyses prior call recordings and transcripts to profile each analyst's sentiment and likely questions — helps CEO/CFO anticipate focus areas |
| **Live Q&A** | During the call, recognises spoken questions (voice) and written questions (chat); responds with a prepared answer from the deck, or formulates a new one in real time, verifiable against the portal |
| **Knowledge capture** | After each call, files structured call notes and answers back to the portal — preserving IR knowledge in a reusable, searchable form |
| **Tone awareness** | Adapts formulated responses to the tone of voice of the CEO or CFO speaking on the call |

### Data inputs

- **Internal:** previous Q&A decks, previously asked non-deck questions and responses, call recordings/transcripts
- **External:** all externally published company information from current and comparative reporting periods

### Key benefits

- Increased call readiness for CEO/CFO (specific to the investor/analyst on the call)
- Speed + completeness + quality of live response — with human in the loop
- Documents tacit IR knowledge in a structured, transferable way
- Solution is transferable to future IR team (including US/Transamerica post-Magnolia)

### Key risks

- Privacy / compliance of voice recognition during live calls (requires attendee consent)
- Risk of generic or outdated responses — must be constrained to recent, relevant data
- Zero-hallucination requirement: every response must be instantly verifiable
- Limited availability of key end-users (CEO, CFO, IR director) for testing

### Demo walkthrough (page 9)

1. **Calendar** flags upcoming investor calls and surfaces preparation materials in one portal workspace
2. **Sentiment Checker** profiles each analyst's prior-call history and likely question focus areas
3. **Live Q&A** serves prepared answers or formulates new ones in real time, with a human-in-the-loop verification step
4. **Knowledge filing** stores call notes and answers back to the portal in a structured, reusable format

### Teams integration decision

**Pattern B — Meeting Side Panel App** is the chosen integration. Full details: `Aegon/lh1-teams-integration.md`.

- The **Teams Live Transcription API** (Microsoft-hosted, diarized) does the in-call STT — not Azure AI Speech. Teams Premium licence required at Aegon.
- A **Meeting Side Panel App** (Teams SDK v2 / Fluent UI React) runs inside the Teams meeting window and shows the suggested answer + citations to the CEO/CFO.
- **TTS is permanently out of scope.** The agent produces text only; the CEO/CFO reads and speaks the answer. No AI voice on an earnings call — ever.
- **Azure AI Speech** is retained for **post-call batch transcription** (archive path only): Teams recording → Blob → batch STT → AI Search LH1 index.

### Architecture notes (ARA-A mapping)

| Component needed | ARA-A service / pattern |
|---|---|
| **In-call STT** | Teams Live Transcription API (Microsoft-hosted, diarized) — no Azure Speech for live calls |
| In-meeting UX for CEO/CFO | Teams Meeting Side Panel App (ACA-hosted BFF + Teams SDK v2) |
| Speaker identification (analyst vs. Aegon) | Teams meeting roster API (comes with Live Transcription events) |
| Q&A document retrieval (RAG, cited) | Azure AI Search (hybrid) + `/rag` MCP tool |
| Analyst sentiment / profile lookup | `/sentiment` MCP tool → Cosmos DB (analyst profiles) |
| Live answer synthesis | Azure OpenAI GPT-4o via APIM AI Gateway |
| HITL gate (answer shown, human speaks) | LangGraph interrupt node → Teams Side Panel [Use / Skip / Edit] buttons |
| **Post-call archive STT** | Azure AI Speech batch (recording → Blob → transcript → AI Search) |
| Post-call knowledge capture | Cosmos DB (call notes) + Logic Apps (Graph API → Blob copy) |
| Observability | LangSmith traces + App Insights |
| TTS | ❌ **Not present — explicitly excluded** |

---

## Lighthouse 2 — Historical Knowledge Base

**Pages 10–11 | Primary users:** Future US Group Finance teams, FR&O, Reporting, FP&A, Accounting Policy, new joiners, country units

### Problem being solved

- Critical Group Finance knowledge (reporting instructions, design documents, position papers, accounting treatments, press release Q&A packs, project decisions) is scattered across SharePoint, Teams, emails, shared folders, and individual memory.
- As Aegon relocates Group Finance activities to the US (Project Magnolia), this knowledge is at risk of being lost — new US-based teams face a steep learning curve.
- Manually searching for a prior reporting treatment, an approved decision rationale, or a historical instruction takes hours and depends on knowing the right person to ask.

### What the agent does

| Capability | Description |
|---|---|
| **Unified repository** | Ingests approved docs, emails, and Teams notes into a single searchable knowledge base |
| **Natural-language Q&A** | Answers questions in plain language: "What was the rationale for this reporting treatment?", "Where is the latest approved guidance on X?", "How was this item handled in previous cycles?" |
| **Source tracing** | Every answer is linked to the original approved source document — no answer without a citation |
| **Project knowledge** | Surfaces open questions with sourced draft answers and review actions for ongoing projects |
| **External enrichment** | External feeds (benchmarks, regulatory updates) can enrich the knowledge base, kept clearly separate from internal Aegon data |
| **Role-based access** | Selected users get role-based access depending on data sensitivity |

### Data inputs

- **Internal:** reporting instructions, design documents, position papers, accounting papers, internal memos, press release documentation, Q&A reporting packs, Internal Financial Supplement, historical project documentation (decisions, meeting materials, issue logs, sign-off docs), SharePoint/Teams/shared folder documentation (subject to access rights and data classification), document metadata (owner, reporting period, approval status, version number)
- **External:** regulatory publications, market benchmarks (kept clearly separate from internal data)

### Key benefits

- Preserves critical Group Finance knowledge through the relocation and team transition
- Single access point for approved historical documentation and decisions
- Reduces dependency on individual knowledge holders
- Accelerates onboarding of new teams and new joiners
- Improves consistency in interpreting reporting requirements and past decisions
- Saves significant time currently spent manually searching

### Key risks

- **Completeness and quality** of historical documentation — garbage in, garbage out
- **Outdated or non-approved** documents being used as source material (governance of what enters the knowledge base is critical)
- **Access restrictions** — sensitive financial information must respect existing data classification
- **Relevance / hallucination** — if source data is not well curated, AI may return irrelevant or overly broad answers
- Dependency on: data classification, tagging, version control, and retention rules being in place before ingestion

### Demo walkthrough (page 11)

1. **Repository** — unites approved docs, emails, and Teams notes in one searchable place
2. **Ongoing projects** — shows open questions with sourced draft answers and review actions
3. **Plain-language Q&A** — ask a question, get an answer with its approved source citations
4. **External feeds** — enriches internal knowledge with external data, kept clearly labelled as external

### Architecture notes (ARA-A mapping)

This lighthouse is the closest match to the **Knowledge Base** product in the ARA-A three-product model, and to Research pattern **B5 (Lakehouse as backend for agents)** and **A6 (Document processing accelerator)**.

| Component needed | ARA-A service |
|---|---|
| Document ingestion pipeline | Azure Document Intelligence (OCR) → Blob Storage → DLT pipeline |
| Vector embeddings + search | Azure AI Search (hybrid) or Mosaic AI Vector Search on Delta Lake |
| Source-linked RAG | `/rag` MCP tool with citation metadata preserved |
| Role-based data isolation | Unity Catalog row-level security (if Databricks) or AI Search row-level filter |
| Approval status metadata | `asset.toml`-style document metadata; Microsoft Purview for lifecycle |
| Natural-language Q&A interface | Foundry Agent Service or LangGraph RAG agent |
| External feed separation | Separate index with clear `source_type: external` metadata flag |
| Audit (who asked what) | App Insights custom events + Event Hub → ADLS Gen2 |

> **Note for PwC delivery:** The document governance problem (ensuring only approved, current documents enter the knowledge base) is not a technology problem — it is a **process and ownership problem**. The data classification, version control, and approval workflow must be resolved with Aegon before the technical build starts. This is the highest-risk dependency for LH 2.

---

## Lighthouse 3 — Data Anomaly Detection

**Pages 12–13 | Primary users:** Group Reporting team (FR&O), country/reporting units, optionally Reporting team Transamerica**

### Problem being solved

- During the financial close, the Group Reporting team manually checks Tagetik data dumps for integrity issues — this is time-consuming, limited to a single expert (doesn't scale), and only happens during the close window.
- The manual review approach is judgement-based, making it hard to hand over, onboard new team members, or extend to units.
- There is no consistent, automated way to compare the current period's data against the prior quarter and flag deviations above a threshold.

### What the agent does

| Capability | Description |
|---|---|
| **Automated report download** | Copilot downloads Tagetik data dump report(s) on a scheduled basis (daily during close) |
| **Quarter-on-quarter comparison** | Compares current period data against the previous quarter for each reporting unit |
| **Threshold-based anomaly flagging** | Flags data points that exceed defined thresholds; thresholds can be set flexibly per unit |
| **Anomaly summary + daily email** | Creates a summary of anomaly data and sends it per email daily — reviewers receive a structured daily briefing |
| **Overview dashboard** | Shows KPIs, anomaly charts, and a live action overview |
| **Drill-down + evidence** | Report view with adjustable thresholds and the ability to drill into a flagged anomaly and view its underlying evidence |
| **Action dispatch** | Reviewer can assign and dispatch a follow-up action, generating an automated email; the human reviewer stays in control at all times |
| **Self-learning (future option)** | AI generates its own additional analysis commentary based on patterns observed over time |
| **Extensibility** | Can extend beyond Tagetik to other data sets |

### Data inputs

- **Internal:** Tagetik data dump report or other specific reports; configurable thresholds (per unit, per metric)

### Key benefits

- **Efficiency + effectiveness:** frees team from daily manual data review; reviewer focuses on confirmed anomalies, not scanning
- **Speed:** ad-hoc analyses can be run immediately on request
- **Consistency:** same review approach applied by all country-unit reviewers (no more judgement variance)
- **Scalability:** solution is transferable to future reporting teams and to Transamerica

### Key risks

- Requires similar Tagetik setup (or equivalent in future Oracle solution) to scale to Transamerica
- **Adoption:** teams accustomed to manual review may resist; change management required especially when extending to units
- Resource availability during the close period (the busiest time is when the agent is most needed)

### Demo walkthrough (page 13)

1. **Daily summary email** — anomalies flagged overnight, actions ready to dispatch
2. **Overview dashboard** — KPIs, anomaly charts, and live action overview
3. **Report view** — adjustable thresholds, drill-down into a flagged anomaly with its evidence
4. **Action dispatch** — reviewer assigns and sends follow-up; reviewer stays in control throughout

### Architecture notes (ARA-A mapping)

This lighthouse maps to Research pattern **A3 (APIM AI Gateway) + A6 (Document/Data pipeline)** for data ingestion, and **B1 (Mosaic AI Agent Framework)** if Databricks holds the Tagetik data.

| Component needed | ARA-A service |
|---|---|
| Scheduled data download (Tagetik) | Azure Logic Apps or Databricks Workflow (scheduled trigger) |
| Data comparison + anomaly logic | Python agent (LangGraph node) or Databricks SQL + PySpark |
| Threshold configuration store | Cosmos DB or Azure Table Storage (per-unit thresholds) |
| Anomaly detection logic | Statistical z-score / percentage-deviation check in Python; upgradeable to ML |
| Daily summary email | Azure Logic Apps → SendGrid / Azure Communication Services |
| Dashboard | Power BI Embedded (on Log Analytics or Databricks SQL) |
| Drill-down evidence view | Azure AI Search or Delta table query via Genie Space |
| Action dispatch | Azure Logic Apps workflow triggered from dashboard action button |
| Observability / audit | App Insights (all agent runs logged) + Event Hub → ADLS Gen2 (immutable) |
| Human-in-the-loop control | Reviewer must approve action before dispatch — hard gate, not optional |

> **Note for PwC delivery:** The "adjustable thresholds per unit" feature is a strong adoption driver — it respects country-unit autonomy. Prioritise this in the prototype. The "self-learning comments" (AI generates its own analysis) is a Phase 2 feature; do not build it in the prototype — it introduces hallucination risk in a high-stakes close context.

---

## Cross-lighthouse patterns — reuse opportunities

All three lighthouses share common technical building blocks. These are the assets that should be **built once and reused**, aligned with the ARA-A Marketplace:

| Shared component | Lighthouses that use it | ARA-A CORE asset |
|---|---|---|
| Document ingestion + OCR pipeline | LH 2, (LH 1 for call transcripts) | `/extract` MCP tool |
| RAG with source citation | LH 1 (Q&A deck), LH 2 (knowledge base) | `/rag` MCP tool |
| Natural-language Q&A interface | LH 1, LH 2 | LangGraph RAG node |
| Structured data comparison (quarter-on-quarter) | LH 3 | Python data-transformer snippet |
| Scheduled trigger + email dispatch | LH 3 | Azure Logic Apps template (WRAPPER asset) |
| Threshold configuration store | LH 3 (extendable to LH 4 FTA, LH 5) | Cosmos DB config component |
| Human-in-the-loop gate | LH 1 (live Q&A verify), LH 3 (action approve) | LangGraph interrupt node |
| Role-based data isolation | LH 2 (sensitive finance docs) | Auth wrapper + UC/AI Search row filter |
| Observability + audit log | All | App Insights + Event Hub → ADLS Gen2 |

**Recommendation:** extract the RAG-with-citation component and the HITL gate from LH 1 before starting LH 2 — they are the highest-reuse items and will save significant build time on subsequent lighthouses.

---

## Delivery sequencing (from the proposal)

The proposal runs a 7-week Design & Preparation phase with lighthouses developed iteratively:

| Week | Milestone |
|---|---|
| W1–W2 | Outside-in design: starter requirements + visual prototype for all 5 lighthouses |
| W3–W4 | Refinement workshops with Aegon stakeholders; prototype updated |
| W5–W6 | Detailed design + go-live plan; finalised requirements and prototypes |
| W6 | Aegon builders can kickstart implementation |
| W7–W8 | Regroup and re-accelerate |

All three lighthouses summarised here have **demos already available** as of the proposal date.

---

*Source: PwC / Strategy& — Aegon AI Acceleration Proposal, 17 June 2026. Summarised by Raimondo Marino, Solution AI Architect, 2026-07-01.*
