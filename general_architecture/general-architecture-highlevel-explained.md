---
title: "PwC AI Platform — General High-Level Architecture"
subtitle: "L1 Showroom · L2 Marketplace · L3 Knowledge Base · L4 Shared Substrate"
author: "Raimondo Marino — Solution AI Architect"
date: "2026-07-02"
---

# PwC AI Platform — General High-Level Architecture

## Architecture diagram

![PwC AI Platform general high-level architecture — four numbered layers](general-architecture-highlevel.png)

\bigskip

### How to read this diagram

The diagram shows the **full PwC AI Platform** as four numbered layers, stacked from external (top) to shared infrastructure (bottom).

- **Colour** identifies the layer: orange = L1 Showroom · green = L2 Marketplace · blue = L3 Knowledge Base · grey = L4 Shared Substrate.
- **Arrows** show data and request flows. Solid = synchronous (request/response). Dashed = asynchronous (sidecar / telemetry / silent refresh).
- **The funnel** is intentional: three distinct product layers at the top all converge onto a single shared grey substrate. The substrate is built once and never duplicated.
- **Dashed edges from Observability** represent always-on sidecars — App Insights, LangSmith, the audit log — that run passively alongside every interaction without being in the critical path.

---

\newpage

## Layer breakdown

| Layer | Purpose | Users | Azure services |
|---|---|---|---|
| **L1 — Showroom** | External-facing demo environment. PwC salesperson generates a QR code; prospect scans it and gets 1-hour scoped access — no account creation, no login screen. | External prospects / client contacts | Showroom UI (Next.js), Presenter Admin (Next.js + MSAL), Showroom BFF (Node.js), Cosmos DB session store, Key Vault (JWT signing key), App Insights |
| **L2 — Marketplace** | Internal PwC firm-wide asset catalogue. Producers publish certified AI assets; consumers discover, evaluate, and adopt them. Enforces CI certification, metadata schema, governance signals. | ~400 PwC entities worldwide (internal staff, Entra ID SSO) | Marketplace Portal (Next.js), Asset Registry (Cosmos DB + Blob), CI Certification pipeline (Azure DevOps / GitHub Actions), ACR (signed container images), Private PyPI feed |
| **L3 — Knowledge Base** *(Phase 3 — deferred)* | Domain intelligence layer. RAG over structured and unstructured client data. Per-client AI Search indexes. Plugs into the L4 runtime via the `/rag` MCP tool. | Client staff (per-engagement) | Knowledge Base UI (embed or portal), AI Search indexes (per-client), Ingestion pipeline (Logic Apps + Document Intelligence + Embedding model) |
| **L4 — Shared Substrate** | The technical plumbing that all three product layers run on. Built once, version-controlled, never duplicated per product. | All of the above | See Section 3 |

\bigskip

## Shared Substrate (L4) — component detail

| Sub-layer | Components | Role |
|---|---|---|
| **Identity & Edge** | Entra ID (staff SSO), Entra External ID (guest sessions), Azure Front Door + WAF | Every HTTPS request enters through Front Door. Token type determines which identity layer validates it — Entra ID for staff, self-signed JWT (session token) for Showroom guests. WAF blocks OWASP Top 10 before anything reaches the application. |
| **AI Gateway** | Azure API Management (APIM) | The single enforcement point. Validates tokens inline (`validate-jwt`), rate-limits per session/user, applies Azure Content Safety filters, tags requests with cost-centre metadata, writes every request/response to the immutable audit log via Event Hub. No backend service accepts unauthenticated calls directly. |
| **Agent Runtime** | LangGraph on Azure Container Apps + MCP Tool Servers | Stateful multi-step agent graphs. The HITL gate is an interrupt node — the agent pauses and presents its proposed answer to a human reviewer before acting. MCP tools (`/rag`, `/extract`, `/anomaly`, `/notify`) are independently versioned and deployed from the L2 Marketplace. |
| **AI Models** | Azure OpenAI (Foundation LLM + Embedding model) | Shared compute for all product layers. Foundation LLM (GPT-4o / GPT-4o-mini) handles all chat and reasoning. Embedding model powers semantic search in every AI Search index. |
| **Observability** | App Insights + Log Analytics, LangSmith, Event Hub → ADLS Gen2, Key Vault | Every agent run, tool call, latency figure, and error is logged. LLM traces and prompt versions tracked in LangSmith. Immutable audit log (Event Hub → ADLS Gen2) stores every APIM request/response. Key Vault holds all secrets and the JWT signing key, accessed via Managed Identity only — no stored credentials. |

\bigskip

## The three product layers — how they differ and how they share

| Concern | L1 Showroom | L2 Marketplace | L3 Knowledge Base |
|---|---|---|---|
| **Target user** | External prospect (anonymous, 1-hour session) | Internal PwC staff (long-term, Entra ID) | Client staff (per-engagement, Entra B2B or client Entra) |
| **Auth mechanism** | Self-signed RS256 JWT, 5-min TTL, session-horizon 1h in Cosmos | Entra ID Bearer token (PKCE) | Client Entra ID or Entra B2B guest invite |
| **Access scope** | Presenter-selected demos only (JWT `scope` claim) | Full catalogue (RBAC per asset tier) | Per-client index (row-level security in AI Search) |
| **UI pattern** | Mobile-first · countdown timer · silent refresh | Desktop portal · search + filter · asset detail pages | Embedded widget or standalone portal (per client spec) |
| **Data sovereignty** | PwC-hosted session metadata only (no client data) | PwC asset registry only (no client data) | Client data stays in client tenant (tenancy model) |
| **Relation to L4 runtime** | Calls APIM → LangGraph → MCP tools for live AI demos | Calls APIM → LangGraph → MCP tools for "Try it now" in catalogue | Calls APIM → LangGraph → `/rag` tool → AI Search index |

\bigskip

## Gateway vs. Agent Runtime — why they are two separate components

| Concern | AI Gateway (APIM) | Agent Runtime (LangGraph) |
|---|---|---|
| **Responsibility** | Traffic management — who is allowed in, at what rate | Task execution — what the agent does once inside |
| **State** | Stateless per request | Stateful — tracks multi-step progress across turns |
| **Knows about** | Tokens, quotas, models, cost centres, safety policies | Tools, context, reasoning steps, human approvals |
| **Scales** | Horizontally, independently of agent logic | Independently, based on active agent sessions |

Separating them means the Gateway can be upgraded (new model, new safety policy, new cost allocation rule) without touching agent logic, and agent logic can change (new tool, new orchestration step) without touching the Gateway.

\bigskip

## Relation to client engagements

This general architecture is a **pattern, not a deployment**. When PwC engages a client:

1. **L4 Shared Substrate** is provisioned into **the client's own Azure tenant** (tenancy model — see `Aegon/architecture-highlevel-explained.md` Section "Tenancy model").
2. **L2 Marketplace assets** (certified container images, IaC modules, MCP tool packages, APIM policies) are pulled from PwC's ACR and registries **at deploy time only** via Entra ID Workload Identity Federation — no stored secrets, no runtime connection to PwC.
3. **L1 Showroom** lives in PwC's own tenant — it is the *pre-sales* and *demo* layer; the client never hosts the Showroom.
4. **L3 Knowledge Base** is built **within the client's tenant** once the engagement reaches Phase 3 — client data never leaves the client tenant.

| Layer | Lives in | Data crosses boundary? |
|---|---|---|
| L1 Showroom | PwC tenant | No client data |
| L2 Marketplace | PwC tenant | Signed artefacts only, at deploy time, pull-only |
| L3 Knowledge Base | Client tenant | No — client data stays in client tenant |
| L4 Shared Substrate | Client tenant | No — only artefacts from L2 at deploy time |

\bigskip

## Acronym reference

| Acronym | Meaning |
|---|---|
| APIM | Azure API Management |
| ACA | Azure Container Apps |
| ACR | Azure Container Registry |
| ADLS | Azure Data Lake Storage Gen2 |
| BFF | Backend for Frontend — a thin server-side API layer that owns session tokens and calls downstream APIs on behalf of the UI |
| HITL | Human-in-the-Loop — a mandatory human review/approval step in the agent workflow |
| JWT | JSON Web Token |
| MCP | Model Context Protocol — open standard for agent tool-calling |
| MSAL | Microsoft Authentication Library |
| PKCE | Proof Key for Code Exchange — OAuth 2.0 extension for public clients |
| RAG | Retrieval-Augmented Generation |
| RBAC | Role-Based Access Control |
| SSO | Single Sign-On |
| TLS | Transport Layer Security |
| WAF | Web Application Firewall |

