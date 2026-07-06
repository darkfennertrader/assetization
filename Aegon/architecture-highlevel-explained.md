---
title: "Aegon AI Lighthouses — High-Level Azure Architecture"
subtitle: "Explained: layers, responsibilities, shared substrate, and per-lighthouse configuration"
author: "Raimondo Marino — Solution AI Architect"
date: "2026-07-01"
---

# Aegon AI Lighthouses — High-Level Azure Architecture

## Architecture diagram

![High-level architecture — three lighthouses on one shared Azure substrate](architecture-azure-highlevel.png)

\bigskip

### How to read this diagram

The architecture follows a single design principle: **build the substrate once, configure per lighthouse**.

- **Colour** (blue / green / orange) identifies which lighthouse a component belongs to: LH1 Investor Relations Agent (blue), LH2 Historical Knowledge Base (green), LH3 Data Anomaly Detection (orange).
- **Grey** means the component is **shared across all lighthouses** — built once and reused. No lighthouse owns a grey box; every lighthouse plugs into it.
- **The funnel shape** is intentional: three coloured columns at the top converge into a single grey substrate at the bottom. This is the assetization message — three products, one investment in infrastructure.
- **Dashed boxes on the right** label the architectural layers in terms that connect to the general reference architecture: Showroom, Marketplace, Substrate (see Section 2 below).
- **Dashed edges** (grey, thin) represent always-on sidecars — observability and identity — that run passively alongside every interaction without being in the critical path.

---

\newpage

## Layer breakdown

| Layer | Azure services | Role | Shared? |
|---|---|---|---|
| **Showroom** — L1 Experience | Azure Container Apps (React / Fluent UI) | Per-lighthouse UI products. Each lighthouse has its own UX tuned to its users, but all run on the same container shell with the same auth integration. LH1 has a web portal *and* a Teams Meeting Side Panel App for live investor calls. | Per-LH UI, shared shell |
| **Identity & Edge** | Entra ID, Entra External ID, Azure Front Door, WAF | Single sign-on for Aegon staff; guest access for external analysts (LH1 only). All HTTPS traffic enters through a single Front Door with WAF before reaching any application. | Fully shared |
| **Marketplace** — AI Gateway | Azure API Management (APIM) | The traffic cop. Validates tokens, enforces rate limits, tags requests for cost reporting, routes to the correct foundation model (or fallback), applies content-safety filters, exposes MCP tool endpoints, and writes a full immutable audit log of every request and response. Does **not** reason or orchestrate. | Fully shared |
| **Marketplace** — Agent Runtime | LangGraph on Azure Container Apps | The brain. Executes stateful multi-step agent graphs: selects which MCP tools to call, passes context between steps, checkpoints state for long-running tasks, and runs the HITL gate. The HITL gate is an interrupt node — the agent pauses and presents its proposed answer or action to a human reviewer before anything is sent or fired. Does **not** handle auth, rate limiting, or routing. | Fully shared |
| **Substrate** — AI Models | Azure OpenAI (Foundation LLM + Embedding), Azure AI Speech (batch STT), Azure Document Intelligence (OCR) | The AI compute plane. The Foundation LLM handles all chat and reasoning tasks across all three lighthouses. The Embedding model powers semantic search in every AI Search index. Speech STT is used only for post-call batch transcription in LH1 (never for live calls — see note below). Document OCR is used only in LH2 document ingestion. | Shared compute, per-LH model config |
| **Substrate** — Data Stores | AI Search, Blob, Cosmos DB, Databricks, Key Vault, Microsoft Purview | Shared infrastructure with per-lighthouse configuration (see Section 3). | Shared infra, per-LH data |
| **Substrate** — Observability | App Insights, LangSmith, Event Hub, Log Analytics, ADLS Gen2 | Every agent run, tool call, latency figure, and error is logged in App Insights. LLM traces and prompt versions are tracked in LangSmith. Every APIM request/response is written to an immutable audit log via Event Hub -> ADLS Gen2. | Fully shared |

\bigskip

> **Note on live-call voice (LH1):** Voice-to-text during live investor calls is handled by the **Teams Live Transcription API** — a Microsoft-hosted, diarized service that comes with Teams Premium. Azure AI Speech is **not** used for live calls. Text-to-Speech (TTS) is **explicitly excluded**: the agent produces a text answer with citations; the CEO or CFO reads it and speaks it aloud. No AI voice is ever present on an earnings or investor call.

\bigskip

## How the shared substrate connects to each lighthouse (per-LH configuration)

The grey boxes are shared infrastructure. Each lighthouse plugs its own configuration into them — it does not own or replicate the box. This is what makes the assetization model cost-efficient.

| Shared component | LH1 — IR Agent (blue) | LH2 — Knowledge Base (green) | LH3 — Anomaly Detection (orange) |
|---|---|---|---|
| **AI Search index** | Q&A decks + archived call transcripts (post-call batch STT output) | Approved Finance documents (internal) + external regulatory feeds (separate index, labelled) | Not used |
| **Cosmos DB collection** | Analyst profiles, sentiment history, post-call Q&A notes, HITL state | Document approval metadata, review workflow state | Threshold config per reporting unit, anomaly HITL state |
| **Blob Storage** | Teams call recordings (Logic Apps copy from Stream/SharePoint) | Raw Finance documents pending OCR + approval | Tagetik data dumps (scheduled Logic Apps download) |
| **Databricks / Delta Lake** | Not used | Not used | Tagetik QoQ financial data with row-level security per country unit |
| **Microsoft Purview** | Not used | Data classification, lineage, approval-status tags that gate what enters the LH2 index | Not used |
| **Foundation LLM calls** | Formulate investor Q&A answers | Answer natural-language document queries | Generate anomaly narrative commentary |
| **Embedding model** | Index + search call transcripts and Q&A decks | Index + search approved Finance documents | Not used |
| **HITL Gate** | Human (CEO/CFO) reviews suggested answer before it is spoken on the call | Human reviewer approves documents before they enter the knowledge base | Human reviewer approves anomaly action before it is dispatched to country units |
| **MCP /rag tool** | Retrieves cited answers from LH1 AI Search index | Retrieves cited answers from LH2 AI Search index | Not used |
| **MCP /anomaly tool** | Not used | Not used | Runs QoQ diff, threshold check, LLM narrative |
| **MCP /notify tool** | Not used | Not used | Sends daily anomaly summary email via Azure Communication Services |

\bigskip

## Gateway vs. Agent Runtime — why they are separate

A common question when first reading the diagram: why are the AI Gateway and the Agent Runtime two separate boxes, and not one?

| Concern | AI Gateway (APIM) | Agent Runtime (LangGraph) |
|---|---|---|
| **Responsibility** | Traffic management — who is allowed in, at what rate, at what cost | Task execution — what the agent does once it is inside |
| **State** | Stateless per request | Stateful — tracks multi-step progress across turns |
| **Knows about** | Tokens, quotas, models, cost centres, safety policies | Tools, context, reasoning steps, human approvals |
| **Fails if** | Authentication fails or rate limit exceeded | Tool returns an error or LLM returns a low-confidence answer |
| **Scales** | Horizontally, independently of agent logic | Independently, based on active agent sessions |

Separating them means: the Gateway can be upgraded (new model, new safety policy, new cost allocation rule) without touching agent logic; and agent logic can be changed (new tool, new orchestration step) without touching the Gateway. This is the correct layering for a production AI system.

\bigskip

## Acronym reference

| Acronym | Meaning |
|---|---|
| LH | Lighthouse — a focused AI use case |
| IR | Investor Relations |
| MCP | Model Context Protocol — open standard for agent tool-calling |
| RAG | Retrieval-Augmented Generation — answering questions using retrieved documents, with citations |
| HITL | Human-in-the-Loop — a mandatory human review/approval step in the agent workflow |
| APIM | Azure API Management |
| ACA | Azure Container Apps |
| ADLS | Azure Data Lake Storage Gen2 |
| WAF | Web Application Firewall |
| STT | Speech-to-Text |
| TTS | Text-to-Speech (explicitly excluded from LH1) |
| LLM | Large Language Model |
| SSO | Single Sign-On |
| RBAC | Role-Based Access Control |
| QoQ | Quarter-on-Quarter |
| KB | Knowledge Base |
| PoC | Proof of Concept |
| MVP | Minimum Viable Product |
| OCR | Optical Character Recognition |
| FR&O | Finance Reporting & Operations |
| FP&A | Financial Planning & Analysis |

---

## Relation to PwC ARA-A — how this architecture maps onto the general playbook

The Aegon AI Lighthouses architecture is a **direct application of the PwC AI Assetization Reference Architecture (ARA-A)** to a single client engagement. The table below maps the four PwC ARA-A concepts onto what is built for Aegon.

| PwC ARA-A concept | Definition in the general playbook | Aegon equivalent |
|---|---|---|
| **Showroom** (external) | Client-facing demo environment; prospects scan a QR code and access a polished UI for 1 hour; run by Entra External ID short-lived guest tokens | **Does not exist in this engagement.** Aegon's lighthouses serve Aegon staff (plus a small number of external analyst guests for LH1 only, handled via Entra External ID guest access). There are no external prospects being demoed to. |
| **Marketplace** (internal) | The platform layer that lets producers publish reusable AI assets and consumers discover, evaluate, and adopt them; enforces CI certification, metadata schema, governance signals | **The Reusable AI Assets layer** — AI Gateway (APIM) + Agent Runtime (LangGraph on ACA) + four MCP tools (/rag · /extract · /anomaly · /notify). These are the "Lego pieces" built once and reused across all three lighthouses. They follow the Marketplace pattern: built to a standard, versioned independently, consumed by configuration. |
| **Knowledge Base** (Priority 3 — deferred in the general playbook) | Domain intelligence layer: RAG over structured and unstructured data, graph database, Databricks + Mosaic AI for tabular domain knowledge | **Already implemented here — but split across two lighthouses.** LH2 is a Knowledge Base by design (RAG over approved Finance documents). LH1 also has a Knowledge Base component (AI Search index over call transcripts and Q&A decks). In the general playbook the Knowledge Base is deferred; in this Aegon engagement it is a first-class deliverable because it is the core value proposition of LH1 and LH2. |
| **Shared Substrate** (build first, Weeks 1–4) | The technical plumbing that all products run on: auth (Entra ID + Entra External ID), AI Gateway (APIM), Foundation LLM access, observability (App Insights, LangSmith, audit log) | **Rows 2a–4 of the diagram** — Auth / Front Door / WAF + AI Gateway (APIM) + Foundation LLM + Embedding model + Databricks + Key Vault + Purview + Observability. The Knowledge Bases (AI Search indexes for LH1 and LH2) are domain-specific configurations that run on top of this substrate. |

### Why the Aegon diagram uses different labels

The Aegon diagram uses Aegon-appropriate labels ("User Experience", "Reusable AI Assets", "Shared Substrate") rather than PwC's "Showroom/Marketplace" vocabulary because:

1. **There is no external Showroom** at Aegon. Using the word "Showroom" on a slide shown to Aegon executives would be confusing — it would imply they are being demoed to.
2. **The Marketplace concept maps to the asset-reuse layer within Aegon**, not to a PwC-facing product. The Aegon lighthouses *consume* the Marketplace pattern; they are not themselves a marketplace.
3. **Knowledge Bases are front-and-centre**, not deferred. The PwC general playbook defers the Knowledge Base to Phase 3; here it is the primary deliverable for LH1 and LH2.

The underlying engineering principles — shared substrate, reusable assets, per-use-case configuration, HITL governance — are identical in both cases.

---

## Tenancy model & PwC Marketplace supply chain

![PwC Marketplace supply chain — signed artefacts flow at deploy time only; no Aegon data crosses the tenant boundary](tenancy-supply-chain.png)

\bigskip

### How to read this diagram

The diagram shows **two separate Azure tenants** and what flows between them. There is no shared runtime infrastructure across the two tenants — only **signed, versioned artefacts** flow from PwC's Marketplace into Aegon's tenant, and only at deploy time.

- **PwC Tenant B (red, left)** — the firm-wide AI Marketplace. Contains the registries, container images, Python packages, APIM policy templates, and the CI/CD pipeline that builds, signs, and scans them before publishing.
- **Deploy pipeline (grey, centre)** — runs in Aegon's Azure DevOps or GitHub Actions environment. PwC engineers access it via Just-in-Time Entra B2B guest access (MFA-protected, time-bounded, fully audited). At deploy time it *pulls* artefacts from PwC's registries and provisions them into Aegon's subscription.
- **Aegon Tenant A (blue, right)** — Aegon's production environment. Every running component — APIM, LangGraph runtime, MCP tools, observability, Entra ID — lives here, inside Aegon's subscription, in an EU region Aegon controls.
- **Aegon Data (dark blue cylinder)** — Tagetik financial data, Finance documents, call transcripts, analyst profiles, Key Vault secrets. **This data never leaves Aegon's tenant.** No runtime API call, no log stream, no telemetry crosses the tenant boundary to PwC.

### The five artefact channels

| Artefact | Where it lives in PwC Tenant B | How it reaches Aegon Tenant A |
|---|---|---|
| **Bicep / Terraform IaC modules** | Private ACR (`pwcaimktplace.azurecr.io/iac`) | Pulled by Aegon's deployment pipeline at `az deployment` time; resources provisioned into Aegon's subscription |
| **Container images** (LangGraph runtime, MCP tools) | PwC Container Registry (`pwcaimktplace.azurecr.io`) | Pulled by Aegon's Container Apps at deploy time; images run entirely in Aegon's compute |
| **Python packages** (MCP tool libraries) | PwC private PyPI feed | Installed into Aegon's build agents at CI time; code runs in Aegon's Container Apps |
| **APIM policy library & prompt library** | PwC Git repo (versioned XML/YAML) | Imported into Aegon's APIM instance at deploy time; policies execute in Aegon's APIM |
| **Observability schemas** (dashboards, alert rules, KQL queries) | PwC Git repo | Deployed into Aegon's Log Analytics workspace; all telemetry stays in Aegon's tenant |

### Runtime guarantee

> **Aegon's operational data never leaves Aegon's tenant.** The only cross-tenant flow is signed artefacts, pulled one-way (PwC → Aegon), at deploy time. There is no runtime data plane connection between the two tenants.

This guarantee is what allows the assetization model to work in a regulated financial-services environment: Aegon's data sovereignty, DNB/ECB compliance requirements, and audit obligations are not compromised because all sensitive data remains in Aegon's own Azure subscription.

### Governance & commercial model

| Concern | Position |
|---|---|
| **Azure consumption cost** | Aegon pays for their own subscription (compute, storage, LLM tokens) |
| **PwC Marketplace access** | PwC charges a programme licence for access to versioned Marketplace assets (per engagement or flat programme fee) |
| **Aegon exit right** | Protected — running system is in Aegon's tenant, IaC owned by Aegon; system continues to run if PwC disengages |
| **PwC engineer access** | JIT Entra B2B guest access only; auto-expires; full audit trail in Aegon's Log Analytics |

---

*Owner: Raimondo Marino, Solution AI Architect · PwC / Strategy& engagement for Aegon Finance · 2026-07-01*

\newpage

## Appendix A — Entra ID federated identity (deep dive for InfoSec)

**Entra ID federated identity** is a trust relationship between two Entra ID tenants — or between an Entra ID tenant and an external identity provider such as GitHub Actions — that allows a workload in one tenant to authenticate into the other **without any password, secret, or key being stored anywhere**.

### The problem it solves

Aegon's deployment pipeline (running in Aegon's Azure DevOps or GitHub Actions) needs to pull container images from PwC's Container Registry (PwC Tenant B). The traditional approach:

1. Create a service principal in PwC's tenant with pull permissions on the ACR.
2. Generate a client secret (essentially a password) for that service principal.
3. Store the secret in Aegon's Key Vault.
4. Rotate it every 90 days.
5. Ensure it never leaks in a CI log.

This works, but it is fragile and audit-hostile. **Federated identity eliminates the secret entirely.**

### How it works — step by step

1. **PwC's Entra ID tenant** has a service principal `aegon-deployment-pipeline` with permissions to pull images from `pwcaimktplace.azurecr.io`.
2. PwC's admin **configures a federated credential** on that service principal: *"Trust tokens issued by Aegon's GitHub Actions OIDC provider, but only if the token comes from the `aegon-lighthouses` repository, on the `main` branch, running the `deploy.yml` workflow."*
3. When Aegon's GitHub Actions pipeline runs, it requests a token from **GitHub's built-in OIDC provider**. GitHub signs a token that says: *"This is workflow `deploy.yml`, repository `aegon-lighthouses`, branch `main`."*
4. The pipeline presents that token to **PwC's Entra ID** and requests an access token for the ACR pull permission.
5. PwC's Entra ID inspects the incoming token, verifies it matches the federated credential rule exactly, and issues a **short-lived (1-hour) access token**.
6. The pipeline uses that access token to pull the container image. **No secret was ever stored.**

The trust is based on cryptographically signed metadata about *who is running, from where, in what context* — not on a shared password.

### Why it matters

- **No cross-tenant secrets** — nothing for an attacker to steal, no 90-day rotation schedule, no Key Vault entry to manage.
- **Fine-grained scope** — PwC restricts the federated credential to a specific repo, branch, and workflow. A fork of Aegon's repo or a different workflow will not receive a token.
- **Full audit trail** — every token issuance is logged in PwC's Entra ID sign-in logs. Both tenants can see exactly which Aegon workflow pulled which image and when.
- **Auto-expiry** — access tokens are short-lived (typically 1 hour). There is no long-lived credential to revoke or that could be silently exfiltrated.

### Where it appears in the architecture

In the tenancy supply-chain diagram the deploy pipeline cluster is labelled *"Deploy time only — Entra ID federated identity, MFA"*. This covers two related but distinct mechanisms:

| Mechanism | Who it authenticates | Credential type |
|---|---|---|
| **Federated identity** (Workload Identity Federation) | Aegon's pipeline — machine-to-PwC-tenant | No secret; OIDC token signed by GitHub, exchanged for a short-lived Entra access token |
| **JIT Entra B2B guest access** | PwC engineer — human-to-Aegon-tenant | MFA-protected, time-bounded guest invitation (Privileged Identity Management); full sign-in audit in Aegon's Log Analytics |

### One-line phrasing for the client

*"Aegon's deployment pipeline authenticates into PwC's registries using Entra ID Workload Identity Federation — an OIDC-based trust that eliminates stored secrets, is scoped to a specific repository and workflow, issues short-lived tokens, and leaves a full audit trail in both tenants' sign-in logs."*
