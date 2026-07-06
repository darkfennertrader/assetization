---
title: "PwC Showroom — 1-hour QR-code Demo Access Flow"
subtitle: "Auth & Authorisation design · Self-signed JWT (D3) · No Redis (D8) · Frontend guidance"
author: "Raimondo Marino — Solution AI Architect"
date: "2026-07-02"
---

# PwC Showroom — 1-hour QR-code Demo Access Flow

## 1. Business scenario

A PwC salesperson is presenting AI capabilities to a prospective client at their office or at a PwC event. They open the **Showroom Admin panel** on their laptop, select the demos they want to show (e.g. "Claims Triage Agent", "Investor Relations Agent"), and click **"Generate Demo Access"**. A QR code appears on their screen. Prospects scan the QR code with their phone cameras — their browser opens instantly and they are in the demo environment in under 2 seconds. No login, no account creation, no email verification. After 60 minutes the session expires automatically; the salesperson can also invalidate it immediately if needed.

This document describes how this is built on top of the **Identity & Edge + AI Gateway layers** of the general architecture (see `general_architecture/general-architecture-highlevel-explained.md`).

---

## 2. Flow diagram

![QR-code demo access flow — three swimlanes: Presenter / Shared Substrate / Prospect](showroom-qr-flow.png)

\bigskip

---

\newpage

## 3. Token model — no Redis

**Design decisions applied:**

- **D3 (applied) Self-signed JWT (RS256)** — access tokens are signed with a private key stored in Azure Key Vault. No Entra External ID account creation ceremony. Prospects get zero-friction access.
- **D8 (applied) No Redis blacklist** — instead of a Redis revocation cache, the system uses a **short access-token TTL (5 minutes) + a session horizon in Cosmos DB (1 hour) + a silent refresh loop**.

### Token anatomy

```
Header: { "alg": "RS256", "kid": "showroom-session-key" }
Payload: {
  "sub":       "<uuid — session ID>",
  "aud":       "https://showroom.pwc.example",
  "iss":       "https://bff.showroom.pwc.example",
  "iat":       <unix timestamp>,
  "exp":       <iat + 300>,          // 5-minute access token TTL
  "scope":     "demo:claims-triage demo:ir-agent",
  "presenter": "<Entra OID of the salesperson>",
  "session":   "<same uuid as sub>"
}
```

### Session lifecycle (no Redis)

| Phase | Mechanism |
|---|---|
| **Session created** | BFF writes `{ sessionId, demoIds[], expiresAt: now+3600, status: "active" }` to Cosmos DB. Mints first 5-min access JWT. |
| **Access token alive** | APIM `validate-jwt` validates signature + `exp` + `aud` inline — no database round-trip. |
| **Silent refresh (every ~4 min)** | Frontend calls `GET /api/session/refresh`. BFF validates current 5-min JWT, reads Cosmos record, checks `status == "active"` AND `now < expiresAt`. If both true: mints a new 5-min JWT. |
| **Natural expiry** | After 1 hour `expiresAt` is in the past. Next refresh call returns 401. Current 5-min JWT expires on its own within 5 minutes at most. |
| **Immediate revocation** | Presenter clicks "Invalidate" → BFF sets Cosmos `status = "revoked"`. Next refresh call returns 401. Current access token dies within ≤lt;= 5 minutes (its own TTL). |

> **Why no Redis?** Redis adds operational complexity (provisioning, failover, cache-aside pattern in APIM policies). The 5-minute access-token TTL means the worst-case window between revocation and enforcement is ≤lt;= 5 minutes — acceptable for a sales demo scenario. If a stricter revocation SLA is required in future (e.g. < 30 seconds), add Redis then.

---

## 4. Step-by-step walkthrough

### 4.1 Presenter side

1. Salesperson opens `https://admin.showroom.pwc.example` — authenticates with their PwC Entra ID via MSAL React (PKCE flow). No separate credentials.
2. In the **"Generate Demo Access"** form: selects demo IDs and a duration (15 / 30 / 60 minutes, default 60).
3. Clicks **"Generate"**. The Showroom BFF receives `POST /sessions { demoIds[], duration }`:
   a. Fetches the RS256 private key from **Key Vault** (via Managed Identity — no stored credentials anywhere).
   b. Mints a **5-minute RS256 JWT** with `scope = demoIds`, `sub = sessionId`.
   c. Writes a session record to **Cosmos DB**: `{ sessionId, demoIds[], expiresAt: now+duration, presenterId, status: "active" }`.
   d. Emits a **`ShowroomSessionCreated`** event to App Insights: `{ sessionId, presenterId, demoIds, expiresAt }`.
   e. Returns a QR code image encoding `https://showroom.pwc.example/enter?token=<JWT>`.
4. The QR code is displayed on the presenter's screen. Prospects scan it.

### 4.2 Prospect side

5. Phone camera opens `https://showroom.pwc.example/enter?token=<JWT>`.
6. The request reaches **Azure Front Door → WAF** → routes to **APIM**.
7. APIM's `validate-jwt` policy fires inline:
   - Verifies RS256 signature against the public key fetched from Key Vault JWKS endpoint.
   - Checks `exp` (must be future), `aud` (must be `showroom.pwc.example`).
   - On failure → `401 Unauthorized`. On success → forwards to the BFF `/enter` handler.
8. BFF `/enter`:
   - Sets an **httpOnly session cookie** containing the JWT.
   - Redirects to `/demo/<firstDemoId>`.
9. Prospect's browser renders the **Showroom UI** — mobile-first Next.js app. The navigation menu shows only the demos listed in the JWT `scope` claim. The header displays a countdown timer showing time remaining.
10. Every subsequent API call (agent chat, tool invocations): Phone → Front Door → APIM → LangGraph → MCP tools → LLM. APIM re-validates the JWT on every call (stateless, inline).

### 4.3 Silent refresh loop

11. A **TanStack Query hook** fires every ~4 minutes: `GET /api/session/refresh` (carries the session cookie).
12. APIM `/session/refresh` route validates the incoming JWT and forwards to BFF.
13. BFF:
    - Re-validates the JWT signature and `exp`.
    - Reads the Cosmos session record: is `status == "active"`? Is `now < expiresAt`?
    - **YES** → mints a new 5-min JWT → returns it as a new httpOnly cookie. The prospect never sees this — the UI keeps working seamlessly.
    - **NO** (expired or revoked) → returns `401`. The frontend React hook catches this and renders the **"Session ended"** screen.

### 4.4 Session end

14a. **Natural expiry** — `expiresAt` passes. Next refresh call returns 401. The prospect sees the "Session ended" screen.
14b. **Immediate revocation** — Presenter clicks "Invalidate" in the Admin panel → BFF `POST /sessions/{id}/revoke` → sets Cosmos `status = "revoked"`. Next refresh call (within ≤lt;= 4 minutes) returns 401.
15. BFF emits **`ShowroomSessionEnded`**: `{ sessionId, reason: "expired" | "revoked", durationSeconds }`.

---

## 5. Security properties

| Property | Enforced by | Detail |
|---|---|---|
| No account creation for the prospect | Self-signed JWT (D3) | Zero Entra lifecycle for a 1-hour demo |
| Scoped access — only presenter-selected demos | JWT `scope` claim, validated on every APIM call | Inline `validate-jwt` policy; no round-trip |
| Hard time limit | JWT `exp` (5-min) + Cosmos `expiresAt` (1h) | APIM enforces `exp` on every call; BFF enforces `expiresAt` on every refresh |
| Revocation within ≤lt;= 5 minutes | Cosmos `status=revoked` + 5-min JWT TTL | No Redis required |
| Full audit trail | App Insights `ShowroomSessionCreated/Ended` + APIM request log | Every request tagged with `sessionId` as correlation key |
| No credential stored anywhere | Key Vault (Managed Identity) + PKCE for admin | RS256 private key never leaves Key Vault |
| Rate limiting per session | APIM `rate-limit-by-key(sub)` | One runaway prospect cannot exhaust LLM budget |
| Content safety | APIM `azure-content-safety` policy | Applied to all agent inputs and outputs |

---

\newpage

## 6. APIM policy skeleton (simplified — no Redis)

```xml
<policies>
  <inbound>
    <!-- 1. Validate the session JWT inline (no external IdP round-trip) -->
    <validate-jwt header-name="Authorization"
                  failed-validation-httpcode="401"
                  failed-validation-error-message="Invalid or expired session token">
      <issuer-signing-keys>
        <!-- Public key fetched from Key Vault JWKS endpoint at policy load time -->
        <key certificate-id="showroom-session-key" />
      </issuer-signing-keys>
      <required-claims>
        <claim name="aud" match="any">
          <value>https://showroom.pwc.example</value>
        </claim>
      </required-claims>
    </validate-jwt>

    <!-- 2. Check scope claim covers the requested demo -->
    <set-variable name="allowedScope"
                  value="@(context.Request.Claims.GetValueOrDefault("scope",""))" />
    <!-- (per-route scope validation — check requested demo is in allowedScope) -->

    <!-- 3. Rate-limit per session — prevent runaway token spend -->
    <rate-limit-by-key calls="60" renewal-period="60"
                        counter-key="@(context.Request.Claims.GetValueOrDefault("sub","anon"))" />

    <!-- 4. Content safety on all agent inputs -->
    <azure-content-safety ... />

    <!-- 5. Tag cost metrics with sessionId for chargeback reporting -->
    <emit-token-metric
      namespace="ShowroomSessions"
      subscription-message-count="1">
      <dimension name="sessionId"
                  value="@(context.Request.Claims.GetValueOrDefault("sub",""))" />
    </emit-token-metric>
  </inbound>
</policies>
```

---

## 7. Frontend development guidance

### 7.1 Stack

| Concern | Choice | Rationale |
|---|---|---|
| Framework | **Next.js 14 (App Router)** | SSR + streaming; first-class Azure Container Apps support; MSAL React integration; `httpOnly` cookie handling in Route Handlers |
| UI library | **Fluent UI React v9** | Microsoft-native design language; matches PwC / client enterprise branding; free / MIT |
| Utility CSS | **Tailwind CSS v3** | Rapid layout; mobile-first utilities |
| Server state | **TanStack Query v5** | Handles the silent refresh loop, retry on network loss, stale-while-revalidate |
| Admin auth SDK | **@azure/msal-react** | Entra ID PKCE flow for the Presenter Admin panel |
| QR generation (BFF) | **qrcode** npm package | Server-side PNG generation; no client-side JS required |
| Observability | **@microsoft/applicationinsights-react-js** | RUM: page views, clicks, feature usage, tagged with `sessionId` |

### 7.2 Application structure — one codebase, two apps by route

```
app/
+-- admin/          -> Presenter Admin (requires Entra ID MSAL auth)
|   +-- page.tsx       (session list)
|   +-- new/page.tsx   (session generator form)
|   +-- analytics/     (App Insights workbook embed)
+-- demo/[demoId]/  -> Prospect UI (requires session cookie)
|   +-- page.tsx
+-- enter/          -> Cookie setter + redirect (public route)
|   +-- route.ts
+-- api/
    +-- sessions/
    |   +-- route.ts          POST /api/sessions (create)
    |   +-- [id]/revoke/route.ts
    +-- session/refresh/
        +-- route.ts          GET /api/session/refresh
```

Single Next.js app deployed as one container image to Azure Container Apps. Two Azure Front Door routes:
- `admin.showroom.pwc.example` → same ACA app, APIM enforces Entra ID token
- `showroom.pwc.example` → same ACA app, APIM enforces self-signed session JWT

### 7.3 Prospect UI — key requirements

| Requirement | Implementation |
|---|---|
| **Mobile-first** | Tailwind `sm:` breakpoints as primary target; minimum touch target 44px |
| **Zero-friction landing** | `/enter` route handler validates JWT, sets `httpOnly` cookie, redirects to `/demo/<firstDemoId>` — no login page |
| **Countdown timer** | Decode JWT `exp` client-side (public info, not sensitive); show `HH:MM:SS` remaining in the header using a `useEffect` interval |
| **Scope-filtered navigation** | Decode JWT `scope` claim on the server (in the Route Handler); pass allowed demo IDs as props; nav menu only shows allowed items |
| **Silent refresh** | TanStack Query hook: `useQuery({ queryKey: ['session'], queryFn: fetchRefresh, refetchInterval: 240_000 })`. On 401 → set `sessionEnded = true` → render "Session ended" screen |
| **Session ended screen** | Full-screen friendly message: "Your demo session has ended. Ask your PwC host to generate a new QR code." |
| **App Insights RUM** | `ApplicationInsights` initialised in the root layout with `sessionId` as a custom dimension |
| **Offline handling** | TanStack Query `retry: 3` + `staleTime: 60_000`; "Reconnecting…" banner via `useNetworkStatus` |

### 7.4 Presenter Admin panel — key features

| Feature | Implementation |
|---|---|
| **Login** | `@azure/msal-react` `MsalProvider` + `useMsal` hook; PKCE flow; no separate credentials |
| **Session generator form** | Multi-select checkbox list of available demos (fetched from Asset Registry API); duration radio: 15 / 30 / 60 min; optional prospect name field (stored in Cosmos for audit, never in JWT) |
| **QR code display** | After `POST /api/sessions` returns, display the QR code PNG inline + a copyable short URL + expiry countdown |
| **Live session list** | Table: sessionId · prospect name · demos · expires · status (active/revoked/expired). Auto-refreshes every 30s via TanStack Query. |
| **Invalidate button** | `POST /api/sessions/{id}/revoke` → optimistic UI update (row turns red) |
| **Analytics tab** | iFrame embed of an App Insights Workbook showing: sessions per week, avg duration, most-viewed demo, drop-off rate |

### 7.5 BFF session endpoints (TypeScript sketch)

```typescript
// app/api/sessions/route.ts — create session
export async function POST(req: Request) {
  // 1. Verify caller has valid Entra ID token (from Authorization header)
  const presenter = await verifyEntraToken(req);

  const { demoIds, durationMinutes } = await req.json();
  const sessionId = crypto.randomUUID();
  const expiresAt = new Date(Date.now() + durationMinutes * 60_000);

  // 2. Mint 5-min access JWT (RS256, private key from Key Vault via Managed Identity)
  const accessToken = await mintSessionJWT({
    sub: sessionId,
    scope: demoIds.join(" "),
    presenter: presenter.oid,
    expiresInSeconds: 300, // 5 minutes
  });

  // 3. Write session to Cosmos DB
  await cosmosClient.items.upsert({
    id: sessionId,
    demoIds,
    expiresAt: expiresAt.toISOString(),
    presenterId: presenter.oid,
    status: "active",
  });

  // 4. Emit audit event
  appInsights.trackEvent({
    name: "ShowroomSessionCreated",
    properties: { sessionId, presenterId: presenter.oid, demoIds, expiresAt },
  });

  // 5. Generate QR code PNG (base64)
  const qrDataUrl = await QRCode.toDataURL(
    `https://showroom.pwc.example/enter?token=${accessToken}`
  );

  return Response.json({ sessionId, qrDataUrl, expiresAt });
}
```

```typescript
// app/api/session/refresh/route.ts — silent refresh
export async function GET(req: Request) {
  // 1. Validate incoming 5-min JWT (already done by APIM; BFF re-validates for defence-in-depth)
  const claims = await verifySessionJWT(req);

  // 2. Check Cosmos session record
  const session = await cosmosClient.items.read(claims.sub);
  if (session.status !== "active" || new Date() >= new Date(session.expiresAt)) {
    return new Response("Session expired or revoked", { status: 401 });
  }

  // 3. Mint new 5-min JWT with same claims
  const newToken = await mintSessionJWT({
    sub: claims.sub,
    scope: claims.scope,
    presenter: claims.presenter,
    expiresInSeconds: 300,
  });

  // 4. Return as httpOnly cookie
  const response = new Response(null, { status: 204 });
  response.headers.set("Set-Cookie",
    `session=${newToken}; HttpOnly; Secure; SameSite=Strict; Path=/`);
  return response;
}
```

### 7.6 Deployment

```
Container image:  pwcaimktplace.azurecr.io/showroom-app:<version>
Runtime:          Azure Container Apps (scale-to-zero when no active sessions)
Config:           Environment variables from Key Vault (Managed Identity)
CI/CD:            GitHub Actions → build → sign → push to ACR → deploy to ACA
Front Door:
  admin.showroom.pwc.example  → ACA  (APIM: Entra ID validate-jwt)
  showroom.pwc.example        → ACA  (APIM: self-signed JWT validate-jwt)
```

---

## 8. Decision alignment

| Decision ID | Decision | Status in this document |
|---|---|---|
| D1 | Entra ID for internal users (presenter admin panel) | **Applied** — MSAL React PKCE in Presenter Admin |
| D2 | Entra External ID for external guests | **Not used here** — replaced by self-signed JWT for 1-hour scenario (D3) |
| D3 | Self-signed JWT (RS256) for 1-hour demo tokens | **Applied** — Key Vault RS256 key, 5-min TTL |
| D4 | OpenFGA for fine-grained authz | **Deferred** — JWT `scope` claim + APIM scope check is sufficient for demos; OpenFGA needed when catalogue RBAC becomes complex |
| D6 | No Auth0 / Okta | **Applied** — pure Azure stack (Key Vault + APIM + Cosmos) |
| D7 | No custom ping-pong liveness endpoint | **Applied** — TanStack Query `refetchInterval` handles refresh; RUM is separate telemetry |
| D8 | No Redis — short TTL + Cosmos status | **Applied** — 5-min access JWT + Cosmos session record |
| D9 | APIM is the single enforcement point | **Applied** — no BFF accepts unauthenticated calls; APIM validates every request |

Source: `docs/auth-design-note.md` decision log.

