---
title: "Agent Assetization on Azure & Databricks"
subtitle: "Architectural Patterns for Exposing AI Services to Internal Teams and External Clients"
author: "Architecture Research"
date: "2026-06-29"
---

# Agent Assetization on Azure & Databricks

> **Architectural Patterns for Exposing AI Services to Internal Teams and External Clients**
>
> Date: 2026-06-29 | Edition: 1.0

---

## Table of Contents

1. Executive Summary
2. Motivation: Why "Assetize" AI Capabilities?
3. Glossary of Key Terms
4. Recurring Architecture Layers — The 6-Layer Taxonomy
5. Section A — Azure-Native Architectures
6. Section B — Azure + Databricks (Mosaic AI) Architectures
7. Section C — Cross-Vendor Gateways, MCP, and Agent Marketplaces
8. Case Study Deep Dives
9. Comparison Matrices
10. Decision Framework
11. Appendix A — Numbered Citation List
12. Appendix B — Acronym Index

---

## 1. Executive Summary

"Agent assetization" is the practice of packaging discrete AI capabilities — summarization, document extraction, translation, classification, retrieval-augmented generation (RAG), code generation — into **reusable, governed, discoverable assets** that can be called by AI agents, developer teams, or external client systems.

This report synthesizes the key architectural patterns that enterprises worldwide have implemented or published for this purpose, with a focus on **Microsoft Azure** (alone) and **Azure + Databricks** as the primary cloud platforms. It also covers cross-vendor patterns — AI gateways, Model Context Protocol (MCP) servers, and agent marketplaces — that complement or replace cloud-native services.

Key findings:

- **Six architectural layers** recur across every pattern: identity/tenancy, gateway/quota, agent runtime, tools/assets, models, and observability.
- **Azure APIM as an AI/GenAI Gateway** is the most widely adopted production pattern for multi-team or multi-client exposure of shared OpenAI services.
- **Azure AI Foundry Agent Service** is the recommended runtime for well-architected production agents on Azure.
- **Databricks Mosaic AI** provides the strongest story when data gravity is in the Lakehouse and governance (Unity Catalog) matters.
- **Model Context Protocol (MCP)** is rapidly becoming the standard wire protocol for agent-tool communication, with Microsoft, OpenAI, Anthropic, and Google all adopting it.
- A **hybrid pattern** — Databricks Lakehouse for data + tools governance, Azure AI Foundry or Container Apps for agent runtime — is the dominant production choice in regulated European industries.

---

## 2. Motivation: Why "Assetize" AI Capabilities?

### 2.1 The Problem Without Assetization

Without an assetization layer, every product team builds its own:

- Direct calls to an LLM API with hardcoded keys.
- Bespoke document-extraction pipelines with no reuse.
- Duplicate RAG stacks (different chunking strategies, different embedding models).
- No cost attribution: one team's runaway experiment starves others of token quota.
- No audit trail: compliance teams cannot demonstrate which model version produced which output.

The result is **shadow AI** — valuable but fragile, expensive, non-compliant, and impossible to maintain at scale.

### 2.2 What Assetization Solves

| Business Need | Assetization Mechanism |
|---|---|
| Reuse across teams | Shared service endpoints / SDK |
| Cost attribution & chargeback | API gateway with per-team subscription keys + token metering |
| Compliance & audit | Immutable inference logs, model versioning, data lineage |
| Quality assurance | Evaluation pipelines (LLM-as-judge, human review) before promotion |
| Model upgrades | Swap backend model without changing consumer contract |
| External monetization | Multi-tenant gateway with customer isolation |

### 2.3 Internal vs External Exposure

| Mode | Typical Patterns |
|---|---|
| **Internal (dev teams)** | APIM AI Gateway + inner-loop SDK, Mosaic AI Gateway, UC Functions, MCP servers on private networks |
| **External (B2B clients)** | Multi-tenant APIM, Foundry Project-per-tenant, external-facing MCP/A2A endpoints, Copilot Studio extensions |
| **Hybrid** | Internal Gateway promoted to external tier with additional auth (Entra External ID) and stronger isolation (row-level or silo tenancy) |

---

## 3. Glossary of Key Terms

| Term | Definition |
|---|---|
| **Agent** | A software entity that uses an LLM to plan, reason, and invoke tools in order to complete a goal. |
| **Agent Assetization** | Packaging an AI capability (a model, a pipeline, a tool, a workflow) as a governed, versioned, discoverable, callable asset. |
| **A2A (Agent-to-Agent)** | Google-proposed protocol (now multi-vendor) for agents to discover and call other agents. |
| **AI Gateway** | A reverse proxy in front of LLM endpoints that adds auth, rate-limiting, caching, logging, and content safety. |
| **Azure AI Foundry** | Microsoft's unified platform for AI model selection, fine-tuning, evaluation, and agent orchestration. |
| **Foundry Agent Service** | The managed runtime inside Azure AI Foundry for deploying and running stateful prompt agents with tools. |
| **MCP (Model Context Protocol)** | Anthropic-originated open standard for a server that exposes tools, resources, and prompts to any MCP-capable agent client. |
| **Mosaic AI** | Databricks' AI product suite: Model Serving, Agent Framework, Vector Search, AI Gateway, AI Functions. |
| **RAG (Retrieval-Augmented Generation)** | Pattern where retrieved context (from a search index) is injected into an LLM prompt before generation. |
| **Unity Catalog** | Databricks' data + AI governance layer providing access control, lineage, auditing for tables, models, and functions. |
| **Lakehouse** | Data architecture combining the flexibility of a data lake with the management features of a data warehouse (Databricks' term). |
| **APIM** | Azure API Management — Microsoft's enterprise API gateway. |
| **LLM-as-Judge** | Using a language model to automatically evaluate another language model's output against a rubric. |
| **TPM / PTU** | Tokens Per Minute / Provisioned Throughput Units — Azure OpenAI capacity units. |

---

## 4. Recurring Architecture Layers — The 6-Layer Taxonomy

Research across all patterns reveals **six layers** that every production "agent assetization" platform must address:

```
┌──────────────────────────────────────────────────────┐
│ 6. Observability & Evaluation                        │
│    (tracing, eval, monitoring, feedback loops)       │
├──────────────────────────────────────────────────────┤
│ 5. Models                                            │
│    (model catalog, versioning, fine-tuning, routing) │
├──────────────────────────────────────────────────────┤
│ 4. Tools / Assets                                    │
│    (summarization, extraction, search, code, …)      │
├──────────────────────────────────────────────────────┤
│ 3. Agent Runtime                                     │
│    (orchestration, memory, planning, tool calling)   │
├──────────────────────────────────────────────────────┤
│ 2. Gateway / Quota / Safety                          │
│    (auth, rate-limit, cache, content-safety, billing)│
├──────────────────────────────────────────────────────┤
│ 1. Identity & Tenancy                                │
│    (who can call what, data isolation per tenant)    │
└──────────────────────────────────────────────────────┘
```

| Layer | Azure-native option | Azure + Databricks |
|---|---|---|
| **1. Identity & Tenancy** | Entra ID + APIM subscription keys / managed identity | Entra ID + Unity Catalog privileges + workspace-per-tenant |
| **2. Gateway / Quota / Safety** | APIM GenAI Gateway (token-rate-limit, semantic-cache, content-safety) | Mosaic AI Gateway (rate limits, PII detection, inference tables) |
| **3. Agent Runtime** | Foundry Agent Service / Azure Container Apps / AKS | Mosaic AI Agent Framework on Model Serving |
| **4. Tools / Assets** | Foundry tools, OpenAPI-exposed services, MCP servers | UC Functions, Vector Search, Genie spaces, MLflow-registered tools |
| **5. Models** | Azure OpenAI / Foundry Models catalog | Databricks Foundation Model APIs + External Models (pass-through to AOAI) |
| **6. Observability & Eval** | App Insights, Azure Monitor, Foundry Evaluations | MLflow Tracing, Agent Evaluation (LLM-judge + Review App), Lakehouse Monitoring |

---

## 5. Section A — Azure-Native Architectures

### A1. Baseline Microsoft Foundry Chat / Agent Architecture

**Pattern type:** Production-baseline reference architecture
**Published by:** Microsoft (Azure Architecture Center)

#### Components

| Component | Role |
|---|---|
| Azure AI Foundry | Hub for model catalog, prompt flows, evaluations |
| Foundry Agent Service | Managed runtime executing stateful prompt agents |
| Azure OpenAI | LLM backend (GPT-4o, GPT-4, Embeddings) |
| Azure AI Search | Vector + hybrid retrieval (RAG knowledge base) |
| Azure App Service / Container Apps | Chat UI / API surface |
| Azure Front Door + WAF | Global load balancing, DDoS, geo-filtering |
| Private Endpoints + VNet | All traffic on private network; no public FQDN for backends |
| Azure Key Vault | Secrets and encryption keys |
| Log Analytics / App Insights | Distributed tracing, telemetry |
| Microsoft Agent Framework SDK | .NET / Python SDK for orchestrating agents with tools |

#### Description

This is Microsoft's canonical "well-architected" enterprise baseline for any chat or agent application built on Foundry Agent Service. It extends the simpler "basic" pattern with:

- **Zone-redundant** deployments for Azure OpenAI, AI Search, and App Service.
- **Private networking** — every AI service is behind a private endpoint; no traffic traverses the public internet within the Azure boundary.
- **Identity-based access** — workloads authenticate to Foundry and OpenAI via managed identities, eliminating stored API keys.
- **Observability** — distributed traces flow from the agent runtime through App Insights; cost / token usage is exported to Log Analytics.

#### When to Use

- Building an internal or customer-facing chat/agent application where security posture and uptime SLAs are non-negotiable.
- Starting point for any regulated-industry (finance, healthcare) deployment.

#### Trade-offs

| Pro | Con |
|---|---|
| Well-architected, HA, private | Complex initial setup (VNet, private DNS) |
| Managed runtime (no k8s ops) | Foundry Agent Service region availability limitations |
| First-party SLA on each component | Vendor lock-in to Foundry tool ecosystem |

#### Citations

- **[1]** [Microsoft Learn — Baseline Foundry chat architecture](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat)
- **[2]** [Microsoft Learn — Basic Foundry chat architecture](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/basic-azure-ai-foundry-chat)

---

### A2. Azure AI Foundry Agent Service — Multi-Agent Platform

**Pattern type:** Managed multi-agent platform
**Published by:** Microsoft (Azure AI documentation)

#### Components

| Component | Role |
|---|---|
| Foundry Agent Service | Manages agent lifecycle, state, tool routing |
| Connected Agents | First-class sub-agents callable from a parent agent |
| Foundry Models catalog | Browse, compare, deploy models (Azure OpenAI, Mistral, Meta Llama, Phi, etc.) |
| Built-in tools | Bing Search, File Search, Azure AI Search, Code Interpreter, Azure Functions, Logic Apps, OpenAPI connectors |
| Tracing | Request → span → token-level traces to App Insights |
| Azure RBAC | Fine-grained control over who can create/manage/call agents |

#### Description

Foundry Agent Service is the managed runtime layer for agent assetization. Each agent is a **first-class Azure resource** with its own identity, tool list, versioning history, and execution trace. The platform supports:

- **Tool registration**: any REST API (via OpenAPI spec) or Azure-native service becomes a callable tool in seconds.
- **Connected Agents**: one orchestrator agent delegates tasks to specialist agents (extraction agent, summarization agent, search agent) — a natural fit for the assetization paradigm.
- **Durable execution**: long-running threads persist beyond a single HTTP request, enabling async workflows over minutes or hours.

For assetization, the pattern is: *build each capability as a specialist Foundry Agent → register it as a connected agent → expose the orchestrator via APIM or a front-end app*.

#### When to Use

- Greenfield agent platform on Azure, no existing data in Databricks.
- You need low-ops managed hosting (no Kubernetes expertise in team).
- Mix of in-house models + marketplace models.

#### Trade-offs

| Pro | Con |
|---|---|
| Fully managed, auto-scales | Less flexible than self-hosted runtimes |
| Rich tool ecosystem | Tracing depth limited vs MLflow |
| Native Azure RBAC | Not yet GA in all Azure regions (as of 2026) |

#### Citations

- **[3]** [Microsoft Docs — Azure AI Foundry Agent Service overview](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview)
- **[4]** [Microsoft Docs — Foundry connected agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/connected-agents)
- **[5]** [Microsoft Docs — Foundry Agent Service tools](https://learn.microsoft.com/en-us/azure/ai-services/agents/tools/overview)

---

### A3. Azure API Management (APIM) "GenAI Gateway"

**Pattern type:** Shared-services AI gateway — **the most widely deployed pattern** for enterprise agent assetization
**Published by:** Microsoft (Azure Architecture Center + open-source accelerator)

#### Components

| Component | Role |
|---|---|
| APIM (AI Gateway tier) | Central reverse proxy for all LLM traffic |
| `azure-openai-token-limit` policy | Per-subscription TPM quota enforcement |
| `llm-content-safety` policy | Azure Content Safety integration per request |
| `azure-openai-semantic-cache` policy | Redis-backed semantic (embedding-similarity) cache |
| `emit-token-metric` policy | Token usage → App Insights / Cost Management |
| Load-balanced OpenAI pool | PTU backends + PAYG fallback across regions |
| Unified model API | Single OpenAI-compatible endpoint routing to Anthropic / Bedrock / Vertex |
| MCP server exposure | `expose-mcp-server` policy: wraps APIM-hosted REST APIs as MCP servers |
| A2A agent governance | Registers and governs agent-to-agent calls |

#### Description

This is the **most adopted** enterprise pattern for exposing shared AI services to many teams or clients, as documented in the Microsoft AI-Gateway GitHub accelerator (1,000+ stars). APIM sits in front of all Azure OpenAI (or Foundry Models) deployments and provides:

1. **Per-team quotas**: each squad gets its own APIM subscription key with a monthly TPM cap; overage → 429 response.
2. **Chargeback**: `emit-token-metric` exports per-subscription token counts to Application Insights, feeding dashboards and showback reports.
3. **Semantic caching**: frequently asked questions are answered from an embedding-similarity cache (Redis), cutting LLM calls and cost by 20–40% in typical enterprise Q&A workloads.
4. **Content safety**: every request passes through Azure Content Safety before reaching the model.
5. **PTU + PAYG load balancing**: automatically fail over from provisioned-throughput (PTU) deployments to pay-as-you-go when capacity is exhausted.
6. **Model abstraction**: a single `POST /openai/deployments/{model}/chat/completions` endpoint routes to whichever backend (Azure OpenAI, Anthropic Claude via proxy, Mistral, etc.) matches the requested model name.
7. **MCP server generation**: APIM can wrap any of its REST API products as an MCP server, making them natively callable by any MCP-capable agent.

#### When to Use

- Exposing Azure OpenAI to many internal dev teams or external clients from a single, governed endpoint.
- Multi-cloud or multi-vendor LLM routing from a single API surface.
- Anywhere cost attribution, quota enforcement, and audit are required.

#### Trade-offs

| Pro | Con |
|---|---|
| Battle-tested, production-proven | APIM adds ~2–5 ms latency |
| Rich built-in AI policies | Policy syntax (Liquid) has learning curve |
| Single control plane for all AI traffic | Per-call semantic cache requires Redis (cost) |
| OpenAI-compatible — no client changes | Does not manage agent state (use Foundry for that) |

#### Citations

- **[6]** [Azure Architecture Center — AI gateway guide](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/azure-openai-gateway-guide)
- **[7]** [Azure API Management — GenAI gateway capabilities](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities)
- **[8]** [GitHub — AI-Gateway accelerator (Microsoft)](https://github.com/Azure-Samples/AI-Gateway)
- **[9]** [APIM — Expose MCP servers](https://learn.microsoft.com/en-us/azure/api-management/expose-mcp-servers)

---

### A4. Azure Cloud Adoption Framework (CAF) — GenAI Landing Zone

**Pattern type:** Enterprise-scale platform landing zone for GenAI workloads
**Published by:** Microsoft (Cloud Adoption Framework)

#### Components

| Component | Role |
|---|---|
| Hub-and-spoke VNet topology | Network isolation; AI services on spoke VNets |
| Azure Policy as Code (Bicep/Terraform) | Enforce private endpoint, approved regions, encryption |
| Central APIM | Shared AI gateway for all landing zone subscriptions |
| Azure OpenAI + AI Search + Document Intelligence | Shared AI services in "platform" subscription |
| Microsoft Defender for Cloud | Threat detection for AI workloads |
| Azure Purview / Microsoft Purview | Data governance and sensitivity labeling |
| Subscription vending | Self-service subscription creation for each product team |

#### Description

The CAF GenAI landing zone provides the **organizational and governance scaffolding** for agent assetization at scale. It separates responsibilities:

- **Platform team** owns the hub, APIM, shared OpenAI deployments, AI Search, and Document Intelligence — the "platform services" that get assetized.
- **Product teams** land in spoke subscriptions with controlled access to platform services via private endpoints and APIM subscription keys.
- **Azure Policy** enforces that no product team can call OpenAI directly from the internet; all traffic must traverse the hub.

This is often the first architecture an enterprise sets up *before* choosing between Foundry Agent Service and Databricks for the runtime layer.

#### When to Use

- Large enterprise (1,000+ developers) building multiple AI products simultaneously.
- Regulated industry where network isolation and audit trails are mandatory.
- Multi-subsidiary or holding-company structure needing charge-back by legal entity.

#### Citations

- **[10]** [Microsoft CAF — AI platform landing zone](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/scenarios/ai/platform/landing-zone)
- **[11]** [Microsoft CAF — AI ready landing zones overview](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/scenarios/ai/)

---

### A5. Agent Hosting on Azure Container Apps / AKS (LangGraph, Semantic Kernel, AutoGen)

**Pattern type:** Self-hosted agent runtime on Azure compute
**Published by:** Microsoft + community (Azure Architecture Center, devblogs)

#### Components

| Component | Role |
|---|---|
| Azure Container Apps (ACA) | Serverless container hosting; scale-to-zero for agents |
| Azure Kubernetes Service (AKS) | Full Kubernetes for complex multi-agent topologies |
| Dapr (Distributed Application Runtime) | State management, pub/sub, service-to-service for agent microservices |
| Azure Service Bus | Async message queue for long-running agent tasks |
| Azure Cosmos DB | Conversation memory, agent state persistence |
| Azure OpenAI | LLM backend |
| LangGraph / LangChain | Agent graph orchestration (Python) |
| Semantic Kernel | Microsoft's SDK for agent orchestration (.NET / Python) |
| AutoGen | Microsoft Research's multi-agent conversation framework |
| KEDA | Kubernetes-based event-driven autoscaling (for AKS) |

#### Description

When Foundry Agent Service is too restrictive (e.g., custom graph topologies, proprietary orchestrators, latency requirements), teams **self-host** agent runtimes in containers on ACA or AKS. Common patterns include:

- **LangGraph on ACA**: each LangGraph node (tool call, LLM call, routing decision) is a microservice container; Dapr pub/sub connects them. Scale-to-zero when idle.
- **Semantic Kernel + AKS**: enterprise .NET shops run SK agents in AKS pods with KEDA autoscaling based on Service Bus queue depth.
- **AutoGen multi-agent on ACA**: AutoGen conversation patterns (round-robin, hierarchical) run as ACA apps sharing a Cosmos DB state store.

The "assetized" capabilities (summarization endpoint, doc-extraction service, RAG endpoint) are exposed as REST APIs behind APIM and called by the agent via tool definitions.

#### When to Use

- Custom orchestration logic not supported by Foundry Agent Service.
- Existing investment in LangChain/LangGraph or AutoGen.
- Need to mix agent traffic with non-AI microservices in the same cluster.

#### Citations

- **[12]** [Azure Architecture Center — Multi-agent system using Azure AI Agents](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/multi-agent-system-using-azure-ai-agents)
- **[13]** [GitHub — Container Apps + OpenAI samples](https://github.com/Azure-Samples/container-apps-openai)
- **[14]** [Microsoft DevBlog — Semantic Kernel](https://devblogs.microsoft.com/semantic-kernel/)
- **[15]** [Microsoft Research — AutoGen](https://github.com/microsoft/autogen)

---

### A6. Document-Processing Accelerator (Assetized "Extraction Service")

**Pattern type:** Reusable extraction + summarization service pipeline
**Published by:** Microsoft (Azure Architecture Center + Azure-Samples)

#### Components

| Component | Role |
|---|---|
| Azure AI Document Intelligence (Form Recognizer) | OCR, key-value extraction, table extraction from PDFs/images |
| Azure OpenAI | Summarization, entity extraction, classification on extracted text |
| Azure AI Search | Semantic / hybrid search index over extracted content |
| Azure Blob Storage | Raw document store (ingestion trigger) |
| Azure Functions | Event-driven orchestration of extraction pipeline |
| Azure Logic Apps | Low-code connectors for integrating with Line-of-Business systems |
| Cosmos DB | Metadata and extraction result store |

#### Description

This is the canonical **document intelligence as a service** pattern. The pipeline:

1. Document lands in Blob Storage → Function trigger fires.
2. Document Intelligence performs layout analysis, OCR, key-value extraction, table recognition.
3. Extracted text chunks are sent to Azure OpenAI for summarization, classification, or entity extraction.
4. Results + embeddings are indexed into Azure AI Search.
5. A REST API (via APIM) exposes: `/extract`, `/summarize`, `/search-by-document`.

AI agents on the platform register this as a **tool** via OpenAPI spec — they call `/extract?doc_url=...` and receive structured JSON. It is shared across all teams, versioned via APIM, and metered per document processed.

#### When to Use

- Any enterprise with high volumes of unstructured documents (invoices, contracts, medical records, financial filings).
- Building an internal "docs-as-knowledge" service consumed by multiple agent-based products.

#### Citations

- **[16]** [Azure Architecture Center — Automate document processing](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/automate-document-processing-azure-form-recognizer)
- **[17]** [GitHub — Azure Search OpenAI Demo (RAG over documents)](https://github.com/Azure-Samples/azure-search-openai-demo)
- **[18]** [Microsoft Docs — Document Intelligence overview](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview)

---

### A7. Multi-Tenant SaaS Agent Platform on Azure

**Pattern type:** B2B platform for reselling AI services to external clients
**Published by:** Microsoft (Architecture Center — multitenant guidance)

#### Components

| Component | Role |
|---|---|
| APIM (per-customer subscriptions) | Quota isolation, API key management, usage metering |
| Foundry Project per tenant (silo model) | Strongest isolation; each client has own model deployments |
| Row-level tenant isolation in AI Search (pool model) | Cost-efficient; metadata filter isolates tenant data |
| Entra External ID (formerly Azure AD B2C) | Customer identity and authentication |
| Azure Cost Management + exports | Per-tenant billing data feeds for invoice generation |
| Customer-Managed Keys (CMK) | Tenant encrypts own data with own key in Key Vault |
| Private Link per tenant (optional) | Dedicated private connectivity for enterprise clients |

#### Description

Microsoft's multitenant guidance for Azure OpenAI covers three **tenancy models**:

1. **Silo** — fully dedicated resources per tenant (Foundry Project, OpenAI deployment, AI Search index, Storage account). Maximum isolation, highest cost.
2. **Pool** — shared resources with logical separation (row-level security in AI Search, tenant-prefixed keys in Cosmos DB). Most cost-efficient, requires careful "noisy-neighbor" mitigation via APIM token limits.
3. **Hybrid** — shared compute (pool) for standard features + dedicated resources for premium customers or sensitive data.

For external B2B exposure, the typical architecture adds:
- **Entra External ID** for customer user authentication.
- **APIM developer portal** as a self-service API key vending machine.
- **Usage exports** to a billing system for consumption-based invoicing.
- **Webhook notifications** when a customer's quota is 80% consumed.

#### When to Use

- ISV building an AI SaaS product powered by Azure OpenAI.
- Enterprise creating a "private marketplace" of AI tools for subsidiary companies.
- Consulting firm productizing AI deliverables as a recurring managed service.

#### Citations

- **[19]** [Azure Architecture Center — Multitenant Azure OpenAI](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/openai)
- **[20]** [Azure Architecture Center — Multitenant AI strategy](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/multitenant-strategy-ai)
- **[21]** [Microsoft Docs — Entra External ID](https://learn.microsoft.com/en-us/entra/external-id/)

---

## 6. Section B — Azure + Databricks (Mosaic AI) Architectures

### B1. Mosaic AI Agent Framework + Agent Evaluation

**Pattern type:** End-to-end agent SDLC on the Databricks Lakehouse
**Published by:** Databricks (official documentation + blog)

#### Components

| Component | Role |
|---|---|
| Mosaic AI Agent Framework | Python authoring library (LangGraph, LangChain, LlamaIndex, raw OpenAI SDK all supported) |
| MLflow Tracing (auto-tracing) | Automatic capture of every LLM call, tool invocation, and retrieval |
| Agent Evaluation | LLM-as-judge scorers (correctness, groundedness, safety, relevance) + human Review App |
| Databricks Apps | Iterative testing UI for agent developers |
| Model Serving | One-click deployment of agent as MLflow model to a REST endpoint |
| AI Playground | No-code interface for rapid prototyping |
| Unity Catalog | Registry for agent models + tools (versioning, ACLs, lineage) |

#### Description

Databricks' end-to-end agent SDLC pattern, described as "evaluation-driven development." The workflow:

1. **Author**: developer writes agent in any Python framework; MLflow auto-tracing instruments all LLM calls without code changes.
2. **Evaluate offline**: Agent Evaluation runs LLM-as-judge scorers on a labeled dataset (golden Q&A pairs); scores are tracked as MLflow metrics.
3. **Iterate**: Review App surfaces bad outputs to SMEs; feedback is added to the evaluation dataset.
4. **Promote**: agent is registered as an MLflow model in Unity Catalog with all evaluation scores attached as metadata.
5. **Deploy**: one-click deployment to a Model Serving endpoint; the endpoint URL becomes the "asset" that other agents or apps consume.
6. **Monitor**: same LLM-judge scorers run online; drift alerts fire when quality degrades.

For assetization: each capability (summarization, extraction, RAG, classification) is a separate registered agent model in Unity Catalog, discoverable by catalog name, and called via a standard REST endpoint.

#### When to Use

- Existing Databricks workspace with data already in Delta Lake.
- Teams that want strong evaluation and quality gates before any capability is promoted to production.
- Python-first data science / ML teams.

#### Citations

- **[22]** [Databricks Docs — Mosaic AI Agent Framework](https://docs.databricks.com/en/generative-ai/agent-framework/index.html)
- **[23]** [Databricks Docs — Agent Evaluation](https://docs.databricks.com/en/generative-ai/agent-evaluation/index.html)
- **[24]** [Databricks Blog — Announcing Mosaic AI Agent Framework and Evaluation](https://www.databricks.com/blog/announcing-mosaic-ai-agent-framework-and-agent-evaluation)

---

### B2. Mosaic AI Gateway — Governed LLM Access

**Pattern type:** Databricks-native LLM gateway (the Databricks equivalent of Azure APIM GenAI Gateway)
**Published by:** Databricks (official documentation)

#### Components

| Component | Role |
|---|---|
| AI Gateway (endpoint config) | Configured on any Model Serving endpoint |
| Rate limits | Per-user, per-group, or global tokens-per-minute limits |
| PII detection | Filter / mask PII in requests and responses |
| Guardrails (input/output) | Block unsafe content, sensitive topics, profanity |
| Payload logging | All requests + responses logged to a Delta inference table |
| Inference tables | Delta tables in Unity Catalog for audit + offline evaluation |
| Fallback routing | Automatic failover to secondary model on error/timeout |
| Lakehouse Monitoring | Statistical drift detection on inference tables |

#### Description

Mosaic AI Gateway is a **built-in governance layer** applied to Model Serving endpoints without writing a proxy service. Any external model endpoint (Azure OpenAI, Anthropic, Mistral, etc.) can be placed behind the Gateway, which then:

- Enforces per-user token budgets (chargeback data flows into Unity Catalog).
- Optionally scrubs PII from the logged inference data before writing to Delta.
- Routes to a fallback model if the primary errors (cost-efficient hybrid routing).
- Stores every inference in a Delta table, making it auditable and queryable via SQL.

For assetization: teams that have LLM access mediated through the AI Gateway get a governed, auditable, and cost-attributed surface identical to APIM-based patterns, but natively on the Databricks platform.

#### When to Use

- Existing Databricks workspace; don't want to introduce APIM for LLM governance.
- Need inference logging in Delta (e.g., financial audit requirements).
- Data platform team is the primary owner of AI governance.

#### Citations

- **[25]** [Databricks Docs — AI Gateway](https://docs.databricks.com/en/ai-gateway/index.html)
- **[26]** [Databricks Docs — Configure AI Gateway on external model endpoints](https://docs.databricks.com/en/generative-ai/external-models/ai-gateway.html)

---

### B3. Unity Catalog Functions & Vector Search as Agent Tools

**Pattern type:** Data-layer tool assetization
**Published by:** Databricks (documentation + blog)

#### Components

| Component | Role |
|---|---|
| Unity Catalog Functions (UC Functions) | Python or SQL functions registered as first-class UC assets with ACLs and lineage |
| Mosaic AI Vector Search | Managed vector index over Delta table embeddings; automatic sync on data updates |
| Online Tables | Low-latency key-value lookups over Delta for real-time agent context |
| Genie Spaces (AI/BI) | Text-to-SQL natural language interface over Delta tables registered in UC |
| MLflow logged models | Registered ML/DL models callable as tools |
| UC permissions | Column-level, row-level, and function-level access control |

#### Description

This is "assetization at the data layer." Instead of building a separate microservice for each tool, you register business logic directly in Unity Catalog:

- A **Python UC Function** `summarize_document(doc_text STRING) RETURNS STRING` wraps an LLM call with your prompt template — it's registered with a description, versioned, and protected by UC ACLs.
- A **Vector Search index** over a Delta table of product documentation is registered in UC — any agent with the appropriate permission can call it as a semantic search tool.
- A **Genie Space** over a customer analytics table lets agents ask natural-language questions ("what is the churn rate for segment X?") that resolve to SQL queries.

The Mosaic AI Agent Framework natively discovers UC Functions as tools via `get_tools()` — developers don't write glue code.

#### When to Use

- Organization with mature Unity Catalog governance; want AI tools to inherit the same ACL model as data assets.
- Mixed ML + analytics teams where SQL functions and Python models coexist as tools.
- Compliance requirements mandate that every tool call be auditable in the same lineage system as data access.

#### Citations

- **[27]** [Databricks Docs — Create tools for agents (UC Functions)](https://docs.databricks.com/en/generative-ai/agent-framework/create-tools.html)
- **[28]** [Databricks Docs — Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html)
- **[29]** [Databricks Blog — Introducing Databricks AI/BI Genie](https://www.databricks.com/blog/introducing-databricks-ai-bi-genie)

---

### B4. Azure Databricks + Azure AI Foundry Hybrid Architecture

**Pattern type:** Hybrid cloud-native + Lakehouse
**Published by:** Databricks + Microsoft (joint documentation)

#### Components

| Component | Role |
|---|---|
| Databricks Lakehouse | Data platform: Delta Lake, Unity Catalog, Vector Search |
| Mosaic AI Model Serving | Inference endpoint for custom models (fine-tuned) |
| Azure AI Foundry / Foundry Agent Service | Agent runtime and orchestration |
| Azure OpenAI | Primary LLM inference (GPT-4o etc.) |
| Azure AI Search (optional) | Additional Azure-native retrieval index |
| Microsoft Purview ↔ Unity Catalog | Federated governance and lineage across both platforms |
| Private Endpoints | Databricks workspace behind Azure VNet; Foundry accesses it via private link |

#### Description

The dominant **European enterprise pattern** in regulated industries (banking, pharma, insurance). The split of responsibilities:

- **Databricks Lakehouse** owns: proprietary data, governed tools (UC Functions), vector indexes, fine-tuned model variants, inference audit logs.
- **Azure AI Foundry** owns: agent orchestration, user-facing conversation threads, Azure-native identity, front-end connectivity.

Foundry Agents call Databricks Model Serving endpoints as **OpenAPI tools**. The UC Function `summarize_contract()` is registered in Foundry as an external tool. Unity Catalog enforces which Foundry service principal is allowed to invoke which tool.

This pattern avoids duplicating either platform's strengths: Databricks' data governance is not replaced, and Azure's user-facing networking and identity capabilities are not replicated in Databricks.

#### When to Use

- Organization already has significant Databricks investment; doesn't want to migrate data to Azure AI Search.
- Data governance mandates that all PII-bearing data stays inside the Databricks compliance boundary.
- Need Foundry's user-facing features (Copilot Studio, Teams integration, Power Platform) layered over Lakehouse data.

#### Citations

- **[30]** [Databricks Blog — Build GenAI apps with Databricks and Azure OpenAI](https://www.databricks.com/blog/build-genai-apps-databricks-and-azure-openai)
- **[31]** [Microsoft Docs — Azure Databricks generative AI guide](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/)

---

### B5. Lakehouse-as-Backend for Agents (Data-Centric Compound AI)

**Pattern type:** Unified data + AI platform as agent backend
**Published by:** Databricks (Data + AI Summit presentations, research blog)

#### Components

| Component | Role |
|---|---|
| Delta Lake + Unity Catalog | Single governed store for raw data, features, embeddings, and inference logs |
| Delta Live Tables (DLT) | Streaming ingestion pipeline into the Lakehouse |
| MLflow + Model Registry | All models (embedding, fine-tuned, base) registered with evaluation results |
| Model Serving | All agent tool endpoints served from one platform |
| Lakehouse Monitoring | Statistical drift detection on Delta inference tables |
| Databricks Apps | React-based UI layer for agent interactions |
| Workflow Orchestrator | Long-running multi-step agent pipelines as Databricks Workflows jobs |

#### Description

Databricks positions the Lakehouse as the **single platform** behind every agent: data, tools, models, traces, evaluation, and serving converge in one governed boundary. This "compound AI systems" philosophy (from the Databricks research paper) means:

- The same Delta table that stores raw customer documents also stores embedding vectors (Vector Search) and inference audit records — no data silos.
- MLflow is the single registry for all model artifacts: embedding models, fine-tuned LLMs, agent definitions, tool descriptions.
- Every inference is written to a Delta inference table in Unity Catalog — making it auditable, queryable with SQL, and available for offline evaluation without additional ETL.

For financial-services organizations, this is particularly compelling because the audit requirement ("show me every prompt that led to this customer recommendation") is satisfied by a simple SQL query on the inference table.

#### When to Use

- Data teams are the primary owner of AI quality (not separate ML platform team).
- Compliance requires a single auditability surface for both data access and AI inference.
- Organization wants to avoid managing multiple platforms (no separate vector DB, no separate model registry, no separate monitoring tool).

#### Citations

- **[32]** [Databricks Blog — Lakehouse AI: Data-centric approach to GenAI](https://www.databricks.com/blog/lakehouse-ai-data-centric-approach-building-generative-ai-applications)
- **[33]** [Databricks Blog — Compound AI systems](https://www.databricks.com/blog/compound-ai-systems)
- **[34]** [MLflow documentation — MLflow Tracing](https://mlflow.org/docs/latest/llms/tracing/index.html)

---

### B6. Industry Customer Case Studies on Mosaic AI

These are verified published customer stories from Databricks:

| Customer | Industry | Capability Assetized | Source |
|---|---|---|---|
| **JetBlue** | Airline / Travel | Multi-agent BlueBot customer service platform, intent routing, baggage policies | [\[50\]](https://www.databricks.com/customers/jetblue) |
| **Block (Square / Cash App)** | FinTech | Internal "Goose" developer agent framework; code generation + incident response tools | [\[51\]](https://www.databricks.com/customers/block) |
| **AstraZeneca** | Pharma / Healthcare | Document summarization agents over clinical trial documents in Lakehouse | [\[54\]](https://www.databricks.com/customers/astrazeneca) |
| **S&P Global** | Financial Data | RAG agents over financial filings + earnings calls; analyst productivity | [\[50+\]](https://www.databricks.com/customers) |
| **Bayer** | Life Sciences | Agentic pipeline for regulatory document synthesis | [\[50+\]](https://www.databricks.com/customers) |

---

## 7. Section C — Cross-Vendor Gateways, MCP, and Agent Marketplaces

### C1. Model Context Protocol (MCP) Servers as the Universal Assetization Protocol

**Pattern type:** Open protocol for tool/resource exposure
**Published by:** Anthropic (protocol); adopted by Microsoft, OpenAI, Google, Meta (2024–2025)

#### Description

MCP is the fastest-growing standard for "assetizing" capabilities for agents. An **MCP server** is a lightweight process (Python, Node.js, Go, .NET, Java) that exposes:

- **Tools** — callable functions (e.g., `summarize_text`, `extract_invoice_fields`, `search_knowledge_base`).
- **Resources** — readable data sources (e.g., a Delta table, a SharePoint folder, a REST API response).
- **Prompts** — reusable prompt templates (e.g., "executive-summary prompt").

Any **MCP client** (Claude Desktop, GitHub Copilot, Cursor, VS Code Copilot, Azure AI Foundry Agent, Copilot Studio, custom agents) can connect to an MCP server and immediately call its tools.

Microsoft has integrated MCP at multiple levels:
- **APIM can wrap any REST API product as an MCP server** with a single policy (`expose-mcp-server`).
- **Foundry Agent Service** supports registering MCP servers as tool providers.
- **Copilot Studio** supports MCP server connectors (2025 release).
- **.NET C# MCP SDK** co-developed with Anthropic.

For assetization: host one internal MCP server per capability (or one aggregator server), place it behind APIM, and any future agent client can discover and use it without bespoke integration.

#### Citations

- **[35]** [Model Context Protocol specification](https://modelcontextprotocol.io/)
- **[36]** [Microsoft + Anthropic — official C# MCP SDK](https://devblogs.microsoft.com/dotnet/microsoft-partners-with-anthropic-to-create-official-c-sdk-for-model-context-protocol)
- **[37]** [Azure APIM — Expose MCP servers](https://learn.microsoft.com/en-us/azure/api-management/expose-mcp-servers)
- **[38]** [Anthropic — MCP GitHub](https://github.com/modelcontextprotocol)

---

### C2. Microsoft Copilot Studio + Microsoft 365 Agents SDK

**Pattern type:** Low-code / pro-code agent publishing platform
**Published by:** Microsoft

#### Components

| Component | Role |
|---|---|
| Copilot Studio | Low-code agent authoring (topics, generative actions, tool connectors) |
| Power Platform Connectors | 1,500+ pre-built connectors to SaaS + on-prem systems |
| Microsoft 365 Agents SDK | Pro-code multi-channel agent deployment (Teams, Web, Slack, Email) |
| Microsoft Dataverse | Agent memory + business data store |
| Foundry / Azure OpenAI backend | LLM inference for generative actions |
| Azure Bot Service | Channel management and delivery |
| MCP server connectors | Call external MCP-registered tools from Studio agents |

#### Description

Copilot Studio is the **low-code surface** for publishing internal AI services as agents to business users without requiring Python expertise. A business analyst can configure a "Contract Summarizer" agent in Copilot Studio that:

1. Calls the APIM-backed `/summarize` endpoint (as a Power Platform connector or MCP tool).
2. Presents results in Teams, SharePoint, or Outlook.
3. Is governed by Entra ID — only employees in the Legal department can access it.

For external client exposure, Copilot Studio agents can be published to customer-facing web channels with Entra External ID authentication. This is the fastest path from "AI capability" to "employee-facing chatbot."

#### Citations

- **[39]** [Microsoft Copilot Studio documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/)
- **[40]** [Microsoft 365 Agents SDK](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/)

---

### C3. Vendor-Neutral LLM Gateways (LiteLLM, Portkey, Kong AI Gateway, Cloudflare AI Gateway)

**Pattern type:** Open-source / SaaS LLM proxy gateways
**Published by:** Various vendors

#### Summary Table

| Gateway | Type | Key Differentiator | Citation |
|---|---|---|---|
| **LiteLLM** | Open-source Python proxy | 100+ LLM providers via unified OpenAI API; budget management, fallbacks, Langfuse/Helicone integration | [\[41\]](https://docs.litellm.ai/docs/) |
| **Portkey** | SaaS + open-source | AI gateway with guardrails, prompt management, multi-provider routing, observability | [\[42\]](https://portkey.ai/docs/product/ai-gateway) |
| **Kong AI Gateway** | Enterprise (Kong-based) | Plugin ecosystem (rate-limit, auth, cache, semantic-router) layered on Kong's existing API platform | [\[43\]](https://konghq.com/products/kong-ai-gateway) |
| **Cloudflare AI Gateway** | SaaS (Cloudflare Workers) | Edge-deployed LLM proxy with caching, analytics, fallbacks; no infrastructure to manage | [\[44\]](https://developers.cloudflare.com/ai-gateway/) |

#### Description

These gateways serve enterprises that:
- Have **multi-cloud LLM strategy** (don't want lock-in to Azure OpenAI alone).
- Have existing API gateway investment (Kong, AWS API Gateway) and want to extend it for AI.
- Prioritize **vendor-neutral** evaluation and observability tooling.

In a Databricks + Azure context, LiteLLM is frequently used to proxy calls from Databricks notebooks and agents to any LLM backend, with Azure OpenAI as the primary and Anthropic/Mistral as fallback.

#### Citations

- **[41]** [LiteLLM docs](https://docs.litellm.ai/docs/)
- **[42]** [Portkey docs](https://portkey.ai/docs/product/ai-gateway)
- **[43]** [Kong AI Gateway](https://konghq.com/products/kong-ai-gateway)
- **[44]** [Cloudflare AI Gateway](https://developers.cloudflare.com/ai-gateway/)

---

### C4. Hyperscaler Agent Marketplaces — Design Vocabulary

The other major clouds have published "agent marketplace" concepts that provide useful vocabulary for Azure/Databricks designs:

| Platform | Concept | URL |
|---|---|---|
| **AWS Bedrock AgentCore** | Managed agent runtime with tool registry, memory, code execution sandboxes | [aws.amazon.com/bedrock/agentcore](https://aws.amazon.com/bedrock/agentcore/) |
| **Google Vertex AI Agent Builder** | Grounding, extensions, data stores, agent orchestration; "Agent Garden" for tool sharing | [cloud.google.com — Agent Builder](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-builder/overview) |
| **Salesforce Agentforce** | Autonomous agents for CRM actions; agent topic + action marketplace | [salesforce.com/agentforce](https://www.salesforce.com/agentforce/) |
| **ServiceNow AI Agents** | Enterprise workflow agents; tool catalog in Now Platform | [servicenow.com — AI Agents](https://www.servicenow.com/products/ai-agents.html) |

These platforms all converge on the same 6-layer taxonomy described in Section 4, validating the framework as cloud-agnostic.

#### Citations

- **[45]** [AWS Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
- **[46]** [Google Vertex AI Agent Builder](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-builder/overview)
- **[47]** [Salesforce Agentforce](https://www.salesforce.com/agentforce/)
- **[48]** [ServiceNow AI Agents](https://www.servicenow.com/products/ai-agents.html)

---

### C5. Industry Analyst Frameworks

| Source | Finding | Citation |
|---|---|---|
| **a16z** | "Emerging architectures for LLM applications" — defines orchestration layer, retrieval layer, and tool layer as core building blocks of any production LLM system | [a16z.com — Emerging LLM architectures](https://a16z.com/emerging-architectures-for-llm-applications/) |
| **Thoughtworks Technology Radar** | "Adopt" recommendation for RAG, "Trial" for MCP and evaluation-driven development, "Assess" for A2A protocol | [thoughtworks.com/radar](https://www.thoughtworks.com/radar) |
| **McKinsey State of AI 2024** | "Platformization" of enterprise AI — building reusable, governed AI capabilities vs one-off experiments — is the primary driver of ROI in AI at scale | [McKinsey — State of AI 2024](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai) |
| **Gartner** | By 2026, 80% of enterprises will have used GenAI APIs and models; "AI engineering" (the practice of building governed AI platforms) is the critical success factor | [Gartner — GenAI Hype Cycle](https://www.gartner.com/en/articles/what-s-new-in-artificial-intelligence-from-the-2023-gartner-hype-cycle) |

---

## 8. Case Study Deep Dives

### CS1. ANZ Bank — Internal GenAI Platform for 6,000 Developers

- **Pattern used:** Azure OpenAI + APIM AI Gateway + Azure AI Foundry
- **Scale:** 6,000+ internal developers consuming shared OpenAI services
- **Key design decisions:**
  - APIM as the single entry point for all Azure OpenAI calls across all business units.
  - Per-squad subscription keys with monthly TPM budgets + showback dashboards.
  - Centrally managed content-safety policies applied universally via APIM policy.
  - Foundry for the agent development inner loop (prompt evaluation, model comparison).
- **Outcome:** Accelerated rollout of 50+ internal AI products in under 12 months with consistent governance.
- **Citation [49]:** [news.microsoft.com — ANZ GenAI platform](https://news.microsoft.com/en-au/2024/06/19/anz-builds-generative-ai-platform-for-developers/)

---

### CS2. JetBlue — BlueBot Multi-Agent Platform (Databricks)

- **Pattern used:** Mosaic AI Agent Framework + Agent Evaluation + Model Serving
- **Scale:** Customer-facing and agent-facing tools; millions of customer interactions
- **Key design decisions:**
  - Multi-agent orchestration: intent-classification agent → specialist agents (baggage, rebooking, loyalty).
  - Agent Evaluation with LLM-as-judge used to qualify each specialist agent before deployment.
  - All inference logs in Delta; fed back to offline evaluation dataset continuously.
  - A/B testing of agent versions managed through MLflow model registry stages.
- **Outcome:** Significant reduction in human escalation rate; faster time-to-market for new agent capabilities.
- **Citation [50]:** [databricks.com/customers/jetblue](https://www.databricks.com/customers/jetblue)

---

### CS3. Block (Square / Cash App) — Internal "Goose" Developer Agent

- **Pattern used:** Custom agent framework on Databricks Model Serving + Mosaic AI Gateway
- **Scale:** Internal developer productivity tool; used by engineering org
- **Key design decisions:**
  - Open-source Goose agent framework (LLM-powered CLI + IDE agent) deployed internally.
  - Databricks Model Serving hosts fine-tuned coding models + RAG over internal codebase.
  - Mosaic AI Gateway enforces per-developer token budgets; inference tables for cost attribution.
  - Tool registry in Unity Catalog: `run_sql`, `deploy_service`, `query_incident_db`.
- **Outcome:** Developer velocity improvement; self-service internal tooling.
- **Citation [51]:** [databricks.com/customers/block](https://www.databricks.com/customers/block)

---

### CS4. Commerzbank — Foundry-Based Internal Agent Platform

- **Pattern used:** Azure AI Foundry + APIM + Private Endpoints (Azure-native baseline)
- **Scale:** Internal banking operations; multiple business units
- **Key design decisions:**
  - Entire platform on private VNet; no LLM traffic on public internet.
  - APIM controls access with Entra ID integration for employee authentication.
  - Foundry Evaluations used to gate model upgrades (regression testing before GPT version bumps).
  - Document Intelligence integrated as an assetized extraction tool for compliance documents.
- **Outcome:** Compliant internal AI services deployed within EU data residency requirements.
- **Citation [52]:** [customers.microsoft.com — Commerzbank](https://customers.microsoft.com/en-us/story/commerzbank)

---

### CS5. Vodafone — "TOBi" Multi-Country Customer Agent (Azure OpenAI)

- **Pattern used:** Azure OpenAI + multi-region APIM + Container Apps
- **Scale:** 21 countries; consumer-facing; millions of interactions per day
- **Key design decisions:**
  - Multi-region Azure OpenAI deployments (EU, UK, APAC) behind APIM with geo-routing.
  - Container Apps hosting the orchestration layer (custom NLP + intent routing pre-Foundry).
  - Customer context injected from Salesforce CRM via a RAG-style retrieval step.
  - APIM rate-limits per country to prevent cross-region noisy-neighbor issues.
- **Outcome:** Deflected millions of contact-center calls; 10-year strategic partnership with Microsoft.
- **Citation [53]:** [news.microsoft.com — Vodafone partnership](https://news.microsoft.com/source/emea/features/vodafone-and-microsoft-announce-ten-year-strategic-partnership/)

---

### CS6. AstraZeneca — Clinical Document Summarization Agents (Databricks)

- **Pattern used:** Mosaic AI Agent Framework + Lakehouse-as-backend + Azure OpenAI
- **Scale:** Internal pharma R&D; clinical trial document corpus
- **Key design decisions:**
  - Clinical trial reports ingested to Delta Lake via DLT pipelines; Document Intelligence used for OCR extraction.
  - Custom summarization agent (Azure OpenAI GPT-4 via Mosaic AI Gateway) registered as a UC Function.
  - Agent Evaluation with domain-specific judges (medically trained SME Review App).
  - Unity Catalog row-level security ensures molecule-level data access control carries through to agent calls.
- **Outcome:** Significant reduction in time for regulatory submission preparation.
- **Citation [54]:** [databricks.com/customers/astrazeneca](https://www.databricks.com/customers/astrazeneca)

---

## 9. Comparison Matrices

### 9.1 Capability × Pattern Matrix

| Capability | A1 Foundry Baseline | A3 APIM Gateway | A5 ACA/AKS | A6 Doc Pipeline | B1 Mosaic Agent | B4 Hybrid | C1 MCP |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Summarization service | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Document extraction | ○ | ○ | ✓ | ✓ | ✓ | ✓ | ✓ |
| RAG / semantic search | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Text classification | ✓ | ○ | ✓ | ○ | ✓ | ✓ | ✓ |
| Multi-agent orchestration | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | ○ |
| Per-team quota enforcement | ○ | ✓ | ○ | ○ | ✓ | ✓ | ✗ |
| Data lineage / governance | ○ | ○ | ✗ | ○ | ✓ | ✓ | ✗ |
| LLM evaluation pipeline | ✓ | ✗ | ○ | ✗ | ✓ | ✓ | ✗ |
| External client exposure | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ✓ |
| Low-code agent authoring | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

> ✓ = strong fit, ○ = partial fit, ✗ = not designed for this

### 9.2 Azure-Only vs Hybrid vs Databricks-Only

| Dimension | Azure-only (Foundry + APIM) | Hybrid (Foundry + Databricks) | Databricks-only (Mosaic AI) |
|---|---|---|---|
| **Setup complexity** | Medium | High | Medium |
| **Data governance** | Azure Purview | Unity Catalog + Purview federated | Unity Catalog |
| **LLM evaluation** | Foundry Evaluations | Both | Mosaic AI Agent Evaluation |
| **Model fine-tuning** | Foundry fine-tune (AOAI) | Mosaic AI (DBRX, Llama) | Mosaic AI fine-tuning |
| **Best for** | Greenfield Azure-first, MS-heavy shops | Enterprise with Databricks + Azure investment | Data-centric, Databricks-native teams |
| **External exposure** | APIM + Entra External ID | APIM + Foundry front-end | Databricks Apps + API layer |
| **Compliance / audit** | App Insights + Defender | Delta inference tables + Defender | Delta inference tables |
| **Cost model** | Azure consumption | Dual platform costs | DBU consumption |

---

## 10. Decision Framework

Use the following decision tree to select the right architecture for your context:

> A high-resolution graphical version of this decision tree is available at `docs/decision-tree.png`.

```
Q1: Is data already in Databricks?
├── YES → Q1b: Also need Azure/Foundry front-end or Teams/Power Platform?
│          ├── YES → B4 Hybrid (Foundry runtime + Databricks data/tools)
│          └── NO  → Databricks-native: B1 Mosaic Agent Framework
│                    + B2 Mosaic AI Gateway + B5 Lakehouse backend
│
└── NO  → Q2: Is the audience external / B2B clients?
           ├── YES → A7 Multi-tenant APIM + A3 GenAI Gateway
           │         + Entra External ID
           └── NO  → Q3: Is the audience both internal AND external?
                      ├── YES → A3 APIM (serves both tiers)
                      │         + A2 Foundry Agent Service
                      └── NO  → Q4: Regulated industry? (finance/pharma/EU)
                                 ├── YES → A1 Foundry Baseline (private
                                 │         endpoints + CMK) or B4 Hybrid
                                 └── NO  → Q5: Is this a PoC (< 8 weeks)?
                                            ├── YES → A2 Foundry basic or
                                            │         B1 Mosaic notebook
                                            └── NO  → Q6: Delivery channel?
                                                       ├── Teams / SharePoint
                                                       │   → C2 Copilot Studio
                                                       ├── Custom web / mobile
                                                       │   → A1 Foundry +
                                                       │     App Service / ACA
                                                       ├── REST API / SDK
                                                       │   → A3 APIM + C1 MCP
                                                       └── Any agent client
                                                           → C1 MCP server
                                                             behind A3 APIM
```

---

# 11. Appendix A — Numbered Citation List

| # | Description & Link |
|---|---|
| 1 | [Azure Architecture Center — Baseline Foundry chat](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat) |
| 2 | [Azure Architecture Center — Basic Foundry chat](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/basic-azure-ai-foundry-chat) |
| 3 | [Azure AI Foundry Agent Service overview](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview) |
| 4 | [Foundry connected agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/connected-agents) |
| 5 | [Foundry Agent Service tools](https://learn.microsoft.com/en-us/azure/ai-services/agents/tools/overview) |
| 6 | [Azure Architecture Center — AI gateway guide](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/azure-openai-gateway-guide) |
| 7 | [Azure API Management — GenAI gateway capabilities](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities) |
| 8 | [GitHub — AI-Gateway accelerator](https://github.com/Azure-Samples/AI-Gateway) |
| 9 | [APIM — Expose MCP servers](https://learn.microsoft.com/en-us/azure/api-management/expose-mcp-servers) |
| 10 | [Microsoft CAF — AI platform landing zone](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/scenarios/ai/platform/landing-zone) |
| 11 | [Microsoft CAF — AI ready landing zones](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/scenarios/ai/) |
| 12 | [Azure Architecture Center — Multi-agent system](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/multi-agent-system-using-azure-ai-agents) |
| 13 | [GitHub — Container Apps + OpenAI](https://github.com/Azure-Samples/container-apps-openai) |
| 14 | [Microsoft DevBlog — Semantic Kernel](https://devblogs.microsoft.com/semantic-kernel/) |
| 15 | [Microsoft Research — AutoGen](https://github.com/microsoft/autogen) |
| 16 | [Azure Architecture Center — Automate document processing](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/automate-document-processing-azure-form-recognizer) |
| 17 | [GitHub — Azure Search OpenAI Demo](https://github.com/Azure-Samples/azure-search-openai-demo) |
| 18 | [Microsoft Docs — Document Intelligence overview](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview) |
| 19 | [Azure Architecture Center — Multitenant Azure OpenAI](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/openai) |
| 20 | [Azure Architecture Center — Multitenant AI strategy](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/multitenant-strategy-ai) |
| 21 | [Microsoft Docs — Entra External ID](https://learn.microsoft.com/en-us/entra/external-id/) |
| 22 | [Databricks Docs — Mosaic AI Agent Framework](https://docs.databricks.com/en/generative-ai/agent-framework/index.html) |
| 23 | [Databricks Docs — Agent Evaluation](https://docs.databricks.com/en/generative-ai/agent-evaluation/index.html) |
| 24 | [Databricks Blog — Mosaic AI Agent Framework announcement](https://www.databricks.com/blog/announcing-mosaic-ai-agent-framework-and-agent-evaluation) |
| 25 | [Databricks Docs — AI Gateway](https://docs.databricks.com/en/ai-gateway/index.html) |
| 26 | [Databricks Docs — AI Gateway on external models](https://docs.databricks.com/en/generative-ai/external-models/ai-gateway.html) |
| 27 | [Databricks Docs — Create tools for agents (UC Functions)](https://docs.databricks.com/en/generative-ai/agent-framework/create-tools.html) |
| 28 | [Databricks Docs — Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html) |
| 29 | [Databricks Blog — AI/BI Genie](https://www.databricks.com/blog/introducing-databricks-ai-bi-genie) |
| 30 | [Databricks Blog — GenAI with Databricks + Azure OpenAI](https://www.databricks.com/blog/build-genai-apps-databricks-and-azure-openai) |
| 31 | [Microsoft Docs — Azure Databricks generative AI](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/) |
| 32 | [Databricks Blog — Lakehouse AI](https://www.databricks.com/blog/lakehouse-ai-data-centric-approach-building-generative-ai-applications) |
| 33 | [Databricks Blog — Compound AI systems](https://www.databricks.com/blog/compound-ai-systems) |
| 34 | [MLflow Docs — Tracing](https://mlflow.org/docs/latest/llms/tracing/index.html) |
| 35 | [Model Context Protocol specification](https://modelcontextprotocol.io/) |
| 36 | [Microsoft + Anthropic — C# MCP SDK](https://devblogs.microsoft.com/dotnet/microsoft-partners-with-anthropic-to-create-official-c-sdk-for-model-context-protocol) |
| 37 | [Azure APIM — Expose MCP servers](https://learn.microsoft.com/en-us/azure/api-management/expose-mcp-servers) |
| 38 | [Anthropic — MCP GitHub](https://github.com/modelcontextprotocol) |
| 39 | [Microsoft Copilot Studio docs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/) |
| 40 | [Microsoft 365 Agents SDK](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/) |
| 41 | [LiteLLM docs](https://docs.litellm.ai/docs/) |
| 42 | [Portkey docs](https://portkey.ai/docs/product/ai-gateway) |
| 43 | [Kong AI Gateway](https://konghq.com/products/kong-ai-gateway) |
| 44 | [Cloudflare AI Gateway](https://developers.cloudflare.com/ai-gateway/) |
| 45 | [AWS Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) |
| 46 | [Google Vertex AI Agent Builder](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-builder/overview) |
| 47 | [Salesforce Agentforce](https://www.salesforce.com/agentforce/) |
| 48 | [ServiceNow AI Agents](https://www.servicenow.com/products/ai-agents.html) |
| 49 | [ANZ Bank GenAI platform (Microsoft News)](https://news.microsoft.com/en-au/2024/06/19/anz-builds-generative-ai-platform-for-developers/) |
| 50 | [JetBlue BlueBot — Databricks customers](https://www.databricks.com/customers/jetblue) |
| 51 | [Block / Square — Databricks customers](https://www.databricks.com/customers/block) |
| 52 | [Commerzbank — Microsoft customers](https://customers.microsoft.com/en-us/story/commerzbank) |
| 53 | [Vodafone TOBi — Microsoft + Vodafone partnership](https://news.microsoft.com/source/emea/features/vodafone-and-microsoft-announce-ten-year-strategic-partnership/) |
| 54 | [AstraZeneca — Databricks customers](https://www.databricks.com/customers/astrazeneca) |
| 55 | [a16z — Emerging architectures for LLM applications](https://a16z.com/emerging-architectures-for-llm-applications/) |
| 56 | [Thoughtworks Technology Radar](https://www.thoughtworks.com/radar) |
| 57 | [McKinsey — State of AI 2024](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai) |
| 58 | [Gartner — GenAI Hype Cycle](https://www.gartner.com/en/articles/what-s-new-in-artificial-intelligence-from-the-2023-gartner-hype-cycle) |

---

## 12. Appendix B — Acronym Index

| Acronym | Full Term |
|---|---|
| A2A | Agent-to-Agent (protocol) |
| AOAI | Azure OpenAI |
| APIM | Azure API Management |
| ACA | Azure Container Apps |
| AKS | Azure Kubernetes Service |
| CAF | Cloud Adoption Framework |
| CMK | Customer-Managed Keys |
| DBU | Databricks Unit (billing unit) |
| DLT | Delta Live Tables |
| DORA | Digital Operational Resilience Act (EU financial regulation) |
| GenAI | Generative AI |
| ISV | Independent Software Vendor |
| KEDA | Kubernetes Event-Driven Autoscaling |
| LLM | Large Language Model |
| MCP | Model Context Protocol |
| MLflow | Open-source ML lifecycle management platform (Databricks + Linux Foundation) |
| PAYG | Pay As You Go |
| PII | Personally Identifiable Information |
| PTU | Provisioned Throughput Units (Azure OpenAI capacity) |
| RAG | Retrieval-Augmented Generation |
| RBAC | Role-Based Access Control |
| SDK | Software Development Kit |
| SLA | Service Level Agreement |
| TPM | Tokens Per Minute |
| UC | Unity Catalog (Databricks) |
| VNet | Virtual Network |
| WAF | Web Application Firewall |

---

*End of document — Agent Assetization on Azure & Databricks — v1.0 — 2026-06-29*
