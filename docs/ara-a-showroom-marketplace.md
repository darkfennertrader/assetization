---
title: "ARA-A: Marketplace, Showroom & Knowledge Base — Architecture Overview"
subtitle: "One-page view in Adrian's vocabulary — v1.0 · July 2026"
author: "Raimondo Marino, Solution AI Architect"
date: "2026-07-01"
---

# ARA-A: Marketplace, Showroom & Knowledge Base

> **One-page architecture overview using the vocabulary agreed with Adrian (PwC Director)**
>
> This document is the team-facing companion to `docs/ara-a-reference-architecture.md`.
> Use it in cross-functional sessions to align on what we are building, in what order, and why.

---

## The three products — and their shared substrate

Adrian's three priorities map cleanly onto the assetization loop:

```
                 ┌─────────────────────────────────────────────────────┐
                 │          SHARED SUBSTRATE (build first)             │
                 │                                                     │
                 │  Identity layer: Entra ID (internal) +              │
                 │                  Entra External ID (clients)        │
                 │  Auth/Authz:     OpenFGA + APIM subscription keys   │
                 │  Gateway:        Azure APIM (AI Gateway tier)       │
                 │  Observability:  App Insights + LangSmith           │
                 └──────────────┬──────────────────┬───────────────────┘
                                │                  │
              ┌─────────────────▼───┐    ┌─────────▼─────────────────┐
              │   MARKETPLACE       │    │      SHOWROOM             │
              │   (Priority 1)      │    │      (Priority 1)         │
              │   Internal          │    │      External             │
              └─────────────────────┘    └───────────────────────────┘
                                │                  │
                 ┌──────────────▼──────────────────▼─────────────────┐
                 │        KNOWLEDGE BASE  (Priority 3 — deferred)    │
                 │        RAG · graph DB · domain intelligence        │
                 └────────────────────────────────────────────────────┘
```

---

## Product 1 — MARKETPLACE (internal)

**What it is:** The catalogue of reusable "Lego pieces" — small, certified, tested components that any team can pick up and use without rebuilding from scratch.

**Who uses it:** Internal PwC teams (400+ entities) building prototypes and products.

**What "small Lego piece" means in practice:**

| Lego piece | Playbook form | First examples |
|---|---|---|
| ~10-line function (single responsibility) | **Snippet** | `parse_date_range()`, `normalise_currency()`, abort-controller wrapper |
| Standalone package with tests + semver | **Component** | auth wrapper, BFF data filter, OpenAI call with retry |
| Deployable service with its own endpoint | **Service** | `/summarize` API, `/extract` API, `/rag` API |
| Agent workflow you can plug into a graph | **Template** | LangGraph extraction node, classification node |

**Governance rule (non-negotiable):** every piece that enters the marketplace has passed the CI certification gate (tests, lint, security scan, RAI checklist, `asset.toml` with semver). CI enforces standards — not a wiki.

**What the marketplace is NOT in phase 1:** a browsable web UI. It is a **searchable index** (Azure AI Search over `asset.toml` files) + a Markdown catalogue in the repo. A UI is built only after ≥50 assets and ≥3 consuming teams.

**Key numbers:**
- Target: 20 certified CORE assets published by end of Month 3
- Reuse rate target: 5% at Month 3 → 25% at Month 6 → 40%+ at Month 12
- Deprecation: assets with 0 consumers for 2 quarters are auto-flagged and removed

---

## Product 2 — SHOWROOM (external)

**What it is:** The client-facing demo environment. A curated set of use cases that PwC can demonstrate to prospects, assembled from Marketplace Lego pieces.

**Who uses it:** External prospects, during presentations and sales demos. Also: new client onboarding.

**Critical requirement (from Adrian's notes):**
- Access via **QR code** during a presentation.
- Credential lives for **1 hour only** (then auto-expired).
- Presenter can **invalidate** any credential immediately.
- Every access is **logged** (who opened it, for how long, which features touched).

**How the 1-hour access works (high level):**

```
Presenter clicks "Generate Demo"
         │
         ▼
Backend creates a short-lived guest session
  · Entra External ID guest invitation (or signed JWT)
  · exp = now + 3600 seconds
  · Scope = this showroom demo only
  · Session ID logged in App Insights
         │
         ▼
QR code encodes https://showroom.pwc.example/enter?token=<signed>
         │
Visitor scans on phone
         │
         ▼
Browser exchanges token → SSO session
APIM validates on every subsequent call
         │
Token expires → session ends automatically (SDK handles this)
Presenter can invalidate early via admin panel
```

**What the showroom is NOT:** it is not the marketplace. The showroom *consumes* marketplace assets to compose demos. It is a product in its own right — it has a front-end (TypeScript / Next.js on App Service or ACA) and a polished UX. The marketplace supply enables the showroom to be assembled cheaply and quickly.

**Full technical details:** see `docs/auth-design-note.md`.

---

## Product 3 — KNOWLEDGE BASE (deferred — Priority 3)

**What it is:** The company brain — a governed repository of documents, structured data, and domain knowledge that agents can query.

**Why deferred:**
- No pressing client demo depends on it yet.
- Building it well requires Databricks Lakehouse maturity (data pipelines, Unity Catalog governance, Vector Search) — skills not yet on the team.
- Building it badly (a quick RAG demo) creates technical debt that is expensive to undo.

**When to start:** when the Showroom needs it for a specific demo, or when an internal team has a concrete use case. Not before.

**What it will look like when we build it:**

```
Raw documents (PDFs, Word, SharePoint)
         │ Azure Document Intelligence (OCR, extraction)
         ▼
Delta Lake (Azure Databricks)
         │ DLT pipelines (streaming ingestion)
         ├─► Mosaic AI Vector Search (semantic retrieval)
         ├─► Genie Spaces (text-to-SQL for structured data)
         └─► MLflow Model Registry (all models versioned)
         │ Unity Catalog (access control, lineage, audit)
         ▼
Exposed as a /knowledge-search MCP server behind APIM
(plugs into the marketplace just like any other CORE asset)
```

---

## Shared substrate — what to build first

The three products all depend on the same foundation. **This is the correct build order:**

```
WEEK 1–2   WEEK 3–4   MONTH 2     MONTH 3         MONTH 4+
─────────────────────────────────────────────────────────────────►

[Auth layer]──────────────────────────────────────────────────────
  Entra ID + External ID tenant
  OpenFGA on ACA
  1-hour QR-code credential flow

[APIM Gateway]────────────────────────────────────────────────────
  token-limit · content-safety · emit-token

[CI gate + repo skeleton]─────────────────────────────────────────
  asset.toml schema · Ruff/mypy/pytest · gitleaks · semver

[First 5 CORE assets]──────────────────────────────────────────────
  auth-wrapper · summarize · extract · classify · embed

[Showroom v1]──────────────────────────────────────────────────────
                  [TypeScript front-end consuming CORE assets]
                  [1-hour QR-code access live]

[Marketplace metadata index]───────────────────────────────────────
                             [Azure AI Search over asset.toml]

[20 CORE assets as MCP servers]────────────────────────────────────
                                    [APIM expose-mcp-server]

[Knowledge Base]───────────────────────────────────────────────────
                                               [when needed]
```

---

## Team split (agreed in meeting 2026-07-01)

| Area | Owner | Stack |
|---|---|---|
| Auth layer (Entra + OpenFGA + QR-code flow) | **Michael** | TypeScript |
| BFF server-side data correctness (SQL tests, abort controllers) | **Michael** | TypeScript |
| Showroom front-end (HTML, CSS, TypeScript) | **Michael** (+ agents for markup) | TypeScript / Next.js |
| Agent graph design (LangGraph orchestration) | **Raimondo** | Python |
| CORE asset Lego pieces (LangGraph nodes, data transformers) | **Michael** (building) + **Raimondo** (assembling) | Python nodes in the graph |
| APIM policies, MCP server registration | **Raimondo** | Bicep / APIM policy |
| Marketplace metadata schema + CI gate | **Raimondo** | TOML + GitHub Actions / Azure DevOps |
| Knowledge Base (when it starts) | **TBD — Databricks skills needed** | Python + Databricks |

---

## Questions to resolve with Adrian (before Friday if possible)

1. **Marketplace vs. Showroom scope:** Are these two separate deployments (two ACA apps, two Entra app registrations) sharing a common auth substrate? Or a single app with two "views" (internal / external)? Architectural recommendation: **two products, one shared substrate** (cheaper to secure independently, cleaner RBAC boundary).

2. **Showroom audience:** Are we demoing to external clients at PwC presentations (→ Entra External ID), or to PwC's own clients within an ongoing engagement (→ could use a guest in the client's Entra tenant)? This changes the External ID tenant design.

---

## Graphviz source

A high-resolution diagram of this overview is available at `docs/ara-a-showroom-marketplace.png` (rendered from `docs/ara-a-showroom-marketplace.dot`).

---

*Last updated: 2026-07-01. Owner: Raimondo Marino. Next review: after Friday 2026-07-04 meeting.*
