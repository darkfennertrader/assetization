---
title: "PwC AI Platform — Kick-off Meeting Speech"
subtitle: "Walking the general high-level architecture diagram — plain language"
author: "Raimondo Marino — Solution AI Architect"
date: "2026-07-02"
---

# PwC AI Platform — Kick-off Speech

> **Speaker notes format**
> — `— pause —` = deliberate breath / let the room absorb
> — `— point at [X] —` = point at the screen
> — `[Q&A likely]` = expect a question here, be ready
> — *italics* = emphasis
> — **bold** = key phrase, say it clearly

---

\newpage

## Section 0 — Opening hook *(~30 seconds)*

Good morning everyone.

I want to start with one sentence that frames *everything* we are going to build together.

— pause —

**We are deliberately building one platform that does three very different things — and we are building the foundation only once.**

That is the idea. One shared technical spine, three products on top of it. Not three separate projects, not three separate teams with overlapping infrastructure. One platform, intentionally designed that way from day one.

Let me show you what that looks like.

— pause —

---

## Section 1 — Why we are doing this now *(~1 minute)*

This is a **greenfield build**. We are not replacing something that already exists — we are laying the foundation for how PwC delivers AI going forward. That is a rare and important opportunity.

And it comes with one specific responsibility: **do it once, do it right, and design it so it never fragments.**

— pause —

Here is the trap we are deliberately avoiding. If we build each engagement in isolation — one identity system for this project, a different gateway for that one, three different agent frameworks across three teams — we end up a few years from now with something nobody wants: a collection of overlapping AI systems, each requiring its own maintenance, none of them benefiting from what the others built.

**We are preventing that from day one.** The decisions we make today — which components go into the shared substrate, how we govern AI assets, how we manage identity — those decisions will save every future engagement weeks of work.

— pause —

**No duplicated wheels. No reinvented plumbing. That principle shapes everything on this diagram.**

---

## Section 2 — The diagram on screen *(~30 seconds)*

— point at the diagram on screen —

What you see here is our high-level architecture. It has **four layers**, stacked top to bottom. Each layer has a colour.

- **Orange** at the top — the Showroom. External-facing. Prospects.
- **Green** in the middle — the Marketplace. Internal PwC staff.
- **Blue** below that — the Knowledge Base. Client-specific intelligence.
- **Grey** at the bottom — the Shared Substrate. The foundation everything else sits on.

I am going to walk through each layer, box by box, in plain language. No jargon without an immediate explanation.

— pause —

---

\newpage

## Section 3 — L1 Orange layer: the Showroom *(~1.5 minutes)*

— point at the orange area —

The **Showroom** is the first thing a *prospect* — someone who is not yet a PwC client — sees.

With the Showroom, the salesperson opens their laptop, clicks a button, and a QR code appears. The prospect scans it with their phone. They are in. **A scoped AI experience, live, in thirty seconds.**

The access lasts one hour. After that, it expires automatically. The prospect never creates an account. They do not give us their email.

Now let me explain each box you see in the orange area.

— point at individual boxes —

**Showroom UI** — the screen the prospect sees on their phone. A clean, mobile-first interface showing the AI demos they have been given access to.

**Presenter Admin** — the screen the salesperson uses on their laptop. They log in with their normal PwC credentials, choose which demos to include in the session, and generate the QR code.

**Showroom BFF** — BFF stands for Backend For Frontend. Think of it as the brain behind both screens. When the salesperson clicks "create session", the BFF creates a secure token, stores the session, and generates the QR code. When the prospect scans the code, the BFF checks the token is still valid and lets them in.

**Session Store** — a small database that holds the session record: which demos are included, when the session expires, and whether it is still active. Nothing else. No prospect data, no names, no emails.

— pause —

**The key point about the Showroom: it is *disposable by design*. The session expires, the data is gone, the prospect never created an account. Secure by default.**

---

\newpage

## Section 4 — L2 Green layer: the Marketplace *(~1.5 minutes)*

— point at the green area —

The **Marketplace** is for *internal PwC staff* — consultants, solution architects, delivery teams across all ~400 PwC entities worldwide.

The problem it solves: *we keep building the same things*. One team builds an AI asset for financial anomaly detection. Another team builds something very similar six months later without knowing the first existed.

The Marketplace stops that. It is an internal catalogue where teams **publish** what they build, **discover** what others have already built, and **adopt** it directly into their engagement.

— point at individual boxes —

**Marketplace Portal** — the web interface. PwC staff log in with their corporate account. They search the catalogue, read documentation, try the asset in a sandbox, and adopt it into their project in a few clicks.

**Asset Registry** — the database behind the portal. Every asset has a metadata record: what it does, which version it is, whether it has passed quality and security checks, user ratings, and the download location.

**CI Certification pipeline** — before any asset can appear in the Marketplace, it must pass this. CI stands for Continuous Integration — an automated process that runs every time a team submits an asset. It checks for security vulnerabilities, runs quality tests, signs the asset with a digital signature, and only then publishes it to the registry. **Nothing enters the Marketplace without passing that check. No exceptions.**

— pause —

**The key point: one team's solution becomes every team's starting point.**

---

\newpage

## Section 5 — L3 Blue layer: the Knowledge Base *(~1 minute)*

— point at the blue area —

The **Knowledge Base** is Phase 3 — on the roadmap, not in the next sprint. But it is on the diagram because it shapes design decisions we make today.

The Knowledge Base is what we build for clients who want the AI to understand *their* specific domain — their contracts, their regulations, their internal processes.

— point at individual boxes —

**Knowledge Base UI** — the interface for client staff. They ask questions in natural language and get answers grounded in their own documents.

**Vector Search indexes** — the engine underneath. Each client gets their own private index. Note the label: it says *Databricks Vector Search or Azure AI Search*. This is intentional — I will explain the Databricks path when we get to the substrate.

**Ingestion pipeline** — the process that takes raw client documents — PDFs, Word files, spreadsheets — and prepares them for the search index. Again, the label shows two options: *Databricks DLT or Logic Apps plus Document Intelligence*. Two paths, same outcome, chosen based on the client's existing platform.

— pause —

**The key point: the client's data never leaves the client's environment. We bring the platform to their data.**

---

\newpage

## Section 6 — L4 Grey layer: the Shared Substrate *(~2.5 minutes)*

— point at the grey area —

And now the most important part.

Everything I just described — Showroom, Marketplace, Knowledge Base — all three sit on top of *this*. The grey layer. The **Shared Substrate**.

The rule of the Substrate: **build it once, reuse it everywhere.** Every product uses the same identity system, the same gateway, the same agent framework, the same observability stack. We never build any of these twice.

Let me walk through each group.

— point at "Identity & Edge" cluster —

**Identity and Edge.** Three boxes.

**Entra ID** — Microsoft's enterprise identity platform. Every PwC staff member across all ~400 entities already has an account. When someone logs into the Marketplace or the Presenter Admin, they use their existing PwC login. No new passwords.

**Entra External ID** — the same technology for external guests. When a prospect scans a QR code and gets a one-hour session, this validates their temporary token.

**Azure Front Door plus WAF** — the front door to the entire platform. Literally. Every request, from every user, enters through here. The WAF — Web Application Firewall — is the security guard blocking attacks before they reach the application.

— pause —

— point at "AI Gateway" cluster —

**AI Gateway.** One box: **Azure APIM** — the traffic guard.

APIM checks every request: is this token valid? Is this user allowed? Are they sending too many requests? Does the content look safe? All in milliseconds. Every request is also logged here — a complete, tamper-proof audit trail.

— pause —

— point at "Agent Runtime" cluster —

**Agent Runtime.** This cluster now shows *two* options side by side — and both are equally important.

**LangGraph Runtime on Azure Container Apps** — this is the *lightweight orchestration* runtime. For the Showroom demos, for workflow agents, for chat agents, for anything that primarily calls APIs, coordinates steps, and manages conversation. It scales to zero when idle — near-zero cost between events. LangGraph manages the agent's decision graph and the mandatory human-in-the-loop gate.

**Databricks Model Serving** — this is the *data-heavy* runtime. For agents whose main job is reasoning over the client's data lake: running Spark queries, calling a fine-tuned custom model, doing text-to-SQL over the client's warehouse. This agent lives *next to the data* inside the Databricks environment. No data egress, full Unity Catalog governance.

The rule for choosing between them: **if the agent is orchestrating → ACA. If the agent is computing over data → Databricks.**

**MCP Tool Servers** — the agent's hands. Both runtimes call MCP tools. Each tool server does one specific thing: search a document index, extract data from a file, detect anomalies, send a notification.

— pause —

— point at "AI Models" cluster —

**AI Models.** Two boxes.

**Foundation LLM on Azure OpenAI** — the language model. Reads and generates natural language. All traffic stays within Azure infrastructure.

**Embedding Model on Azure OpenAI** — converts text into numbers that capture meaning. Powers semantic search across document indexes.

— pause —

— point at "Databricks" cluster — *(light blue area)*

**Data and ML Platform — Databricks.** This is the optional module. It appears in the substrate because for clients who are already on Databricks — or for whom a lakehouse architecture makes sense — every component in this cluster is reused, not rebuilt per engagement.

**Unity Catalog** — the governance plane. One catalog per client, fully isolated. Every data asset, every ML model, every vector index registered here. Permissions, lineage, audit — all in one place. This is the biggest operational win: governance stops being a per-tool configuration problem.

**Delta Lake plus Lakehouse Federation** — the governed data lake. Federation means we can query the client's existing systems — SQL Server, SAP, Oracle, Snowflake — as if they were tables inside Delta, without moving the data.

**Databricks Vector Search** — the vector index for the Knowledge Base when the client is on Databricks. Permissions are inherited automatically from the source Delta table via Unity Catalog — no separate ACL sync needed.

**MLflow Model Registry** — where custom and fine-tuned models live. Versioned, tracked, auditable. When a client wants their own model trained on their data, it is managed here.

**Delta Live Tables** — the ingestion pipeline for the Knowledge Base on the Databricks path. Incremental processing, full lineage in Unity Catalog, automatic retry.

— pause —

**The key point about Databricks: it is an optional module. For a client on a pure Azure-native stack, the substrate uses Azure AI Search, Azure ML Endpoints, and Logic Apps instead — same architecture, different implementations. The platform degrades gracefully.**

— point at "Observability" cluster —

**Observability — always on.** Four boxes.

**Application Insights** — live metrics: request rates, errors, response times.

**LangSmith** — AI-specific observability: every LLM call, every agent step, every prompt version recorded.

**Event Hub to ADLS Gen2** — the immutable audit log. Every request through the gateway, permanently recorded for two years. Databricks reads this Delta output for long-term compliance analysis.

**Key Vault** — the safe. Every secret, every signing key, every certificate. Nothing sensitive is stored anywhere else.

— pause —

**The key point about the Substrate: the client gets all of this for free the moment they adopt a Marketplace asset. They do not build any of it. They plug into it.**

---

\newpage

## Section 7 — What this means for this engagement *(~1 minute)*

Let me be concrete.

When we deliver an AI solution to a client, the Shared Substrate deploys into *the client's own Azure environment*. It lives in their tenant. Their data never crosses into ours.

The Marketplace assets arrive as *signed, versioned packages*. There is no live connection back to PwC during client operations. The client's AI runs independently.

— pause —

The Showroom is how we validate the direction *before* we build. We can show them a live AI experience within minutes of arriving at their office. The conversation — "does this match what you need?" — happens before a single line of client-specific code is written.

For your teams: the architecture on screen is the target state. Sprint one starts in the orange layer. But every decision in sprint one must be compatible with the grey layer underneath it.

If the client is on Databricks, plan for the blue cluster in the substrate from the start. If they are Azure-native, the same architecture applies with Azure AI Search and Azure ML in place of the Databricks components. **The shapes are the same. The pluggable parts are different.**

---

## Section 8 — Closing call to action *(~30 seconds)*

Three products. One platform. Built once, deliberately.

The Showroom turns a conversation into a live AI experience in thirty seconds.

The Marketplace turns individual work into shared knowledge.

The Knowledge Base turns a generic AI into the client's own domain expert.

And the Substrate — built once — powers all three, securely, observably, at scale. With Databricks as a first-class option when the client's world lives in a lakehouse.

**That is what we are kicking off today. Let's build it.**

— pause —

I am happy to take questions.

---

\newpage

## Speaker cheat sheet *(hold this page during the meeting)*

**0. Hook:** one platform, three products, deliberately built once.

**1. Why now:** greenfield — build it right from day one. No duplicated wheels, no reinvented plumbing.

**2. Showroom (orange):** QR code → 1-hour prospect demo → session expires → no account created.
- Boxes: Showroom UI / Presenter Admin / Showroom BFF / Session Store

**3. Marketplace (green):** internal catalogue — publish, discover, adopt certified AI assets.
- Boxes: Marketplace Portal / Asset Registry / CI Certification pipeline

**4. Knowledge Base (blue):** Phase 3. Per-client domain intelligence. Two paths: Databricks DLT + Vector Search **or** Logic Apps + Azure AI Search.

**5. Shared Substrate (grey):** build once, reuse everywhere.
- Identity & Edge: Entra ID (staff SSO) / Entra External ID (guest tokens) / Front Door + WAF
- AI Gateway: APIM (validate, rate-limit, audit)
- Agent Runtime *(two options)*: LangGraph on ACA (lightweight/orchestration) / Databricks Model Serving (data-heavy)
- MCP Tool Servers: agent's hands — called by both runtimes
- AI Models: Foundation LLM / Embedding Model (Azure OpenAI)
- Databricks module *(optional)*: Unity Catalog / Delta Lake + Federation / Vector Search / MLflow / DLT
- Observability: App Insights / LangSmith / Event Hub→ADLS / Key Vault

**6. Client engagement:** Substrate in client's own Azure tenant. Signed assets. No live PwC link. Databricks module active if client is lakehouse-native; Azure-native otherwise.

**7. Closing:** Three products. One platform. Built once. Let's build it.

---

\newpage

## Acronym and term glossary

| Term | Plain meaning |
|---|---|
| **ACA** | Azure Container Apps — runs application containers in the cloud, scales to zero when idle |
| **ACR** | Azure Container Registry — private secure store for container images (packaged application code) |
| **ADLS Gen2** | Azure Data Lake Storage Generation 2 — large-scale secure cloud storage; used here for the immutable audit log |
| **AI** | Artificial Intelligence — in this context, large language models and the systems built around them |
| **APIM** | Azure API Management — the gateway in front of all AI services; enforces security, rate limits, and logging |
| **AVM** | Azure Verified Modules — pre-built, Microsoft-certified infrastructure code blocks for Bicep/Terraform |
| **azd** | Azure Developer CLI — provisions Azure infrastructure and deploys applications in one step |
| **BFF** | Backend For Frontend — a server-side layer dedicated to serving one specific user interface |
| **Bicep** | Microsoft's Infrastructure-as-Code language for defining Azure resources in readable text files |
| **CI / CD** | Continuous Integration / Continuous Delivery — automated pipelines that build, test, sign, and deploy software every time a change is made |
| **Cosmos DB** | Azure Cosmos DB — a globally distributed, serverless-capable database; used here as the Showroom session store |
| **CRS** | Core Rule Set — the standard set of web attack rules used by the WAF (published by OWASP) |
| **Databricks** | A unified data and AI platform — provides the lakehouse (Delta Lake), governance (Unity Catalog), ML (MLflow, Model Serving), and pipelines (DLT) in one environment |
| **Databricks Model Serving** | Real-time inference endpoints inside Databricks — hosts data-heavy agents and custom/fine-tuned models; agents run next to the data, no egress |
| **Databricks Vector Search** | A vector index managed inside Unity Catalog — permissions flow automatically from the source Delta table; alternative to Azure AI Search for the Knowledge Base |
| **Delta Lake** | The open-source storage layer at the core of the Databricks lakehouse — provides ACID transactions and schema enforcement on cloud storage |
| **DLT** | Delta Live Tables — Databricks' pipeline framework for incremental, reliable data ingestion with full lineage tracked in Unity Catalog |
| **Entra External ID** | Microsoft's identity service for external (non-employee) users — validates guest tokens in the Showroom |
| **Entra ID** | Microsoft's enterprise identity platform — handles employee single sign-on across all PwC entities |
| **Event Hub** | Azure Event Hub — a high-throughput message bus that captures every API request/response for the audit log |
| **HITL** | Human In The Loop — a mandatory checkpoint where a human reviews and approves an agent's intended action before it executes |
| **IaC** | Infrastructure as Code — defining cloud infrastructure in version-controlled text files |
| **JWT** | JSON Web Token — a compact, signed digital token used to prove identity; the Showroom uses a short-lived JWT for guest session access |
| **Key Vault** | Azure Key Vault — a hardware-backed safe for cryptographic keys, certificates, and secrets; nothing sensitive is stored anywhere else |
| **KQL** | Kusto Query Language — the query language used to query Log Analytics and Application Insights |
| **Lakehouse** | An architecture that combines the flexibility of a data lake with the governance and performance of a data warehouse; Databricks is the primary lakehouse platform |
| **Lakehouse Federation** | A Databricks feature that lets you query external systems (SQL Server, SAP, Oracle, Snowflake) as if they were Delta tables — no data movement required |
| **LangGraph** | Open-source framework for building stateful AI agent graphs — manages multi-step agent reasoning and the HITL gate |
| **LangSmith** | Observability platform for AI — records every LLM call, agent step, and prompt version |
| **LLM** | Large Language Model — the AI model that reads and generates natural language; hosted on Azure OpenAI |
| **Log Analytics** | Azure Log Analytics Workspace — centralised service that stores and queries operational logs from all platform components |
| **Managed Identity** | Azure feature that gives a service its own automatically managed identity — no stored passwords or API keys |
| **Marketplace** | The internal PwC platform (L2) where AI assets are published, discovered, and adopted |
| **MCP** | Model Context Protocol — open standard for connecting AI agents to external tools; each MCP server exposes one specific capability |
| **MLflow** | Open-source ML lifecycle platform; inside Databricks it is the Model Registry — versioned storage for custom and fine-tuned models |
| **MSAL** | Microsoft Authentication Library — handles the Entra ID login flow in browser applications |
| **OWASP** | Open Web Application Security Project — publishes the CRS used by the WAF |
| **PKCE** | Proof Key for Code Exchange — a secure OAuth 2.0 login variant for browser applications |
| **QR code** | Quick Response code — a scannable 2D barcode; scanning it opens the prospect's Showroom session on their phone |
| **RAG** | Retrieval-Augmented Generation — searching a document index for relevant content *before* sending a question to the LLM, so the AI answers from real documents |
| **RBAC** | Role-Based Access Control — granting permissions based on a user or service's role |
| **RUM** | Real User Monitoring — telemetry from the user's browser sent to Application Insights |
| **Shared Substrate** | The common technical foundation (L4) — identity, gateway, agent runtime, AI models, and observability — built once and reused by all products |
| **Showroom** | The external-facing platform layer (L1) — scoped AI demo environment accessible to prospects via QR code for 1 hour |
| **SSO** | Single Sign-On — one login for multiple systems; PwC staff use Entra ID SSO |
| **TLS** | Transport Layer Security — encrypts data in transit between the browser and the platform (the "S" in HTTPS) |
| **Unity Catalog** | Databricks' unified governance layer — one place for permissions, lineage, and discovery across all data assets, ML models, and vector indexes in the lakehouse |
| **VNet** | Azure Virtual Network — a private network in Azure isolating resources from the public internet |
| **WAF** | Web Application Firewall — inspects incoming web traffic and blocks known attack patterns |
| **WORM** | Write Once Read Many — a storage policy that makes data immutable once written; used for the audit log in ADLS Gen2 |

---

\newpage

## 3-Minute elevator version *(standalone — for a corridor conversation or short intro slot)*

---

**Opening**

*"We are building one AI platform for PwC. Three products, one foundation, built deliberately — so every future engagement pulls from what already exists rather than starting from scratch."*

— pause —

**The four layers in sixty seconds**

If you look at the diagram, you see four layers.

At the top, **orange — the Showroom.** When a salesperson is with a prospect, they generate a QR code on their laptop. The prospect scans it on their phone. They have one hour to experience a live AI demo. After that, it expires. No account, no data retained.

Below that, **green — the Marketplace.** An internal catalogue for PwC staff. Teams publish the AI assets they build — agents, tools, models — and other teams discover and reuse them. Before anything goes in, it passes an automated quality and security certification. Build once, reuse everywhere.

Then **blue — the Knowledge Base.** Phase 3. When a client wants the AI to understand *their* specific domain — their contracts, their regulations — we build a private knowledge index inside their own environment. Their data never leaves their tenant.

And at the bottom, **grey — the Shared Substrate.** This is the foundation. Identity, security gateway, agent runtime, AI models, observability. Built once, shared across all three products. Every engagement that uses this platform gets all of it for free.

— pause —

**The Databricks angle in thirty seconds**

One important design decision in the substrate: the agent runtime has two options. For lightweight orchestration agents — demos, chat, workflow — we use Azure Container Apps. For agents that need to reason over a client's data lake — querying terabytes, running a fine-tuned model — we use Databricks Model Serving. The agent runs *next to the data*, inside the client's Databricks environment. Unity Catalog handles governance automatically. If the client is not on Databricks, we use the Azure-native equivalents instead. Same architecture, pluggable components.

— pause —

**Closing**

*"Three products. One platform. A shared foundation that means we never rebuild the plumbing twice. That is what we are kicking off."*

---
