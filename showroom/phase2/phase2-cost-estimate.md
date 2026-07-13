---
title: "PwC Showroom Phase 2 — Azure Cost Estimate"
---

## Scope and exclusions

This estimate covers **Azure resources operated by the Showroom component only**.
The following are explicitly excluded:

- External demo apps (Overwatch, UBO, KBOT, etc.) — billed to their own product
  budgets; the Showroom does not host or run them.
- PwC Entra ID — existing tenant, zero marginal cost to Phase 2.
- Google and Microsoft consumer OAuth — both providers offer their OAuth service
  free of charge to application developers.
- Azure Container Registry — shared platform resource; cost amortised across all
  hosted products (not attributable to Showroom alone).
- Engineering time, DNS registrar fees, and Azure DevOps pipeline minutes.

Prices are EUR list price, Azure West Europe region, July 2026. USD list prices
converted at Azure's published monthly reference rate. Enterprise Agreement or
committed-use discounts are not applied; list price is the ceiling, not the
expected invoice.

## Fixed vs. variable cost per resource

Every Azure service used by the Showroom falls into one of two categories:

- **Fixed:** charged unconditionally every month the resource exists, regardless
  of traffic or usage.
- **Variable:** charged only when the resource is actively used; scales down to
  near-zero at idle.

| Azure resource | Fixed cost (EUR/month) | Variable cost |
|---|---|---|
| Azure Front Door Standard profile | ~32 (base fee, billed hourly) | Outbound egress to clients: ~0.08 EUR/GB (Europe, first 10 TB); per-million requests to Front Door edge |
| Front Door WAF Policy (OWASP CRS 3.2) | ~18 (policy base fee) | Per-million evaluated requests: ~0.50 EUR/million |
| Azure Container Apps -- Consumption (showroom-app) | **0** (serverless, no minimum fee) | Per active-vCPU-second + per active-GiB-second + per request, consumed beyond monthly free grants: 180 k vCPU-s, 360 k GiB-s, 2 M requests per subscription |
| Azure Cosmos DB Serverless | **0** (no provisioned throughput) | Per Request Unit consumed: ~0.26 EUR per million RU; per GB stored: ~0.25 EUR/GB/month |
| Azure Key Vault Standard | **0** | Per 10 k secret operations: ~0.03 EUR (negligible at Showroom volume) |
| App Insights + Log Analytics (workspace-based) | **0** (first 5 GB/month ingested free) | Per GB ingested beyond free tier: ~2.30 EUR/GB; retention beyond 31 days priced separately |
| Azure Functions Consumption (keep-warm ping) | **0** (1 M executions/month free) | Per execution beyond free tier: ~0.17 EUR per million (well within free tier: ~9 k executions/month at 5-minute intervals) |
| Azure DNS zone | ~0.45 (per hosted zone) | Per million queries: ~0.40 EUR/million |
| **Fixed floor total** | **~51 EUR/month** | |

The ~51 EUR/month fixed floor is what PwC pays **regardless of whether any
prospect logs in**. All remaining costs are proportional to actual usage.

## What drives the variable cost

The three variable meters that actually move in practice at Showroom volume:

**1. ACA compute (vCPU-seconds and GiB-seconds)**
The showroom-app container is configured with 0.5 vCPU and 1 GiB per replica.
During idle periods it scales to zero -- no charge. A 1-hour demo event with
20 concurrent prospects sustains roughly 2 replicas active, consuming
approximately 3,600 vCPU-seconds and 7,200 GiB-seconds. Monthly free grants
(180 k vCPU-s, 360 k GiB-s) absorb roughly 50 events before any charge applies.

**2. App Insights ingested GB**
Custom events (`ProspectLoggedIn`, `DemoOpened`, `UsageReported`) and RUM
telemetry are the primary ingest source. At default sampling the Showroom
generates roughly 0.1-0.5 GB/month depending on event frequency. Configuring
25% adaptive sampling keeps ingestion below the 5 GB free tier at low-to-medium
volume. This is the most unpredictable lever at burst events.

**3. Front Door egress**
Each page load transfers approximately 500 KB (HTML, JS bundle, thumbnails).
500 sessions x 500 KB = ~0.25 GB/month -- well under 1 EUR at the ~0.08 EUR/GB
rate. Egress becomes relevant only if demo thumbnail images are large or if the
catalog page is loaded many times per session.

## Illustrative monthly total ranges

The following ranges combine the fixed floor with estimated variable consumption.
They are illustrative, not contractual. Actual spend should be validated against
the Azure Cost Management dashboard after the first month of live traffic.

| Scenario | Demo events / month | Prospects / event | Estimated EUR/month |
|---|---|---|---|
| Idle (no live events; keep-warm ping only) | 0 | 0 | ~51 (fixed floor only) |
| Active (~1 event per workday) | 22 | 20 | ~70-90 |
| Heavy (5 events per workday) | 110 | 20 | ~140-200 |

The idle scenario is entirely dominated by the Front Door Standard + WAF fixed
fees (~50 EUR). See `frontdoor-waf-justification.pdf` for the security rationale
behind those fixed costs.

The heavy scenario is dominated by App Insights ingestion if sampling is not
configured, and by ACA compute once monthly free grants are exhausted
(approximately after 50 events per month per subscription).

## What does NOT increase the bill

- Number of registered prospects in Cosmos DB (user records are a few hundred
  bytes each; 10,000 registered users costs less than 0.01 EUR in storage).
- Number of demo tiles in the catalog (configuration data, not compute).
- Number of OAuth providers configured in NextAuth (code-only change).
- Idle time between events (ACA scales to zero; Cosmos bills nothing at rest).

## Pricing sources consulted

Prices verified July 2026 from the following Azure public pricing pages:

- <https://azure.microsoft.com/en-us/pricing/details/container-apps/>
- <https://azure.microsoft.com/en-us/pricing/details/cosmos-db/serverless/>
- <https://azure.microsoft.com/en-us/pricing/details/frontdoor/>
- <https://azure.microsoft.com/en-us/pricing/details/web-application-firewall/>
- <https://azure.microsoft.com/en-us/pricing/details/key-vault/>
- <https://azure.microsoft.com/en-us/pricing/details/monitor/>
- <https://azure.microsoft.com/en-us/pricing/details/functions/>
- <https://azure.microsoft.com/en-us/pricing/details/dns/>
