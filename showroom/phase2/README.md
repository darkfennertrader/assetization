# Showroom Phase 2 — External Prospects, OAuth, and Usage Tracking

**Decision basis:** 2026-07-09 kickoff meeting — see `meetings/2026-07-09-summary.md`.

Phase 2 extends Phase 1 (internal PwC employees only) to support **external prospects**
authenticated via Google or Microsoft consumer OAuth, with a per-user usage-tracking and
quota layer backed by Cosmos DB Serverless.

## Key design decisions (from 2026-07-09 meeting)

| Decision | Detail |
|---|---|
| QR code | **Dropped.** No development value vs OAuth login friction. |
| External auth | Google OAuth + Microsoft consumer OAuth via NextAuth (no account creation). |
| APIM | **Not used in Phase 2.** Phase 2 uses NextAuth-only stack (~220 EUR/month saving). |
| Tracking | Cosmos DB Serverless: `users`, `connection_events`, `demo_visits` containers. |
| Access control | Presenter-managed email allow-list + per-user `allowedDemoIds` array. |
| Session | NextAuth httpOnly encrypted cookie. Idle 1h, absolute 8h. No Redis. |
| Demo launch | Top-level browser redirect to demo's own ACA FQDN. No iframe. |

## Documents

| File | Description |
|---|---|
| `showroom-azure-architecture.md` / `.pdf` | Azure service topology: Front Door, WAF, ACA, Cosmos DB, Key Vault, ACR, App Insights. Service rationale, networking model, Cosmos schema, cost estimate (~44 EUR/month idle), IaC. |
| `showroom-azure-architecture.dot` / `.png` | Graphviz source and rendered diagram — three-tier layout: users, edge+identity, ACA app, Cosmos tracking layer, observability. |
| `showroom-external-auth-flow.md` / `.pdf` | Auth and tracking flow: Presenter Admin (Entra ID) + Prospect (Google/MS OAuth), 13-step walkthrough, Cosmos writes, usage callback contract, session model, security properties. |
| `showroom-external-auth-flow.dot` / `.png` | Graphviz source — three swimlanes: Presenter / BFF+Tracking / Prospect. |

## Build

```bash
bash showroom/phase2/build_all.sh
```

Renders both PNGs and builds both PDFs.

## Phase scope

| Concern | Phase 1 | Phase 2 (this folder) |
|---|---|---|
| Users | Internal PwC (Entra ID) | + External prospects (Google / MS OAuth) |
| Auth enforcement | NextAuth (PwC Entra ID) | NextAuth (3 providers) |
| Demo access control | `demo-map.json` keyed on OID | Cosmos `users.allowedDemoIds[]` |
| Usage tracking | None | Cosmos `connection_events` + `demo_visits` |
| Rate limiting | None | BFF middleware (quota counter in Cosmos) |
| Content Safety | None | None |
| Audit log | ACA container logs | App Insights custom events |
| Cost (idle) | ~5 EUR/month | ~44 EUR/month |
