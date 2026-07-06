---
title: "Showroom Phase 1 — Internal-Only"
---

# Showroom Phase 1 — Internal-Only

**Status:** In planning — sprint 1 target  
**Phase-2 reference (production target):** `../showroom-azure-architecture.md`, `../showroom-qr-flow.md`

This folder contains all design and operational artefacts scoped to **Phase 1 of the PwC AI Showroom**. Phase 1 is deliberately minimal: internal PwC FinCrime staff only, PwC Entra ID, mocked user-to-demo authorization map, no QR flow, no external users, no APIM, no Cosmos DB, no Event Hub.

Direction from the project sponsor at kickoff (2026-07-02):
> *"Phase 1: showroom strictly internal, enable the PwC tenant Entra ID and that's it. Access to our FinCrime teams. Simple UI, plug in micro-frontend, take it from there. Make it simple, really — because we need to give something to the hands of our partners first."*

---

## Who does what

| Role | Person | Responsibilities in Phase 1 |
|---|---|---|
| **Solution Architect** | Solution Architect | Overall architecture, phase-1 design spec, alignment meeting with the developer, handoff to DevOps and developer |
| **Full-Stack Engineer** | Developer | Next.js application, MSAL React integration, micro-frontend catalog, mock authorization, CI/CD pipeline, Overwatch embedding |
| **DevOps / Infra / Security** | DevOps engineer | Azure subscription setup, App Registration, ACR, ACA environment, Azure DevOps pipelines, Log Analytics, access grants |
| **Product / Content** | Technical reviewer | Overwatch demo content, micro-frontend package handoff, FinCrime use-case context briefing to the team |

---

## Files in this folder

| File | Purpose | Audience |
|---|---|---|
| `README.md` | This file — scope, roles, folder map | All |
| `showroom-phase1-architecture.dot/.png` | Architecture diagram (source + rendered PNG) | All |
| `showroom-phase1-architecture.pdf` | Architecture diagram (PDF) | All |
| `showroom-phase1-flow.md/.mmd/.pdf` | Runtime OIDC flow — narrative + sequence diagram | Developer · Architect |
| `devops-runbook.md` | Azure setup runbook | DevOps engineer |
| `aca-vs-appservice-decision.md` | Hosting platform decision record | Architect |
| `integration-options.md` | Micro-frontend integration options analysis | Developer · Architect |

---

## Phase scope: what's in, what's out

| Concern | Phase 1 (this folder) | Phase 2 (target) |
|---|---|---|
| **Users** | Internal PwC FinCrime (Entra ID, group-gated) | Internal + external prospects |
| **Identity** | PwC Entra ID, MSAL React PKCE | + Entra External ID for prospects |
| **Demo access control** | Hardcoded JSON map `userOid → [demoIds]` | QR-code session flow, RS256 JWT, Cosmos DB session store |
| **Gateway** | None (ACA direct ingress or Front Door) | APIM with full policy library |
| **Micro-frontends** | Overwatch launched as independent ACA app via top-level redirect (no iframe, no proxy) | Full catalog, Module Federation shell, Content Safety |
| **Observability** | ACA container logs → Log Analytics (default) | App Insights RUM, custom events, Event Hub → ADLS audit |
| **Backend data** | Mocked | Live agent backends, Key Vault, Private Endpoints |
| **Infrastructure** | ACA + ACR + (optionally) Front Door | Full networking: VNet, Private Endpoints, WAF |

---

## Folder structure expected after sprint 1

```
showroom/
  phase1/
    README.md                             <- this file
    showroom-phase1-architecture.dot/.png <- architecture diagram
    showroom-phase1-flow.mmd/.md/.pdf     <- runtime OIDC flow
    devops-runbook.md/.pdf                <- DevOps runbook
    aca-vs-appservice-decision.md/.pdf    <- hosting decision record
    integration-options.md               <- micro-frontend options
    footer.tex                           <- PDF footer (runbook only)
    build_all.sh                         <- regenerate all artefacts
  phase2/
    showroom-azure-architecture.md        <- phase-2 full spec
    showroom-qr-flow.md                   <- phase-2 QR session flow
```
