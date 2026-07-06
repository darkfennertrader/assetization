---
title: "PwC Showroom — Azure Architecture"
subtitle: "L1 Showroom + L4 Shared Substrate services consumed"
author: "Raimondo Marino — Solution AI Architect"
date: "2026-07-02"
---

# PwC Showroom — Azure Architecture

## 1. Scope

This document describes the **Azure service topology for L1 Showroom** — the external-facing demo environment that PwC salespersons use to give prospects a 1-hour scoped AI experience via a QR code. It covers every Azure service required, the rationale for each choice, networking, identity, scaling, and deployment.

For the auth and session flow in detail see `showroom-qr-flow.md`. For the overall four-layer platform picture see `general_architecture/general-architecture-highlevel-explained.md`.

---

## 2. Architecture diagram

![PwC Showroom — Azure services diagram](showroom-azure-architecture.png)

\bigskip

---

\newpage

## 3. Azure service selection and rationale

| Azure service | SKU / tier | Role in Showroom | Why this, not alternatives |
|---|---|---|---|
| **Azure Front Door** | Standard/Premium | Global CDN, TLS termination, custom domains, multi-origin failover, WAF policy attachment | Front Door is the only Azure service that combines a global anycast edge, CDN, WAF, and custom domain TLS in a single resource. Application Gateway is regional — not suitable for a global demo platform. |
| **Front Door WAF Policy** | DRS 2.1 + Bot manager | OWASP CRS 3.2 rule set, bot manager, edge rate limiting before any traffic reaches the app | WAF at the edge means bad traffic is stopped before it reaches the ACA environment. No additional cost vs attaching at Application Gateway, but lower latency (inspection happens at the PoP). |
| **Azure DNS** | Standard zone | Apex and subdomain records for `admin.showroom.pwc.example` and `showroom.pwc.example` | Already part of the PwC tenant DNS infrastructure — no additional service. CNAME to Front Door endpoint. |
| **Entra ID** | Existing PwC tenant | PKCE Bearer token for the Presenter Admin panel (`/admin/*` routes). Salesperson logs in with their PwC credentials — no separate account. | Entra ID is already the PwC identity provider. MSAL React handles PKCE entirely client-side. No additional Entra configuration beyond registering the Showroom SPA app. |
| **Azure Key Vault** | Standard tier | Stores the RS256 private key used to sign session JWTs. Accessed via Managed Identity only — no stored connection strings. Also stores APIM gateway certificate and any future secrets. | Key Vault is the only acceptable location for a signing key. The private key never leaves Key Vault — the app calls the Key Vault Crypto API (`sign` operation). No alternative considered. |
| **Azure API Management** | Standard v2 | Single enforcement point for all routes. Validates JWTs inline (`validate-jwt` policy), rate-limits per session (`rate-limit-by-key`), applies Azure AI Content Safety, emits token metrics, streams every request/response to Event Hub for audit. | APIM Standard v2 supports auto-scale (0–N units), VNet integration, and the full policy library. Standard v1 is deprecated. Consumption tier lacks VNet integration needed for private link to Key Vault JWKS. Developer tier is single-instance (no HA). |
| **Azure AI Content Safety** | Standard | Inline content moderation policy in APIM — applied to all agent inputs and outputs. Blocks prompt injection, harmful content, PII leakage before it reaches the LLM or the prospect. | Azure AI Content Safety integrates natively with APIM via a built-in policy element. No custom middleware needed. Alternatively Azure OpenAI has built-in content filtering, but APIM-layer filtering stops bad inputs before they consume tokens. |
| **Azure Container Apps** | Consumption + Dedicated profile | Hosts the single Next.js application (Option A). Scale-to-zero when no active sessions. HTTP concurrency scale-out during demo events. Managed Identity assigned for Key Vault and ACR access. | ACA is the right fit for a bursty, event-driven workload that is idle most of the time. App Service does not scale to zero on the standard tier. AKS is over-engineered for a single Next.js app with no microservice complexity. ACA Consumption profile bills per request-second — near-zero cost when idle. |
| **Azure Container Registry** | Standard tier (shared) | Stores the signed container image `showroom-app:<version>`. Notation signing enforced — APIM + ACA only pull signed images. Shared with L2 Marketplace registry. | Shared ACR avoids per-product registry overhead. Standard tier supports geo-replication (add `northeurope` replica for failover). Image signing (Notation/ORAS) prevents supply-chain attacks. |
| **Azure Cosmos DB** | Serverless | Session store: one database `showroom`, one container `sessions`. Partition key `/presenterId`. No provisioned throughput — Cosmos Serverless bills per RU consumed. Ideal for bursty, low-average load. | Cosmos Serverless is the correct SKU when average load is near zero (idle most of the time) but peaks sharply during demo events. Provisioned throughput wastes ~€40/month minimum. The session document is small (<1 KB) and the access pattern is simple (point read by sessionId, update status). Redis would add operational complexity for no benefit over the 5-min JWT TTL approach. |
| **Application Insights** | Workspace-based | RUM from the Next.js app (presenter + prospect), custom events (`ShowroomSessionCreated`, `ShowroomSessionEnded`), all tagged with `sessionId` as a custom dimension for per-session drill-down. | Workspace-based App Insights sends all telemetry to Log Analytics — one query surface for everything. Classic (non-workspace) App Insights is deprecated. |
| **Log Analytics Workspace** | Pay-as-you-go | Central sink for App Insights telemetry, APIM diagnostic logs, ACA container logs. Shared with the broader L4 Substrate workspace. | Shared workspace reduces cost (single daily cap, single data export configuration). All Showroom-specific data can be filtered by `cloud_RoleName = showroom-app`. |
| **Azure Event Hub** | Basic namespace, 1 partition | Receives every APIM request/response log via `log-to-eventhub` policy. Acts as the intake buffer for the immutable audit stream. | Event Hub decouples APIM from the audit storage layer. If ADLS is temporarily unavailable, Event Hub buffers up to 24h. Kafka-compatible — audit pipeline can be replaced without changing APIM policy. |
| **ADLS Gen2** | LRS (locally redundant) | Immutable audit log. Event Hub capture writes Avro files. 2-year retention enforced via lifecycle management policy. EU data residency (`westeurope`). | ADLS Gen2 immutable storage (WORM policy) satisfies audit and compliance requirements. Cheaper than Cosmos DB or SQL for append-only audit data at scale. |
| **Azure Workbook** | Included with Log Analytics | Embedded in the Presenter Admin panel analytics tab. Shows: sessions per week, average session duration, most-viewed demo, drop-off rate. | Azure Workbooks are free with Log Analytics and can be embedded via iframe with a bearer token. No separate BI tool (Power BI, Grafana) needed for an internal usage dashboard of this complexity. |

\bigskip

---

\newpage

## 4. Networking model

### 4.1 Request path — inbound (public)

```
User browser
  --> Azure DNS (CNAME to Front Door endpoint)
  --> Azure Front Door PoP (global anycast)
  --> Front Door WAF Policy (OWASP + bot + rate limit)
  --> APIM (Standard v2, public IP with custom domain)
      validate-jwt (inline, no hop to Key Vault at runtime)
      rate-limit-by-key
      content-safety
  --> ACA showroom-app (internal ingress via Front Door private link)
      Next.js Route Handler
  --> Cosmos DB (Private Endpoint on ACA subnet)
  --> Key Vault (Private Endpoint on ACA subnet — sign/read operations)
```

### 4.2 Private connectivity (internal)

| Resource | Connectivity | Detail |
|---|---|---|
| ACA environment | Internal VNet integration | ACA environment injected into a dedicated subnet `snet-showroom-aca` in `vnet-showroom-westeurope`. No public IP on the ACA container. All inbound traffic via Front Door private link to APIM, then APIM to ACA. |
| Cosmos DB | Private Endpoint | `pe-cosmos-showroom` on `snet-showroom-pe`. No public network access on the Cosmos account. ACA accesses Cosmos via Private DNS zone `privatelink.documents.azure.com`. |
| Key Vault | Private Endpoint | `pe-kv-showroom` on `snet-showroom-pe`. No public network access on the Key Vault. APIM accesses Key Vault JWKS via a separate private link (APIM managed VNet). |
| ACR | Private Endpoint | `pe-acr-showroom` on `snet-showroom-pe`. ACA pulls images via private link. Public pull disabled on the registry. |

### 4.3 VNet layout

```
vnet-showroom-westeurope  (10.100.0.0/16)
  snet-showroom-aca     10.100.0.0/23   ACA environment subnet
  snet-showroom-pe      10.100.2.0/24   Private Endpoints (Cosmos, KV, ACR)
  snet-showroom-apim    10.100.3.0/24   APIM internal VNet subnet
```

---

## 5. Identity and secrets

### 5.1 Managed Identity assignments

| Resource | Identity type | RBAC assignments |
|---|---|---|
| ACA `showroom-app` | System-assigned | Key Vault Crypto User (sign + verify), Key Vault Secrets User (read app config), Cosmos DB Built-in Data Contributor (sessions container), ACR Pull (registry) |
| APIM | System-assigned | Key Vault Secrets User (read RS256 public key for JWKS), Event Hub Data Sender |

### 5.2 What lives in Key Vault

| Secret / key | Type | Rotation |
|---|---|---|
| `showroom-jwt-signing-key` | RSA 2048 key (Key Vault managed key, never exported) | Rotate every 90 days via Key Vault key rotation policy. APIM caches JWKS for 1h — overlap period ensures no validation failure during rotation. |
| `showroom-apim-gateway-cert` | Certificate | Auto-renewed by Key Vault via DigiCert or Let's Encrypt integration. |

### 5.3 No stored credentials anywhere

- ACA pulls from ACR via Managed Identity — no `docker login` credentials.
- ACA reads Key Vault via Managed Identity — no connection strings in environment variables.
- APIM reads Key Vault via Managed Identity — no API keys in APIM named values.
- Cosmos DB access from ACA uses Entra RBAC (Built-in Data Contributor) — no primary/secondary keys.

---

\newpage

## 6. Scaling and cost profile

### 6.1 Traffic pattern

The Showroom workload is **highly bursty**:

- Idle most of the time (nights, weekends, between demo events)
- Short sharp peaks: a demo event with 20 prospects generates ~20 concurrent sessions, each making ~1 agent request per minute = ~20 RPM at peak
- Realistic peak: 5 demo events in parallel, 20 prospects each = ~100 concurrent sessions = ~100 RPM

### 6.2 Scaling configuration

| Component | Scale rule | Min | Max |
|---|---|---|---|
| ACA `showroom-app` | HTTP concurrency target: 10 requests/replica | 0 (scale-to-zero) | 10 replicas |
| APIM Standard v2 | Auto-scale: CPU > 70% | 1 unit | 4 units |
| Cosmos DB | Serverless — no scale config needed | — | — |
| Event Hub | Basic, 1 partition | — | — |

Scale-to-zero on ACA means the app has **zero compute cost** when no demo events are running. Cold start from zero is ~8–12 seconds for the Next.js container — acceptable because the QR code URL opens in the prospect's browser only after the presenter has already generated the session (the app is likely already warm by then from the presenter's admin session).

### 6.3 Cost estimate

| Resource | Idle (no events) | Active (1 demo event/day, 1h) | Heavy week (5 events/day) |
|---|---|---|---|
| ACA (Consumption) | ~€0 | ~€15/month | ~€60/month |
| Cosmos DB Serverless | ~€1/month | ~€5/month | ~€20/month |
| APIM Standard v2 | ~€220/month | ~€220/month | ~€220/month |
| Front Door Standard | ~€35/month | ~€38/month | ~€45/month |
| Key Vault | ~€1/month | ~€2/month | ~€5/month |
| App Insights + Log Analytics | ~€5/month | ~€15/month | ~€50/month |
| Event Hub + ADLS | ~€5/month | ~€8/month | ~€20/month |
| ACR (shared) | shared cost | shared cost | shared cost |
| **Total (Showroom-specific)** | **~€267/month** | **~€303/month** | **~€420/month** |

> APIM Standard v2 dominates cost and is shared across all L4 Substrate consumers (Showroom, Marketplace, Knowledge Base). The Showroom-specific share of APIM is proportional to request volume — typically <10% of total APIM traffic.

---

## 7. Deployment topology

### 7.1 Resource group and region

| Resource group | Primary region | Secondary (failover) |
|---|---|---|
| `rg-pwc-showroom-westeurope` | West Europe (Amsterdam) | North Europe (Dublin) via Front Door multi-origin |

All Showroom-specific resources live in `rg-pwc-showroom-westeurope`. Shared L4 Substrate resources (APIM, Key Vault, Log Analytics, Event Hub, ADLS) live in `rg-pwc-substrate-westeurope` and are referenced by resource ID.

### 7.2 Front Door origins and routing

| Origin group | Origin | Priority | Route |
|---|---|---|---|
| `og-showroom` | ACA `showroom-app` West Europe | 1 | `showroom.pwc.example/*` and `admin.showroom.pwc.example/*` |
| `og-showroom` | ACA `showroom-app` North Europe (standby) | 2 | Same routes — failover only |

### 7.3 IaC and CI/CD

| Concern | Tooling |
|---|---|
| Infrastructure as Code | Bicep modules in `iac/showroom/` in the platform repo |
| Module registry | Azure Verified Modules (AVM) for ACA, Cosmos, Key Vault, Front Door |
| Container build | GitHub Actions: `docker build` → `notation sign` → `docker push` to ACR |
| Deployment | `azd up` (Azure Developer CLI) — provisions infra + deploys container in one command |
| Environment promotion | `dev` → `staging` → `prod` via GitHub Actions environments with manual approval gate on `prod` |
| Secret rotation | Key Vault key rotation policy (90-day) + Azure Policy `Key Vault keys should have a rotation policy` |

---

## 8. Compliance posture

| Requirement | How it is met |
|---|---|
| **No client data stored** | Only session metadata is stored (sessionId, presenterId OID, demoIds[], expiresAt, status). No prospect name, no prospect email, no demo content. Demo content is generated at runtime by the LLM and never persisted. |
| **EU data residency** | All resources in `westeurope` (primary) and `northeurope` (failover). No data leaves the EU. ADLS Gen2 LRS stores audit logs in `westeurope`. |
| **Audit log immutability** | Event Hub capture → ADLS Gen2 with WORM (time-based retention policy, 2 years). APIM logs every request/response including headers, JWT claims (except `sub` which is a UUID), and response codes. |
| **No stored credentials** | Managed Identity everywhere. Zero connection strings, zero API keys in environment variables or APIM named values. |
| **TLS everywhere** | Front Door enforces HTTPS-only redirect. ACA internal ingress is TLS. Private Endpoints encrypt traffic on the Microsoft backbone. |
| **WAF protection** | Front Door WAF with OWASP CRS 3.2 + bot manager in `Prevention` mode. Custom rules: block requests from non-EU IPs if required by client policy. |
| **Content safety** | Azure AI Content Safety applied at the APIM layer — all agent inputs and outputs moderated before the LLM sees them and before the prospect sees the response. |
