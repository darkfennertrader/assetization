---
title: "Showroom Build Checklist for the Showroom Developer Team"
---

## Purpose and Audience

This document is addressed to the Full-Stack Developer (and any developer who
works on the Showroom BFF). It lists every activity the Showroom developer team
must implement to deliver a platform that is **correct, secure, and ready for
external prospects**.

**Phase 1** covers the internal PwC employee audience, authenticated via the
corporate Entra ID tenant. **Phase 2** extends the platform to external
prospects who sign in via Google or Microsoft consumer accounts, and introduces
a WAF and CDN layer via Azure Front Door, a signed JWT handoff mechanism for
demo apps, and usage telemetry via Cosmos DB.

This document is **implementation-agnostic**: it specifies *what* to build, not
which framework or library to use. It contains no code.

**Out of scope:** infrastructure provisioning (Front Door, Cosmos DB, Key Vault,
App Insights, ACR, DNS, WAF policies, Managed Identity role assignments).
Those are owned and operated by the Showroom DevOps team and documented in
the Phase 1 and Phase 2 DevOps runbooks.


## Phase 1 Activities — Internal Audience (PwC Employees)

Phase 1 delivers the internal catalog portal for PwC employees. Authentication
is delegated to the corporate PwC Entra ID tenant. All activities in this
section are **mandatory** before Phase 1 go-live.


### Authentication and Identity

**Implement OIDC Authorization Code + PKCE in the Showroom BFF.**
The BFF must generate a `code_verifier` and `code_challenge`, redirect the user
to the PwC Entra `/authorize` endpoint with the Showroom client ID and scopes,
exchange the returned code at the `/token` endpoint, and store the resulting
tokens in an encrypted server-side session. Tokens must not be present in the
browser at any time.

**Retrieve the Entra client secret from Key Vault at startup.**
The BFF reads `KEY_VAULT_URL` and `CLIENT_SECRET_NAME` from its environment
variables and authenticates to Key Vault using `DefaultAzureCredential`, which
picks up the container's system-assigned Managed Identity automatically. The
resolved secret is held in memory for the lifetime of the process. It is never
written to disk, logs, or environment variables at rest.

**Enforce the Layer-1 group check on every request.**
After token acquisition, verify that the user's ID token contains the
`FINCRIME_GROUP_OID` Group Object ID in the `groups` claim. Reject any session
whose token does not contain this group. Perform the check on every request,
not only at login time.

**Handle group-claim overage gracefully.**
When a user belongs to more than 200 groups, Entra omits the `groups` claim and
includes a `_claim_names` hint instead. The BFF must detect this overage
condition and call the Microsoft Graph `transitiveMemberOf` endpoint to resolve
group membership. The `GroupMember.Read.All` delegated permission and admin
consent are provisioned by DevOps (Phase 1 runbook §3.1).

**Return a human-readable access-denied page, not HTTP 4xx.**
When the Layer-1 group check fails, return an HTML page with HTTP **200** and a
clear message (e.g. *"You do not have access to the PwC AI Showroom. Please
contact your line manager."*). Do not return 401 or 403 — clients that receive
those status codes may surface a browser-default error page.

**Silent SSO must not re-prompt.**
When a PwC user is already authenticated to their corporate device, the Showroom
must detect the existing session and not issue a new login challenge. Use the
`prompt=none` parameter and handle the `login_required` error gracefully by
falling back to a visible redirect when truly necessary.


### Catalog and Navigation

**Implement the demo catalog from `demo-map.json`.**
The BFF reads `demo-map.json` from the application bundle (or a well-known
mounted path) to build the catalog. Each entry provides at minimum the demo
name, URL slug, thumbnail URL, and the group Object IDs that may access it.

**Enforce the Layer-2 tile filter.**
For each tile in the catalog, check whether the authenticated user's token
groups include at least one of the tile's required group Object IDs. Render only
the tiles the user is authorised to see. A user who passes the Layer-1 check may
still see an empty catalog if none of their groups match any tile.

**Launch tiles by top-level navigation only.**
When the user clicks a demo tile, the BFF must redirect the browser to the
demo's `launchUrl` using a top-level navigation (HTTP redirect or `window.location`
assignment). Do not embed demos in an `<iframe>` and do not proxy demo traffic
through the Showroom BFF. The Showroom's responsibility ends at the redirect.

**Propagate the correlation ID.**
Inject a `traceparent` header (W3C Trace Context) or `X-Request-ID` on all
outbound requests and log the same value in every log entry for the session.
Read any inbound `traceparent` and use it as the parent span.


### HTTP Contract

**Expose an unauthenticated liveness endpoint.**
Implement `GET /api/health` returning HTTP 200 within 5 seconds, with no
authentication required. The response body may be minimal (e.g. `{"status":"ok"}`).
This endpoint is called by the keep-warm timer function (DevOps runbook §8)
and by Front Door health probes (Phase 2). It must not trigger BFF logic or
session checks.

**Honour reverse-proxy headers.**
The BFF sits behind the ACA ingress reverse proxy. Honour `X-Forwarded-Proto`
and `X-Forwarded-Host` when constructing absolute URLs (e.g. in OAuth redirect
responses) so that HTTPS-scheme URLs are generated correctly.

**Session cookie security attributes.**
Set `Secure`, `HttpOnly`, and `SameSite=Lax` on all session cookies. Do not
set cookies without `Secure` — they will be silently dropped by modern browsers
on HTTPS pages.

**Use Managed Identity for all secret retrieval.**
`DefaultAzureCredential` must be the only mechanism by which the BFF acquires
credentials. No connection strings, shared keys, or service principal passwords
may appear in environment variables at rest, configuration files, or source
control.


### Operations

**Log structured output to stdout/stderr.**
The ACA environment captures container stdout/stderr and forwards it to the Log
Analytics workspace automatically. Emit structured JSON logs. Include the
correlation ID, HTTP method, path, status code, and latency on every request.


## Phase 2 Additional Activities — External Audience (Prospects)

Phase 2 extends the Showroom to unauthenticated external visitors who sign in
via Google or Microsoft consumer accounts. All Phase 1 activities remain
mandatory. Phase 2 adds the following.


### External Authentication Handlers

**Implement the Google OAuth 2.0 handler.**
The BFF must initiate the Google OAuth 2.0 Authorization Code flow using the
`GOOGLE_CLIENT_ID` environment variable and the `google-oauth-client-secret`
retrieved from Key Vault (secret name in `GOOGLE_SECRET_NAME`). Redirect the
user to Google's `/authorize` endpoint, handle the callback at
`/api/auth/callback/google`, exchange the code for tokens, and extract the
`email` and `name` claims from the ID token.

**Implement the Microsoft consumer OAuth handler.**
The BFF must initiate the Microsoft identity platform Authorization Code flow
for personal accounts using `MICROSOFT_CLIENT_ID` and
`ms-oauth-client-secret` (Key Vault secret name in `MICROSOFT_SECRET_NAME`).
Callback path: `/api/auth/callback/microsoft-consumer`.

**Implement subdomain-aware routing.**
The BFF must inspect the `Host` header (or `X-Forwarded-Host`) on every request
and apply different authentication and routing logic per subdomain:

- `showroom.pwc.example` (value of `PROSPECT_ORIGIN`): accept only Google /
  Microsoft-consumer sessions. Render the external prospect catalog.
- `admin.showroom.pwc.example` (value of `ADMIN_ORIGIN`): accept only PwC Entra
  ID sessions. Render the internal admin panel and presenter catalog.

A session established on one subdomain must not be accepted on the other.

**Retrieve the auth session secret from Key Vault.**
The BFF reads the `AUTH_SECRET_NAME` environment variable to determine the Key
Vault secret name for the `AUTH_SECRET` value used to encrypt session cookies.
This value is retrieved via Managed Identity at startup.

**Enforce the Cosmos DB allow-list for external prospects.**
After a successful Google or Microsoft consumer login, look up the user's email
in the Cosmos DB `users` container (endpoint in `COSMOS_ENDPOINT`, database name
in `COSMOS_DB`). Accept the session only if `users.status` is `active`. Return
an access-denied page (HTTP 200, human-readable message) if the user is absent
from the list, has `status = banned`, or has `status = quota_exhausted`.

**Write to Cosmos DB using Managed Identity.**
The BFF accesses Cosmos DB using `DefaultAzureCredential`. The Managed Identity
has been granted the `Cosmos DB Built-in Data Contributor` role by DevOps. Never
use a Cosmos DB connection string or primary key.


### Signed JWT Handoff

**Do not implement an external OAuth flow for demo apps.**
The Showroom is the sole identity provider for external prospects. Demo apps
must not initiate their own Google or Microsoft consumer OAuth flows. The
Showroom mints a signed JWT and the demo app validates it.

**Mint the handoff JWT by calling the Key Vault Sign API.**
On demo launch, the BFF must:

1. Read the current key version from the `HANDOFF_KEY_NAME` Key Vault key
   (`demo-handoff-key`). Refresh the cached version every 15 minutes.
2. Construct the JWT header and payload (see below) and serialize them as the
   unsigned token input.
3. Call the Key Vault Sign API (`RS256` algorithm) with the input bytes. Key
   Vault performs the RSA operation; the private key material never leaves
   Key Vault.
4. Assemble the final JWT from the header, payload, and the signature returned
   by Key Vault.

**JWT claims the Showroom must include.**
Every handoff JWT must carry: `iss` set to the Showroom issuer URL (the
`PROSPECT_ORIGIN` value); `aud` set to the demo's `demoId` string (from
`demo-map.json`); `sub` set to the SHA-256 hash of the user's email; `email`
set to the SHA-256 hash of the user's email; `visitId` as a new UUID per
launch; `exp` set to 60 seconds from issuance; `nbf` set to the current time;
`kid` set to the current Key Vault key version string.

**Keep the JWT TTL at 60 seconds.**
The JWT is a single-use launch credential. Its TTL must be 60 seconds. After
delivery, the demo app establishes its own session; the JWT is not reused.

**Publish `/.well-known/jwks.json`.**
The BFF must serve a JWKS document at `/.well-known/jwks.json` containing the
public components of all active key versions (current and any version in the
48-hour rotation overlap window). Derive the public key parameters from the Key
Vault Get Key API response. Set `Cache-Control: max-age=900` on the response.
The private key material must never appear in the JWKS document.


### Origin Protection

**Enforce the `X-Azure-FDID` header check.**
Implement a BFF middleware that runs before any routing or authentication logic
on every inbound request:

1. Read the `X-Azure-FDID` header.
2. Compare it with the `FRONT_DOOR_ID` environment variable using a
   constant-time string comparison.
3. If the header is absent or the values differ, return `403 Forbidden`
   immediately and log the source IP and the received header value.
4. If the values match, pass the request to the next middleware.

This check prevents direct-to-origin access that bypasses the WAF.


### Usage Telemetry

**Record connection events in Cosmos DB.**
On every successful external login, write one document to the
`connection_events` container with fields: `email`, `connectionAt` (ISO 8601
UTC), `ip`, `userAgent`. Append-only; never update these records.

**Record demo visits in Cosmos DB.**
On every demo launch, write one document to the `demo_visits` container with
fields: `visitId` (UUID), `email`, `demoId`, `openedAt` (ISO 8601 UTC).
`messageCount` and `closedAt` are back-filled later by the usage callback.

**Implement the usage callback receiver.**
Expose `POST /api/internal/demo-usage`. On every inbound POST:

1. Read the `X-Demo-Callback-Secret` header. Retrieve the expected value from
   Key Vault (secret name in `DEMO_CALLBACK_SECRET_NAME`) and compare using a
   constant-time comparison. Return `401 Unauthorized` if the values do not
   match.
2. Parse the JSON payload and update the matching `demo_visits` document with
   `messageCount` and `closedAt`.
3. Decrement `messageQuotaRemaining` in the `users` document by the reported
   message count. If the result reaches zero, set `status = quota_exhausted`.
4. Return `200 OK`.

**Emit App Insights custom events.**
Emit exactly three custom events to App Insights using the connection string in
`APPINSIGHTS_CONNECTION_STRING`: `ProspectLoggedIn` on external login,
`DemoOpened` on demo launch, `UsageReported` on receipt of a usage callback.
Always SHA-256-hash the email before including it in any App Insights payload.
Never emit raw email addresses to App Insights.

**Rate-limit external users independently.**
Apply separate rate-limit counters for external (Phase 2 JWT) sessions and
internal (Entra) sessions. External prospect loads are less predictable and
must not degrade the experience for internal users.

**Log external identity claims separately for GDPR.**
Write access logs for sessions established via Google or Microsoft consumer
login to a separate log stream with the retention period agreed with Showroom
DevOps. Do not co-mingle these records with application-logic logs. Obtain
data-protection officer sign-off before the first external user reaches
production.


### Business Reporting Surface

**Build the Azure Monitor Workbook `wb-pwc-showroom-usage`.**
This workbook is the primary business-reporting surface for PwC presenters and
managers. Build it in the dev environment first, then clone to prod. DevOps
runbook §14 specifies the resource location, naming convention, and the RBAC
assignments that DevOps will provision for presenter accounts.

**Source all workbook data from Cosmos DB, not App Insights.**
The workbook queries the `users`, `connection_events`, and `demo_visits`
containers directly using Cosmos DB SQL. Do not query App Insights for business
data — App Insights holds hashed emails for operational telemetry only. Plain
emails and quota state live in Cosmos DB and must stay there.

**Deliver a three-panel initial workbook.**
Minimum viable delivery: (a) a prospect table showing email, status, quota
remaining, and last connection timestamp; (b) a sign-ins-over-time line chart
by day; (c) a demo-popularity bar chart grouped by `demoId`. Additional panels
may be added iteratively based on presenter feedback.


### Operations Additions

**Alert on repeated JWT-verification failures.**
Configure an alert that fires when the JWKS-signature-verification failure rate
for the JWKS endpoint itself (i.e. demo apps failing to verify the
`/.well-known/jwks.json` response) exceeds five failures in a five-minute
window. This may indicate a key-rotation event that demo apps have not yet
picked up.

**Alert on usage-callback rejection spikes.**
Configure an alert that fires when the rate of `401 Unauthorized` responses from
`POST /api/internal/demo-usage` exceeds five in a five-minute window. This may
indicate a secret-rotation mismatch.


## Point of Contact with Showroom DevOps

This section governs all communication between the Showroom developer team and
the Showroom DevOps team. Follow it exactly to avoid delays, security incidents
from mishandled secrets, or wiring errors caused by stale values.


### What You Send to Showroom DevOps

Deliver the following artefacts to Showroom DevOps before each milestone. Never
transmit secrets via email, Teams direct message, WhatsApp, or any uncontrolled
channel. Any secret transmitted outside approved paths must be rotated
immediately.

| Artefact | Format | Required for |
|---|---|---|
| Entra redirect URI for custom subdomain | URL | Phase 2 wiring |
| Google OAuth callback URI | URL | Phase 2 wiring |
| Microsoft consumer OAuth callback URI | URL | Phase 2 wiring |
| Confirmation that FDID check is implemented | plain text | Phase 2 go-live |
| GDPR note and data-protection sign-off | document | Phase 2 go-live |
| Notification of any route or callback path change | plain text | Whenever it changes |


### What You Receive from Showroom DevOps

Showroom DevOps will supply the following values. Store each one as directed;
never in source control or plain-text configuration.

| Artefact | Where to store | Notes |
|---|---|---|
| Key Vault URL (`KEY_VAULT_URL`) | ACA env var | Points to `kv-pwc-showroom-<env>-<region>` |
| Entra client secret name (`CLIENT_SECRET_NAME`) | ACA env var | Value: `showroom-client-secret` |
| Entra tenant ID (`AZURE_TENANT_ID`) | ACA env var | PwC Entra tenant GUID |
| Entra App Registration client ID (`AZURE_CLIENT_ID`) | ACA env var | Showroom App Registration |
| Security group Object ID (`FINCRIME_GROUP_OID`) | ACA env var | Layer-1 group check |
| Cosmos DB endpoint (`COSMOS_ENDPOINT`) | ACA env var | Cosmos account HTTPS endpoint — copy from Portal |
| Cosmos DB database name (`COSMOS_DB`) | ACA env var | Value: `showroom` |
| App Insights connection string (`APPINSIGHTS_CONNECTION_STRING`) | ACA env var | Non-secret; safe to log |
| Google client ID (`GOOGLE_CLIENT_ID`) | ACA env var | Non-secret |
| Microsoft consumer client ID (`MICROSOFT_CLIENT_ID`) | ACA env var | Non-secret |
| Prospect origin URL (`PROSPECT_ORIGIN`) | ACA env var | External prospect subdomain HTTPS origin |
| Admin origin URL (`ADMIN_ORIGIN`) | ACA env var | Admin subdomain HTTPS origin |
| Auth secret name (`AUTH_SECRET_NAME`) | ACA env var | Key Vault secret name: `auth-secret` |
| Google secret name (`GOOGLE_SECRET_NAME`) | ACA env var | Key Vault secret name: `google-oauth-client-secret` |
| Microsoft secret name (`MICROSOFT_SECRET_NAME`) | ACA env var | Key Vault secret name: `ms-oauth-client-secret` |
| Handoff key name (`HANDOFF_KEY_NAME`) | ACA env var | Key Vault Key name: `demo-handoff-key` |
| Front Door ID (`FRONT_DOOR_ID`) | ACA env var | Front Door instance GUID; used for FDID header check |
| Callback secret name (`DEMO_CALLBACK_SECRET_NAME`) | ACA env var | Key Vault secret name: `demo-callback-shared-secret` |
| Front Door endpoint hostname | plain text | ACA-to-Front-Door wiring; needed during dev |
| Custom FQDNs once DNS is validated | plain text | `showroom.pwc.example`, `admin.showroom.pwc.example` |
| Test-tenant credentials for dev validation | scoped credentials | Per test cycle; store in Key Vault |
| Cosmos DB Reader RBAC for presenter accounts | plain text confirmation | Provisioned by DevOps per §14; needed before workbook go-live |


## Build Sequence

Follow these steps in order. Do not attempt Phase 2 implementation before Phase
1 is validated end-to-end.

1. Read this checklist in full and identify any items that require clarification
   from DevOps (environment variable values, Key Vault secret names, group OIDs).
2. Receive the Phase 1 §4.2 artefacts from Showroom DevOps.
3. Implement all Phase 1 activities (§2).
4. Perform end-to-end validation in the dev environment: login, group check,
   access-denied page, catalog render, tile filter, demo launch, health endpoint,
   correlation ID in logs.
5. Obtain Phase 1 go-live sign-off from Showroom DevOps.
6. Receive the Phase 2 §4.2 artefacts from Showroom DevOps.
7. Implement all Phase 2 activities (§3).
8. Perform end-to-end Phase 2 validation: Google login, Microsoft consumer login,
   subdomain routing, Cosmos DB allow-list check, handoff JWT mint and delivery,
   JWKS publication, FDID check, usage callback receipt, App Insights events,
   GDPR log separation, rate-limit behaviour.
9. Obtain Phase 2 go-live sign-off from Showroom DevOps.

\newpage

## Pre-flight Readiness Summary

Use this table as a final checklist before requesting go-live sign-off from
Showroom DevOps. Every row must be ticked.

### Phase 1 readiness

| Activity | Done |
|---|---|
| OIDC Authorization Code + PKCE implemented in BFF; tokens not in browser | |
| Client secret retrieved from Key Vault via Managed Identity at startup | |
| Layer-1 group check enforced on every request, not only at login | |
| Group-claim overage handled via Graph API | |
| Access-denied page returns HTTP 200 with human-readable message | |
| Silent SSO verified; no spurious re-prompts | |
| Catalog built from `demo-map.json` | |
| Layer-2 tile filter applied per user's group membership | |
| Demo launch uses top-level navigation, no iframe or proxy | |
| `GET /api/health` returns HTTP 200 unauthenticated within 5 s | |
| `X-Forwarded-Proto` and `X-Forwarded-Host` honoured in redirect URIs | |
| Session cookies carry Secure, HttpOnly, SameSite attributes | |
| Managed Identity used for all Key Vault secret retrieval | |
| Correlation ID propagated in all outbound calls and log entries | |
| Structured JSON logs emitted to stdout | |

### Phase 2 readiness (in addition to all Phase 1 rows)

| Activity | Done |
|---|---|
| Google OAuth 2.0 handler implemented; secret from Key Vault | |
| Microsoft consumer OAuth handler implemented; secret from Key Vault | |
| Subdomain routing implemented: prospect vs. admin path | |
| Auth session secret retrieved from Key Vault at startup | |
| Cosmos DB allow-list check enforced for external prospects | |
| Cosmos DB writes use Managed Identity, not a connection string | |
| `X-Azure-FDID` header check implemented; non-matching requests return 403 | |
| Handoff JWT minted via Key Vault Sign API (private key never in process) | |
| JWT claims include iss, aud, sub (hashed), email (hashed), visitId, exp, kid | |
| JWT TTL set to 60 seconds | |
| `/.well-known/jwks.json` published; Cache-Control: max-age=900 | |
| JWKS derived from Key Vault Get Key API; no private material in document | |
| `connection_events` document written on every external login | |
| `demo_visits` document written on every demo launch | |
| `POST /api/internal/demo-usage` implemented; HMAC check on callback secret | |
| Cosmos DB quota decremented and status updated on usage callback | |
| Three App Insights custom events emitted; email always SHA-256-hashed | |
| External identity claims logged separately; GDPR sign-off obtained | |
| Rate-limiting applied separately to external and internal sessions | |
| Alert on JWKS verification failure spike configured | |
| Alert on usage-callback rejection spike configured | |
| Workbook `wb-pwc-showroom-usage` built in dev and cloned to prod | |
