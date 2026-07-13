---
title: "Showroom Phase 2 — External Prospect Runtime Flow"
---

![Showroom Phase 2 external prospect runtime flow](showroom-phase2-flow.png)

\clearpage

Every numbered step below maps to exactly one numbered arrow in the sequence
diagram on the preceding page. Steps marked **(alt)** belong to a branch that
fires only under the stated condition; one branch fires, the other does not.

## Step 1 — Prospect Browser → Front Door: `GET /`

The external customer navigates to <https://showroom.pwc.example>. Azure DNS
resolves the hostname to a CNAME pointing at the Front Door endpoint, so the
TCP connection is established to the nearest Azure Front Door PoP.

Note: this URL is the **customer-facing** entry point only. PwC presenters and
administrators use a separate subdomain (<https://admin.showroom.pwc.example>)
which routes to the same showroom-app container but enforces PwC Entra ID
authentication exclusively — Google and Microsoft consumer OAuth are not offered
there. The two paths share no sign-in page.

## Step 2 — Front Door → ACA showroom-app: forward (WAF passed)

Front Door Standard terminates TLS at the PoP, runs the request through the
WAF Policy (OWASP CRS 3.2 + bot manager), and forwards clean traffic to the ACA
showroom-app over a private link. The container has no public IP of its own; it
is unreachable except through Front Door.

## Step 3 — Showroom → Browser: `302` (no session cookie found)

The Next.js middleware runs on every incoming request. It detects the absence of
a valid session cookie and redirects the browser to `/api/auth/signin`.

## Step 4 — Browser → Showroom: `GET /api/auth/signin`

The browser follows the redirect and requests the sign-in page.

## Step 5 — Showroom → Browser: sign-in page (Google or Microsoft)

NextAuth serves the sign-in page. It presents exactly two buttons:
**Sign in with Google** and **Sign in with Microsoft** (consumer accounts).

No PwC Entra ID option is shown at this URL. Internal presenters reach the
Entra ID path through the `admin.showroom.pwc.example` subdomain.

## Step 6 — Browser → Provider: `/authorize + code_challenge` (PKCE)

The prospect clicks one provider button. NextAuth generates a `code_verifier`,
computes `code_challenge = SHA-256(code_verifier)`, stores the verifier in an
encrypted httpOnly cookie, and redirects the browser to the chosen provider's
authorization endpoint. No client secret is transmitted to the browser at any
point.

## Step 7 — Provider → Browser: login form

The provider (Google or Microsoft) returns its standard login form. The prospect
authenticates with their existing personal account. No new account is created in
any PwC system.

## Step 8 — Browser → Provider: submit credentials

The prospect submits their email address and password. If the account has MFA
enabled at the provider level, the provider challenges for the second factor.

## Step 9 — Provider → Browser: `302 → /api/auth/callback/<provider>?code=…`

The provider validates the credentials, and redirects the browser to the
showroom callback path with a short-lived single-use authorization code.

## Step 10 — Browser → Showroom: `/api/auth/callback/<provider>?code=…`

The browser follows the redirect back to the showroom BFF. The BFF receives both
the authorization code and the encrypted `code_verifier` cookie it stored in
Step 6.

## Step 11 — Showroom → Provider: `POST /token` (PKCE verifier)

NextAuth sends the authorization code and the plaintext `code_verifier` to the
provider's token endpoint. The provider re-computes `SHA-256(code_verifier)` and
checks it against the `code_challenge` it received in Step 6, proving the party
exchanging the code is the same one that initiated the flow. This prevents
authorization-code interception attacks.

## Step 12 — Provider → Showroom: ID token (`email`, `sub`, `name`)

The provider returns a signed ID token. NextAuth extracts `email`, `sub`
(provider-scoped user identifier), and `name` from the token claims. No refresh
token is stored.

## Step 13 — Showroom → Cosmos DB: user look-up by email

The NextAuth `signIn` callback looks up the prospect's email address in the
Cosmos DB `users` container. This is the coarse-grained authorization gate.

## Step 14 — Cosmos DB → Showroom: user record (or not found)

Cosmos DB returns the user document if it exists, or a 404-equivalent if not.

## Step 15 — Showroom → Browser: access-denied page (alt: user not active)

*This step fires only when the look-up in Step 14 returns one of:*

- *email not found in Cosmos DB*
- *`status = banned`*
- *`status = quota_exhausted`*

NextAuth returns `false` from the `signIn` callback. The prospect sees a plain
HTML page with HTTP **200**:

- Not found or banned: *"You are not authorised. Please contact your PwC host."*
- Quota exhausted: *"Your message quota is exhausted. Please ask your PwC host
  to top up."*

The flow ends here for this sign-in attempt.

## Step 16 — Showroom → Cosmos DB: `INSERT connection_events` (alt: `status = active`)

*This step fires only when the look-up in Step 14 returns `status = active`.*

The BFF inserts a `connection_events` document:

```json
{
  "email": "prospect@example.com",
  "connectionAt": "2026-07-10T08:37:00Z",
  "ip": "203.0.113.42",
  "userAgent": "Mozilla/5.0 ..."
}
```

An edge middleware cookie (`sr_tracked`) prevents this write from firing on
every subsequent page request within the same session — it fires once per
sign-in only.

## Step 17 — Showroom → Cosmos DB: `UPDATE users` (`totalConnections++`, `lastSeenAt`)

The BFF increments `users.totalConnections` and sets `users.lastSeenAt` to the
current UTC timestamp.

## Step 18 — Showroom → App Insights: `ProspectLoggedIn` (custom event)

The BFF emits a single structured custom event:

```json
{ "email_hashed": "<sha256>", "provider": "google" }
```

App Insights is used **only** for three backend custom events
(`ProspectLoggedIn`, `DemoOpened`, `UsageReported`). There is no browser RUM
SDK and no page-view telemetry. Email is always SHA-256-hashed before being sent
to any telemetry sink; the raw email address never leaves the Cosmos DB boundary.

## Step 19 — Showroom → Browser: session cookie

NextAuth creates an encrypted httpOnly session cookie using `AUTH_SECRET`
(pulled from Key Vault at startup via Managed Identity). Cookie settings:

- `HttpOnly` — not accessible to JavaScript.
- `Secure` — HTTPS only.
- `SameSite=Lax` — CSRF mitigation.
- **Idle timeout: 7 days.** The prospect can close the browser and return within
  a week without signing in again.
- **Absolute timeout: 7 days.** The session expires unconditionally 7 days after
  it was created, regardless of activity.

## Step 20 — Browser → Showroom: `GET /api/demos` (session cookie presented)

The browser loads the catalog page and presents the session cookie on the API
call. The NextAuth `session` callback runs.

## Step 21 — Showroom → Cosmos DB: read `allowedDemoIds` + `messageQuotaRemaining`

The session callback reads two fields from the `users` document to determine
what the prospect may see and how much budget they have.

## Step 22 — Cosmos DB → Showroom: allowed demo list + quota

Cosmos returns `allowedDemoIds` (an array of demo ID strings) and
`messageQuotaRemaining` (integer). Both are attached to the NextAuth session
object and are available server-side on every subsequent request.

## Step 23 — Showroom → Browser: empty catalog page (alt: `allowedDemoIds` is empty)

*This step fires only when `allowedDemoIds` is an empty array.*

The catalog page renders with the message:
*"No demos have been assigned to your account yet. Please contact your PwC
host."*

## Step 24 — Showroom → Browser: catalog HTML with filtered demo tiles (alt: demos assigned)

*This step fires only when `allowedDemoIds` contains at least one entry.*

The React frontend renders one tile per demo in the allowed list. Each tile
shows a thumbnail, a title, and a short description. Demos not in
`allowedDemoIds` are never sent to the client.

## Step 25 — Browser → Showroom: tile click

The prospect clicks a demo tile (e.g. Overwatch). The browser sends a request to
the BFF to record the visit and mint the handoff token.

## Step 26 — Showroom → Cosmos DB: `INSERT demo_visits`

The BFF inserts a `demo_visits` document:

```json
{
  "visitId": "a1b2c3d4-...",
  "email": "prospect@example.com",
  "demoId": "overwatch",
  "openedAt": "2026-07-10T08:45:00Z"
}
```

## Step 27 — Showroom → Key Vault: read demo-handoff private key

The BFF fetches the RSA-256 private key from Key Vault via Managed Identity.
This key is used to sign the handoff JWT that authorises the prospect to enter
the demo app without a second login. The key is stored only in Key Vault and
never in environment variables or container images.

## Step 28 — Showroom (self): mint handoff JWT

The BFF mints a short-lived JSON Web Token:

```json
{
  "iss": "https://showroom.pwc.example",
  "aud": "overwatch",
  "sub": "prospect@example.com",
  "visitId": "a1b2c3d4-...",
  "iat": 1752140700,
  "exp": 1752140760,
  "kid": "sr-2026-07"
}
```

TTL is 60 seconds — enough for the browser round-trip; not enough to be useful
if intercepted. The `aud` claim is the `demoId`; a token minted for `overwatch`
is invalid at any other demo app.

## Step 29 — Showroom → App Insights: `DemoOpened` (custom event)

The BFF emits:

```json
{ "email_hashed": "<sha256>", "demoId": "overwatch" }
```

## Step 30 — Showroom → Browser: auto-POST form to `demo.launchUrl`

The BFF responds with a tiny self-submitting HTML form:

```html
<form method="POST" action="https://demo.launchUrl/">
  <input type="hidden" name="token" value="<signed JWT>">
</form>
<script>document.forms[0].submit();</script>
```

The browser executes the form submission immediately. The prospect sees no
second login screen. The JWT travels in the POST body (not in the URL), so it
does not appear in browser history or server access logs.

## Step 31 — Browser → Demo app: `POST /` with `token=<JWT>`

The browser posts to the demo app's own FQDN. The showroom app is no longer in
the request path from this point on.

## Step 32 — Demo app → Showroom: `GET /.well-known/jwks.json`

The demo app fetches the showroom's public key set. The response is cached for
24 hours keyed by `kid`. On a signature-verification failure the cache is
invalidated and refetched once before returning `401` (handles key rotation
transparently). The JWKS array may contain more than one key during a
signing-key rotation window — the demo app must select the entry whose `kid`
matches the token header's `kid`, not assume a single key.

## Step 33 — Showroom → Demo app: JWKS document (Key Vault-backed, RAM-cached)

The showroom-app's `GET /.well-known/jwks.json` handler serves the **public
projection** of the RSA-256 signing key stored in Azure Key Vault. The handler
works as follows:

- At startup (and every 15 minutes thereafter), the showroom-app reads the
  **current** and — during a rotation window — the **previous** key version
  from Key Vault via Managed Identity.
- It derives the public-key JWKS document (n, e, kid, kty, alg) entirely in
  RAM from the public components of those key versions. The private key material
  never leaves Key Vault.
- The JWKS document is held in an in-process cache with a 15-minute TTL. No
  database or external store is required.
- During a key rotation, both the outgoing and the incoming public keys appear
  in the JWKS array simultaneously, each with a distinct `kid`. Demo apps
  already holding the old JWKS document in their 24-hour cache will continue
  validating tokens until they next refresh; tokens signed with the new key are
  also valid as soon as they are issued.

The demo app selects the key whose `kid` matches the JWT header and uses it for
signature verification.

## Step 34 — Demo app (self): verify JWT + extract identity

The demo app verifies:

1. Signature (RSA-256, public key from Step 33).
2. `iss` claim equals <https://showroom.pwc.example>.
3. `aud = overwatch` (must equal the demo's own ID).
4. `exp` not in the past.

On success it extracts `sub` (prospect email) and `visitId`. If any check fails
the demo responds `401 Unauthorized` and renders no content.

## Step 35 — Demo app → Browser: `Set-Cookie: demo_session` + `302 /`

The demo app creates its own session cookie (httpOnly, Secure, SameSite=Lax)
containing the verified `email` and `visitId`, then redirects the browser to
`GET /`. The one-use handoff JWT is discarded.

## Step 36 — Browser → Demo app: `GET /` with `demo_session` cookie

The browser follows the redirect with the new session cookie. The demo app
renders its UI and the prospect starts interacting with it. No second login
screen has been shown at any point.

## Step 37 — Demo app → Browser: demo application UI

The demo app renders its full UI. The prospect starts their session.

## Step 38 — Demo app → Showroom: `POST /api/internal/demo-usage`

After the demo session ends (or periodically), the demo app reports usage back
to the showroom:

```
POST https://showroom.pwc.example/api/internal/demo-usage
X-Demo-Callback-Secret: <shared secret from Key Vault>

{
  "email": "prospect@example.com",
  "demoId": "overwatch",
  "visitId": "a1b2c3d4-...",
  "messageCount": 12,
  "closedAt": "2026-07-10T09:05:00Z"
}
```

## Step 39 — Showroom (self): validate `X-Demo-Callback-Secret`

The BFF reads the expected secret from Key Vault via Managed Identity and
compares it with the header value using a constant-time comparison. If the
header is absent or incorrect the request is rejected with `401 Unauthorized`.

## Step 40 — Showroom → Cosmos DB: `UPDATE demo_visits`

The BFF sets `messageCount` and `closedAt` on the `demo_visits` document
created in Step 26, closing the visit record.

## Step 41 — Showroom → Cosmos DB: decrement `messageQuotaRemaining`

The BFF decrements `users.messageQuotaRemaining` by the reported `messageCount`.

## Step 42 — Showroom → Cosmos DB: `SET status = quota_exhausted` (alt: quota <= 0)

*This step fires only when `messageQuotaRemaining` reaches zero or below after
the decrement in Step 41.*

The BFF sets `users.status = quota_exhausted`. On the prospect's next sign-in
attempt Step 15 fires and denies access with the quota message. The presenter
can top up by setting `messageQuotaRemaining` back to a positive value in the
Admin panel, which simultaneously resets `status` to `active`.

## Step 43 — Showroom → App Insights: `UsageReported`

The BFF emits:

```json
{
  "email_hashed": "<sha256>",
  "demoId": "overwatch",
  "messageCount": 12
}
```

## Step 44 — Showroom → Demo app: `200 OK`

The BFF returns `200 OK` to confirm the usage callback was accepted. The demo
app can safely discard its local usage counter.

## Infrastructure notes

- **TLS and edge security:** Azure Front Door enforces HTTPS-only redirects.
  The ACA showroom-app has internal ingress only; it is unreachable from the
  public internet except through Front Door's private link.
- **Secrets management:** `AUTH_SECRET`, the Google client secret, the
  Microsoft client secret, the demo-handoff RSA private key, and the
  demo-callback shared secret are stored in Azure Key Vault. The ACA app
  accesses them via system-assigned Managed Identity. No secrets appear in
  environment variables or container images.
- **JWKS endpoint:** The showroom exposes its public key at
  `/.well-known/jwks.json`. Demo apps cache this response for 24 hours
  (keyed by `kid`) and refetch on signature-verification failure to support
  key rotation without downtime.
- **Container image supply chain:** the container image is pulled from Azure
  Container Registry using Managed Identity. No Docker credentials are stored
  anywhere.
- **Observability:** the showroom-app writes `stdout`/`stderr` to Log Analytics
  automatically via the ACA environment link. App Insights receives the three
  custom events (`ProspectLoggedIn`, `DemoOpened`, `UsageReported`). No browser
  RUM SDK is deployed. Email is always hashed before being sent to App Insights.
- **Session storage:** no Redis or external session store is required. The
  showroom session lives entirely in the encrypted httpOnly cookie managed by
  NextAuth. Each demo app maintains its own session cookie independently.

## Phase 3 upgrade path

When APIM is inserted between Front Door and ACA in Phase 3:

- APIM validates the handoff JWT (or a NextAuth session cookie) via the
  `validate-jwt` policy before any request reaches the BFF or a demo app. The
  in-app JWT validation in each demo app remains as defence-in-depth but is no
  longer the primary enforcement point.
- Rate-limiting per user moves from BFF middleware to APIM
  `rate-limit-by-key(email)`.
- Content Safety screening is applied at APIM for all agent inputs and outputs.
- The audit trail moves from App Insights custom events to APIM emitting to
  Event Hub and landing in ADLS Gen2 (WORM), satisfying longer retention and
  compliance requirements.

No application code changes are required to adopt APIM in Phase 3.
