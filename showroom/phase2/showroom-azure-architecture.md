---
title: "PwC Showroom Phase 2 — Azure Architecture"
---

# PwC Showroom Phase 2 — Azure Architecture

**Decision basis:** 2026-07-09 kickoff meeting (see `meetings/2026-07-09-summary.md`).
**Previous QR-code design superseded** — QR access dropped; Google + Microsoft OAuth adopted.
**APIM not used** — Phase 2 uses a NextAuth-only authentication stack.

## 1. Scope

This document describes the Azure service topology for the **external-facing PwC AI Showroom
(Phase 2)**. Phase 2 extends Phase 1 (internal PwC employees only) by adding:

- External prospect access via **Google OAuth and Microsoft consumer OAuth** (no account creation).
- A **user tracking and usage-quota layer** backed by Cosmos DB Serverless.
- A **Presenter Admin panel** for managing the prospect allow-list, demo assignments, and quotas.
- **Azure Front Door + WAF** as the public ingress edge (replacing the Phase 1 direct ACA FQDN).

For the identity and session flow see `showroom-external-auth-flow.md`.
For the overall platform picture see `general_architecture/general-architecture-highlevel-explained.md`.

## 2. Architecture diagram

![PwC Showroom Phase 2 — Azure services diagram](showroom-azure-architecture.png)

## 3. Azure service selection and rationale

| Azure service | SKU / tier | Role in Phase 2 | Why this, not alternatives |
|---|---|---|---|
| **Azure Front Door** | Standard | Global anycast edge, TLS termination, custom domain, WAF attachment, multi-origin failover | Only Azure service combining global CDN, WAF, and custom-domain TLS in one resource. Application Gateway is regional. |
| **Front Door WAF Policy** | DRS 2.1 + Bot manager | OWASP CRS 3.2, bot manager, edge rate-limiting before traffic reaches ACA | WAF at the PoP stops bad traffic before it consumes compute or Cosmos RUs. |
| **Azure DNS** | Standard zone | CNAME records for `showroom.pwc.example` and `admin.showroom.pwc.example` | Already part of PwC tenant DNS; no additional service. |
| **PwC Entra ID** | Existing tenant | PKCE token for the Presenter Admin panel (`/admin/*` routes). Salesperson logs in with PwC credentials. | Entra ID is the PwC identity provider. MSAL React handles PKCE client-side. |
| **Google OAuth 2.0** | Google Cloud Console app | External prospect authentication — consumer Google accounts | Zero account-creation friction. Prospects already have a Google account. NextAuth provider. |
| **Microsoft OAuth (consumer)** | Microsoft identity platform | External prospect authentication — Microsoft consumer accounts | Same zero-friction model. Works for prospects who prefer Microsoft accounts. NextAuth provider. |
| **Azure Key Vault** | Standard tier | Stores `AUTH_SECRET` (NextAuth encryption key), Google and Microsoft OAuth client secrets. Accessed via Managed Identity only. | Key Vault is the only acceptable location for secrets. No stored connection strings. |
| **Azure Container Apps** | Consumption plan | Hosts the single Next.js application. Scale-to-zero when idle. HTTP-concurrency scale-out during demo events. | ACA Consumption bills per request-second -- near-zero cost when idle. Scale-to-zero is not available on App Service Standard. AKS is over-engineered for one Next.js app. |
| **Azure Container Registry** | Standard (shared) | Signed container image `showroom-app:<version>`. Notation signing enforced. Managed Identity pull. | Shared ACR avoids per-product registry overhead. Standard tier supports geo-replication. |
| **Azure Cosmos DB** | Serverless | User tracking and session analytics. Database `showroom`, three containers (see section 5). No provisioned throughput. | Cosmos Serverless is correct for bursty low-average load. Provisioned throughput wastes ~40 EUR/month minimum at idle. Postgres can be revisited if reporting queries later require SQL joins. |
| **Azure Function** | Consumption | Keep-warm ping to the ACA app every 5 minutes during office hours. Prevents cold-start latency that could look like an outage to clients. | Cost: approximately 2 EUR/month. The ACA scale-to-zero cold-start from zero is 8-12 seconds -- unacceptable as a first impression during a live demo. |
| **Application Insights** | Workspace-based | RUM from the Next.js app (presenter + prospect), custom events (`ProspectLoggedIn`, `DemoOpened`, `UsageReported`), all tagged with `userId` as a custom dimension. | Workspace-based App Insights sends all telemetry to Log Analytics -- one query surface. |
| **Log Analytics Workspace** | Pay-as-you-go | Sink for App Insights telemetry and ACA container logs. Shared with the broader platform workspace. | Shared workspace reduces cost. Showroom data filtered by `cloud_RoleName = showroom-app`. |

| **Azure Monitor Workbook** | Standard (free) | Business reporting surface for presenters: prospect table, sign-in time chart, demo popularity chart. Data sourced from Cosmos DB directly, not App Insights. Built by the Full-Stack Developer; RBAC provisioned by DevOps. | App Insights is not the reporting surface for business data — it holds hashed email for operational telemetry only. Cosmos DB holds plain email and is queried directly for reports. |

**Not used in Phase 2:** Azure API Management, Azure AI Content Safety, Azure Event Hub,
ADLS Gen2 immutable audit log.

## 4. Networking model

### 4.1 Request path (inbound)

```
User browser
  --> Azure DNS  (CNAME to Front Door endpoint)
  --> Azure Front Door PoP  (global anycast)
  --> Front Door WAF Policy  (OWASP CRS 3.2 + bot + rate limit)
  --> ACA showroom-app
      (public FQDN, FDID header + IP allowlist)
      Next.js Route Handler
  --> Cosmos DB  (public endpoint, Entra RBAC via Managed Identity)
  --> Key Vault  (public endpoint, Managed Identity access only)
```

### 4.2 Origin protection

The ACA app has a public FQDN but is protected by two controls:

| Control | Layer | Detail |
|---|---|---|
| ACA ingress IP allowlist | Azure network | Ingress accepts source IPs only from `AzureFrontDoor.Backend` service tag. All other sources are dropped. |
| FDID header check | Application | BFF middleware rejects any request whose `X-Azure-FDID` header does not match the `FRONT_DOOR_ID` env variable (provisioned Front Door instance GUID). |

No VNet, no Private Endpoints, no private DNS zones are required in Phase 2.

## 5. Cosmos DB schema — tracking layer

### Phase 1 vs. Phase 2 — what moved to Cosmos and what stayed in git

In Phase 1 a single file `demo-map.json` baked into the container image held two
concerns: (1) the **demo catalog** (id, title, thumbnail, launchUrl, description)
and (2) the **AuthZ mapping** (which Entra `oid` may see which tiles).

In Phase 2 these two concerns are separated:

| Concern | Phase 1 | Phase 2 |
|---|---|---|
| Demo catalog metadata (id, title, thumbnail, launchUrl) | `demo-map.json` — AuthZ block + catalog in one file | `demo-map.json` — catalog block only (AuthZ block removed) |
| Coarse AuthZ (is this user allowed in?) | Entra security-group membership (Layer 1) | Cosmos `users` document existence + `status = active` |
| Fine-grained AuthZ (which tiles may this user see?) | `demo-map.json` AuthZ block keyed by Entra `oid` | Cosmos `users.allowedDemoIds` — edited at runtime by presenters |
| Per-user quota | Not applicable (internal staff) | Cosmos `users.messageQuotaRemaining` |

**Why the catalog stays in git, not in Cosmos.** Adding a demo tile is never
only a metadata change: it requires DevOps to add the demo's Managed Identity to
ACR, provision a callback shared secret in Key Vault, add a synthetic-monitoring
row, and confirm the demo team has implemented JWT verification. All of these
travel together in one PR. A Cosmos-backed tile form would create the illusion of
self-service on-boarding while the engineering steps still require a deploy; it
would also lose version history, code review, and environment-parity guarantees
that git provides at zero cost. Cosmos is correct for per-user runtime state that
changes many times per day; git is correct for per-release configuration that
changes once every one to three months when a new demo joins.

Database: `showroom`

### Container: `users`

Partition key: `/email`

One document per external identity. Created on first successful OAuth login.

```json
{
  "id": "<email>",
  "email": "prospect@example.com",
  "provider": "google",
  "providerSub": "<optional: provider subject claim>",
  "displayName": "<optional: display name from profile scope>",
  "firstSeenAt": "2026-07-09T10:00:00Z",
  "lastSeenAt": "2026-07-09T14:30:00Z",
  "totalConnections": 3,
  "allowedDemoIds": ["overwatch", "ubo"],
  "messageQuotaTotal": 100,
  "messageQuotaRemaining": 67,
  "status": "active"
}
```

`email` is the only required field. `providerSub` and `displayName` are
optional metadata captured by NextAuth when the provider returns them (which
it does by default with `openid email profile` scopes); they are never read for
authorization decisions.

`status` values: `active` (default), `banned` (blocked by presenter), `pending` (invited but not yet logged in).

### Container: `connection_events`

Partition key: `/email`

Append-only. One document per login event.

```json
{
  "id": "<uuid>",
  "email": "prospect@example.com",
  "connectionAt": "2026-07-09T14:30:00Z",
  "ip": "1.2.3.4",
  "userAgent": "Mozilla/5.0 ..."
}
```

### Container: `demo_visits`

Partition key: `/email`

Append-only. One document per demo-tile click (open event). Closed and message count filled
in by the demo app callback (see section 7).

```json
{
  "id": "<uuid>",
  "email": "prospect@example.com",
  "demoId": "overwatch",
  "openedAt": "2026-07-09T14:31:00Z",
  "closedAt": "2026-07-09T14:58:00Z",
  "messageCount": 12
}
```

## 6. Identity and secrets

### 6.1 Managed Identity assignments

| Resource | Identity type | RBAC assignments |
|---|---|---|
| ACA `showroom-app` | System-assigned | Key Vault Secrets User (read `AUTH_SECRET`, OAuth client secrets), Cosmos DB Built-in Data Contributor (all three containers), ACR Pull |
| Azure Function (keep-warm) | System-assigned | None required (outbound HTTPS to ACA public domain only) |

### 6.2 What lives in Key Vault

| Secret | Purpose | Rotation |
|---|---|---|
| `showroom-auth-secret` | NextAuth `AUTH_SECRET` — used to encrypt session cookies | Rotate every 90 days. All active sessions invalidated on rotation (users re-login). |
| `showroom-google-client-secret` | Google OAuth client secret | Rotate per Google Cloud Console policy. |
| `showroom-microsoft-client-secret` | Microsoft OAuth client secret | Rotate every 24 months (Azure AD app registration). |

### 6.3 No stored credentials anywhere

- ACA pulls from ACR via Managed Identity.
- ACA reads Key Vault via Managed Identity.
- Cosmos DB access from ACA uses Entra RBAC (Built-in Data Contributor) -- no primary keys.
- The Azure Function requires no secrets.

## 7. Demo app usage callback

Each demo app must report message counts back to the showroom so the quota layer can enforce limits.

**Endpoint:** `POST` <https://showroom.pwc.example/api/internal/demo-usage>

**Authentication:** Shared secret header `X-Demo-Callback-Secret` (value stored in Key Vault,
injected into demo app environment at deploy time).

**Request body:**

```json
{
  "email": "prospect@example.com",
  "demoId": "overwatch",
  "visitId": "<uuid from demo_visits>",
  "messageCount": 12,
  "closedAt": "2026-07-09T14:58:00Z"
}
```

The BFF handler:

1. Validates the shared secret.
2. Updates `demo_visits` document: sets `messageCount` and `closedAt`.
3. Decrements `users.messageQuotaRemaining` by `messageCount`.
4. If `messageQuotaRemaining <= 0` sets `users.status = quota_exhausted`.

## 8. Scaling and cost profile

### 8.1 Traffic pattern

The showroom is highly bursty: idle most of the time, short sharp peaks during demo events.
Peak estimate: 5 events in parallel, 20 prospects each = 100 concurrent sessions, ~100 RPM.

### 8.2 Scaling configuration

| Component | Scale rule | Min | Max |
|---|---|---|---|
| ACA `showroom-app` | HTTP concurrency target: 10 requests/replica | 0 (scale-to-zero) | 10 replicas |
| Cosmos DB | Serverless -- no scale config needed | -- | -- |
| Azure Function (keep-warm) | Timer trigger, 1 instance | -- | 1 |

### 8.3 Cost estimate (Phase 2, APIM excluded)

| Resource | Idle (no events) | Active (1 demo event/day, 1h) | Heavy week (5 events/day) |
|---|---|---|---|
| ACA (Consumption) | ~0 EUR | ~15 EUR/month | ~60 EUR/month |
| Cosmos DB Serverless | ~1 EUR/month | ~5 EUR/month | ~20 EUR/month |
| Front Door Standard | ~35 EUR/month | ~38 EUR/month | ~45 EUR/month |
| Key Vault | ~1 EUR/month | ~2 EUR/month | ~5 EUR/month |
| App Insights + Log Analytics | ~5 EUR/month | ~15 EUR/month | ~50 EUR/month |
| Azure Function (keep-warm) | ~2 EUR/month | ~2 EUR/month | ~2 EUR/month |
| ACR (shared) | shared cost | shared cost | shared cost |
| **Total (Phase 2)** | **~44 EUR/month** | **~77 EUR/month** | **~182 EUR/month** |

Compared to the original Phase 2 design with APIM Standard v2 (~267 EUR/month idle),
this saves approximately 220 EUR/month at idle.

## 9. Deployment topology

### 9.1 Resource groups and regions

| Resource group | Primary region | Failover |
|---|---|---|
| `rg-pwc-showroom-westeurope` | West Europe (Amsterdam) | North Europe (Dublin) via Front Door multi-origin |

### 9.2 Front Door routing

| Route | Origin | Auth enforced by |
|---|---|---|
| `showroom.pwc.example/*` | ACA `showroom-app` | NextAuth middleware (Google or Microsoft OAuth session cookie) |
| `admin.showroom.pwc.example/*` | ACA `showroom-app` | NextAuth middleware (PwC Entra ID MSAL session) |

### 9.3 IaC and CI/CD

| Concern | Tooling |
|---|---|
| Infrastructure as Code | Bicep modules in `iac/showroom/` |
| Module registry | Azure Verified Modules (AVM) for ACA, Cosmos, Key Vault, Front Door |
| Container build | Azure DevOps pipeline: `docker build` -> `notation sign` -> push to ACR |
| Deployment | `azd up` provisions infra and deploys container in one command |
| Environment promotion | `develop` branch -> dev environment; `main` branch -> prod (manual approval gate) |
| Secret rotation | Key Vault rotation policy + Azure Policy enforcement |

## 10. Application structure

One Next.js codebase, two audiences separated by route prefix and NextAuth provider config.

```
app/
  admin/              Presenter Admin  (requires Entra ID session)
    page.tsx            prospect allow-list management
    new/page.tsx        add / edit prospect (email, demoIds, quota)
    analytics/          usage dashboard (App Insights queries)
  demo/[demoId]/      Prospect UI
                      (requires OAuth session, demo in allowedDemoIds)
    page.tsx
  api/
    auth/[...nextauth]/ NextAuth handler (all providers)
    demos/              GET -- authorized demo list for session
    internal/
      demo-usage/       POST -- callback from demo apps
```

### 10.1 NextAuth provider configuration (sketch)

```typescript
// auth.ts
import NextAuth from "next-auth";
import MicrosoftEntraID from "next-auth/providers/microsoft-entra-id";
import Google from "next-auth/providers/google";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    // Presenter Admin: PwC Entra ID tenant
    MicrosoftEntraID({
      clientId: process.env.ENTRA_CLIENT_ID!,
      clientSecret: process.env.ENTRA_CLIENT_SECRET!,
      issuer: `https://login.microsoftonline.com/` +
        `${process.env.ENTRA_TENANT_ID}/v2.0`,
    }),
    // External prospects: consumer Microsoft accounts
    MicrosoftEntraID({
      id: "microsoft-consumer",
      clientId: process.env.MS_CONSUMER_CLIENT_ID!,
      clientSecret: process.env.MS_CONSUMER_CLIENT_SECRET!,
      issuer: "https://login.microsoftonline.com/consumers/v2.0",
    }),
    // External prospects: Google accounts
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      // PwC employees always allowed
      if (account?.provider === "microsoft-entra-id") return true;
      // For external providers: look up email in Cosmos users container
      const prospect = await getUserByEmail(user.email!);
      return prospect?.status === "active";
    },
    async session({ session, token }) {
      // Attach allowedDemoIds to the session for BFF use
      if (token.provider !== "microsoft-entra-id") {
        const prospect = await getUserByEmail(session.user.email!);
        session.user.allowedDemoIds = prospect?.allowedDemoIds ?? [];
        session.user.messageQuotaRemaining =
          prospect?.messageQuotaRemaining ?? 0;
      }
      return session;
    },
  },
});
```

### 10.2 Tracking middleware (sketch)

```typescript
// middleware.ts -- runs on every request via Next.js Edge Middleware
export async function middleware(req: NextRequest) {
  const session = await auth();
  if (!session) return NextResponse.redirect("/api/auth/signin");

  // On first hit per session: update lastSeenAt,
  // increment totalConnections, write connection_events
  // (fire-and-forget, non-blocking)
  if (!req.cookies.get("sr_tracked")) {
    void trackConnection(session.user.email!);
    const res = NextResponse.next();
    res.cookies.set("sr_tracked", "1",
      { httpOnly: true, maxAge: 86400 });
    return res;
  }
  return NextResponse.next();
}
```

