---
title: "Authentication & Authorisation Design Note"
subtitle: "Showroom · Marketplace · Knowledge Base — v1.0 · July 2026"
author: "Raimondo Marino, Solution AI Architect"
date: "2026-07-01"
---

# Authentication & Authorisation Design Note

> **Scope:** Covers all three PwC products — Marketplace (internal), Showroom (external), Knowledge Base (deferred).
>
> **Status:** Draft for review at Friday 2026-07-04 meeting. Decisions marked ⚠️ require explicit sign-off from Adrian / the team.
>
> **Primary implementer:** Michael (TypeScript auth layer). Architecture decisions: Raimondo.

---

## 1. Guiding principles

1. **Never reinvent the wheel.** Use standard SDKs (MSAL, Entra, OpenFGA client libs) rather than custom token logic.
2. **Separation of concerns.** Authentication (who are you?) and authorisation (what can you do?) are distinct layers with distinct tooling.
3. **Every request is audited.** Every token issuance, every API call, every token expiry is written to the immutable audit log (App Insights → Event Hub → ADLS Gen2). This is not optional.
4. **Short-lived credentials for external access.** No credential issued to an external guest lasts longer than the session it was created for. Default max: 1 hour. Programmable.
5. **No vendor lock-in on authz.** The fine-grained authorisation layer (OpenFGA) is self-hosted and replaceable. The interface boundary is a clean JSON relation-check API.
6. **APIM is the enforcement point.** Every API call — internal or external — passes through APIM. No backend service accepts unauthenticated calls directly.

---

## 2. The two user populations

| Population | Size | Products | Auth mechanism |
|---|---|---|---|
| **Internal users** | ~400 PwC entities worldwide | Marketplace | Entra ID (corporate SSO) |
| **External guests** | Prospects, client contacts, showroom visitors | Showroom | Entra External ID |
| **Service-to-service** | Agent runtimes, CI/CD pipelines, APIM → OpenAI | All | Managed Identity (no stored keys) |

---

## 3. Authentication stack

### 3.1 Internal users — Entra ID (corporate)

**How it works:**
- Employees sign in via their existing PwC Entra ID account (federated across all ~400 entities via Entra ID cross-tenant federation or B2B guest invite at the shared tenant level).
- Single Sign-On — no additional account creation required.
- All Marketplace API calls carry an Entra ID Bearer token; APIM validates via the `validate-jwt` policy with the PwC Entra tenant's JWKS endpoint.
- Service-to-service (e.g., LangGraph agent → APIM → Azure OpenAI): **Managed Identity** throughout. No API keys stored anywhere.

**Implementation (TypeScript / Michael):**
```typescript
// MSAL Node for backend-to-backend (confidential client)
import { ConfidentialClientApplication } from "@azure/msal-node";

const cca = new ConfidentialClientApplication({
  auth: {
    clientId: process.env.AZURE_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.AZURE_TENANT_ID}`,
    clientCertificate: { /* managed cert from Key Vault */ }
  }
});

// For user-facing flows: use @azure/msal-browser with PKCE
```

**Do not use:** client secrets stored in environment variables. Use **Key Vault references** or **Managed Identity** only.

### 3.2 External guests — Entra External ID

**What it is:** Entra External ID is Microsoft's identity service for customer-facing scenarios. It creates an isolated external tenant (separate from the internal PwC tenant) where guests are registered, authenticated, and managed.

**Why not Auth0 / Okta / similar SaaS:**
- Auth0 pricing: free tier ends at 7,500 MAU; paid plans scale sharply. Multiple projects have hit unexpected cost cliffs at 50k+ MAU.
- Entra External ID is part of the existing Microsoft enterprise agreement — no additional licensing surprise.
- Native integration with APIM `validate-jwt`, Conditional Access, and Audit Logs.

**Tenant design decision ⚠️ (needs Adrian sign-off):**

| Option | Description | When to use |
|---|---|---|
| **Option A (recommended):** Single external tenant | One `showroom.pwc.com` external tenant; all showroom guests are registered here | Standard: PwC is demoing to external prospects in a PwC-controlled environment |
| **Option B:** Per-client guest in client's Entra tenant | Guest users in the *client's own* Entra ID tenant | When the client is an enterprise with their own Entra and wants to control their own user lifecycle |
| **Option C:** Hybrid | External tenant for cold prospects; client Entra guest for active engagements | Most flexible; more operational complexity |

**Recommended: Option A** for the Showroom. Switch to Option B/C when a specific client engagement requires it (the WRAPPER pattern in the repo skeleton handles this switch without changing the application code).

---

## 4. The 1-hour QR-code demo credential flow

This is the most novel requirement. The full sequence:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PRESENTER SIDE (internal user, Entra ID)                                  │
│                                                                             │
│  1. Presenter opens Showroom Admin panel (authenticated via Entra ID)      │
│  2. Clicks "Generate Demo Access"                                          │
│     → selects: which demo(s) to show, duration (default 60 min)           │
│  3. Backend creates:                                                        │
│     a. An Entra External ID one-time guest invitation link                 │
│        OR a short-lived signed JWT (see §4.1)                              │
│     b. A session record in Cosmos DB:                                      │
│        { sessionId, demoIds[], expiresAt, presenterId, status: "active" }  │
│     c. An audit entry in App Insights (session created, by whom, for what) │
│  4. Backend generates a QR code encoding:                                  │
│        https://showroom.pwc.example/enter?token=<signed-session-token>     │
│  5. QR code displayed on screen / printed                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │  (guest scans QR with phone)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  GUEST SIDE (external user, phone browser)                                 │
│                                                                             │
│  6. Browser opens /enter?token=<signed-session-token>                      │
│  7. BFF validates token signature + expiry                                 │
│  8. If valid: Entra External ID initiates a lightweight SSO session        │
│     (no account creation required for 1-hour guest access)                 │
│  9. Guest receives a session cookie / short-lived access token             │
│     scoped ONLY to the demoIds[] specified in step 2                       │
│ 10. APIM validates the session token on every API call:                    │
│     · Token still active?                                                  │
│     · Is the requested asset in the allowed demoIds[]?                     │
│     · Is the expiresAt timestamp in the future?                            │
│     → If any check fails: 401 / 403                                        │
│ 11. All requests logged: App Insights (session ID, endpoint, timestamp)    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │  (token expires or presenter invalidates)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SESSION END                                                                │
│                                                                             │
│ 12a. Token TTL expires → SDK auto-rejects all subsequent calls (no action  │
│      needed — the expiry is encoded in the JWT, APIM enforces it)          │
│ 12b. Presenter clicks "Invalidate" → backend sets status: "revoked"        │
│      in Cosmos DB → APIM policy checks Cosmos on each call (or uses a     │
│      short TTL + blacklist in Redis for immediate effect)                  │
│ 13. App Insights logs session end + total duration + features used         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Token implementation choice ⚠️

Two options for the session token:

| Approach | Pros | Cons | Recommendation |
|---|---|---|---|
| **Signed JWT (HS256/RS256), self-issued** | No Entra round-trip on validate; APIM validates inline | Revocation requires Redis blacklist or short TTL | **Recommended for demos** |
| **Entra External ID Invitation Link + OTP** | Full Entra lifecycle; revocation native | Guest must create (or re-use) an Entra account; adds friction for 1-hour demo | Use for longer-lived external access |

**For the 1-hour QR-code scenario:** use a **self-signed JWT** (RS256, private key in Key Vault) with:
- `sub`: generated UUID (session ID)
- `aud`: `https://showroom.pwc.example`
- `exp`: `iat + 3600` (1 hour)
- `scope`: comma-separated list of allowed demo IDs
- `presenter`: Entra OID of the presenter who created it

APIM's `validate-jwt` policy handles validation with the public key fetched from Key Vault. No external round-trip per call.

**For revocation:** maintain a Redis Cache entry `revoked:{sessionId}` with TTL = token remaining lifetime. APIM policy checks this cache (< 1 ms) before allowing the call.

### 4.2 Real-user metrics — separate from token refresh

This came up in the meeting (confusion between ping-pong for liveness and analytics). These are **two separate concerns**:

| Concern | Mechanism | Owner |
|---|---|---|
| **Token liveness** | JWT `exp` claim + APIM validation. SDK auto-handles refresh. NO custom ping-pong endpoint needed. | APIM / SDK |
| **Real-user metrics** (time in app, features used, clicks) | **App Insights JavaScript SDK (RUM)** instrumented in the front-end. Sends telemetry independently. | Michael (front-end) |
| **Session audit** (who, when, which demo, how long) | App Insights custom events emitted from the BFF on session create / end. | Michael (BFF) |

The BFF should emit these custom events:
```typescript
// BFF — session lifecycle
appInsights.trackEvent({ name: "ShowroomSessionCreated", properties: {
  sessionId, presenterId, demoIds, expiresAt
}});

appInsights.trackEvent({ name: "ShowroomSessionEnded", properties: {
  sessionId, reason: "expired" | "revoked", durationSeconds
}});
```

---

## 5. Fine-grained authorisation — OpenFGA

### 5.1 Why OpenFGA

OpenFGA is an open-source implementation of **Google's Zanzibar** relation-based authorisation model. It answers the question: "can user U perform action A on object O, given the current set of relations?"

| Requirement | How OpenFGA handles it |
|---|---|
| "Show this user only these 3 demo apps" | `user:michael can view demo:claims-triage` |
| "This session is valid for 1 hour" | Relation TTL (time-bounded tuples via expiry metadata) |
| "Internal teams can see all assets; external guests can see only published ones" | `user:*#member of group:internal can read asset:*` vs `user:{guest} can read asset:{specific-demo-asset}` |
| "Presenter can invalidate any session they created" | `user:{presenter} can invalidate session:{sessionId}` |
| Audit: log every check | OpenFGA check audit log |

### 5.2 Deployment

```
ACA container: openfga/openfga:latest
  · Scale-to-zero when idle
  · Postgres backend (Azure Database for PostgreSQL Flexible Server)
  · REST API on port 8080 (internal VNet only — not exposed to internet)
  · Called by BFF on every permission-sensitive operation
```

No public endpoint. The BFF is the only caller. APIM does not call OpenFGA directly — APIM validates the JWT (authentication), and the BFF calls OpenFGA for fine-grained authorisation decisions *before* constructing the APIM request.

### 5.3 Relation model (starter schema)

```
model
  schema 1.1

type user

type group
  relations
    define member: [user]

type demo
  relations
    define can_view: [user, group#member]
    define can_manage: [user]

type session
  relations
    define created_by: [user]
    define can_invalidate: [user] or created_by
    define active_for: [user]

type asset
  relations
    define can_read: [user, group#member]
    define can_contribute: [user]
    define can_certify: [user]
```

### 5.4 Why NOT Auth0 / Okta for authZ

Michael flagged this correctly: Auth0's pricing model changes sharply above 50k MAU. PwC demos to hundreds of clients; if even 1% of prospects scan a QR code, you hit that tier quickly in a high-volume engagement. OpenFGA running on ACA costs ~€30–50/month at this scale (Postgres + ACA idle billing). Auth0 at 50k MAU+ costs hundreds to thousands per month depending on features.

**OpenFGA is open-source (Apache 2.0), CNCF sandbox project, with contributions from Google, Okta, and the community.** The operational risk is low with a simple deployment model.

---

## 6. APIM enforcement — the policy skeleton

Every showroom API product in APIM gets these policies in order:

```xml
<policies>
  <inbound>
    <!-- 1. Validate the Bearer JWT (session token or Entra token) -->
    <validate-jwt header-name="Authorization" failed-validation-httpcode="401"
                  failed-validation-error-message="Invalid or expired token">
      <openid-config url="https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration" />
      <!-- OR for self-signed session tokens: -->
      <issuer-signing-keys>
        <key certificate-id="showroom-session-key" />  <!-- Key Vault ref -->
      </issuer-signing-keys>
      <required-claims>
        <claim name="aud" match="any">
          <value>https://showroom.pwc.example</value>
        </claim>
      </required-claims>
    </validate-jwt>

    <!-- 2. Check Redis revocation list -->
    <cache-lookup-value key="@("revoked:" + context.Request.Headers.GetValueOrDefault("X-Session-Id",""))"
                        variable-name="isRevoked" />
    <choose>
      <when condition="@(context.Variables.GetValueOrDefault("isRevoked", "") == "true")">
        <return-response>
          <set-status code="401" reason="Session revoked" />
        </return-response>
      </when>
    </choose>

    <!-- 3. Check scope claim covers the requested demo/asset -->
    <set-variable name="allowedScopes"
                  value="@(context.Request.Claims.GetValueOrDefault("scope",""))" />
    <!-- (scope validation logic per asset/demo) -->

    <!-- 4. Content safety (all requests) -->
    <azure-content-safety ... />

    <!-- 5. Token quota (internal teams) -->
    <azure-openai-token-limit tokens-per-minute="10000" ... />

    <!-- 6. Emit token metrics for chargeback -->
    <emit-token-metric ... />
  </inbound>
</policies>
```

---

## 7. Scope boundaries — what Michael owns vs. what Raimondo owns

| Component | Michael (TypeScript) | Raimondo (Python / Bicep / APIM) |
|---|---|---|
| Entra ID + External ID tenant setup | MSAL integration in BFF | Bicep IaC for tenant + app registrations |
| Session token generation (JWT, RS256) | BFF endpoint: `POST /sessions` | Key Vault key provisioning |
| QR code generation | `qrcode` npm package in BFF | — |
| OpenFGA relation tuple writes | BFF: create tuples on session create | OpenFGA schema + ACA deployment (Bicep) |
| Redis revocation list write | BFF: `POST /sessions/{id}/revoke` | Redis provisioning (APIM Cache + ACA shared cache) |
| App Insights RUM (front-end) | JS SDK in Next.js | App Insights workspace (Bicep) |
| App Insights custom events (BFF) | `trackEvent` calls in BFF | Log Analytics queries + Power BI |
| APIM policy enforcement | — | `validate-jwt` + revocation-check + content-safety policies |
| Abort controllers (late-response guard) | TypeScript fetch wrapper in BFF | — |
| SQL unit tests (data correctness) | BFF data-layer tests | — |

---

## 8. Decision log

| # | Decision | Status | Owner | Notes |
|---|---|---|---|---|
| D1 | Entra ID for internal users | ✅ Agreed | Adrian + Raimondo | Confirmed in meeting |
| D2 | Entra External ID for external guests | ✅ Agreed | Adrian + Raimondo | Confirmed in meeting |
| D3 | Self-signed JWT for 1-hour demo tokens | ⚠️ Proposed | Raimondo | Alternative: Entra one-time invitation link (more friction) |
| D4 | OpenFGA for fine-grained authz | ⚠️ Proposed | Raimondo | Alternative: Entra app roles + APIM policies (less expressive but simpler) |
| D5 | Single external tenant (Option A) vs. per-client tenant | ⚠️ Needs Adrian sign-off | Raimondo | Recommendation: Option A. Ask Adrian Friday. |
| D6 | Auth0 / Okta SaaS: **not used** | ✅ Agreed | Michael + Raimondo | Cost cliff risk confirmed by Michael (50k MAU pricing trap) |
| D7 | No custom ping-pong liveness endpoint | ✅ Agreed | Both | Token expiry is SDK-handled; RUM is separate telemetry |
| D8 | Redis blacklist for immediate revocation | ⚠️ Proposed | Raimondo | Alternative: short JWT TTL (5 min) + re-issue (no revocation needed) |
| D9 | APIM is the single enforcement point — no backend accepts unauthenticated calls | ✅ Agreed | Raimondo | Non-negotiable architectural decision |

---

## 9. Open questions for Friday (2026-07-04)

1. **D5** — Single external tenant vs. per-client guest tenant. Adrian's answer changes the Bicep IaC and the Entra app registration model.
2. **D3** — Are self-signed JWTs acceptable from a PwC security / InfoSec policy perspective, or must all tokens be issued by Entra? (If InfoSec says "must be Entra", we use Entra External ID one-time passcode links instead.)
3. **D4** — OpenFGA or Entra app roles for fine-grained authz? OpenFGA is more expressive and the right long-term choice; Entra app roles are simpler to operate initially. Decide based on how complex the showroom RBAC will be in the first 3 months.
4. **D8** — Immediate revocation requirement: is "token expires within 5 minutes even if presenter clicks Revoke" acceptable? If yes, short TTL simplifies the Redis blacklist requirement significantly.

---

*Last updated: 2026-07-01. Owner: Raimondo Marino. Implementation lead: Michael.*
