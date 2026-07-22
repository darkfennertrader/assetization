---
title: "Aegon Finance AI Lighthouses: Use Case Summary"
---

## Programme Context

Aegon is building five AI lighthouses in its Group Finance function to prove
value, build internal AI capability, and create reusable foundations that
will scale across the organisation. The initiative runs in parallel with
Project Magnolia, the relocation of Group Finance activities to Transamerica
in the United States.

PwC Strategy& is engaged for a 7-week design and preparation phase (July to
August 2026) at EUR 100,000 per lighthouse. The technical delivery platform
is the Aegon Launchpad: an AWS-native, governed AI gateway built by
Barrington and operated by Dean Holland's team. All five lighthouses must
run within Aegon's AI guardrails on that platform.

The lighthouses are numbered in priority order and cover the full spectrum
of Finance sub-functions: investor relations, knowledge management, data
quality, financial analysis, and competitive intelligence.

## Five-Lighthouse Overview

| # | Lighthouse | Primary Users | Agentic Capability |
|---|---|---|---|
| 1 | Investor Relations agent | IR team NL, CEO, CFO | In-call Q&A, Q&A deck prep, call-note filing |
| 2 | Historical Knowledge Base | US / Group Finance, FR&O, FP&A, new joiners | Source-linked RAG retrieval |
| 3 | Data Anomaly Detection | Group Reporting, Country Units | Automated report analysis, anomaly flagging |
| 4 | Financial Trend Analytics | FP&A, IR, Strategy, senior management | Trend analysis, table and visual generation |
| 5 | Competitor Analysis | Strategy, Corp Dev, FP&A, general staff | Market monitoring, competitor intelligence |

Lighthouses 1, 2, and 4 have HTML demos already available. All five will
move through an iterative playbook: outside-in design, refinement,
detailing, and go-live planning, with Aegon builders able to kick-start
implementation from week 6.

## Lighthouse 1: Investor Relations Agent

### Problem

Preparing for investor calls is manual and time-consuming. When unexpected
shareholder questions arise live, the IR team must respond slowly and
without consistent grounding. Tacit knowledge held by individual IR team
members is at risk of being lost during team transitions.

### What the agent does

The agent operates in two modes.

During live investor calls it recognises spoken questions and responds
with either an existing Q&A deck answer (extended where necessary) or a
newly formulated response. It adapts its output to the tone of voice of
the CEO or CFO speaking at that moment. A human-in-the-loop step allows
instant verification before the answer is surfaced.

During preparation it collects previously asked questions across prior
calls, identifies patterns by investor or analyst, and builds a new Q&A
deck draft that flags areas where specific parties are likely to probe.

After each call it files structured notes and answers back to a central
portal, preserving institutional IR knowledge for future teams including
Transamerica.

### Data

Internal: previous Q&A decks, prior questions and answers (where
available). External: all publicly published company information for
the current and prior reporting periods.

### Key risks for PwC

- Voice-recognition privacy: attendee consent is required before any
  recording or transcription.
- Response quality: keeping answers specific and well-grounded; avoiding
  generic output.
- Recency: ensuring the latest published information is always in scope.
- Latency: human-in-the-loop verification must be fast enough to be
  useful in a live call setting.
- SME availability: IR team and CEO/CFO time for testing and training
  is limited.

## Lighthouse 2: Historical Knowledge Base

### Problem

Critical Group Finance knowledge is scattered across documents, emails,
SharePoint, Teams, and individual memory. As Group Finance activities
relocate to Transamerica under Project Magnolia, the risk of losing
institutional knowledge is significant. New US-based teams will face a
steep learning curve without a structured way to access historical
decisions and instructions.

### What the agent does

The system is an AI-powered retrieval agent over approved historical
Finance documentation. Users can ask natural-language questions such as:
"What was the rationale for this reporting treatment?", "Where is the
latest approved guidance?", or "How was this item handled in previous
reporting cycles?"

For every answer the agent points to the original source document,
ensuring full traceability. Role-based access is applied depending on
data sensitivity. External feeds (for example, market context) can be
ingested but are kept clearly separate from internal Aegon data.

### Data

Reporting instructions, design documents, position papers, accounting
papers, internal memos, press releases, Q&A reporting packs, Internal
Financial Supplement, project documentation (decisions, meeting
materials, issue logs, sign-offs), SharePoint and Teams content subject
to access rights, and document metadata (owner, reporting period,
approval status, version number).

### Key risks for PwC

- Completeness: historical documentation may be incomplete or
  inconsistently structured.
- Source quality: outdated or unapproved documents must be excluded;
  ownership and approval status must be clear for every source.
- Over-broad answers: if source curation is weak the agent will return
  irrelevant results.
- Access control: sensitive financial information requires careful
  role-based access design.
- Dependency on classification and tagging: metadata quality is a
  pre-condition for reliable retrieval.

## Lighthouse 3: Data Anomaly Detection

### Problem

The Group Reporting team manually checks data integrity every day during
the reporting close. The process is time-consuming, limited to Tagetik
data, dependent on a small group of key people, and difficult to scale
because the review approach is largely judgement-based.

### What the agent does

The agent downloads Tagetik data-dump reports on a scheduled basis,
compares them against the previous quarter, and flags anomalies where
values exceed configurable thresholds. A daily summary email is sent
automatically with the anomalies grouped and prioritised. The agent can
also generate self-learning additional analyses over time.

The solution is designed to extend beyond Tagetik to other data sets
and to scale to the Transamerica Reporting team once a comparable data
structure exists in the future Oracle environment.

### Data

Tagetik data-dump reports or other specific reports; threshold input
configured by the team.

### Key risks for PwC

- Resource availability on the Aegon reporting side for configuration
  and threshold calibration.
- Scalability to Transamerica requires a comparable data structure in
  the future Oracle solution.
- Adoption: extending the tool to country units requires change
  management effort.

## Lighthouse 4: Financial Trend Analytics

### Problem

Tagetik is complex and static. Ad-hoc analysis depends on a small group
of Tagetik-literate people. When FP&A, IR, or senior management need a
quick answer on a trend or want to write a narrative, they either wait
or cannot get the insight at all.

### What the agent does

One or more connected agents have access to Press Releases, Annual
Reports, and External Financial Supplements across multiple reporting
periods. On request the agent creates tables or graphs, compares data
across periods and scenarios, and identifies trends. Frequently asked
analyses are available as prompt-buttons. The output is visual and
can be used as an ad-hoc Power BI replacement.

The solution supports two modes: outside-close analysis over stable
published data, and during-close support for narrative writing when
numbers are not yet stable.

### Data

Internal: Internal Financial Supplement (PDF or structured data),
frequently asked trend questions. External: Press Releases, External
Financial Supplements, Annual Reports over several years.

### Key risks for PwC

- Restatement handling: the agent must correctly identify and use
  restated figures rather than original published values.
- Extraction is limited to published data, not the underlying database;
  analysis depth is constrained by what has already been reported.
- During-close instability: numbers change during the close period and
  the agent must handle provisional data gracefully.
- PDF parsing: agents sometimes struggle to reliably extract structured
  data from complex PDF layouts such as Financial Supplement tables.

## Lighthouse 5: Competitor Analysis

### Problem

Aegon needs a scalable way to track competitors, market news, and new
market entrants, including in periods when Aegon does not report
externally itself. Today this is done manually and inconsistently.

### What the agent does

The agent aggregates and filters external RSS feeds covering peers,
press releases, financial and global news, and novelty sources (by
keyword and local language). It uses intelligent prioritisation to
surface what is most relevant to each business unit or location.

The solution has two delivery modes. A simple form produces a general
"what is happening in our industry" digest for broad staff engagement.
A complex form provides function-specific intelligence for daily
activities such as FP&A scenario building or corporate development
monitoring. Output is sent by email on a regular cadence.

### Data

Exclusively external: RSS feeds from peers and competitors (press
releases), financial and global news sites, novelty news sources
by keyword and local language.

### Key risks for PwC

- Source quality and relevance: automated filtering across many
  languages and regions requires careful calibration.
- Separation: external feeds must be kept cleanly separate from
  internal Aegon data to avoid contamination of internal knowledge
  bases such as Lighthouse 2.
- Novelty source identification: defining what constitutes a relevant
  new source (for example, a "next-generation Bloomberg") requires
  ongoing curation.

## Cross-Cutting Themes

### Shared foundation

All five lighthouses share the same underlying infrastructure: the
Aegon Launchpad platform (ALB gateway, HMAC authentication, Bedrock
models, guardrails). Common components such as document retrieval
(Lighthouses 2 and 4 both read Financial Supplement PDFs), access
control, audit logging, and monitoring should be built once and reused
across all five lighthouses. Each lighthouse should receive its own
API key so that logs and billing remain separated.

### Project Magnolia and Transamerica

Lighthouses 2 and 3 explicitly flag Transamerica scalability as a
future state. Lighthouse 1 references scaling the IR agent to the
Transamerica IR team. The Historical Knowledge Base is, in part, a
knowledge-preservation vehicle to support US-based teams taking over
Group Finance activities. Architecture decisions made in Phase 1 must
account for this US landing.

### Governance and go / no-go criteria

Before any lighthouse moves from prototype to MVP, Aegon's governance
process requires: data access approval, security review, agreed
success KPIs (baseline, target, threshold for MVP justification),
human-approved outputs defined, runtime controls specified, and a
rollback approach documented. PwC must raise these criteria explicitly
at the design phase rather than retrofitting them later.

## Key Open Questions for the Design Phase

The following questions should be resolved in the first weeks of the
project before technical architecture decisions are made.

**Process:** What pre-work (SOPs, control narratives, prior pilots)
exists for each lighthouse and can be reused?

**Technology:** Which development environment account will PwC work in
from day one? When will the Aegon Launchpad landing-zone VPC be ready
(target: request initiated week of 14 July 2026, 10-day SLA)?

**Data:** Which structured data, documents, and systems can be accessed
in Phase 1? Will the prototypes use real Aegon data and is that access
approved before project start?

**Metrics:** What are the 2 to 3 hard KPIs that define success for each
lighthouse, including the improvement threshold that would justify MVP
and scale-up?

**People:** Who is the Lighthouse Owner, Builder, and Data and Systems
Navigator for each of the five lighthouses on the Aegon side? Who is the
day-to-day product owner able to make fast scope and data decisions?

**Governance:** What outputs must remain human-approved for each
lighthouse and must AI never take autonomously? What runtime controls
and evidence are required before moving beyond prototype?
