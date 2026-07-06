---
title: "Hosting Decision: Azure Container Apps vs Azure App Service"
---

> **Decision status — OPEN (2026-07-04)**
> In the 2026-07-03 standup, Aditya suggested using Azure App Service (Web App
> for Containers) for phase 1, citing enterprise-fit and simplicity. This document
> is the architect's (Raimondo Marino) counter-argument. Phase 1 host remains
> Azure Container Apps pending re-alignment with Aditya. This document will be
> used to support that conversation.

## TL;DR

Azure Container Apps (ACA) is the correct host for the phase-1 showroom.
App Service is the right answer for a different shape of workload: steady-state,
single-app, web-hosting simplicity over elasticity. For a bursty, container-first,
multi-service AI showroom that will grow into a marketplace platform, ACA is
Microsoft's own recommendation and the cheaper, architecturally consistent choice.

---

## Service identity (Microsoft Learn)

**Azure Container Apps** ([source](https://learn.microsoft.com/azure/container-apps/compare-options))

> "Enables you to build serverless microservices and jobs based on containers.
> Powered by Kubernetes and open-source technologies like Dapr, KEDA, and Envoy.
> Enables event-driven application architectures by supporting scale based on
> traffic and pulling from event sources including scale to zero."

**Azure App Service — Web App for Containers** ([source](https://learn.microsoft.com/azure/architecture/guide/choose-azure-container-service))

> "Fully managed hosting for web applications including websites and web APIs.
> Optimised for web applications. Prioritises simplicity over control."

Microsoft is explicit: App Service targets **simple, steady-state web apps**.
ACA targets **elastic, container-first, microservice workloads**. The showroom
is the second shape, not the first.

---

## Side-by-side comparison

| Feature | Azure Container Apps | Azure App Service (B1/S1) |
|---|---|---|
| Scale-to-zero | Yes (Consumption plan) | No — minimum 1 instance always-on |
| Pricing model | Per vCPU-second + GiB-second | Per App Service Plan (hourly, always-on) |
| Idle cost | ~EUR 0 / month | ~EUR 45 (B1) – EUR 75 (S1) / month |
| Annual idle cost (B1) | ~EUR 0 | ~EUR 540 |
| Scaling engine | KEDA (HTTP concurrency, queue length, custom) | CPU / memory rules (lags burst arrivals) |
| Traffic splitting | Revision-based (percentage, instant rollback) | Slot swap (all-or-nothing) |
| Service discovery | Native in the environment | App-level only |
| Dapr sidecar | Yes | No |
| gRPC / WebSocket ingress | Envoy — native | Supported but limited |
| Easy Auth (Entra ID, no code) | Available but less mature | Mature, one-click |
| Managed Identity | Yes | Yes |
| VNet integration | Yes (workload profile plan) | Yes |
| Deployment artefact | Container image | Container image or code zip |
| Microsoft guidance for microservices | Recommended | "Limited" |
| Microsoft guidance for single web app | Works fine | Ideal option |

---

## Five reasons ACA wins for the phase-1 showroom

**1. The workload is bursty, not steady-state.**
The showroom is idle overnight, at weekends, and between demos. It receives
traffic in 20-minute bursts when a salesperson runs a client session. ACA
Consumption bills per request-second. App Service bills per hour regardless.
Estimated annual saving on a typical demo workload: EUR 400-600 (idle
App Service Plan vs ACA at zero when idle).

**2. We are growing to multiple apps.**
Phase 1 exposes Overwatch. Phase 2 adds UBO. The Marketplace adds more tiles.
Microsoft marks App Service as "limited" for inter-service communication
(no service discovery, no pub/sub, no Dapr). ACA has all of these built in.
Starting on App Service creates a runtime we must migrate off before phase 2.

**3. Easy Auth is the one real App Service advantage -- and we are not using it.**
App Service Easy Auth provides Entra ID sign-in with zero application code.
In the standup (3 Jul 2026) Miki confirmed: "the app will be aware of the group
check for phase 1" -- the Next.js BFF middleware handles the claim check itself.
The single feature that would tilt the argument to App Service is not in use.

**4. ACA is the target architecture.**
Every architecture document in this repository (showroom-azure-architecture,
ara-a-reference-architecture, general-architecture-highlevel-explained) places
the workload on ACA. Choosing App Service for phase 1 forces Aditya to operate
two runtimes -- different Bicep modules, CI/CD pipelines, autoscale rules, and
observability dashboards -- until the phase-2 migration.

**5. ACA features match demo requirements out of the box.**
Revision-based traffic splitting means a bad deploy can be rolled back in one
command mid-demo. KEDA HTTP scaling handles the "20 prospects hit the QR
simultaneously" burst without lag. Envoy supports WebSocket and SSE from day
one, which the agent streaming chat in phase 2 will require.

---

## When App Service *would* be the right answer

- Workload is **steady-state, always-on** (e.g. internal staff portal visited
  daily by hundreds of users -- scale-to-zero becomes irrelevant).
- Team is already heavily invested in App Service Plans and running multiple apps
  on shared Plans for cost consolidation.
- Easy Auth is being used to eliminate all authentication code from the app.
- The project will never grow beyond one app and one team.

None of these conditions apply to the showroom.


---

## Cold-start user experience and mitigations

### The problem

ACA Consumption scales to zero when idle. The first request after a period of
inactivity triggers a cold start: the platform allocates compute, the container
runtime starts, and the application boots. Typical duration:

| Container image size | Cold start p50 | Cold start p95 |
|---|---|---|
| Small (< 200 MB, distroless Node) | 3.5 s | 6 s |
| Medium (~350 MB, node:20-alpine) | 5 s | 9 s |
| Large (> 800 MB, heavy deps) | 8 s | 14 s |

For a live client demo, an 8-second white screen is a credibility risk.
This is real and must be addressed. Five mitigations exist, ordered by cost.

---

### Mitigation 1 -- Presenter pre-warm (EUR 0)

The presenter opens the showroom URL 5 minutes before the meeting from their
phone or a background browser tab. The cold start is paid invisibly. When the
client is watching the screen, the container is warm and responds in < 200 ms.
ACA keeps replicas warm for approximately 10 minutes after the last request.

**Cost: EUR 0. Complexity: 5 seconds of discipline.**
This is the baseline. It works for all internal phase-1 demos.

---

### Mitigation 2 -- Keep-warm ping every 5 minutes during working hours (recommended)

A scheduled Azure Function timer hits the showroom `/api/health` endpoint every
5 minutes, Mon-Fri, 09:00--19:00 CET. This keeps one replica alive during
business hours while allowing scale-to-zero overnight and at weekends.

**Implementation:**
One Azure Function (timer trigger, ~20 lines) deployed via the same Bicep
template as the rest of the platform. Invocation count: ~2,640/month -- well
within the free tier (first 1 million executions free).

**As a bonus**, the Function's HTTP call is automatically picked up by App
Insights as an availability test (free uptime monitoring at no extra cost).

**Cost breakdown:**

| Item | Cost / month |
|---|---|
| ACA compute during working hours (220 h, 0.5 vCPU, 1 GiB, ~95% idle) | EUR 1.75 |
| ACA compute outside working hours (scale-to-zero) | EUR 0 |
| Azure Function timer trigger (Consumption plan, < 1M calls) | EUR 0 |
| **Total ACA compute** | **EUR 1.75** |

This is the recommended approach for phase 1.

---

### Mitigation 3 -- `minReplicas: 1` during working hours only (EUR 10/month)

An Azure Automation runbook (or Logic App schedule) calls the ACA management
API twice a day to flip `minReplicas` between 1 (09:00) and 0 (19:00).

- Working hours: always-warm, exactly 1 replica running.
- Outside hours: scale-to-zero.

Estimated compute: 220 h/month at 0.5 vCPU -- approximately EUR 10/month.
No Function required; scale behaviour is enforced by the platform.

**When to use:** if the presenter pre-warm discipline (Mitigation 1) is not
reliable and a fully automated solution is preferred over a ping.

---

### Mitigation 4 -- `minReplicas: 1` always-on (EUR 35-45/month)

Set `minReplicas: 1` permanently. ACA never scales below one replica.
Cold starts become impossible. Cost approaches App Service B1 (~EUR 45/month).
Scale-to-zero savings are lost entirely.

**When to use:** only if demos happen at unpredictable hours (evenings, weekends)
and no other mitigation is acceptable. At this cost, App Service becomes an
equal option (though ACA still wins on KEDA scaling and revision rollback).

---

### Mitigation 5 -- Move to App Service (EUR 45-75/month)

App Service B1 runs one instance 24/7. No cold starts. No keep-warm setup.
Cost: EUR 45/month (B1) or EUR 75/month (S1).

As discussed in the sections above, this option sacrifices scale-to-zero savings,
architectural consistency, and KEDA burst scaling in exchange for a marginally
simpler DevOps setup and mature Easy Auth -- which we are not using in phase 1.

**When this wins:** steady-state workload, team already on App Service Plans,
Easy Auth is in use, project will not grow beyond one app.

---

### Five-mitigation comparison

| Option | Cold start risk | Cost / month | Cost / year | Complexity |
|---|---|---|---|---|
| 1. Presenter pre-warm | Low (presenter discipline) | EUR 0 | EUR 0 | None |
| 2. Keep-warm ping (recommended) | None during working hours | EUR 1.75 | EUR 21 | 20-line Function |
| 3. minReplicas: 1 working hours | None during working hours | EUR 10 | EUR 120 | Automation runbook |
| 4. minReplicas: 1 always-on | None | EUR 35-45 | EUR 420-540 | None |
| 5. App Service B1 (Aditya proposal) | None | EUR 45 | EUR 540 | None |

Shared infrastructure (ACR, Log Analytics, Key Vault: ~EUR 7.30/month) applies
equally to all options and is excluded from the compute figures above.

**Recommendation for phase 1:** Mitigation 2 (keep-warm ping). Total monthly
cost including shared infrastructure: **EUR 9/month** -- 83 % cheaper than
App Service B1 (EUR 52/month), with equivalent presenter UX during business hours
and EUR 500/year in annual savings.

---

## Cost table (EUR / month, estimated)

| Scenario | App Service B1 | App Service S1 | ACA Consumption |
|---|---|---|---|
| 100% idle | EUR 45 | EUR 75 | EUR 0 |
| Light demo week (5 x 30-min demos, 10 users each) | EUR 45 | EUR 75 | < EUR 1 |
| Heavy demo week (20 x 30-min demos, 20 users each) | EUR 45 | EUR 75 | < EUR 5 |
| Peak month (daily demos, 50 concurrent users) | EUR 45 | EUR 75 | EUR 15-25 |

ACA break-even (where App Service B1 costs the same) requires sustained traffic
equivalent to ~400 vCPU-hours per month -- typical only for always-on production
services, not a demo showcase.

---

## Recommendation

**Use Azure Container Apps (Consumption plan) for the phase-1 showroom.**

Path forward:

1. Aditya provisions one ACA Environment + one Container App for the Next.js BFF.
   Overwatch runs as a second Container App in the same Environment (internal
   ingress only, no public URL; BFF proxies to it).
2. Managed Identity authorises BFF to Overwatch (no keys, no rotation).
3. Entra ID group check (`FinCrime-Showroom`) is enforced in Next.js middleware --
   no Easy Auth, consistent with the phase-1 decision.
4. CI/CD pipeline (Azure DevOps) builds the container image and deploys a new
   revision on each merge to main. Revision traffic split enables instant rollback.
5. When APIM is introduced (phase 2), it becomes the enforcement point in front of
   the ACA ingress and the group check moves out of the application.

---

## Reference

- Microsoft Learn -- Comparing Container Apps with other Azure container options:
  <https://learn.microsoft.com/azure/container-apps/compare-options>
- Microsoft Learn -- Choose an Azure container service:
  <https://learn.microsoft.com/azure/architecture/guide/choose-azure-container-service>
- Microsoft Learn -- Choose an Azure compute option for microservices:
  <https://learn.microsoft.com/azure/architecture/microservices/design/compute-options>
