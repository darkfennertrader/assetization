---
title: "Friday 2026-07-04 — Team Sync Agenda"
subtitle: "Raimondo · Michael · (Adrian if available) — 09:00–10:00 CET"
author: "Raimondo Marino"
date: "2026-07-01"
---

# Friday 2026-07-04 — Team Sync Agenda

> **Time:** 09:00–10:00 CET (Michael's preferred slot — best head condition)
>
> **Participants:** Raimondo Marino (Solution AI Architect), Michael (Senior Developer)
>
> **Optional:** Adrian (PwC Director) — please forward questions D3/D4/D5/D8 before Friday if he is not joining

---

## Pre-read (send to Michael before Thursday EOD)

| Document | Where | Why it matters |
|---|---|---|
| Architecture overview (Adrian's vocabulary) | `docs/ara-a-showroom-marketplace.md` | Shared mental model of what we are building |
| Architecture diagram | `docs/ara-a-showroom-marketplace.png` | Visual for the three products + shared substrate |
| Auth design note | `docs/auth-design-note.md` | Michael's primary build area; contains the four open decisions (D3/D4/D5/D8) |

**Ask Michael to:** skim the auth design note and flag any TypeScript-level blocker. Specifically: has he used MSAL Node before? Has he used `qrcode` npm or similar?

---

## Two questions to send Adrian BEFORE Friday

Send via Teams / email today (Tuesday) so he can reply asynchronously:

> **Q1 (D5 — external tenant model):**
> "Adrian — for the Showroom, when external prospects scan the QR code, do we want all guests registered in a single PwC-controlled external identity tenant (Option A — recommended), or would we rather use guest invitations inside each client's own Entra tenant (Option B)? This affects how we set up the Entra External ID infrastructure."

> **Q2 (scope of Showroom vs. Marketplace):**
> "Adrian — are Marketplace (internal Lego pieces) and Showroom (external demos) two separate deployed apps sharing a common auth layer, or one app with an internal and external view? Architectural recommendation is two apps with one shared substrate — please confirm."

If Adrian is not reachable before Friday, we default to the recommended option on both and flag for next week.

---

## Agenda — 60 minutes

### ① Architecture alignment — 10 min

**Goal:** everyone has the same picture of what we are building.

- Walk through `docs/ara-a-showroom-marketplace.png` (screen-share).
- Confirm the three-product split: **Marketplace** (internal Lego pieces) · **Showroom** (external demos) · **Knowledge Base** (deferred).
- Confirm the **shared substrate** is Phase 0: auth layer first, then gateway, then CI gate, then first assets.
- Confirm the **stack**: LangGraph + LangChain + LangSmith (Python, Raimondo) + TypeScript BFF + Next.js front-end (Michael).

**Decision needed:** none — this is alignment, not decision-making.

---

### ② Auth deep-dive — 20 min

**Goal:** agree on the four open auth decisions so Michael can start coding this week.

Walk through `docs/auth-design-note.md` §8 decision log:

| Decision | Question | Recommended | Default if no answer |
|---|---|---|---|
| **D3** — 1-hour demo token type | Self-signed JWT (RS256) or Entra External ID OTP link? | Self-signed JWT (less friction, phone-friendly) | Self-signed JWT |
| **D4** — Fine-grained authZ tool | OpenFGA or Entra app roles? | OpenFGA (more expressive, no SaaS cost) | OpenFGA |
| **D5** — External tenant model | Single PwC external tenant or per-client guest? | Single external tenant (Option A) | Wait for Adrian |
| **D8** — Immediate revocation | Redis blacklist OR short JWT TTL (5 min re-issue)? | Redis blacklist (instant revocation for demos) | Short TTL if no Redis yet |

**For Michael to prepare:** any concern about MSAL Node implementation for the BFF, or about the `POST /sessions` endpoint generating the signed JWT + QR code.

**For Raimondo to prepare:** Bicep sketch for the Key Vault key + Redis Cache + OpenFGA on ACA.

---

### ③ Repo skeleton walk-through — 10 min

**Goal:** agree on where Michael's first Lego pieces land in the repo.

Proposed folder structure (Raimondo to screen-share):

```
/
├── core-assets/
│   ├── auth/                  ← Michael owns this
│   │   ├── entra-wrapper/     (TypeScript — MSAL wrappers, PKCE flow)
│   │   ├── session-service/   (TypeScript — POST /sessions, QR code gen)
│   │   └── openfga-client/    (TypeScript — relation check wrapper)
│   ├── bff-utilities/         ← Michael owns this
│   │   ├── sql-helpers/       (TypeScript — SQL unit test harness, abort controllers)
│   │   └── data-filters/      (TypeScript — data transform snippets)
│   ├── summarize/             ← Raimondo owns this (Python + MCP server)
│   ├── extract/               ← Raimondo owns this
│   └── classify/              ← Raimondo owns this
├── domain-assets/             (empty — deferred)
├── showroom/                  ← Michael owns this
│   ├── frontend/              (Next.js / TypeScript)
│   └── bff/                   (TypeScript BFF server)
├── marketplace/               (later — after 50 assets)
└── docs/                      (architecture + design notes)
```

**Key governance point to communicate to Michael:**
> Every function he commits to `core-assets/` must have an `asset.toml` file alongside it (Raimondo provides the template) and pass the CI gate. The gate is being configured this week by Raimondo. It will include: Biome/ESLint for TypeScript, Jest for unit tests, `gitleaks` for secret scanning. It will block merge on failure — it's not advisory.

---

### ④ LangGraph overview — 10 min

**Goal:** Michael understands how the Python side connects to his TypeScript work.

Brief explanation (Raimondo):
- A LangGraph agent graph is a set of **Python nodes** (≤50 LOC each) connected in a typed state machine.
- Each Python node is a Lego piece with a single responsibility (e.g., `extract_entities_node`, `summarise_text_node`).
- The graph is hosted on ACA; it exposes a REST endpoint that the TypeScript BFF can call.
- Between the TypeScript BFF and the Python agent: **APIM** (quota + content safety) + **MCP protocol** (standard JSON-RPC) — no direct TypeScript → Python call in production.

Show Michael the planned first graph (one-slide sketch):
```
User query
   │ via BFF → APIM
   ▼
Orchestrator node
   │
   ├─► extract_node  →  /extract MCP tool  →  Azure Document Intelligence
   ├─► summarise_node → /summarize MCP tool → Azure OpenAI
   └─► classify_node  → /classify MCP tool  → Azure OpenAI structured output
   │
   ▼
Response → APIM → BFF → Showroom front-end
```

---

### ⑤ Next-week deliverables — 10 min

**Goal:** concrete, named, testable output by next Friday.

| Owner | Deliverable | Definition of done |
|---|---|---|
| **Michael** | `POST /sessions` endpoint (TypeScript) | Generates a signed RS256 JWT with `sub`, `aud`, `exp`, `scope`, `presenter`; returns a QR-code data URL. Unit-tested with Jest. |
| **Michael** | MSAL Node auth middleware | Validates Entra ID Bearer tokens on internal API routes. Unit-tested. |
| **Michael** | `asset.toml` for the two auth assets above | Filled in from the template Raimondo provides. |
| **Michael** | Abort-controller wrapper (BFF data layer) | Cancels in-flight fetch if client disconnects; unit-tested. |
| **Raimondo** | APIM AI Gateway deployed (Bicep) | `token-limit` + `content-safety` + `emit-token` policies active in dev environment. |
| **Raimondo** | `asset.toml` schema + CI gate skeleton | GitHub Actions workflow: Biome lint + Jest + gitleaks + semver-check. Runs on every PR. |
| **Raimondo** | OpenFGA schema committed + ACA Bicep | OpenFGA running locally (Docker Compose for dev), ACA Bicep template ready for deploy. |
| **Raimondo** | First LangGraph graph scaffold (Python) | Orchestrator node + one specialist node (summarise); LangSmith tracing active; deployable to ACA. |
| **Both** | Repo skeleton created and agreed | Folder structure above committed with `.gitkeep` + `CODEOWNERS` + PR template. |

---

## Standing communication agreement (confirmed in previous meeting)

- **Primary channel:** Teams chat (Raimondo ↔ Michael).
- **If blocked / need a quick call:** message in Teams, schedule same-day.
- **Weekly sync:** Fridays 09:00–10:00 (same slot).
- **Adrian:** weekly demo / status update (day TBD — Raimondo to propose a Thursday afternoon slot).

---

## Notes space (fill in during meeting)

| # | Topic | Decision / action | Owner | Due |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

---

*Prepared by: Raimondo Marino · 2026-07-01*
