---
title: "When and Why to Introduce APIM — Value Proposition for PwC Managers"
---

## The question this document answers

> "We already built SSO into the Showroom. Why would we rip that out and put
> it into APIM? Every app would still need to handle login. Where is the
> saving?"

This is the right question. The short answer is: **APIM does not replace
login. It replaces the six cross-cutting policy concerns that every backend
would otherwise re-implement independently.**

## What APIM does and does not do

### What APIM does NOT do

APIM cannot perform the OAuth 2.0 Authorization Code redirect dance. It cannot
set session cookies or redirect a browser to Google, Microsoft, or Entra ID
for login. The login flow (OIDC handshake, callback, session establishment)
must always live in a BFF (Backend-for-Frontend) or a dedicated auth service
that speaks HTTP redirects. That code does not move into APIM.

If you have one application and one BFF, APIM is overhead. This is true even
if the application is complex.

### What APIM does do

APIM validates the token that the login flow already produced and then enforces
a uniform set of cross-cutting policies on every inbound request **before it
reaches any backend**. The six concerns it centralises are:

| # | Concern | Without APIM | With APIM |
|---|---|---|---|
| 1 | JWT signature and claims validation | One middleware per backend | One APIM policy, applied once |
| 2 | Rate limiting per session / per tenant | One middleware per backend + shared Redis counter store | One APIM policy, built-in counters |
| 3 | Azure Content Safety filter on prompt and completion | One middleware per backend + separate Content Safety wiring per backend | One APIM policy, one Content Safety instance |
| 4 | Cost-centre / engagement tagging for chargeback | One middleware per backend + agreed tag schema repeated N times | One APIM policy, one tag schema |
| 5 | Immutable audit log to Event Hub | One middleware per backend + Event Hub credentials in every backend | One APIM policy, one Event Hub |
| 6 | Uniform 401 / 403 / 429 error response shape | Six different implementations that will drift | One APIM error template |

The saving is not "less login code". The saving is "six cross-cutting concerns
built and maintained once, not N times".

## When does APIM pay for itself?

The decision threshold is a cost inequality, not a fixed number:

```
N x (per-backend cost of concerns 1-6)
    > APIM SKU cost + APIM ops overhead + policy authoring time
```

This inequality flips when you have three or more backend services that all
genuinely need most of concerns 2-6. Below that threshold — or if you only
need concern 1 (JWT validation) and nothing else — a shared validation library
or a JWKS-validating sidecar is cheaper than APIM.

### Applied to the PwC AI Platform roadmap

| Phase | Backends | Cross-cutting concerns active | APIM justified? |
|---|---|---|---|
| Showroom Phase 2 (today) | 1 BFF, no MCP tools at scale | JWT validation only; audit via App Insights; no rate-limit needed | No — Front Door + WAF + inline BFF auth is right |
| Showroom + Marketplace + 3 shared MCP tools | ~5 backends, 2 caller types | JWT (2 issuers), rate-limit per tenant, content safety, cost tagging, audit | Yes — duplicating the 6 concerns across 5 backends costs more than APIM Basic |
| Full three-tier vision with 10+ assettized tools | 10+ backends, 3+ caller types | All 6 concerns plus per-client quota and content-safety policy versioning | Yes, strongly — this is the workload APIM was designed for |

## The login code still exists — but it shrinks

When APIM is introduced:

- **Each BFF still owns login** (the OIDC redirect, callback, and session).
  Nothing changes there.
- **Each BFF stops owning token validation, rate-limiting, content-safety
  calls, cost tagging, and audit logging.** Those move to APIM once.
- **Each backend MCP tool / agent / service stops owning all six concerns.**
  It receives a pre-validated, pre-audited request from APIM and does its job.

Net effect per new backend: instead of implementing six policies, the backend
developer implements zero policies and writes a single APIM subscription key
or Managed Identity trust rule.

## The message for PwC managers

When presenting the three-tier architecture:

> "Short term, each application ships with its own login glue — fastest path to
> first value, lowest overhead. Medium to long term, we introduce a shared
> control plane not to centralise login, but to centralise the six enforcement
> concerns — rate limiting, content safety, cost tagging, audit, and error
> normalisation — that every backend would otherwise re-implement. The moment
> we have three or more backends that all need those policies applied
> consistently, the shared control plane pays for itself in reduced development
> and maintenance cost. Below that threshold it is overhead and we do not
> introduce it."

This framing is defensible because it:

- Admits the real cost of APIM up front (SKU cost, ops overhead, policy
  authoring).
- Ties the introduction to a measurable trigger (number of backends multiplied
  by number of cross-cutting concerns needed), not to a round number or a
  management preference.
- Does not oversell "shared SSO" as the justification, because shared SSO is
  not the justification.
- Aligns with the short-term / medium-long-term roadmap already presented to
  stakeholders.
