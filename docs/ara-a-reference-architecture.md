---
title: "Recommended Azure Architecture for AI Assetization (ARA-A)"
subtitle: "Reference Architecture — v1.0 · July 2026"
author: "Raimondo Marino, Solution AI Architect"
date: "2026-07-01"
---

# Recommended Azure Architecture for AI Assetization (ARA-A)

> **v1.0 — July 2026 | Client-sanitized; suitable for internal & external use**
>
> This document synthesises the _AI Assetization & Acceleration Playbook_ (May 2026) and the _Agent Assetization on Azure & Databricks_ research report (June 2026) into a single, opinionated reference architecture for enterprise agentic AI on Microsoft Azure. It is the anchor artefact that all other delivery documents reference.

---

## Table of Contents

1. Context & Purpose
2. The Assetization Loop
3. ARA-A at a Glance — Architecture Diagram
4. Layer-by-Layer Service Map
5. Two Delivery Profiles
6. Phased Sequencing
7. Key Performance Indicators
8. Trade-offs and Known Risks
9. Cross-Reference Index

---

## 1. Context & Purpose

### Why a reference architecture?

Enterprise agentic AI fails the same way every time: teams prototype in isolation, governance arrives late, and the second engagement rebuilds what the first one already built. The solution is not more tooling — it is **discipline that is enforced by the platform** so that the right behaviour costs less than the wrong one.

ARA-A provides:

- A **concrete Azure service map** for each of the six governance layers that recur across every published production pattern.
- A **two-profile design** — one for a single client at scale, one for cross-engagement portability (the consulting firm's own supply chain).
- An **opinionated sequencing** that matches the Playbook's four-phase assetization maturity model.
- **Testable KPIs** with named Azure sources of truth.

### Scope

ARA-A covers the **technology layer** of the assetization loop. It does not cover:

- Domain transformation methodology (Playbook §I).
- Engagement commercials or operating model (Playbook §V).
- Coding practice and prompt standards (Playbook §VII).

These are referenced where relevant.

---

## 2. The Assetization Loop

Everything in ARA-A hangs off one closed loop:

```
  DOMAIN TRANSFORMATION          ASSETIZATION ENGINEERING
  (creates demand for assets)  ──► (converts delivery into supply)
           ▲                                    │
           │                                    ▼
  ASSET MARKETPLACE  ◄───────────────────────────
  (clears supply ↔ demand; governance industrialised here)
```

**Break any link and the loop stalls.**

| Loop link | If this fails | ARA-A fix |
|---|---|---|
| Domain → Assetization | Assets are built bottom-up with no engagement pull | Use-case rubric gate in Domain Charter enforces Reusability criteria §6 & §7 |
| Assetization → Marketplace | Assets are created but never findable or consumed | CI certification gate + Azure AI Search metadata index from day one |
| Marketplace → Domain | Supply builds up but next engagement ignores it | Asset Reuse Team (ART) is forward-deployed into pods; `reuse_rate` KPI in every engagement status report |

---

## 3. ARA-A at a Glance — Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: IDENTITY & TENANCY                                                │
│  Entra ID (internal — 400+ PwC entities)                                   │
│  Entra External ID (B2B prospects, showroom, client deployments)           │
│  Short-lived guest credentials (QR-code / 1-hour showroom access)          │
│  OpenFGA on ACA (fine-grained relational authorisation)                    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│  LAYER 2: GATEWAY / QUOTA / SAFETY                                          │
│  Azure API Management — AI Gateway tier                                    │
│  · azure-openai-token-limit  (per-team / per-asset TPM quota)              │
│  · azure-openai-semantic-cache (Redis — 20–40% call reduction)             │
│  · llm-content-safety (Azure Content Safety on every request)              │
│  · emit-token-metric (→ App Insights for chargeback)                       │
│  · expose-mcp-server (wraps every REST asset as MCP tool)                  │
│  · PTU primary + PAYG fallback load balancing                              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│  LAYER 3: AGENT RUNTIME                                                     │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────┐    │
│  │ Azure Container Apps        │    │ Foundry Agent Service           │    │
│  │ + LangGraph / LangChain     │    │ (Profile A / managed option)    │    │
│  │ + LangSmith observability   │    │ Connected Agents pattern        │    │
│  │ DEFAULT runtime             │    │ OPTIONAL for greenfield         │    │
│  └─────────────────────────────┘    └─────────────────────────────────┘    │
│  Dapr (state / pub-sub)  │  Azure Service Bus (async agent tasks)          │
│  Azure Cosmos DB (conversation memory / agent state)                       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│  LAYER 4: TOOLS / ASSETS                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  CORE ASSETS (placement: CORE — reusable across all engagements)     │  │
│  │  MCP servers behind APIM:                                            │  │
│  │  /summarize  /extract  /classify  /translate  /rag  /embed           │  │
│  │  Auth components · Data transformers · BFF utilities                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  DOMAIN ASSETS (placement: DOMAIN — per-vertical, reusable within)   │  │
│  │  Azure Databricks — Unity Catalog Functions (data-bearing tools)     │  │
│  │  Mosaic AI Vector Search (Delta-backed semantic retrieval)           │  │
│  │  Genie Spaces (text-to-SQL over domain data)                         │  │
│  │  Deferred until Knowledge Base phase                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│  LAYER 5: MODELS                                                             │
│  Azure OpenAI (PTU primary — GPT-4o, embeddings)                           │
│  Foundry Models catalog (Mistral, Meta Llama, Phi — via APIM)              │
│  Mosaic AI Foundation Model APIs (open models for fine-tuning)             │
│  LiteLLM proxy (vendor-neutral fallback / multi-provider routing)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│  LAYER 6: OBSERVABILITY & EVALUATION                                        │
│  LangSmith / LangFuse (agent traces — default with LangGraph)              │
│  Application Insights (distributed tracing — API / front-end RUM)         │
│  Azure Monitor + Log Analytics (queries, dashboards, alerts)               │
│  MLflow Tracing (Databricks-side, when Databricks tier is active)          │
│  Event Hub → ADLS Gen2 (immutable audit lake — GDPR / SOX)                │
│  Foundry Evaluations (LLM-as-judge, offline eval before model upgrades)   │
│  Power BI on Log Analytics (Reuse Rate KPI dashboard)                      │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════  ASSET MARKETPLACE  ════════════════════════════════════
┌─────────────────────────────────────────────────────────────────────────────┐
│  GIT MONOREPOS (GitHub / Azure DevOps)                                      │
│  /core-assets  /domain-assets  /accelerators  /client-deployments          │
│                                                                             │
│  CI CERTIFICATION GATE (every push)                                         │
│  Ruff · mypy · pytest ≥80% · Defender for DevOps · gitleaks · semver       │
│  RAI checklist · asset.toml validation · 4-hour-extraction-rule check      │
│                    │                                                        │
│                    ▼                                                        │
│  ARTIFACT STORES                                                            │
│  Azure Artifacts (pip / npm packages)  · ACR (Docker images)               │
│  Azure AI Foundry Model Registry (agents & models)                         │
│  MLflow Model Registry (Databricks-side)                                   │
│                    │                                                        │
│                    ▼                                                        │
│  METADATA + DISCOVERY                                                       │
│  asset.toml per asset (semver, data_class, rai_risk, consumers)            │
│  Azure AI Search hybrid index over all asset.toml files  ← Layer 5        │
│  Microsoft Purview (lineage, sensitivity labels, lifecycle)                │
│                    │                                                        │
│                    ▼                                                        │
│  DISCOVERY UI  (Azure Container Apps — BUILD ONLY AFTER ≥50 assets)       │
└─────────────────────────────────────────────────────────────────────────────┘

Foundation:  CAF GenAI Landing Zone
  Hub-and-spoke VNet · Private Endpoints (all AI traffic stays private)
  Azure Policy-as-Code (Bicep/Terraform) — no direct public OpenAI calls
  Microsoft Defender for Cloud · Key Vault + CMK · Azure Purview
  Subscription vending (product teams land in spoke subscriptions)
```

---

## 4. Layer-by-Layer Service Map

### Layer 1 — Identity & Tenancy

| Requirement | Azure service | Notes |
|---|---|---|
| Internal employee auth (PwC ~400 entities) | **Entra ID** with managed identity for workloads | No stored API keys; all service-to-service via managed identity |
| External prospect / client auth | **Entra External ID** (formerly Azure AD External Identities) | B2C-style external tenant; handles guest lifecycle |
| 1-hour demo access (showroom QR-code) | Entra External ID guest invitation + short-lived signed JWT | exp = now+1h; conditional-access policy limits scope to showroom apps |
| Fine-grained relational authorisation | **OpenFGA** (self-hosted on Azure Container Apps) | Time-bounded relations, "who can see which demo for how long"; avoids Auth0 SaaS cost cliff |
| Asset-level access control | **Azure RBAC** on APIM subscriptions + Entra app roles | Coarse grain: which team/client can call which asset |
| Data-level access control (domain assets) | **Unity Catalog** row/column-level security | Carries through to every agent tool call on the Databricks side |

### Layer 2 — Gateway / Quota / Safety

**Azure API Management — AI Gateway tier** is non-negotiable. It is the single control plane for all LLM traffic.

| Policy | What it does | When to configure |
|---|---|---|
| `azure-openai-token-limit` | Per-subscription TPM cap; 429 on overage | From day one for every team |
| `azure-openai-semantic-cache` | Redis-backed similarity cache; 20–40% cost reduction | After first 10 active teams |
| `llm-content-safety` | Azure Content Safety on every prompt/response | From day one, mandatory |
| `emit-token-metric` | Token usage → App Insights → Cost Management | From day one for chargeback |
| `expose-mcp-server` | Wraps any APIM REST product as an MCP tool | Per asset, at certification time |
| `a2a-agent-governance` | Registers and governs agent-to-agent calls | When multi-agent orchestration goes live |
| PTU + PAYG pool | Auto-failover from provisioned to pay-as-you-go | Configure at first production load |

**Latency tax: ~2–5 ms per call.** This is the price of governance. Do not bypass APIM "for performance."

### Layer 3 — Agent Runtime

**Default: Azure Container Apps + LangGraph (Python)**

Rationale: the team has committed to LangGraph/LangChain/LangSmith. ACA provides scale-to-zero when idle, no Kubernetes operations burden, and Dapr for service-to-service and pub/sub between graph nodes.

```
ACA (orchestrator agent)
  │  Dapr pub/sub
  ├─► ACA (specialist agent: summarise)   ─► APIM → /summarize MCP tool
  ├─► ACA (specialist agent: extract)     ─► APIM → /extract MCP tool
  └─► ACA (specialist agent: search/RAG)  ─► APIM → /rag MCP tool
        │  Dapr state-store
        └─► Cosmos DB (conversation memory, agent state)
```

**Optional: Azure AI Foundry Agent Service** (Profile A only — see §5)

Use Foundry Agent Service when: the client is Azure-only greenfield with no LangGraph investment, or when Microsoft Copilot Studio / Teams integration is required from the agent runtime.

**When to use AKS instead of ACA:** only if the organisation already operates AKS and needs to co-locate agent microservices with non-AI workloads in the same cluster. Default to ACA; AKS adds significant operational overhead.

### Layer 4 — Tools / Assets

**CORE placement** (cross-engagement, no domain data):

| Asset | Implementation | MCP exposure |
|---|---|---|
| Document extraction | Azure Document Intelligence → OpenAI enrichment → Blob/Search | `/extract` MCP tool via APIM |
| Summarisation | Azure OpenAI (GPT-4o) with managed prompt template + semver | `/summarize` MCP tool |
| Semantic / hybrid search | Azure AI Search (vector + BM25 hybrid) | `/search` MCP tool |
| Text classification | Azure OpenAI + structured output | `/classify` MCP tool |
| Translation | Azure AI Translator | `/translate` MCP tool |
| Embedding | Azure OpenAI text-embedding-3-large | `/embed` MCP tool |
| Authentication components | Entra ID SDK wrappers (TypeScript + Python) | Not MCP — shared package in Azure Artifacts |
| Data transformers | LangGraph node library (Python, ≤50 LOC each) | Imported directly in agent graphs |

**DOMAIN placement** (data-gravity assets — deferred to Knowledge Base phase):

| Asset | Implementation | Governance |
|---|---|---|
| Domain vector search | Mosaic AI Vector Search over Delta table | UC permissions → auto-sync on data update |
| Domain SQL agent | Genie Space over UC-registered table | Text-to-SQL; UC row-level security enforced |
| Domain Python tools | UC Functions (`@uc_function` Python decorators) | UC ACLs + lineage; callable via `get_tools()` |
| Fine-tuned models | Mosaic AI Model Serving (MLflow-registered) | MLflow stage promotions: Staging → Production |

### Layer 5 — Models

| Model type | Primary | Fallback | Routing |
|---|---|---|---|
| Chat / reasoning | Azure OpenAI GPT-4o (PTU) | Azure OpenAI GPT-4o PAYG | APIM load-balance policy |
| Embeddings | Azure OpenAI text-embedding-3-large | Foundry Models | APIM routing header |
| Open / fine-tuned | Databricks Mosaic AI FMAPI (DBRX, Llama) | — | Direct endpoint via APIM product |
| Vendor-neutral fallback | LiteLLM proxy container on ACA | — | Routes to Anthropic / Mistral / Bedrock as needed |

**Model upgrade governance**: Foundry Evaluations runs regression tests before any GPT version bump reaches production. Regression gate is encoded in the CI/CD pipeline — no human committee.

### Layer 6 — Observability & Evaluation

Every inference produces **four streams**:

1. **LangSmith trace** — every LangGraph node: input, output, token count, latency. Used by developers for debugging and by LangSmith eval runs for quality gates.
2. **Application Insights span** — distributed trace from APIM → agent → tool → model. Used by platform team for SLA monitoring and by Product Owner for usage dashboards.
3. **Emit-token-metric → Cost Management** — per-subscription token usage for chargeback.
4. **Event Hub → ADLS Gen2** — immutable audit lake. Every request, every tool call, every model response, timestamped and signed. Required for GDPR data-subject requests and for SOX-style AI audit.

**Real-user metrics (showroom)**: Application Insights JavaScript SDK (RUM) instrumented in the showroom front-end. Session duration, feature usage, and error rates flow to Log Analytics. Power BI dashboard over Log Analytics provides the "how long did the customer spend in the app" view Adrian requested.

---

## 5. Two Delivery Profiles

### Profile A — Single client at scale

Use when: delivering an assetization engagement for a large enterprise client (1,000+ employees, regulated industry, existing Azure investment).

| Dimension | Profile A choice |
|---|---|
| Landing zone | CAF GenAI Landing Zone — full hub-and-spoke, Azure Policy-as-Code, Defender for Cloud |
| Runtime | Foundry Agent Service (managed, no k8s ops) preferred over ACA |
| Data governance | Unity Catalog (if Databricks present) + Microsoft Purview federated |
| Model access | PTU primary (committed capacity) + PAYG fallback |
| Identity | Entra ID throughout; no external tenant needed |
| Marketplace topology | Playbook Topology A (internal to the client) |
| Build-vs-buy for auth | Entra-native; Copilot Studio for Teams delivery channel |

### Profile B — Cross-engagement portable (PwC delivery side)

Use when: building PwC's own asset supply chain — the Lego pieces that travel from engagement to engagement.

| Dimension | Profile B choice |
|---|---|
| Runtime | ACA + LangGraph (Python) — portable, no Foundry lock-in |
| Every asset has TWO implementations | `azure/` (Azure-native) and `generic/` (LiteLLM + standard SDK) |
| MCP as universal contract | Every capability is an MCP server so it plugs into any client's runtime |
| Data governance | Metadata in `asset.toml` + Azure AI Search index; Databricks only if data gravity demands it |
| Identity | Entra ID (internal, Profile B-side) + Entra External ID (Topology C external clients) |
| Marketplace topology | Playbook Topology B → C as maturity grows |
| Auth for showroom | Short-lived guest tokens + OpenFGA (see `docs/auth-design-note.md`) |

**These profiles are not mutually exclusive.** A Profile B portable agent can deploy into a Profile A client landing zone via a WRAPPER asset (Playbook §II.1 WRAPPER placement) that adapts the portable agent to the client's identity, networking, and data model.

---

## 6. Phased Sequencing

The Playbook's four-phase assetization maturity model, mapped to Azure deliverables:

### Phase 1 — Lock in standards (Months 0–1)

**Goal:** discipline before tooling. No marketplace without governance.

| Deliverable | Azure / tool |
|---|---|
| `asset.toml` metadata schema published | Git repo + PR template |
| CI certification gate live | GitHub Actions / Azure DevOps Pipeline: Ruff, mypy, pytest ≥80%, gitleaks, semver-action, RAI checklist |
| APIM AI Gateway deployed | Bicep IaC; token-limit + content-safety + emit-token policies active |
| Entra ID + External ID tenant configured | Azure Portal + Bicep; conditional-access policy for 1-hour guest sessions |
| CAF Landing Zone foundations | Hub VNet, private endpoints for Azure OpenAI, Key Vault |
| ART (Asset Reuse Team) operating rhythm | Weekly extraction retrospective; ART lead assigned |
| First 5 CORE assets committed and certified | Summarise, extract, classify, embed, auth wrapper |

**Do not ship the marketplace discovery UI in this phase.**

### Phase 2 — Launch Marketplace v1 (Months 1–3)

**Goal:** searchable, instrumented, first real reuse.

| Deliverable | Azure / tool |
|---|---|
| Azure AI Search metadata index live | Indexes all `asset.toml` files across repos; hybrid vector + BM25 |
| APIM semantic cache deployed | Redis Premium; configure per-asset caching headers |
| 20 certified CORE assets published as MCP servers | All behind APIM `expose-mcp-server` policy |
| Showroom v1 deployed to ACA | Front-end consuming CORE assets; 1-hour QR-code access live |
| LangSmith workspace + eval dataset | First 50 golden Q&A pairs per CORE asset |
| Reuse Rate KPI dashboard | Power BI on Log Analytics; target 5% by end of Month 3 |

**Prerequisite for showroom:** auth-design-note.md design must be approved and implemented.

### Phase 3 — Secure proof points (Months 3–4)

**Goal:** demonstrable reuse across ≥3 engagements or internal teams.

| Deliverable | Azure / tool |
|---|---|
| ≥3 consuming teams using assets via APIM + MCP | Evidenced by `emit-token-metric` dashboards |
| Reuse Rate ≥25% | Measured via Log Analytics query |
| Domain assets v1 (if Knowledge Base phase starts) | Unity Catalog Functions + Mosaic Vector Search on Azure Databricks |
| Automated deprecation pipeline | Azure DevOps / GitHub Action: flag assets with 0 consumers for 2 quarters |
| Chargeback showback report | Cost Management export + Power BI per-team token spend |

### Phase 4 — Culture change (Months 4–6)

**Goal:** reuse-first is the default, not the exception.

| Deliverable | Azure / tool |
|---|---|
| Reuse Rate ≥40% | Sustained, not one-off |
| Marketplace discovery UI | ACA-hosted web app; **only after ≥50 assets** |
| Reputation + recognition in perf review | Operating model change, not a tool |
| Hall of fame dashboard live | Power BI + Teams channel notifications |
| External marketplace open (Topology C) | APIM developer portal with Entra External ID SSO |
| A2A governance live | APIM a2a-agent-governance policy; registered agent-to-agent calls |

---

## 7. Key Performance Indicators

| KPI | Target trajectory | Azure source of truth |
|---|---|---|
| **Reuse rate** (% of assets consumed by ≥2 teams) | 5% M3 → 25% M6 → 40%+ M12 | Log Analytics: join `asset.toml` tags with APIM `emit-token-metric` + MLflow deployment records → Power BI |
| **Time-to-first-reuse** | < 48h from certification | Delta between Azure Artifacts publish timestamp and first APIM call with asset ID |
| **Contribution SLA** | < 5 business days from PR open to DRAFT status | Azure DevOps / GitHub PR analytics on CI pipeline |
| **Stale-asset rate** | < 10% of catalogue | Azure AI Search + APIM: assets with 0 calls in last 2 quarters; automated deprecation flag |
| **Engagement reuse uplift** | ≥40% build-hour reduction on second engagement | Cost Management exports by engagement subscription tag; compared engagement N vs. engagement 1 |
| **LLM quality score** | ≥0.85 groundedness (LangSmith eval) | LangSmith evaluation run on golden dataset; must pass before BETA → STABLE promotion |
| **Showroom session duration** | Track only; no target set yet | App Insights RUM: session duration, feature engagement |
| **Cost per inference** | Track only; optimise per asset | APIM `emit-token-metric` → Cost Management; semantic cache hit rate in Redis |

**Asset count is NOT tracked as a KPI.** It is a vanity metric that incentivises low-quality snippets.

---

## 8. Trade-offs and Known Risks

### 8.1 Two governance surfaces (Purview + Unity Catalog)

**The risk:** operators must maintain governance metadata in two systems.

**The mitigation:** assign clear ownership:
- **Unity Catalog** is the source of truth for: data lineage, data classification (`pii`, `financial`, `public`), row/column-level access rules on domain assets.
- **Microsoft Purview** is the source of truth for: asset lifecycle (DRAFT → STABLE → DEPRECATED), sensitivity labels, cross-platform search federation.
Both are federated — do not duplicate metadata across them.

### 8.2 Foundry Agent Service regional availability

**The risk:** Foundry Agent Service is not GA in all Azure regions as of mid-2026, particularly in some EU-regulated regions.

**The mitigation:** ACA + LangGraph is the default runtime precisely because it has no region restrictions. Design every agent to be deployable on either runtime without code changes (the WRAPPER pattern handles environmental adaptation).

### 8.3 APIM latency

**The risk:** APIM adds 2–5 ms per call. Teams will ask to bypass it "for performance."

**The response:** the chargeback, quota enforcement, content safety, and MCP exposure are all implemented in APIM. Bypassing it is equivalent to removing governance. The 2–5 ms cost is the price of compliance. Document this as a non-negotiable architectural decision.

### 8.4 OpenFGA maturity

**The risk:** OpenFGA is relatively young (originally Auth0 open-source, now CNCF sandbox) and the operations knowledge within most enterprise teams is low.

**The mitigation:** run OpenFGA self-hosted on a single ACA container (scale-to-zero when idle). It has a simple deployment model and a well-documented Zanzibar relation model. If it proves operationally burdensome, the fallback is Entra ID app-role claims for coarse authz + APIM subscription policies. The interface boundary is clean.

### 8.5 Marketplace UI temptation

**The risk:** stakeholders will ask for a browsable marketplace catalogue in Month 1.

**The response:** 20 assets fit in a Markdown file with Ctrl+F. The Azure AI Search API already provides programmatic discovery. The UI is the last 10% of the value and the first 50% of the build time. Playbook §III.3 is explicit: build Layer 6 (UI) only after Layer 5 (metadata search) is proven at ≥50 assets.

### 8.6 TypeScript ↔ Python boundary

**The risk:** TypeScript (BFF, auth, front-end) and Python (LangGraph, agent graphs, tools) are both in use. Without a clear boundary, glue code proliferates.

**The resolution:** the APIM gateway + MCP protocol is the language boundary. Python tools are exposed as MCP servers (language-agnostic JSON-RPC over HTTP). TypeScript consumers call them via the standard MCP SDK. No direct Python-TypeScript interop is required in production.

---

## 9. Cross-Reference Index

| ARA-A layer / concept | Playbook section | Research pattern |
|---|---|---|
| The loop | §0.1 (loop diagram) | §2.2 (Assetization solves) |
| CORE / DOMAIN / WRAPPER placement | §II.1 | §4 (Layer 4 tools) |
| CI certification gate | §II.4 | §VII.6 (research §7) |
| Asset metadata schema | §III.4 | §B3 (UC Functions as metadata) |
| APIM AI Gateway | §III.6 (Layer 2) | **A3** |
| Azure AI Search metadata index | §III.5 (Layer 5) | A6 + A3 |
| Marketplace discovery UI | §III.6 (Layer 6) | A5 (ACA hosting) |
| Foundry Agent Service | §VI.1 (phase 3) | **A2** |
| ACA + LangGraph | §VII.8 (2026 default) | A5 |
| CAF GenAI Landing Zone | §IV.1 | **A4** |
| Multi-tenant / external | §III.14 | **A7** |
| Entra ID + External ID | §V.2 | A7 + C2 |
| OpenFGA | *New — from meeting 2026-07-01* | — |
| Short-lived demo tokens | *New — from meeting 2026-07-01* | — |
| Unity Catalog + Databricks (domain tier) | §II.1 DOMAIN | B3 + B4 + B5 |
| MCP as universal protocol | §VII.7 | **C1** |
| LangSmith / LangFuse observability | §VII.8 | Layer 6 |
| Immutable audit lake | §III.13.5 | Layer 6 |
| Reuse Rate KPI | §III.11 | — |
| 4-hour extraction rule | §II.2 | — |
| Automated deprecation | §III.9 | — |
| ART (Asset Reuse Team) | §III.12 | — |

---

*Last updated: 2026-07-01. Review cycle: monthly until Phase 2 complete, then quarterly. Owner: Raimondo Marino, Solution AI Architect.*
