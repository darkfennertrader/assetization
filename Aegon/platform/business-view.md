---
title: "Aegon AI Platform: Business Overview for PwC"
---

## How the platform works

Aegon has built a corporate AI platform called Launchpad. Its job is simple:
every time a lighthouse application needs to ask an AI model a question, the
request must pass through Launchpad first. Launchpad checks the request against
the company's guardrail policies, routes it to an approved model, records the
call in an audit trail, and returns the answer. No lighthouse application ever
calls an AI model directly.

This means the business gets a complete record of every AI interaction, the
company's AI usage policies are applied consistently, and no unapproved model
can ever be used -- without anyone on the PwC delivery team having to implement
any of that governance themselves.

The diagram `business-view.png` shows the five ownership zones and the
seven-step request flow from end user to AI model and back.

All lighthouse data -- whether synthetic data used during the PoC phase or
real Aegon Finance data used during MVP and production -- resides inside the
BU application VPC (the blue zone). When the orchestrator calls the AI model,
the prompt (which may include a snippet of retrieved data) transits through
the Launchpad AI Safety Layer, but Launchpad itself is stateless: it persists
only call metadata for the audit log, never business data at rest.

## Who owns what

| Zone | Owner | What they are responsible for |
|---|---|---|
| Aegon Business | CFO office, lighthouse owners, end users | Business requirements, acceptance criteria, source data |
| Lighthouse Application VPC | Aegon (account owner) / PwC (builder and operator) | Lighthouse applications: user interface, AI orchestrator, tool functions, all application data |
| Aegon Launchpad | Barrington / Stuart's team | AI safety layer: access control, guardrails, model gateway, audit log |
| Aegon Governance | AI Board, data owners, security, compliance | Model approval, guardrail policy, data classification, AI usage policy |
| Foundation Models | Anthropic, Amazon, Meta, others | The underlying large language models (accessed only via Launchpad) |

The blue zone is an Aegon BU AWS account, but PwC has full design freedom
inside it. PwC builds and operates the lighthouse application; Aegon owns the
underlying account and its landing-zone controls. PwC never modifies the red
zone; Aegon Launchpad never modifies the blue zone. The two zones meet at a
single authenticated connection point (the Launchpad ALB).

Inside the blue zone, PwC has free choice of Python libraries, orchestration
frameworks (LangGraph, LangChain, and similar), and any AWS service already in
Aegon's approved catalogue. New non-catalogue components -- a new SaaS
integration, a new AWS service not yet in use at Aegon, a new database engine
-- require a review by Stephanie Reynolds' architecture team. Stuart's rule of
thumb from the kick-off: "nothing is a no, but there might be questions around
what we need to do to make it a yes." The one absolute constraint: no direct
model calls from PwC code. Every AI call must go through the Launchpad AI
Safety Layer.

## Two speeds of delivery

The `data-governance.png` diagram shows that PwC can work at two speeds
depending on whether the lighthouse is using synthetic or real data.

**Fast lane -- synthetic data (days to start).**
PwC authors realistic mock data and connects the lighthouse to it from day one.
No data approvals are needed. The AI orchestrator, the tool functions, and the
user interface are all built and validated against this data. The AI safety
layer -- guardrails, model access, audit trail -- operates exactly as it will
in production. The only thing missing is real Aegon data.

**Governed lane -- real data (weeks to start).**
When the prototype is validated and the business wants to connect real Finance
data, five approval gates must be cleared: data classification, data owner
sign-off, a DPIA review if personal data is involved, AI Board architecture
review, and production-level security controls. Once cleared, the application
moves into an account that is still called a development environment but
operates under full production governance.

The important point is that **the application code is identical on both
sides**. What changes is the account it runs in and the approvals gate in
front of it. Starting on the synthetic fast lane is therefore a feature, not
a compromise: it lets PwC demonstrate working AI logic and earn business
confidence before the governance overhead of real data access is incurred.

PwC's recommended approach for every lighthouse is to complete the prototype
on synthetic data first, get lighthouse-owner sign-off on the AI behaviour,
and then trigger the data governance workstream in parallel with finalising
the MVP design.

## The orchestrator choice

The orchestrator is the brain of a lighthouse application. It is the piece of
software that receives the user's request, decides which tools to call, in
which order, and when to ask the AI model a question. Everything else --
the user interface, the tool functions, the data store -- stays the same
regardless of which orchestrator is chosen. Only the orchestrator logic
changes.

Launchpad provides three options, and the choice is made per lighthouse:

| | Option A: Agent Core blueprint | Option B: Custom LangGraph | Option C: Best of Both |
|---|---|---|---|
| What it is | Pre-built agent patterns provided by Barrington via Launchpad | PwC-built orchestrator using the LangGraph framework | LangGraph runs the main flow; delegates to Agent Core for one specific step |
| Number of pre-built patterns | 10 (all ARB-approved) | None -- built from scratch | Mixed |
| Governance approval | Already cleared -- no extra process | Standard component review (straightforward for LangGraph) | Cleared for the Agent Core parts; standard review for the LangGraph parts |
| Speed to first prototype | Fastest | Fast | Fast |
| Flexibility | Constrained to AWS-native patterns | Full flexibility | Full where it matters |
| Portability | AWS-locked | Portable, PwC-standard | Mostly portable |
| Best for | Lighthouses that map cleanly onto a standard pattern (RAG, MCP, A2A) | Lighthouses with custom logic or external SaaS integrations | Lighthouses that need external SaaS tools but also want the MCP or A2A capability |

**Option A** is best when a lighthouse maps cleanly onto one of the 10
pre-built Launchpad patterns (RAG, MCP, A2A, and others). It is the fastest
path to a first prototype because the patterns are already ARB-approved and
the blueprint can be provisioned without writing orchestrator code. The
trade-off is that it is constrained to AWS-native capabilities; customisation
beyond what the blueprint exposes requires additional work.

**Option B** gives the delivery team full flexibility to implement any agent
logic, connect to any approved data source or tool, and keep the code portable
and easy to test locally. It requires building the orchestrator from scratch,
but frameworks such as LangGraph make this straightforward. Component approval
for LangGraph itself is a routine step. Choose Option B when the lighthouse
logic does not map neatly onto an existing pattern or when portability matters.

**Option C** combines the two: LangGraph handles the main workflow while a
specific step -- for example, an MCP tool call or an agent-to-agent
interaction -- is delegated to Agent Core. This is the right choice when a
lighthouse genuinely needs one of the Agent Core-specific capabilities but
also requires custom logic elsewhere. Most of the codebase remains portable;
only the Agent Core delegation step is AWS-constrained.

All three options call the AI Safety Layer through the same authenticated
connection. The choice of orchestrator has no effect on guardrails, model
access, or the audit trail. The decision is made per lighthouse during the
design phase.

## Named stakeholders from the kick-off meeting

The table below maps the people present in the 10 July 2026 kick-off to the
zones in `business-view.png`.

| Name | Organisation | Role in the programme | Zone |
|---|---|---|---|
| Duncan Russell | Aegon | Group CFO; ultimate business sponsor; chose PwC as delivery partner | Aegon Business |
| Mark | Aegon | Engagement lead on the Aegon side; coordinates the programme; acts as Tenant Admin for the Launchpad platform | Aegon Business |
| Nathalie | Aegon | Programme coordination; organises the per-lighthouse kick-off sessions; tracks lighthouse owners | Aegon Business |
| Lighthouse owners | Aegon Finance | One named owner per lighthouse (Finance); accountable for requirements and acceptance | Aegon Business |
| Dean Holland | Aegon | Senior technology leader; owns AI strategy, guardrail policy, and the Launchpad programme | Aegon Launchpad |
| Steve Kiss | Aegon | Onboarding contact for all landing-zone requests; first call when the environment provisioning starts | Aegon Launchpad |
| Stuart | Barrington | Platform architect and day-to-day technical contact; built and operates Launchpad on Aegon's behalf | Aegon Launchpad (Barrington vendor) |
| Barrington | External vendor | Consulting firm contracted by Aegon to build, operate, and onboard teams onto Launchpad | Aegon Launchpad (Barrington vendor) |
| Stephanie Reynolds | Aegon | Dean Holland's architecture team; component approval and exception-process gatekeeper | Aegon Governance |
