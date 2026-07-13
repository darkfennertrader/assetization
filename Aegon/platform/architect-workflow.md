---
title: "PwC Solution Architect Guide: Designing on Aegon Launchpad"
---

## Purpose

This document describes the decision framework, stakeholder routing, and
design responsibilities for a PwC solution architect working on the Aegon
lighthouse programme. It covers orchestration pattern selection, component
approval, data classification, cross-lighthouse reuse, and the exception
process for non-standard components.

## Workflow diagram

![Architect workflow](architect-workflow.png)

## Orchestration pattern decision tree

![Orchestration decision tree](decision-tree.png)

## The architect's core constraint

Launchpad is a paved road, not a cage. It mandates one thing: every LLM
call must pass through the router blueprint via HMAC-authenticated HTTP.
Everything else -- orchestration logic, data access patterns, tool design,
agent behaviour, UI, integrations -- is entirely the architect's domain.

The architect's job is to design the best possible lighthouse within that
one constraint, and to identify early which design choices require Aegon
approval before the team builds them.

## Design phase workflow

### Step 1 -- Understand the lighthouse requirements

Work with the lighthouse owner (the business-side role who owns the use
case) to understand:

- The user journey (who does what, in which sequence).
- The data sources involved and their classification (synthetic-safe vs.
  regulated finance data).
- The required latency and throughput profile.
- The human-in-the-loop requirements.
- The integration points with existing Aegon systems (Teams, email, SAP,
  ledger exports, etc.).

Do not start designing infrastructure until this is clear. Most early
over-engineering on AI projects traces back to premature component
selection before the user journey is stable.

### Step 2 -- Choose the orchestration pattern

Use the decision tree diagram (above) to select between:

**LangGraph in Business VPC (default).** The orchestrator runs as an ECS
Fargate service or Lambda function in our Business VPC. Tool functions are
plain Python that query local databases. Only LLM inference calls cross the
Transit Gateway to the Launchpad router. This pattern gives maximum
observability, easier local development, and no extra network hops for data
access. Use this for all lighthouses unless a specific reason requires
Agent Core.

**Agent Core blueprint (selective use).** The agent runtime is provisioned
by the Launchpad team via the web UI into the Launchpad VPC. Use this only
when the lighthouse requires agent-to-agent (A2A) calls to another
Aegon-managed agent, or requires the Launchpad-managed MCP gateway to reach
an external SaaS tool with corporate-standard authentication. Every tool
call in this pattern crosses the Transit Gateway.

**Hybrid.** LangGraph handles the main orchestration flow. One or more
specific steps delegate to an Agent Core agent for MCP or A2A capability.
Use this when most of the lighthouse logic is straightforward RAG or
HITL but one step genuinely needs the Agent Core gateway.

### Step 3 -- Identify required AWS components

For every component the design requires, check whether it is on the Aegon
approved component list. Standard components that are almost certainly
pre-approved: DynamoDB, Aurora, OpenSearch, S3, Lambda, ECS Fargate,
SQS, SNS, SES, EventBridge, Secrets Manager, CloudWatch, X-Ray.

Components that may require an exception: Bedrock Knowledge Bases (as a
managed vector store), Textract (OCR), Comprehend (NLP), Kendra (search),
any non-standard ML service, any non-AWS data store, any SaaS integration.

For each potentially unapproved component, open the exception conversation
with the architecture review lead before the team builds anything.

### Step 4 -- Classify data requirements

For each data source the lighthouse will consume, determine its
classification:

**Synthetic / mock data.** No governance process required. Use freely
in all environments from day one. Generate synthetic datasets that match
the schema and statistical properties of the real data without containing
actual Aegon Finance records.

**Real production data.** Requires the data governance workstream to
approve each data source before it enters any environment. Contact the
data governance lead to initiate. Plan for a 2-4 week lead time per data
source. Do not block lighthouse development on this -- build with
synthetic data first, swap in real data when approved.

### Step 5 -- Design for cross-lighthouse reuse

All five lighthouses share one LOB account and one Business VPC. This
creates natural opportunities for reuse that reduce cost and complexity:

- A single router blueprint instance can serve all five lighthouses.
  Each lighthouse gets its own API key, giving separate audit logs and
  cost attribution.
- A single OpenSearch domain can hold multiple indexes, one per
  lighthouse knowledge base, with separate access control per index.
- Shared utility Lambda functions (HMAC signing, citation formatting,
  threshold lookup) can live in a shared-services namespace and be
  invoked by all lighthouse LangGraph flows.
- One throughput-critical lighthouse that needs deterministic model
  latency may warrant its own dedicated router blueprint instance to
  avoid being throttled by a chatty lighthouse on the shared ALB.

### Step 6 -- Write the architecture document

Before any significant component is built, produce an architecture document
using the Aegon ARB template. The document must cover:

- Lighthouse user journey (sequence diagram or equivalent).
- Component diagram showing all AWS resources, VPC placement, and network
  flows.
- Data flow diagram showing which data sources are accessed, by which
  components, and under which IAM roles.
- Orchestration pattern choice and rationale.
- Security and compliance notes (data classification, encryption at rest
  and in transit, IAM least-privilege design).
- Any components that require exception approval (flagged explicitly).

Submit the document to the architecture review lead before week 4 of the
design phase. Allow one review cycle (approximately one week) before
expecting a response.

## Component exception process

When a lighthouse needs a component that is not on the Aegon approved list:

1. Identify the component and the specific capability it provides.
2. Document why no approved alternative meets the requirement.
3. Draft the architecture document section covering that component:
   security posture, data residency, cost model, support model.
4. Submit to the architecture review lead.
5. Expect one of three outcomes: approved as-is, approved with conditions
   (e.g. additional logging required), or rejected with an approved
   alternative suggested.
6. If rejected, design around the approved alternative. If approved,
   the component can be included in the Terraform plan.

The Launchpad team confirmed that exceptions are not blockers -- they are
a process. Start the conversation early, in week 1 if the component is
known to be needed. Do not raise exceptions in week 6 when the team has
already built the dependency.

## Stakeholder routing

The architect is the primary routing point for all design questions on the
engagement. Route questions to the correct Aegon counterpart according to
the table below. Do not use one counterpart as a switchboard to reach
another -- go direct.

| Question type | Aegon counterpart |
|---|---|
| Platform mechanics (blueprints, HMAC, router, agent patterns) | Platform lead (Launchpad team) |
| Account provisioning (landing zone, VPC setup, SLAs) | Provisioning lead |
| Component approval (exception process, ARB submission) | Architecture review lead |
| AI strategy, policy, model governance, DeepSeek/model decisions | AI strategy lead |
| Data governance (real data approval, classification, retention) | Data governance lead |
| Scope, timeline, budget, cross-BU coordination | Business sponsor |
| Lighthouse requirements, user journey, acceptance criteria | Lighthouse owner (per lighthouse) |

Always follow up verbal conversations with a written summary. Send it
to the counterpart within 24 hours with "please flag if anything is
incorrectly captured." This creates an audit trail and catches
misunderstandings before they cost a sprint.

## Key rules for solution architects

**Rule 1 -- Default to LangGraph in Business VPC.**
Agent Core is an option, not the default. It costs more in network hops
and limits local development. Justify the choice in the architecture
document if Agent Core is selected.

**Rule 2 -- Ask before building.**
The platform lead's words: "nothing is a no -- but bring it to the table."
Any component that is not clearly approved should be raised with the
architecture review lead before a developer writes a single line of code
against it.

**Rule 3 -- One API key per lighthouse, documented.**
Maintain a living credential map in the engagement wiki: which lighthouse
uses which API key, which guardrail is bound to it, which blueprint version
is deployed. Update it on every blueprint upgrade. The Launchpad web UI
holds the authoritative record, but the engagement team needs its own
readable copy.

**Rule 4 -- Design the synthetic-data set before design is complete.**
Do not wait until week 4 to think about test data. For each lighthouse,
define the synthetic dataset by week 2: schema, volume, statistical
distribution, edge cases. The developer and DevOps engineer need it
immediately to build and test.

**Rule 5 -- Separate data governance from platform governance.**
Launchpad governs how we call the model. Aegon's data governance process
governs what data we put in front of it. These are parallel workstreams
with different counterparts and different timelines. Never conflate them.

**Rule 6 -- Cross-lighthouse reuse is an architecture decision, not an
afterthought.**
Shared components must be designed as shared components from the start.
Retrofitting shared state into five independently designed lighthouses is
expensive. Make the reuse decisions in the architecture document before
any code is written.
