# PwC (Agentic) AI Assetization & Acceleration Playbook
## Domain Transformation · Assetization · Asset Marketplace

**Version 1.0 — May 2026**

---

## How to use this playbook

This playbook is the productized PwC method for helping enterprise clients move agentic AI from pilot to scale. It is opinionated, evidence-based, and structured around three load-bearing pillars: **domain-based transformation** (where value originates), **assetization engineering** (how supply scales), and **the asset marketplace** (how supply meets demand). Read Part 0 first; then jump to the part that matches your immediate question. Part III (the marketplace) is the deepest section and the highest-leverage piece for differentiation in 2026.

Two audiences are served in one volume:

| Track | Read | Purpose |
|---|---|---|
| Engagement leadership (partner / director / programme lead) | Parts 0, I, V, and the executive summaries inside each part | Frame the engagement; choose the operating model; price the work |
| Delivery leadership (engineering manager / agent architect / asset engineer / change lead) | Parts II, III, IV, VI, VII | Build the assets, run the marketplace, deliver the agents |

Citations to external sources appear inline as `[N]`; the consolidated **Sources** section is at the end. This playbook is intentionally sanitized of any client identifier so it can travel to any engagement.

---

## Part 0 — Strategic frame

### 0.1 The supply-demand-clearing loop

The three pillars are not parallel investments. They form a closed loop that must turn in one direction:

> **Domain transformation generates demand** (concrete agentic use cases with sized value) → **assetization converts delivery into supply** (reusable components, templates, services) → **the marketplace clears supply against demand** (the next domain reuses what the prior one produced).

Break any link and the loop stalls:

- No domain transformation → use cases are random tactical experiments and the asset library has no organizing axis.
- No assetization discipline → every domain rebuilds from scratch; the second domain is no cheaper than the first.
- No marketplace → assets exist but nobody discovers them; reuse stays at single digits and the cost case for AI-at-scale never closes.

The loop is the playbook's central diagram. Every section ties back to it.

### 0.2 The 2026 context

Four shifts in the external environment shape every choice in this playbook:

1. **Agentic AI has crossed the pilot-to-production threshold.** Enterprise reference cases now show 30–40% labor cost reduction in redesigned end-to-end processes (BCG quote-to-order example), 84% reduction in handling time on retail-banking workflows, and automation rates moving from <5% to >80% in claims-style operations [1][9]. The conversation is no longer "can it work?" but "can we scale what works without rebuilding it on every new domain?"
2. **The governance gap is the binding constraint.** Only 21% of organizations have mature governance models for autonomous AI agents, while 73% plan to deploy them within two years [3]. Security (73% of respondents) and data privacy (73%) are the top concerns; lack of governance oversight (50%) and model reliability (50%) follow [3]. Marketplaces are emerging as the dominant industrialization mechanism for governance — pre-vetted assets, embedded compliance signals, integration patterns approved by architecture review [2].
3. **Internal benchmarks have moved.** A leading professional-services firm reports operating ~25,000 internal AI agents across ~40,000 employees with a stated goal of one agent per employee, alongside a shift from fee-for-service to outcome-based pricing [4]. This is the new high-water mark for what "AI-at-scale" looks like inside a knowledge-work organization.
4. **AI is being treated as infrastructure, not as projects.** Major firms are publishing "AI factory" / "AI refinery" architectures with pre-built industry agents (12 → 100+ in one published catalogue) and deployment times collapsed from months and weeks to days [5][6]. The unit of delivery is becoming the *domain accelerator* (a templated, configurable workflow) rather than the *project*.

These shifts compress the value of bespoke engagements and amplify the value of a productized playbook + reusable asset stock. This is exactly what this playbook builds.

### 0.3 Engagement archetypes

Four archetypes cover the vast majority of client situations. Use the archetype to choose the entry point and the sequencing of pillars.

| Archetype | Client signal | Entry pillar | Sequencing |
|---|---|---|---|
| **A. Greenfield ambition** | Strong strategy, weak execution; AI self-assessed 4/5 on strategy but ≤2.5/5 on tech, ops model, change | Domain transformation (Part I) | Domain → Assetization → Marketplace, year 1 |
| **B. Scattered pilots** | 50+ disconnected use cases, low reuse, no central catalog | Assetization (Part II) | Assetization first; harvest the existing pilots; marketplace at month 6 |
| **C. Industrializing reuse** | Has a CoE, has assets, no platform layer; reuse in single digits | Marketplace (Part III) | Marketplace first; domain transformation pulls the demand into the platform |
| **D. AI factory aspirant** | Already at scale; wants outcome-based commercial models and external productization | All three pillars in parallel | Multi-track from day 1; appoint Asset Reuse Team early |

The archetype determines first-90-day mobilization and the shape of the at-risk commercial model in Part V.

---

## Part I — Domain-based transformation

### I.1 Why "domain-first" beats "use-case-first"

A use case improves a step. A domain redesign rebuilds the whole process so that improving any step compounds. The use-case-first approach produces a long tail of point automations whose individual ROI looks fine but whose aggregate fails to move the domain P&L. The domain-first approach starts from the **agentic North Star** — the process as it would be designed today if humans + agents were the workforce — and works backward to the use cases that close the largest gaps first.

This is the same thesis BCG codifies in its **Deploy → Reshape → Invent** framework: deploying AI on top of existing processes captures only a fraction of value; *reshaping* the process to be agent-native captures the next tranche; *inventing* new offerings on top captures the rest [7]. Stay in Deploy too long and the value ceiling is low.

Three signals tell you a client is stuck in use-case-first thinking:

1. The use case backlog is long and unprioritized; nobody can name the value driver any single use case unlocks.
2. The metric of success is "use cases delivered" rather than a domain KPI (loss ratio, AHT, NPS).
3. The architecture is a list of agents, not a redesigned process diagram.

### I.2 The four-step domain transformation method

| Step | What you produce | Time-box |
|---|---|---|
| **1. As-is transparency** | Process map, FTE allocation table by step, pain-point shortlist, current AI initiatives inventory | 1–2 weeks |
| **2. Agentic North Star redesign** | Redesigned process diagram (agent-native), new use-case catalogue mapped to process steps, value driver evaluation matrix | 2–3 weeks |
| **3. Use case prioritization** | 7-criterion grid, shortlist of 6–10 prioritized features, employee time map | 1–2 weeks |
| **4. Delivery roadmap and charter** | Charter (sponsor, scope, KPIs), wave-based roadmap, capability/dependency requirements, first feature card pack | 1 week |

Total: 5–8 weeks for the first domain, compressing to 3–4 weeks per domain by domain three.

**Discipline note.** Skipping step 1 is the most common failure mode. As-is mapping looks "low value" because it doesn't deliver code; in reality it is the only step that surfaces *unstated* pain points (re-familiarization burden, manual reconciliation, hidden waiting time) that the client's KPI dashboard hides. Without it, the North Star is a wish list.

### I.3 The 7-criterion use case prioritization rubric

Use cases are scored on seven criteria. **Reusability is treated as a first-class dimension alongside value and feasibility** — this is what distinguishes a pipeline that compounds from one that does not.

| # | Criterion | Why it matters | Score 1–5 |
|---|---|---|---|
| 1 | Pain point alignment | Use case targets a *named* pain on the as-is map, not a generic opportunity | |
| 2 | Value creation | Sized in € or operational KPI movement (AHT, FCR, loss ratio); not "improves productivity" | |
| 3 | Risk approval likelihood | Will Risk / Compliance / DPO clear it within the engagement timeline? Score down if not | |
| 4 | Ease of build & integration | Concrete: data available, system access feasible, agent decision complexity manageable | |
| 5 | User adoption likelihood | The end user has time, incentive, and authority to change behaviour | |
| 6 | Reusability of tech assets | Building this generates components, templates, or services other domains can consume | |
| 7 | Reusability in agentic redesign | Architectural patterns established here apply to other domains' North Stars | |

A use case scoring **<3 average** is dropped. A use case scoring **<2 on criterion 3 (risk)** is dropped regardless of total score. A use case scoring **≥4 on criteria 6 + 7** is *promoted* even with mid value scores — it pays itself back through downstream reuse.

### I.4 Value sizing patterns

Three sizing approaches stack:

- **Outside-in benchmark.** External reference cases for comparable domains: typical 2× handler productivity, 4–5% reduction in unnecessary external spend, 5–10% reduction in cycle time on judgment-heavy workflows; >3pt loss-ratio improvement is plausible only when AI is embedded end-to-end (not as a screening assistant).
- **Bottom-up FTE map.** For each process step: FTE × hours × value per hour × % automatable. Sum across steps; then haircut by adoption probability (typically 30–70%).
- **Top-down P&L delta.** What does the operating committee need this domain to contribute by year 2? Work back from that number to required use case count and per-use-case sizing. Use this to **stress-test** the bottom-up; the gap between the two is the conversation with the sponsor.

Two sizing scenarios should always be presented: **FTE reduction** (cost out) and **FTE reinvestment** (capacity reallocated to insourced work, faster service, new revenue). The FTE-reinvestment story is almost always the better executive narrative and the one with higher adoption likelihood.

### I.5 Domain charter template

Every domain transformation runs against a one-page charter:

```
DOMAIN CHARTER — <Domain name>

Sponsor (single named accountable executive)
Operating committee (3–5 leaders meeting monthly)
KPI(s) the domain commits to (1–3, leading + lagging)
Scope in / scope out (process boundaries, geographies, customer segments)
Wave plan (Wave 1 features, Wave 2 features, decision gates)
Capability dependencies (data, IT integrations, agentic platform requirements)
Risk + compliance pre-clearances secured
Definition of done per wave (quantified)
Asset reuse expectation (% of build hours expected to come from existing assets)
```

The asset-reuse-expectation field is non-trivial. By domain three it should be ≥40%. By domain five it should be ≥60%.

---

## Part II — Assetization engineering

### II.1 Two-axis taxonomy

A reusable asset is classified on two axes — *placement* (architectural boundary, governance) and *form* (the unit of distribution and the discipline it carries):

**Placement axis (where it lives, who can change it):**

| Category | Domain-agnostic | Client-specific | Examples |
|---|:-:|:-:|---|
| **CORE** | ✓ | – | Data connectors, decision engines, compliance infrastructure, agent orchestration, evaluation harnesses |
| **DOMAIN** | – (vertical-specific) | – (client-agnostic within vertical) | Claims FNOL intake, KYC document extractor, AML alert normalizer, customer-service intent classifier |
| **WRAPPER** | – | ✓ | Configuration files, schema mappings, infrastructure configs |

Rules:
- CORE → extract immediately, benefits all clients.
- DOMAIN → extract when there are 2+ clients in the same vertical.
- WRAPPER → never extract; it is intentionally client-specific.

**Form axis (what it is, what discipline it carries):**

| Level | What it is | Build effort | Standards required |
|---|---|---|---|
| **Component** | Production-grade Python package, importable, semver, CI/CD-gated | Days–weeks | Strong: 80%+ unit coverage, integration tests, type checks, security scan, full docs |
| **Template** | Repository skeleton with placeholders; clones to new project | Hours–days | Strong: same as component for any code in the template |
| **Service** | Running, hosted endpoint with SLAs and observability | Weeks | Strongest: pen-tested, monitored, on-call, runbooks |
| **Snippet** | Single function or short script | Minutes–hours | Minimum: docstring, basic tests, license metadata |
| **Knowledge nugget** | Notebook, prompt pattern, post-mortem, design rationale | Minutes | None mandatory; encourages low-friction sharing |

The two axes combine: a CORE Component is the most rigorous artefact; a DOMAIN Knowledge Nugget is the lightest. The matrix tells contributors and consumers exactly what discipline applies.

### II.2 Extraction discipline — the sprint retrospective protocol

Extraction is a *cadence*, not a *project*. Every two weeks, the delivery team runs a **30-minute extraction review** as the last item of the sprint retrospective. Three questions:

1. **What did we build this sprint that another client / domain would need?**
2. **Can we make it client-agnostic with <4 hours of refactoring?** (test: remove client name, business rules, data schemas; replace with config files, parameter injection, interface contracts.)
3. **Does it meet the entry bar?** (standalone, tested, documented, no client data, no embedded credentials.)

If yes to all three, extract this sprint. Tag with version `v1.0`, add to the registry, link in the retrospective minutes. If extraction would take >4 hours, defer it and flag in the technical debt log; do not extract under pressure or it stays half-extracted forever.

The 4-hour threshold is the most important number in this part. If components require 40 hours of refactoring to become reusable, extraction discipline dies under delivery pressure.

### II.3 Repo skeleton and scaffolding

The repository layout makes extraction the path of least resistance:

```
/core-assets/                 # Extracted reusable components (CORE)
  /data-connectors/
  /decision-engines/
  /compliance/
  /orchestration/
  /evaluation/
  REGISTRY.md                 # Searchable Markdown asset registry
/domain-assets/               # Vertical-specific reusable components (DOMAIN)
  /claims/
  /kyc/
  /aml/
  /customer-service/
/client-deployments/          # Client-specific implementations (WRAPPER)
  /<client-id>/
    /config/
    /integration/
    /deployment/
    README.md                 # What's custom, what's reused
/accelerators/                # Pre-built domain templates
  /<domain>-<workflow>/
```

Every file in `/client-deployments/` carries a header comment that tags the component for extraction triage:

```python
# REUSABILITY: EXTRACTABLE | CLIENT-SPECIFIC | WRAPPER
# DEPENDENCIES: core-assets/data-connectors/<name> v1.2
# EXTRACTION-CANDIDATE: Yes/No — If yes, target: core-assets/<category>/
```

Engineers tag at creation time. If they don't, extraction never happens. The tag is enforced by a pre-commit hook (Part VII).

Each asset carries a metadata file (the form is shown for completeness; field names are stable):

```toml
[asset]
title       = "Alert Normalizer"
description = "Ingest alerts from transaction monitoring systems, normalize to standard schema"
type        = "component"           # component | template | service | snippet | nugget
placement   = "core"                # core | domain | wrapper
version     = "1.2.0"               # semver
authors     = ["@engineer-1"]
tags        = ["data-connector", "fs", "aml"]
license     = "internal"
data_class  = "no-pii"              # no-pii | pii | restricted
maturity    = "stable"              # alpha | beta | stable
deployments = ["client-001", "client-002"]
hours_saved = 72                    # cumulative, updated weekly
```

### II.4 Versioning, certification, hardening

Three concepts kept separate:

**Versioning (always).** Every asset uses semantic versioning from v1.0 (initial extraction). Patch = bug fix; Minor = backward-compatible feature; Major = breaking change. Client deployments pin to specific versions; controlled upgrades.

**Certification (entry bar).** Before an asset can be published to the marketplace, CI/CD must pass: lint, type check, test coverage threshold (80% for components/templates; 0% for snippets/nuggets), security scan, dependency vulnerability scan, README + API docs present, license declared. Certification is a *gate*, not a maturity level.

**Hardening (maturity track).** Three maturity levels signal *how much production-readiness investment* an asset has had:

| Level | Trigger | Investment |
|---|---|---|
| **ALPHA** | Just extracted from one engagement | 0–8 hours of polish |
| **BETA** | Used on 2+ engagements; integration tests pass | ~16–40 hours: error handling, observability, security review |
| **STABLE** | Used on 3+ engagements; SLA-ready | ~40–80 hours: load tests, regression tests, operational runbooks, on-call ownership |

Hardening investment is approved by the Asset Reuse Team (Part III.11), not pushed by individual engineers. Do not harden at ALPHA; you don't yet know which features matter.

### II.5 Cost and ROI tracking

Reuse claims must be auditable. The minimum mechanism is a per-component, per-engagement spreadsheet, automated by week six:

| Component | Engagement | Engineer-hours | Reused from | Hours saved | Marginal cost |
|---|---|---|---|---|---|
| Alert Normalizer | Engagement 1 | 80 | – | 0 | $12,000 |
| Alert Normalizer | Engagement 2 | 8 | Engagement 1 v1.2 | 72 | $1,200 |
| Risk Scorer | Engagement 1 | 120 | – | 0 | $18,000 |
| Risk Scorer | Engagement 2 | 35 | Engagement 1 v1.0 + custom | 85 | $5,250 |

Blended fully-loaded engineer cost (default $150/hour) is the conversion factor.

Automate by month three: parse git commits for component tags and engagement IDs, estimate hours from files-changed × calibration factor, write to a dashboard. The single number every dashboard surfaces:

> **Reuse rate** = hours saved this month / total delivery hours this month.

Target trajectory: 5% by month 3, 25% by month 6, 40%+ by month 12. **Engagement 2's total deployment hours must be ≥40% below Engagement 1's** for the same scope, or the reuse loop is broken and the playbook is mis-implemented.

### II.6 Accelerator templates per domain

After the first engagement in a vertical completes, package an accelerator: configuration file with TODOs, integration code referencing core/domain assets, infrastructure-as-code template, standard EDA + evaluation notebooks, step-by-step deployment README. The next engagement clones the accelerator, fills the TODOs, runs the deployment scripts. This is the mechanism that compresses deployment time from months to days [5][6].

Discipline rule: **start the next engagement by cloning the accelerator, not by copying the prior engagement's repo.** Copying the prior repo carries forward client-specific decisions and silently degrades reuse.

---

## Part III — Asset Marketplace

> *This is the deepest section of the playbook. The marketplace is the connective tissue that turns Parts I and II into compounding value. EY's 2026 thesis is the right frame: the marketplace is not an app store — it is the layer that **industrializes governance** rather than bypassing it [2]. Every design choice below serves that frame.*

### III.1 What the marketplace is, why it exists, what it isn't

**Definition.** An asset marketplace is the platform layer that lets producers publish reusable AI assets and consumers discover, evaluate, adopt, and contribute back — under enforced standards for quality, security, governance, and traceability.

**Why it exists.** Three failure modes a marketplace exists to prevent:

1. **Duplicate effort.** Without discovery, engineers rebuild what already exists. In a 200-engineer organization the duplication tax is conservatively 15–25% of build hours. Marketplaces close this gap by making "what exists" searchable in seconds, not days.
2. **Governance bypass.** Without pre-vetted assets, every project re-runs the same security review, RAI assessment, and architectural validation. Bypassing those reviews is the single largest risk in scaled agentic AI [3]. Pre-vetted marketplace assets carry their compliance signals, integration patterns, and architecture approvals as metadata; consumers inherit them.
3. **Stalled scale.** Without a clearing layer, the asset stock grows but the reuse rate doesn't. Reuse rate, not asset count, is the success metric.

**What it isn't.** It is not a beautiful catalog UI built before there are 100 assets to put in it. It is not a separate platform team disconnected from delivery. It is not a vendor product purchased instead of being built — most viable marketplaces are an opinionated combination of a Git monorepo, an artifact repository, a metadata schema, a search UI, and a governance workflow. The choice of vendor product matters less than the discipline that runs through it.

### III.2 Marketplace topology

Three topologies, each with different unit economics and governance:

| Topology | Scope | When to use | Key risks |
|---|---|---|---|
| **A. Internal-only** | Single firm | Default for years 1–2 | Asset stock grows slowly with one firm's delivery cadence |
| **B. Federated within firm** | Multi-BU within a group; federated repos with central discovery | When the firm has ≥3 BUs delivering AI independently | Federation governance overhead; need for cross-BU IP rules |
| **C. External / cross-firm** | Productized assets sold or licensed across enterprises | When asset stock + delivery method are mature; regulatory and IP ready | New unit economics (licensing, support, SLAs); brand exposure; competition with consultancy revenue |

A robust internal marketplace (Topology A) is a precondition for B and C. A federated marketplace within a firm (Topology B) is a precondition for cross-firm productization (Topology C). Skipping levels produces marketplaces that look impressive in demos but never reach reuse-rate targets.

External marketplace economics are addressed separately in §III.14.

### III.3 Reference architecture

A working marketplace has six functional layers. Vendor choices in brackets are illustrative defaults, not mandates.

```
┌──────────────────────────────────────────────────────────────────┐
│  6. Discovery + governance UI                                    │
│     Browse, search, asset detail page, consumption flow,         │
│     contribution flow, leaderboard / reputation                  │
│     [defaults: lightweight web app on top of monorepo + APIs]    │
├──────────────────────────────────────────────────────────────────┤
│  5. Metadata + search index                                      │
│     Federates across all team repos; normalizes the asset.toml   │
│     schema; indexes for keyword + semantic search                │
│     [defaults: Postgres + pgvector or Azure AI Search]           │
├──────────────────────────────────────────────────────────────────┤
│  4. Artifact store                                               │
│     Versioned binaries: pip-installable packages, Docker images, │
│     model weights, prompt bundles                                │
│     [defaults: JFrog / Azure Artifacts / Nexus + container reg]  │
├──────────────────────────────────────────────────────────────────┤
│  3. Source repositories                                          │
│     Per-team Git repos with mandatory asset metadata files,      │
│     CI/CD pipelines, branch protection                           │
│     [defaults: GitHub / Azure DevOps / GitLab]                   │
├──────────────────────────────────────────────────────────────────┤
│  2. Standards + governance hooks                                 │
│     Pre-commit hooks, CI gates, security scan, dependency check, │
│     license check, RAI checklist                                 │
│     [defaults: Ruff, mypy, pytest+coverage, SonarQube,           │
│                JFrog Xray, fawltydeps, custom RAI checks]        │
├──────────────────────────────────────────────────────────────────┤
│  1. Identity, access, audit                                      │
│     SSO, RBAC, immutable audit log, cost attribution             │
│     [defaults: enterprise IdP, IAM, SIEM/Event Hub + lake]       │
└──────────────────────────────────────────────────────────────────┘
```

**Architectural principle.** Layers 1–3 are *commodity*; do not build them. Layer 4 is *commodity for code, opinionated for prompts and models*; build prompt/model artifact handling on top. Layer 5 is the *core differentiator*; invest here. Layer 6 is *deferred until layer 5 reaches mass*: 20 assets fit in a Markdown registry searchable with Ctrl+F. Build the UI when the asset count crosses ~50–100 and there are ≥3 consuming teams. Doing it earlier is decoration.

### III.4 Asset metadata schema

The metadata is the marketplace. Without a strict schema, search degrades to chaos and governance becomes unenforceable. Required fields in the asset metadata file (`asset.toml`, `pyproject.toml` extension, or equivalent):

| Field | Purpose | Required |
|---|---|---|
| `title`, `description` | Human-readable | ✓ |
| `type` | component / template / service / snippet / nugget | ✓ |
| `placement` | core / domain / wrapper | ✓ |
| `version` | semver | ✓ |
| `authors`, `owner_team` | Accountability | ✓ |
| `license` | internal / open-source-X / proprietary | ✓ |
| `data_class` | no-pii / pii / restricted; drives access controls | ✓ |
| `tags` | Discovery; controlled vocabulary preferred | ✓ |
| `dependencies` | Other marketplace assets and external libraries | ✓ |
| `maturity` | alpha / beta / stable | ✓ |
| `deployments` | Count + identifiers of consuming engagements | ✓ (auto) |
| `hours_saved` | Cumulative measured saving | auto |
| `last_security_scan` | Timestamp + result | auto |
| `rai_signals` | Risk class, HITL requirement, model cards, bias evaluation | ✓ for components/services |
| `reference_architecture` | Which architectural pattern this fits | recommended |
| `peer_usage` | Downloads, views, likes, comments | auto |

Auto-generated fields are populated by the CI/CD pipeline and the marketplace API; never hand-edited. EY's 2026 framing is the right one: every metadata field is a *governance signal*, and the marketplace is the mechanism that surfaces those signals at the moment of consumption rather than weeks later in an architecture review board [2].

### III.5 The asset lifecycle on the marketplace

Five states. Transitions are gated by automation, not committees.

```
DRAFT  ──┐
         │  PR merged to main + CI passes
         ▼
PUBLISHED (alpha) ──┐
                    │  used on 2+ engagements; BETA promotion criteria met
                    ▼
PUBLISHED (beta) ──┐
                   │  used on 3+ engagements; hardening investment complete
                   ▼
PUBLISHED (stable) ──┐
                     │  no consumers for 2 quarters OR superseded by vN+1
                     ▼
                  DEPRECATED ──┐
                               │  6-month sunset window passes
                               ▼
                            ARCHIVED
```

Two transitions deserve emphasis:

- **Promotion to BETA / STABLE** is automated by the marketplace API based on `deployments` count and CI metrics; a maturity bump triggers a notification to the Asset Reuse Team to schedule the corresponding hardening investment. *No human committee approves promotion.* This is what scales.
- **Deprecation** is the most-skipped step. Without it, the marketplace fills with abandoned assets and discovery degrades. Automated rule: an asset with 0 consumers for 2 consecutive quarters and no maintenance commits in 6 months is auto-flagged DEPRECATED. The owner has 30 days to either revive (with a justification) or accept deprecation.

### III.6 Discovery and search

Three discovery modes, in order of frequency:

1. **Goal-driven semantic search.** "I need to extract structured data from a PDF claims form." Backed by embeddings over `description`, `tags`, `reference_architecture`. Semantic search is the default landing page.
2. **Browse by taxonomy.** Pivot by `placement` × `type` × domain. The taxonomy from §II.1 is the navigation tree.
3. **Reference-architecture pattern.** "Show me everything that implements the agentic-orchestrator pattern." This is how senior architects review assets for a new domain.

Two search affordances that disproportionately drive reuse:

- **"Used by these engagements" filter** on every result. Engineers trust assets used by peer teams; this surfaces social proof.
- **"Show similar" link** on every asset detail page. Computed from embedding similarity over descriptions; produces collisions that would otherwise hide forever.

Anti-pattern: keyword-only search over a 200-asset library. Hit rate degrades to <30% and engineers fall back to "ask in Slack," which kills the network effect.

### III.7 Contribution flows

Two contribution paths with different friction:

**Certified contribution (full standards).**

```
1. Identify candidate during sprint retrospective extraction review
2. Scope & design: confirm CORE / DOMAIN classification, choose form (component/template/service)
3. Extract from engagement repo into core-assets/ or domain-assets/
4. Generalize: remove client identifiers, replace business rules with config, add interface contracts
5. Package: src/, tests/, docs, asset.toml, pyproject.toml, README, optional notebook example
6. Open PR; CI runs the certification gate (lint, types, tests, security, license, docs)
7. Marketplace API generates a draft preview page; PR reviewer approves
8. Merge → published as alpha; metadata indexed; appears in search
9. Maintain: own the issues, run the release schedule, respond to consumer PRs
```

**Non-certified contribution (light path).** Snippets and knowledge nuggets bypass the certification gate. Required: a metadata file, a license declaration, and either a test or a working example. The point is to keep the friction low enough that engineers actually publish their useful one-off scripts and patterns. Without a low-friction path, the marketplace fills only with components and the long tail of useful knowledge stays in private notebooks.

A **review SLA** is critical. Certified-asset PRs without a review within 5 business days kill contribution culture. The Asset Reuse Team carries this SLA explicitly.

### III.8 Consumption flows

Six steps, each instrumented:

| Step | What the engineer does | Marketplace mechanism |
|---|---|---|
| **1. Explore** | Search for goal; browse top results | Semantic search; "used by" filter |
| **2. Evaluate** | Read asset detail; check maturity, RAI signals, peer usage; run example | Asset detail page; one-click sandbox notebook |
| **3. Adapt** | Clone or `pip install`; configure for engagement context | Pinned version; config templates |
| **4. Integrate** | Wire into the engagement codebase; update tests | Integration examples in asset README |
| **5. Risk-check** | Validate that inherited RAI signals match the use case's risk class | Inherit `rai_signals` automatically; flag mismatch |
| **6. Share back** | If the engagement extended the asset, contribute the patch back upstream | "Open PR upstream" button on asset page |

The "share back" step is the one that turns reuse into compounding value; without it, every engagement creates a fork and the asset fragments. Track the % of consuming engagements that contribute back as a marketplace KPI.

### III.9 Certification — standards by asset type

Standards are tiered by form (the Form axis from §II.1). The right discipline is the discipline that doesn't suffocate contribution:

| Asset type | Code style | Type checks | Test coverage | Security | Docs | Release |
|---|---|---|---|---|---|---|
| Component | Strong (Ruff/PEP8) | Strong (mypy strict) | ≥80% unit + integration | SonarQube + dep-scan + Xray | API ref + README + arch | Semver + CI gate |
| Template | Strong | Strong | ≥80% on template logic | Same as component | README + walkthrough | Semver |
| Service | Strong | Strong | ≥80% + load + chaos | Pen-tested | Runbooks + on-call | Semver + canary |
| Snippet | Recommended | Recommended | Recommended | Light scan | Docstring | Tag-only |
| Knowledge nugget | – | – | – | – | The doc *is* the asset | – |

The discipline tiers above are enforced **automatically** by CI/CD pipelines, not by checklists. This is non-negotiable. If a standard exists only in a wiki, it doesn't exist.

Concrete tooling defaults (current 2026): **Ruff** for lint+format, **mypy** for static types, **pytest + coverage.py** for testing, **CircleCI / GitHub Actions / Azure DevOps** for CI, **SonarQube + JFrog Xray** for security, **fawltydeps** for unused-dependency detection, **uv** for fast Python dependency management, **semver-action** for release gating. The list moves; the principle (CI-enforced standards, no manual checklists) is stable.

### III.10 Incentives, gamification, reputation

Reuse culture is mostly a question of incentives. Five mechanisms, each load-tested in published 2026 case studies:

1. **Reuse-first as the default.** "Have you searched the marketplace?" is a mandatory question on every architecture review template; CI/CD pipelines flag obvious duplication via code-uniqueness metrics; deviations from reuse require a written justification (1–2 paragraphs).
2. **Contribution recognition.** Per-engineer scoring on three axes — contribution (assets published, weighted by maturity), consumption (assets reused), activity (PRs opened on others' assets). Surface in performance reviews; do not surface as a public leaderboard until V2 (premature gamification produces gaming, not contribution).
3. **Hall-of-fame moments.** Once a quarter, surface the asset with the largest measured hours-saved and the engineer behind it; pair with a 5-minute show-and-tell at all-hands. Costs nothing; high signal.
4. **Reuse-baked-into-prioritization.** Criteria 6 and 7 in the use-case prioritization rubric (§I.3) reward use cases that produce or consume reusable assets. This is the most powerful incentive because it shapes the demand side, not just the supply side.
5. **Asset-product-team accountability.** A small team owns the marketplace platform itself, with explicit KPIs (reuse rate, time-to-first-reuse, contribution SLA). Without an accountable team, the marketplace becomes everybody's-and-nobody's responsibility.

Anti-pattern: monetary bonuses tied to contribution count. They produce a flood of low-quality snippets and degrade discovery faster than any other intervention.

### III.11 The Asset Reuse Team (ART) — operating model

The ART is the small team (typically 5–10 people) accountable for the marketplace and the surrounding reuse engine. Three roles:

| Role | Headcount | Mandate |
|---|:-:|---|
| **Asset platform engineer(s)** | 2–3 | Build and operate layers 4–6 of the reference architecture; own the metadata schema; carry the certification gate |
| **Asset product manager** | 1 | Owns the marketplace roadmap; tracks reuse KPIs; runs the contribution SLA; commissions hardening |
| **Forward-deployed asset engineer(s)** | 2–4 | Embed in delivery pods on 4–8-week rotations; identify extraction candidates in-line with delivery; help generalize the first hardening pass; return to the ART carrying tacit knowledge |

The forward-deployed model is what distinguishes a working ART from a dead-letter platform team. Forward-deployed engineers spend ≥60% of their time inside delivery pods; they are *measured* on assets extracted from those pods, not on platform features.

Reporting line: the ART reports into the AI CoE leadership, not into a delivery business unit. This protects the team from being repurposed as cheap delivery capacity when a delivery deadline slips.

### III.12 Maturity gating — when to upgrade tooling

Marketplaces fail more often from over-engineering than under-engineering. Four maturity stages; do not skip stages:

| Stage | Asset count | Tooling | What's missing |
|---|---|---|---|
| **0. Inception** | 0–20 | Single Markdown registry searchable with Ctrl+F; Git for source; semver tags | Search UI, semantic search, federation |
| **1. Indexed** | 20–100 | Add metadata files with controlled vocabulary; add basic search API over metadata; CI-enforced certification gate | Federation across multiple repos, semantic search |
| **2. Federated** | 100–500 | Federation across team repos via metadata index; semantic search; lightweight web UI; ART team in place | External productization, advanced governance signals |
| **3. Industrialized** | 500+ | Full reference architecture (§III.3); RAI signals embedded; peer-usage analytics; reputation + scoring; explicit deprecation pipeline | (the playbook) |

The most expensive mistake in marketplace engineering is jumping from stage 0 to stage 3 because a vendor offered a "marketplace platform" demo. Asset stock and contribution culture mature in lockstep with tooling; tooling that runs ahead of stock and culture rots.

### III.13 Governance — ownership, IP, license, RAI, data residency

Governance is what the marketplace exists to industrialize, in EY's 2026 framing [2]. Five governance signals must be carried as asset metadata, not asserted in a separate document:

1. **Ownership.** A single named team for every asset. No "shared" ownership; that's a euphemism for orphaned. Owner contact is the on-call rotation for that asset.
2. **License + IP class.** Every asset declares: internal-only / cross-engagement-allowed / external-redistributable / regulated. The license drives which engagements can consume it without a legal review.
3. **Data residency + class.** `data_class` field (`no-pii` / `pii` / `restricted`). Combined with `license`, drives geographic deployability. A GDPR-restricted asset cannot be auto-deployed to a non-EU engagement; the marketplace blocks it.
4. **Responsible AI signals.** Every component or service carries: risk class (matched to the 3×3 risk/complexity matrix from §IV.2), HITL requirement (mandatory / recommended / not-required), model card, bias evaluation summary, prompt-injection test results for any LLM-using asset. These are inputs, not afterthoughts.
5. **Audit trail.** Every consumption event (search, view, install, deploy) is logged with engineer ID, engagement ID, asset version, timestamp. The audit trail is the answer to "where is this asset deployed and what version is in production?" — a question every regulator now asks.

The governance maturity gap measured by Deloitte 2026 — only 21% of organizations have mature governance for autonomous agents while 73% plan to deploy [3] — is the single largest market opportunity for a credible marketplace. Industrialized governance is the differentiator, not the friction.

### III.14 External / cross-firm marketplace economics

Topology C (§III.2) is genuinely new territory; published case studies are thin. A productized external marketplace introduces three economic dimensions absent from internal marketplaces:

1. **Pricing model.**
   - **Per-deployment licensing** (one-off, scaled by client size). Simplest; ignores ongoing value.
   - **Subscription + usage** (annual fee + per-call or per-deployment metered). Best aligned with value; requires metering infrastructure.
   - **Outcome-based** (% of measured savings; co-investment with at-risk component). Alignment is highest; complexity is highest; precedent set by McKinsey's 2026 shift away from fee-for-service [4].
   - **Open-core + paid services** (asset is open-source; revenue is from support, hosting, certification). Best when the asset's defensibility is in the *delivery method* not the *code*.

2. **IP and license design.** The license that enables external monetization is rarely the license that enabled the internal asset to be built quickly. Plan for a cleansing / re-licensing pass before any asset enters the external marketplace; track the lineage of every snippet of third-party code.

3. **Support and SLA.** External consumers expect support tiers (community / standard / premium); internal-only assets typically have none. Build the support function alongside the marketplace, not after.

**Recommendation.** Treat the external marketplace as a separate product stream with its own P&L, brand, and roadmap; do not bolt it onto the internal marketplace governance. The risk of a regulated client deploying an inappropriate asset because internal and external assets are mixed in the same UI is too high.

### III.15 KPIs and measurement

Six headline KPIs, measured monthly:

| KPI | Definition | Target trajectory |
|---|---|---|
| **Reuse rate** | Hours saved via reuse / total delivery hours | 5% (M3) → 25% (M6) → 40%+ (M12) |
| **Asset stock** | Count of certified assets, by maturity tier | Track; do not optimize directly |
| **Time-to-first-reuse** | Days from asset publication to first external consumption | <30 days |
| **Contribution SLA** | % of certified-asset PRs reviewed within 5 business days | ≥90% |
| **Stale-asset rate** | % of assets with 0 consumption in last 2 quarters | ≤10% (drives deprecation discipline) |
| **Engagement reuse uplift** | % cost reduction in Engagement N+1 vs. Engagement 1 (same scope) | ≥40% by Engagement 2 |

Three KPIs explicitly *not* tracked, because they corrupt incentives:

- Asset count alone (drives quantity over quality; spawn rate of low-value snippets).
- Lines of code reused (drives copy-paste, not interface reuse).
- Marketplace UI page views (vanity metric; high views without consumption is a signal of bad search).

### III.16 Implementation roadmap — four phases over six months

| Phase | Months | Goal | Headline deliverables |
|---|---|---|---|
| **1. Lock in standards** | 0–1 | Discipline before tooling | Asset metadata schema; CI/CD gates; repo skeleton; contribution + consumption flow docs; ART team mobilized |
| **2. Launch marketplace V1** | 1–3 | Searchable, instrumented, governed | Federation index across team repos; semantic search; asset detail pages; contribution PR flow; first 20 certified assets |
| **3. Secure first proof points** | 3–4 | Demonstrable reuse on real engagements | 3+ engagements consuming marketplace assets; first measured ≥40% engagement uplift; "used by" social proof live |
| **4. Drive culture change** | 4–6 | Reuse becomes the default | Reuse-first in architecture review template; contribution recognition embedded in performance review cycle; first quarterly hall-of-fame; deprecation pipeline live |

Cumulative target by month 6: 50–80 certified assets, 25%+ reuse rate, ≥3 engagement reuse-uplift proof points, ART operating at full headcount.

### III.17 Marketplace anti-patterns

Six failure modes, observed across multiple 2026 enterprise deployments:

1. **Marketplace-UI-first.** Builds the catalogue UI before there are 20 assets in it. Looks great in board demos; produces zero reuse.
2. **Vendor product as the marketplace.** Buys a "marketplace platform" and assumes the discipline will follow. The discipline is the marketplace; the tool is plumbing.
3. **No deprecation pipeline.** Asset count grows monotonically; discovery degrades; engineers stop searching. Solve from day one with the auto-flag rule (§III.5).
4. **Single team owns everything.** ART becomes a delivery bottleneck. Forward-deployed model + automated certification gates are the antidote.
5. **Mixing internal and external in the same registry.** Compliance accident waiting to happen. Separate registries; separate licenses; separate brands.
6. **No measured reuse rate.** Without the headline KPI, the marketplace optimizes for asset count, which is the wrong objective. Implement reuse-rate measurement in phase 1, not phase 4.

---

## Part IV — Reference architecture, RAI, measurement

### IV.1 Two architecture profiles

Two distinct profiles serve two distinct contexts; choose explicitly per engagement:

**Profile A — Single-client at scale.** Opinionated, vendor-committed, geo-distributed.

- Compute & data: Databricks on the cloud the regulator dictates (Azure, AWS, or GCP), with **dual-cloud** only when a regulator forces it; do not adopt multi-cloud abstraction layers as a hedge.
- LLM serving: Cloud-native (Azure OpenAI / Bedrock / Vertex) with a single internal API gateway that adds rate limits, cost attribution, and prompt audit.
- Agent runtime: Kubernetes for stateful long-running agents; serverless (Databricks notebooks / Azure Functions / Lambda) for short-lived. Single agent framework (LangGraph today; revisit annually).
- Observability: LangFuse / LangSmith for agent decisions; Datadog / Azure Monitor for infrastructure; centralized SIEM for security events.
- Data infrastructure: Vector store on the chosen cloud (Azure AI Search / Mosaic AI vector search / Pinecone); feature store via Databricks Feature Store.
- Governance: MLflow model registry; cloud-native key vault; immutable audit lake (Event Hub → Data Lake / S3).

**Profile B — Cross-engagement portable (PwC delivery side).** Vendor-agnostic, minimal footprint, no hard dependencies on a single client's stack.

- Treat every dependency as a *plug-in* with an interface contract; ship two implementations (Azure-native, AWS-native) for any asset that needs cloud services.
- Avoid LLM-vendor-specific features (function calling syntax, structured outputs SDKs) where a portable equivalent exists.
- Pin every dependency aggressively; assume zero compatibility with the client's stack until proven.

The decision rule for any new platform addition: *add a platform only when a paying engagement requires it.* Every added platform increases infrastructure complexity by ~30%, triples the testing matrix, and degrades delivery velocity.

### IV.2 Responsible AI controls

Five RAI dimensions are mandatory; each translates to a marketplace metadata signal (§III.13) and a runtime control:

1. **Ethical design.** Risk class assigned per the 3×3 decision-making matrix:

| Decision complexity → | Low | Medium | High |
|---|---|---|---|
| **Low risk** | Full automation candidate | AI-assisted | HITL recommended |
| **Medium risk** | AI-assisted | HITL recommended | HITL mandatory |
| **High risk** | HITL recommended | HITL mandatory | Human-only or veto-only AI |

2. **Transparency / explainability.** Every agent decision logs prompt, retrieved context, model output, and confidence. Logs are queryable per case ID.
3. **Data privacy / security.** Data classification flows from data through to outputs; PII detection on every input and output; secrets management via vault with rotation.
4. **Human-in-the-loop integration.** HITL is a *workflow primitive*, not a switch. The agent surfaces a recommendation; a named human role accepts/rejects/edits; the audit trail records both.
5. **Continuous monitoring.** Drift detection (input distribution, output distribution, business KPI), incident response runbooks, periodic bias re-evaluation. Schedule: monthly for stable assets, weekly for components in alpha/beta.

### IV.3 Measurement framework

A unified metric tree connects the three pillars to the engagement P&L:

```
Engagement P&L delta
├── Domain transformation value (Part I)
│   ├── KPI movement (loss ratio, AHT, FCR, NPS, …)
│   ├── FTE reduction or reinvestment value
│   └── Revenue uplift (where applicable)
├── Assetization efficiency (Part II)
│   ├── Reuse rate (hours saved / total hours)
│   ├── Per-component cost trajectory
│   └── Engagement-N-vs-1 cost ratio
└── Marketplace effectiveness (Part III)
    ├── Time-to-first-reuse
    ├── Contribution SLA compliance
    ├── Stale-asset rate
    └── Engagement reuse uplift
```

Every dashboard surfaces all three layers. A delivery team that hits domain KPIs without moving reuse rate has won the battle and lost the war.

A **Definition of Done** is quantified per use case before delivery starts. Six dimensions:

| Dimension | Quantification |
|---|---|
| Accuracy | % within tolerance vs. ground truth or expert label |
| Completeness | % of inputs successfully processed end-to-end |
| Consistency | Variance across reruns on the same input |
| Efficiency | Throughput / latency / cost per call |
| User acceptance | Adoption rate + qualitative feedback |
| Reusability | % of asset signature matching marketplace standards (§III.9) |

A use case is not "done" until all six are at agreed thresholds.

---

## Part V — Operating model, change, talent

### V.1 Operating model archetypes

Three archetypes; choose based on the engagement archetype (§0.3) and the client's organizational maturity:

| Archetype | Where talent sits | When it works | Key risk |
|---|---|---|---|
| **Local** | Inside each BU | Small firm; 1–2 BUs; <100 engineers | Doesn't scale; standards diverge |
| **BU hub** | A small AI team per BU + a thin central CoE | Mid-size; 3–6 BUs | Cross-BU reuse low; politics of central function |
| **Central CoE + delivery pods** | Central CoE owns standards, ART, and CoE-hosted experts; pods are forward-deployed into BUs on rotation | Default for any large firm; required for marketplace scale | Central function disconnects from delivery if not forward-deployed |

The BCG 2026 framing — *"the choice between centralized platform infrastructure versus decentralized agent products"* [7] — is the right framing. The right answer in 2026 for most firms is **central platform infrastructure (Layer 4–6 of the marketplace) + decentralized agent products (delivery pods inside BUs) + a forward-deployed bridge (the ART)**.

### V.2 CoE / guild / pod design

| Unit | Composition | Mandate |
|---|---|---|
| **AI CoE** | 15–30 people: leadership, ART, central platform engineers, RAI / data governance leads | Owns standards, marketplace, platform; commissions hardening; runs the talent pipeline |
| **Domain pod** | 6–12 people per active domain: agent architect, engineers, domain SME, data engineer, change lead, product owner | Owns the domain charter (§I.5); delivers to the wave plan; extracts assets continuously |
| **Data Science guild** | All practitioners across CoE + pods | Cross-cutting community: peer review, internal certifications, knowledge sharing, hiring loops |
| **Asset Reuse Team** | 5–10 (see §III.11) | Sits inside the CoE; forward-deploys into pods |

Talent shape: heavy on agent architects (the scarce role in 2026), even balance on engineers and SMEs, light-but-present on RAI, change, and product. A common 2026 mistake is staffing the CoE with research-style data scientists; the binding skill is *production agent engineering*, which is closer to backend distributed systems with prompt-engineering judgment overlaid.

### V.3 Influence-model change framework

Behaviour change is the binding constraint on adoption, not technology. Four levers, applied together:

| Lever | What it looks like in practice |
|---|---|
| **Role modelling** | Sponsor and operating-committee leaders use the agents themselves and talk about it; do not delegate adoption |
| **Conviction & understanding** | Compelling change story tied to the domain KPI; transparent risk discussion; published learning agenda |
| **Capability building** | Time-protected training; mandatory marketplace orientation for every new engineer; pair-working with ART on the first asset extracted |
| **Formal reinforcement** | Reuse expectation in domain charters; reuse-rate KPI on dashboards; performance review entries for contribution and consumption |

Eight standard initiatives populate the levers:

1. Sponsor activation (lever 1).
2. Operating committee charter and cadence (levers 1, 4).
3. All-hands change story + quarterly hall-of-fame (lever 2).
4. Marketplace orientation onboarding (lever 3).
5. Pair-extraction programme: ART pairs with a delivery engineer on their first asset (lever 3).
6. Reuse expectation in every domain charter (lever 4).
7. Contribution + consumption signal on performance review (lever 4).
8. Architecture review reuse-first checklist (lever 4).

Benchmarks worth keeping for executive conversations: transformations where leaders explicitly role-modelled the change are ~4× more likely to succeed; transformations with a compelling, communicated change story are also ~4× more likely to succeed. These are the two leadership levers with the highest measured payoff.

### V.4 Programme governance

Cadence shape — same in every engagement archetype:

```
Sponsor (executive, single named accountable)
    │
    ▼
Operating Committee (3–5 leaders, monthly, decision-making)
    │
    ▼
Theme working groups (per domain + per cross-cutting workstream, biweekly)
    │
    ▼
KPI heartbeat (weekly, ART + delivery PMs, instrumented dashboards)
```

Two governance disciplines that punch above their weight:

- **Decision logs.** Every operating-committee decision is logged with context, alternatives considered, and the rationale chosen. Six months in, this is the most-referenced artefact in the engagement.
- **Kill criteria.** Every domain charter includes the criteria under which the operating committee will *stop* the domain effort and reallocate. Without explicit kill criteria, stalled domains become political and resource-locked.

### V.5 Commercial models — including outcome-based

Three commercial structures, each appropriate to a different engagement archetype:

| Model | Mechanic | When it fits | Risk to PwC |
|---|---|---|---|
| **Time & materials** | Fixed daily rate × days | Discovery / blueprint phases; novel engagements | Low; familiar |
| **Fixed price + milestones** | Pre-agreed deliverables; milestone payments | Build phases with clear scope | Medium; scope creep |
| **At-risk / outcome-based** | Component of fee tied to measured outcomes (KPI movement, reuse rate, hours saved) | Industrializing-reuse and AI-factory-aspirant archetypes (C, D in §0.3) | Highest; highest upside |

The 2026 trend is clear: leading firms are shifting from fee-for-service to outcome-based engagements [4]. The shift is enabled — not caused — by the productized playbook + asset stock; without those, outcome-based pricing is a way to lose money predictably. Earn the right to outcome pricing through Topology A and Topology B (§III.2) maturity first.

---

## Part VI — Delivery method (engagement-side)

### VI.1 Test-driven agentic delivery — five phases

The delivery method is its own asset. Every engagement that builds agents follows the same five-phase shape:

| Phase | Duration | Output |
|---|---|---|
| **1. Mobilize** | Weeks 1–2 | Charter signed; team in place; environments provisioned; data access cleared; risk pre-cleared |
| **2. Design** | Weeks 2–4 | Agent catalog; per-feature swimlane; data inputs/outputs/contracts; integration points; RAI controls; agreed Definition of Done quantification |
| **3. Build agents** | Weeks 4–8 | Each agent: unit tests first → implementation → component tests → marketplace asset metadata → CI gates passing |
| **4. Build workflows** | Weeks 6–10 | Agents orchestrated into end-to-end workflow; integration tests; HITL flow tested; non-functional tests (load, latency, cost) |
| **5. Prepare roll-out** | Weeks 9–11 | UAT with named users; runbooks; on-call rotation; training pack; deprecation plan for the legacy process; phased adoption schedule |

Three engineering disciplines that are non-negotiable:

- **Tests are written first.** The agent's behaviour is specified by its tests before the prompt or the model choice is made. This is the single largest determinant of scale-readiness.
- **Cross-functional pods.** Every pod has the SME, the engineer, the data person, the RAI lead, and the change lead — all of them — every week.
- **Weekly iterations.** No two-week sprint cadences for agent work in 2026; the inner loop is too long. Weekly demos with the operating committee.

### VI.2 Agent catalog template

Every agent in scope is documented on a one-pager:

```
AGENT NAME: <name>
PURPOSE: <one sentence>
INPUTS: <data sources, formats, schemas, SLA>
OUTPUTS: <decision, recommendation, generated artefact, schema>
DECISION CLASS: <from 3×3 risk/complexity matrix; HITL requirement>
TECHNOLOGY: <model, framework, vector store, retrievers, tools>
INTEGRATIONS: <upstream + downstream systems, APIs, auth>
KPIs: <accuracy / completeness / latency / cost targets>
DEPENDENCIES: <marketplace assets consumed; with versions>
EXTRACTABILITY: <which parts of this agent become marketplace assets>
OWNER: <named team>
```

The agent catalog is itself a marketplace asset: a *template* (§II.1, Form axis). Every engagement contributes its agents back, raising the next engagement's design speed.

### VI.3 BPMN / swimlane standards

Every workflow is documented as a BPMN-style swimlane diagram with explicit lanes for: each agent, each system, each human role, the audit log. Decision points show their criteria. HITL gates show their accept/reject/edit options. Failure paths are first-class, not appendices.

The diagram is a delivery artefact, not a documentation afterthought; it is the contract between SME, engineer, and RAI lead during build, and the source of truth for runbooks and incident response after go-live.

### VI.4 Engagement reference cases — the pattern

Every closed engagement contributes a sanitized one-page reference case to the delivery library:

```
INDUSTRY / FUNCTION: <e.g., insurance / claims, retail banking / mortgage>
PROBLEM: <starting state, sized>
APPROACH: <agents deployed, workflow, integrations>
MEASURED RESULT: <e.g., AHT 25 → 4 min; automation <5% → >80%; €X savings>
ASSETS PRODUCED: <list of marketplace assets created or extended>
LESSONS: <2–3 patterns; 1–2 anti-patterns>
DURATION + TEAM SIZE: <weeks; FTEs>
```

Reference cases compound: by the third engagement in a vertical, the new engagement's design phase is half the length because the reference cases pre-answer most architectural questions.

---

## Part VII — Coding practice for agentic AI delivery (2026)

This part exists because the *engineering* practice for agentic AI delivery has matured rapidly in 2026, and PwC delivery teams must operate at the same standard as the leading internal AI organizations [4][8]. The practices below are the current 2026 stack; review and update annually.

### VII.1 The agentic coding stack

A 2026-current delivery environment combines:

- **An IDE-resident agent** for inline edits, planning, and refactoring (Cursor, Claude Code, GitHub Copilot).
- **A CLI agent** for non-interactive tasks: scripted refactors, batch edits, CI pipelines (Codex CLI, Claude Code in headless mode, Gemini CLI) [8].
- **A subagent / parallel-agent layer** for tasks that benefit from isolation: multi-file research, long-running test runs, parallel exploration of design alternatives [8].
- **Deterministic hooks** as the security and discipline layer: pre-tool-use guards, post-tool-use formatters, stop notifications.
- **A skills layer** for reusable, progressively-disclosed task instructions (current Anthropic SKILL.md format [10]).

Multi-model orchestration is a 2026 norm, not an experiment: different agents are stronger at different tasks (architecture/refactoring vs. rapid generation vs. multimodal vs. long-context analysis), and production teams route work accordingly across isolated branches [8].

### VII.2 Three-file configuration: AGENTS.md, CLAUDE.md, GEMINI.md

A 2026 repository carries three small configuration files at the root, each ≤150 lines [8]:

- **`AGENTS.md`** — the canonical context file (Linux-Foundation–stewarded standard, 60K+ repos). Contains universal rules: security, anti-patterns, definition of done, skill index. Read by Codex CLI, Cursor, Antigravity, Aider, OpenCode, and a growing list of tools.
- **`CLAUDE.md`** — a 5-line shim that imports `AGENTS.md` (`@AGENTS.md`). Claude Code is the major holdout that does not yet read `AGENTS.md` directly; the shim is the accepted workaround.
- **`GEMINI.md`** — the Gemini CLI equivalent; same pattern.

**ETH/DeepMind 2026 evidence.** Bloated context files reduce SWE-bench task success by ~3% and add 20–23% to inference cost. Keep `AGENTS.md` ≤150 lines. Treat it as code: prune quarterly, add a rule only after the same mistake happens twice.

Cursor's published 2026 best practice reinforces the same point: **plan before coding** is the most impactful practice (research from the University of Chicago); manage context tightly, let agents find context through search rather than over-tagging files [11].

### VII.3 Skills with progressive disclosure

Skills (`.agent/skills/<skill>/SKILL.md`) carry domain- or artifact-specific guidance and load on demand. Anthropic's 2026 best-practice articulation is the operating standard [10]:

- **Concise wins.** Only add context the model doesn't already have; assume strong baseline capability.
- **Three-level disclosure.** Frontmatter (always loaded), body (loaded on trigger), bundled `references/` and `scripts/` (loaded on-demand). Keeps context lean until detail is needed.
- **Match specificity to fragility.** High-freedom (text instructions) when many approaches work; medium (pseudocode) when a preferred pattern exists; low (specific scripts) when operations are fragile and consistency is critical.

A delivery repo carries a small set of artifact-typed skills: webapp, micro-site, deck (multiple paths), interactive-tools, brand, client-deliverable, workflow-and-docs. The skill index lives in `AGENTS.md`.

### VII.4 Deterministic hooks

Hooks are the layer that makes "no edits to `.env`" and "auto-format on save" non-negotiable. Three load-bearing hooks per repo:

- **`pre-tool-use-guard.sh`** — blocks edits to `.env*`, `migrations/`, `auth/` directories. Returns exit code 2 to deny.
- **`post-tool-use-format.sh`** — auto-formats edited files (Prettier, Ruff). Idempotent.
- **`stop-notify.sh`** — desktop notification when the agent stops. Surfaces context-switch points.

Hooks are committed to the repo (under `.claude/hooks/` or equivalent) with executable bit set; their behaviour is documented in `AGENTS.md`.

The principle: *deterministic guardrails > prompted instructions.* A prompt instruction is followed *most* of the time; a hook is non-negotiable. Use prompts for nuance; use hooks for safety.

### VII.5 Subagents and parallelism

Subagents are pre-configured roles (`code-reviewer`, `test-runner`, `research`) that receive their own context window and return a summary to the main thread. Three uses dominate in 2026:

1. **Context isolation.** A multi-file research task that would consume 75K tokens in the main thread can be delegated to a subagent that returns a 500-token sanitized summary. The main thread stays clean.
2. **Specialization.** A code-reviewer subagent loads its own checklist and review heuristics; the main thread doesn't carry that context unless reviewing.
3. **Parallel exploration.** Two or three subagents run in worktrees on separate branches, each implementing a different design hypothesis; the main thread compares results.

Each subagent definition lives in `.claude/agents/<name>.md` (or the equivalent for the tool in use). Cheaper models for subagents are a defensible cost optimization (`CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4-5` is a common 2026 choice).

### VII.6 Code quality gates

Defaults that ship in `.cursor/rules/`, `.claude/settings.json`, and CI pipelines:

| Gate | Tool defaults | Threshold |
|---|---|---|
| Lint + format | Ruff (Python), Biome / Prettier (TS) | Zero warnings |
| Static types | mypy strict (Python), tsc strict (TS) | Zero errors |
| Tests | pytest + coverage.py (Python), Vitest (TS) | ≥80% on production code |
| Dead-deps | fawltydeps (Python), depcheck (TS) | Zero unused declared deps |
| Security | SonarQube + JFrog Xray (or GitHub Advanced Security) | Zero high; triaged medium |
| Secrets scan | gitleaks / TruffleHog | Zero hits |
| License | scancode-toolkit / licensee | Allow-list enforced |

CI runs these on every PR; merging is blocked on failure. No checklists in wikis; the gate is the wiki.

### VII.7 Security, dependencies, SBOM

A 2026-grade delivery includes:

- **SBOM** (Software Bill of Materials) generated on every release (CycloneDX or SPDX format). Publish as a build artefact; make it queryable for vulnerability lookup.
- **Pinned dependencies.** Exact versions in lockfiles (`uv.lock`, `pnpm-lock.yaml`); Renovate or Dependabot configured to PR weekly.
- **Secrets management.** No secrets in the repo, ever. Cloud key-vault references in code; pre-commit secret scanning; credentials rotated quarterly.
- **Supply-chain provenance.** Signed commits, signed artefacts (Sigstore / cosign); verify provenance in CI before deployment.

Treat the SBOM as a *governance signal* on every marketplace asset (§III.13).

### VII.8 Observability for agents

Every agent decision is logged:

- **Prompt + retrieved context + tool calls + final output**, all bound to a case ID.
- **Latency, cost, tokens** per call.
- **Confidence / score / refusal flag** if the model emits one.
- **HITL events** (override, edit, reject) bound to the same case ID.

LangFuse and LangSmith are the 2026 defaults for agent telemetry; Datadog / Azure Monitor for infrastructure correlation; centralized SIEM for security event correlation. Do not build custom telemetry; it is plumbing.

The single dashboard to ship in week one: *case throughput × average cost × HITL override rate × accuracy*. Everything else hangs off it.

---

## Appendix A — Anti-pattern catalog

Six "do not build yet" traps and four "do not do" anti-patterns, observed across multiple enterprise deployments:

**Do not build yet (early-stage premature investments)**

1. **Marketplace UI before there are 50+ assets and 3+ consuming teams.** Markdown registry + Ctrl+F is the MVP.
2. **Custom MLOps platform.** Databricks + MLflow + cloud-native tooling cover the requirements; build only the gap.
3. **Multi-cloud abstraction layer.** Adds 30%+ complexity. Pick one cloud; add others when a paying engagement requires it.
4. **Prompt management system.** Git + YAML is sufficient until ~1,000 prompts; LangSmith / LangFuse cover analytics.
5. **Custom LLM fine-tuning pipeline.** Prompt engineering + RAG covers ~90% of cases; fine-tune only when measurable failure persists.
6. **Comprehensive RAI governance platform.** Checklists + manual review work until ~50 deployments; build process before tooling.

**Do not do (durable anti-patterns)**

1. **Stub data presented as real.** Never. Especially not in client-facing demos.
2. **Empty `catch` / silent fallback.** Failures must be loud; silent defaults mask problems until production.
3. **Refactoring unrelated code in the same PR as a bug fix.** Two PRs, always.
4. **Auto-generating `AGENTS.md` or `SKILL.md` via `/init`.** ETH 2026 evidence shows negative ROI; the file is too important to LLM-generate.

---

## Appendix B — Engagement archetype playbooks

Four archetype-specific 90-day mobilizations.

### Archetype A — Greenfield ambition

| Week | Focus | Deliverable |
|---|---|---|
| 1–2 | Sponsor + ambition framing | Six-dimensions self-assessment scored; ambition statement signed by sponsor |
| 3–6 | Domain selection + first charter | Domain × BU value matrix; three priority domains; charter for domain 1 |
| 7–10 | Domain 1 build (Wave 1) | First feature live in pilot; first three assets extracted to marketplace |
| 11–12 | Standards + ART mobilized | ART team in place; metadata schema live; reuse-rate dashboard week-1 |

Commercial: T&M for blueprint; fixed-price + milestones for build; outcome-based reserved for year 2.

### Archetype B — Scattered pilots

| Week | Focus | Deliverable |
|---|---|---|
| 1–2 | Pilot inventory | Catalogue of all existing pilots with status, owner, value, reuse potential |
| 3–6 | Harvest existing | Top 20 pilots harvested; assets extracted; metadata back-filled |
| 7–10 | Marketplace V1 | Federation index + semantic search live; first 30 certified assets |
| 11–12 | Domain pilot | First *new* domain charter pulling demand into the marketplace |

Commercial: fixed-price for the harvest; T&M for the marketplace build; outcome-based for the new domain.

### Archetype C — Industrializing reuse

| Week | Focus | Deliverable |
|---|---|---|
| 1–2 | CoE + ART audit | Gap analysis vs. §III.11; ART team gaps closed |
| 3–6 | Marketplace V2 | RAI signals embedded; reputation/scoring live; deprecation pipeline live |
| 7–10 | Reuse uplift proof points | 3+ engagements showing measured ≥40% reuse uplift |
| 11–12 | Outcome-based commercial pilot | First at-risk engagement structured against reuse rate + KPI movement |

Commercial: outcome-based with floor; reuse-rate KPI as a contractual lever.

### Archetype D — AI factory aspirant

Multi-track from week 1: domain + assetization + marketplace + external productization + outcome-based commercial all advance in parallel. Headcount-heavy mobilization; appoint ART, external-marketplace product manager, and outcome-pricing specialist in week 1.

---

## Appendix C — Worked case study: bodily-injury claims

A representative end-to-end domain transformation (industry, function, and identifiers abstracted):

**Starting state.** ~190 FTE handling ~16,000 claims/year against a ~€535M claim spend. Negative run-off results across the segment over multiple years (an industry-wide pattern). Pain points: case re-familiarization burden across handlers, large volumes of unstructured documents (medical reports, legal correspondence), inconsistency across handlers, "sleeping giants" (cases sitting unworked for months), opaque settlement decisioning.

**Agentic North Star (after redesign).** Six modular AI workflows, each a separable feature with its own metrics and HITL profile:

| Feature | Purpose | Risk class | HITL |
|---|---|---|---|
| **A. Severity check** | Triage claims into fast-track / standard / complex on intake | Medium | Recommended |
| **B. Injury assessment** | Extract structured injury data from medical reports; flag inconsistencies with self-reported | High | Mandatory |
| **C. Missing information detector** | Identify incomplete cases; auto-draft requests to claimants/providers | Low | Not required |
| **D. Inconsistency check** | Cross-reference statements, medical, legal, and prior claims for contradictions | High | Mandatory |
| **E. Structuring the unstructured** | Convert PDFs, scans, emails into a normalized case schema | Low | Not required |
| **F. Automatic summary** | Generate handler-ready case summary on assignment + on update | Medium | Recommended |

**Outcome envelope (sized in design).** €3–8M annual value on the assistant cluster (medium- and large-loss claims), with two scenarios: pure FTE reduction (~€8M cost out) vs. capacity reinvestment into insourcing of external advisors (similar net economic value, materially higher adoption probability). Combined-loss-ratio improvement of ≥3 points is plausible only when the workflows are wired into settlement decisioning end-to-end, not bolted onto the front of the existing process.

**Asset extraction outcomes (illustrative).**
- One CORE component (document extractor; reusable across any insurance, banking, legal triage domain).
- Three DOMAIN components (severity classifier, inconsistency detector, case summarizer — vertical-specific, client-agnostic within insurance claims).
- Two WRAPPERS (claims-management-system integration adapter, schema map for the specific case data model).

A second-engagement BI claims build on this asset base targets ~50–60% of the build hours of the first engagement, with the cost reduction reinvested into deeper feature scope (settlement-decisioning automation, fraud detection extension).

**Delivery shape.** Five-phase test-driven delivery (§VI.1). Cross-functional pod: agent architect, two engineers, claims SME, RAI lead, change lead, product owner. Weekly operating-committee demo. Eleven-week build-and-test phase from kickoff to UAT-complete on a six-feature scope.

---

## Sources

[1] BCG (2026). *Scaling AI Requires New Processes, Not Just New Tools.* `web-assets.bcg.com/pdf-src/prod-live/scaling-ai-requires-new-processes-not-just-new-tools.pdf` — quote-to-order example with 30–40% labor cost reduction; 70/20/10 distribution of agent-handled / collaborative / human-intensive cases.

[2] EY (2026). *How EY Sees Marketplaces Shaping the Future of Enterprise AI.* The Tech Talks Network, *Consulting the Future* podcast. `techtalksnetwork.com/podcast/consulting-the-future/episode/how-ey-sees-marketplaces-shaping-the-future-of-enterprise-ai` — marketplace as governance industrialization layer; pre-vetted assets, integration patterns, security signals; "client zero" approach (269M transactions/day across 13.6K workflows); "industrialize governance rather than bypass it."

[3] Deloitte (2026). *State of AI in the Enterprise — 2026 Report.* `deloitte.com/us/en/what-we-do/capabilities/applied-artificial-intelligence/content/state-of-ai-in-the-enterprise.html` and `hpcwire.com/bigdatawire/2026/03/03/deloittes-state-of-ai-2026-why-enterprise-execution-is-falling-behind-adoption/` — 21% governance maturity for autonomous agents; 73% deployment plans within 2 years; 73% security and data-privacy concerns; execution gap between strategy readiness (42%) and governance readiness (30%).

[4] Flor, G. (2026). *Inside McKinsey's AI Operating System.* The AI Opportunities. `theaiopportunities.com/p/inside-mckinseys-ai-operating-system` — ~25,000 internal AI agents across ~40,000 employees; one-agent-per-employee target; shift from fee-for-service to outcome-based pricing; Lilli, QuantumBlack Horizon, AI Factory model.

[5] Accenture (Jan 2025; cited as 2026 active product line). *AI Refinery for Industry — Accenture Launches AI Refinery for Industry to Reinvent Processes and Accelerate Agentic AI Journeys.* `newsroom.accenture.com/news/2025/accenture-launches-ai-refinery-for-industry-...` — pre-built industry agents (12 → 100+); deployment time months/weeks → days; built on NVIDIA software.

[6] Accenture (Apr 2026). *AI in Manufacturing — Systemic AI for Performance.* `accenture.com/us-en/insights/digital-engineering-manufacturing/ai-manufacturing` — AI as infrastructure with shared data, platforms, and guardrails reusable across plants and deployments.

[7] BCG (2026). *Rebuilding Asset Management for an AI-First World* and *AI@Scale capability page.* `bcg.com/publications/2026/rebuilding-asset-management-for-an-ai-first-world` and `bcg.com/capabilities/artificial-intelligence` — DRI (Deploy / Reshape / Invent) framework; 10-20-70 (algorithms / tech-and-data / people-and-processes); centralized platform infrastructure vs. decentralized agent products as key operating-model decision.

[8] Halallens (2026). *Agentic Coding 2026: AI Agent Teams Guide* and Prusov S. (2026), *The Agentic Coding Landscape in 2026.* `halallens.no/en/blog/agentic-coding-in-2026-...` and `medium.com/@sergey.prusov/the-agentic-coding-landscape-in-2026-a-quick-guide-...` — three-file configuration (AGENTS.md / CLAUDE.md / GEMINI.md); multi-model orchestration in isolated branches; hooks for event-driven automations.

[9] QuantumBlack / McKinsey (Apr 2026). *Creating a Future-Proof Enterprise Agentic Platform Architecture.* Medium. `medium.com/quantumblack/creating-a-future-proof-enterprise-agentic-platform-architecture-c21fc48406a5` — Agents-at-Scale platform; balancing short-term impact against long-term technical debt; standards for security, traceability, and observability in non-deterministic systems; vendor lock-in avoidance.

[10] Anthropic (2026). *Skill Authoring Best Practices.* Claude API Docs. `platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices` — concise-is-key; three-level progressive disclosure; match specificity to task fragility (high / medium / low freedom).

[11] Cursor (2026). *Best Practices for Coding with Agents.* `cursor.com/blog/agent-best-practices` — plan-before-coding (University of Chicago research); context management via search rather than manual tagging.

---

*Last updated: May 2026. Review cycle: quarterly. Owner: PwC AI delivery practice.*
