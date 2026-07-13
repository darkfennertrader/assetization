---
title: "PwC Showroom Phase 2 — External Prospect Auth and Tracking Flow"
---

# PwC Showroom Phase 2 — External Prospect Auth and Tracking Flow

**Decision basis:** 2026-07-09 kickoff meeting (see `meetings/2026-07-09-summary.md`).
**Supersedes:** the QR-code session design (removed per Peter's decision on 2026-07-09).

## 1. Business scenario

A PwC salesperson wants to give a prospective client access to one or more AI demos hosted
in the Showroom. The salesperson logs into the **Presenter Admin panel** with their PwC
credentials, adds the prospect's email, selects which demos they may see, and sets a message
quota. The prospect then opens the Showroom URL on any device, clicks **"Sign in with Google"**
or **"Sign in with Microsoft"**, and immediately sees their personalised demo catalog -- no
account creation, no password, no QR code.

Every login, demo visit, and message count is recorded in Cosmos DB so the presenter can
monitor usage and the quota layer can cut off access when limits are reached.

## 2. Flow diagram

![Showroom Phase 2 -- external prospect auth and tracking flow](showroom-external-auth-flow.png)

## 3. Presenter Admin flow (Entra ID)

### Step 1 -- Presenter opens Admin panel

The salesperson navigates to <https://admin.showroom.pwc.example>.
NextAuth middleware detects no valid session and redirects to the Entra ID authorization
endpoint using the PKCE flow (same as Phase 1). The salesperson logs in with their
`@pwc.com` credentials. No separate account is required.

### Step 2 -- Presenter manages the allow-list

After login the presenter sees a table of prospects. For each entry they can:

- Set or update the prospect's email address.
- Select which demo IDs the prospect may access (`allowedDemoIds`).
- Set the total message quota (`messageQuotaTotal`), e.g. 100 messages.
- Top up `messageQuotaRemaining` when the prospect runs out.
- Set `status` to `banned` to immediately block the prospect.
- View analytics: `lastSeenAt`, `totalConnections`, demos opened, messages used.

The Presenter Admin writes these values to the **Cosmos DB `users` container** via the
BFF route `POST /admin/api/users`.

### Step 3 -- Presenter shares the Showroom URL

The presenter sends the prospect a plain URL: <https://showroom.pwc.example>.
No token, no expiry, no QR code. The prospect can bookmark it and return at any time
within the configured `status = active` window.

## 4. Prospect sign-in flow (Google or Microsoft OAuth)

### Step 4 -- Prospect opens the Showroom URL

The prospect navigates to <https://showroom.pwc.example>. The request path is:

```
Prospect browser
  --> Azure DNS (CNAME to Front Door endpoint)
  --> Azure Front Door PoP (global anycast, TLS termination)
  --> Front Door WAF Policy (OWASP CRS 3.2 + bot manager)
  --> ACA showroom-app (internal ingress via Front Door private link)
  --> Next.js middleware: no session cookie -> redirect to /api/auth/signin
```

### Step 5 -- Sign-in page

NextAuth serves a sign-in page with two buttons:
**"Sign in with Google"** and **"Sign in with Microsoft"**.

There is no PwC Entra ID button on the public prospect URL. Presenters always use the
`admin.showroom.pwc.example` subdomain which shows the Entra ID option only.

### Step 6 -- OAuth PKCE flow

The prospect clicks one of the provider buttons. NextAuth initiates a standard
Authorization Code + PKCE flow to the chosen provider's authorization endpoint.
The prospect authenticates with their existing Google or Microsoft account.
No new account is created in any PwC system.

### Step 7 -- OAuth callback

The provider redirects back to the callback path `/api/auth/callback/<provider>`
with the authorization code. NextAuth exchanges the code for an ID token and reads:

- `email` -- used as the primary key to look up the prospect in Cosmos DB `users`.
- `sub` -- provider-issued subject claim (stored for deduplication if email changes).
- `name` -- display name (stored for audit).

### Step 8 -- Allow-list check (coarse-grained AuthZ)

NextAuth's `signIn` callback looks up the email in Cosmos DB `users`:

- **Not found:** return `false`. NextAuth shows an "Access denied" page.
  The prospect sees: *"You are not authorised. Please contact your PwC host."*
- **Found, `status = banned`:** same denial.
- **Found, `status = quota_exhausted`:** denial with message: *"Your message quota is exhausted.
  Please ask your PwC host to top up your quota."*
- **Found, `status = active`:** proceed to step 9.

### Step 9 -- Session created and tracking written

On successful sign-in:

1. NextAuth creates an encrypted httpOnly session cookie (`AUTH_SECRET` from Key Vault).
   Session idle timeout: 1 hour. Absolute timeout: 8 hours.
2. BFF writes a **`connection_events`** document: `{ email, connectionAt, ip, userAgent }`.
3. BFF updates the **`users`** document: increments `totalConnections`, sets `lastSeenAt`.
4. BFF emits a **`ProspectLoggedIn`** event to App Insights: `{ email (hashed), provider }`.

Step 3 uses an edge middleware cookie (`sr_tracked`) to ensure these writes fire only once
per session, not on every request.

### Step 10 -- Catalog served (fine-grained AuthZ)

NextAuth's `session` callback attaches `allowedDemoIds` and `messageQuotaRemaining`
from the `users` document to the session object.

The BFF route `GET /api/demos` reads the session and returns only the demo tiles
the user is authorised to see. If `allowedDemoIds` is empty, the catalog is empty
and the prospect sees: *"No demos have been assigned to your account yet."*

The React frontend renders one tile per demo with a thumbnail, title, and description.

### Step 11 -- Demo tile clicked

The prospect clicks a demo tile. The BFF:

1. Writes a **`demo_visits`** document: `{ id: uuid, email, demoId, openedAt }`.
   The `visitId` UUID is returned to the frontend as a cookie or embedded in the
   redirect URL so the demo app can reference it in the usage callback.
2. Emits a **`DemoOpened`** event to App Insights: `{ email (hashed), demoId }`.
3. Executes a top-level browser redirect to the demo's `launchUrl`.
   This is `window.location.href = demo.launchUrl` -- not an iframe, not a fetch.
   The browser leaves the showroom URL and opens the demo app directly.

### Step 12 -- Demo app usage callback

After the demo session ends (or periodically), the demo app calls:

```
POST https://showroom.pwc.example/api/internal/demo-usage
X-Demo-Callback-Secret: <shared secret from Key Vault>

{
  "email": "prospect@example.com",
  "demoId": "overwatch",
  "visitId": "<uuid>",
  "messageCount": 12,
  "closedAt": "2026-07-09T14:58:00Z"
}
```

The BFF:

1. Validates the shared secret.
2. Updates `demo_visits`: sets `messageCount` and `closedAt`.
3. Decrements `users.messageQuotaRemaining` by `messageCount`.
4. If `messageQuotaRemaining <= 0` sets `users.status = quota_exhausted`.
5. Emits a **`UsageReported`** event to App Insights: `{ email (hashed), demoId, messageCount }`.

### Step 13 -- Quota exhausted

On the prospect's next sign-in attempt (step 8), the `signIn` callback reads
`status = quota_exhausted` and denies access with the quota message.

The presenter can top up by setting `messageQuotaRemaining` back to a positive value
in the Admin panel; this also resets `status` to `active`.

## 5. Session model

| Property | Value |
|---|---|
| Cookie type | `httpOnly`, `Secure`, `SameSite=Lax` |
| Encryption | NextAuth `AUTH_SECRET` (from Key Vault, rotated every 90 days) |
| Idle timeout | 1 hour (NextAuth default session TTL) |
| Absolute timeout | 8 hours (NextAuth `maxAge` setting) |
| Refresh | Automatic -- NextAuth refreshes the cookie on every server request |
| Revocation | Set `status = banned` in Cosmos. Next sign-in is denied. Current active session expires within the idle timeout (1 hour maximum window). |

No Redis is required. No token signing key is required. No silent refresh loop is required.
This is a standard NextAuth session -- significantly simpler than the Phase 2 QR design.

## 6. Security properties

| Property | Enforced by | Detail |
|---|---|---|
| No account creation for the prospect | Google / Microsoft OAuth | Zero PwC identity lifecycle for the prospect |
| Scoped access -- only presenter-selected demos | Cosmos `allowedDemoIds` in session | BFF returns only allowed tiles on every `/api/demos` request |
| Quota enforcement | Cosmos `messageQuotaRemaining` | Demo apps report usage; BFF decrements and blocks when exhausted |
| Revocation | Cosmos `status = banned` | Effective on next sign-in (within 1h worst case for active sessions) |
| WAF protection | Front Door WAF (OWASP CRS 3.2 + bot manager) | Edge-layer protection before any traffic reaches ACA |
| No stored credentials | Key Vault (Managed Identity) + OAuth PKCE | `AUTH_SECRET` and provider client secrets never in environment variables |
| Audit trail | App Insights custom events + Cosmos `connection_events` + `demo_visits` | Every login and demo visit recorded |
| TLS everywhere | Front Door enforces HTTPS-only redirect | Private endpoints on ACA subnet for Cosmos and Key Vault |

## 7. Presenter Admin panel -- key features

| Feature | Implementation |
|---|---|
| **Login** | PwC Entra ID via NextAuth `microsoft-entra-id` provider; PKCE |
| **Prospect list** | Table: email, provider, status, lastSeenAt, totalConnections, messageQuotaRemaining |
| **Add/edit prospect** | Form: email, allowedDemoIds (multi-select), messageQuotaTotal |
| **Top up quota** | Input field on prospect row: increment `messageQuotaRemaining` |
| **Ban / unban** | Toggle `status` between `active` and `banned` |
| **Analytics per prospect** | Expand row: connection_events timeline, demo_visits with messageCount |
| **Analytics aggregate** | App Insights queries: logins per week, most popular demo, avg messages per session |

## 8. Phase 3 upgrade path

The Phase 2 session model is fully compatible with Phase 3's APIM layer. When APIM is
inserted between Front Door and ACA:

- APIM validates the NextAuth session cookie on the `validate-jwt` or `validate-azure-ad-token`
  policy before requests reach the BFF. Phase 2 middleware remains as defence-in-depth.
- Rate-limiting per user moves from BFF middleware to APIM `rate-limit-by-key(email)`.
- Content Safety is applied at APIM for all agent inputs and outputs.
- Audit log moves from App Insights custom events to APIM -> Event Hub -> ADLS Gen2 (WORM).

No application code changes are required to adopt APIM in Phase 3.
