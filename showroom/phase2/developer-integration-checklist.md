---
title: "Showroom Integration Checklist for Application Teams"
---

## Purpose and Audience

This document is addressed to application team leads and developers who are
onboarding an existing or new application onto the PwC Showroom platform. It
lists every activity your team must perform to become **seamlessly compatible**
with both phases of the Showroom.

**Phase 1** covers demonstrations to internal PwC employees, authenticated via
the corporate Entra ID tenant. **Phase 2** extends the platform to external
prospects authenticated through consumer identity providers (Google,
Microsoft consumer) managed by the Showroom itself, adds a WAF and CDN layer
via Azure Front Door, and introduces usage telemetry callbacks.

This document is **app-agnostic**: it specifies *what* to do, not *how* your
particular stack implements it. It contains no code.

**Out of scope:** Showroom-side infrastructure (Front Door, APIM, Cosmos DB
allow-list, certificate management, WAF policies, JWKS key rotation). Those
are owned and operated by the Showroom DevOps team.


## Phase 1 Activities — Internal Audience (PwC Employees)

Phase 1 allows PwC employees to browse and launch your application from the
internal Showroom portal. Authentication is delegated to the corporate
Entra ID tenant. All activities in this section are **mandatory** before a
Phase 1 go-live.


### Authentication and Identity

**Register an Entra ID App Registration.**
Create a new App Registration in the PwC Entra ID tenant. Register it as a
**Web (confidential client)** application — not a Single-Page App (SPA)
registration, because the Authorization Code + PKCE flow runs on your
server-side BFF, not in the browser.

**Register the redirect URI.**
Under the Web platform section of your App Registration, add a redirect URI
pointing to the path `/api/auth/callback/azure-ad` on your demo hostname,
using the HTTPS scheme. Provide the full URI to Showroom DevOps as part of
the kick-off handoff (see §4.1).

**Enable the groups claim.**
In the App Registration's Token configuration, add the `groups` optional
claim to the ID token. Select "Security groups" to emit Group Object IDs.
This is the mechanism by which the Showroom portal enforces who may see and
launch your demo.

**Enforce group-based authorisation server-side.**
Your application must check the Group Object IDs present in the token against
the list of approved groups supplied by Showroom DevOps (see §4.2). Reject
any session whose token does not contain an approved group. Do this on every
request, not only at login time.

**Store your client secret securely.**
The client secret for your App Registration must reside in **your own** Azure
Key Vault, retrieved at runtime via Managed Identity. Never place it in
environment variables at rest, in configuration files, in code repositories,
or in any messaging channel. If a secret is ever transmitted outside the
approved channels, rotate it immediately.

**Implement OIDC Authorization Code + PKCE in your BFF.**
Your back-end for front-end layer must generate a `code_verifier` and
`code_challenge`, redirect the user to the Entra `/authorize` endpoint with
your `client_id` and `scope`, exchange the returned code at the Entra
`/token` endpoint, and store the resulting tokens in an encrypted server-side
session. Tokens must not be present in the browser.

**Silent SSO must not re-prompt.**
When a PwC user is already authenticated to their corporate device, your
application must detect the existing session and not issue a new login
challenge. Use the `prompt=none` parameter and handle the `login_required`
error gracefully by falling back to a visible redirect when truly necessary.


### HTTP Contract

**Expose a stable public launch URL.**
Your application must be reachable at a stable FQDN, accessible over HTTPS.
Provide this URL to Showroom DevOps at kick-off. Changing the FQDN after
wiring requires advance notice and re-wiring on the Showroom side.

**Expose an unauthenticated liveness endpoint.**
Provide a health endpoint (for example `/health` or `/api/health`) that
returns HTTP 200 for the platform health check probes. The endpoint must not
require authentication and must return within 5 seconds.

**Honour reverse-proxy headers.**
Your application sits behind the Showroom reverse proxy. You must honour
`X-Forwarded-Proto` and `X-Forwarded-Host` when constructing absolute URLs
(for example in redirect responses), so that HTTPS-scheme URLs are generated
correctly and sessions are not broken.

**Cookie security attributes.**
Any session cookie your application sets must carry the `Secure`, `HttpOnly`,
and `SameSite=Lax` attributes (or `SameSite=None; Secure` if your flow
requires cross-site delivery). Cookies without `Secure` will be silently
dropped by modern browsers when the page is served over HTTPS.

**CORS policy.**
Allow only the Showroom origin URLs supplied by DevOps in §4.2. Never
configure a wildcard `*` CORS policy. Preflight (`OPTIONS`) requests must be
handled within your application layer.


### Deployment

**Own your container image and registry.**
The Showroom platform does not host your container. Use your own Azure
Container Registry, App Service, Azure Container Apps, or equivalent. The
Showroom treats your application as an external service reached over HTTPS.

**Provision your own supporting resources.**
Key Vault, Application Insights, storage accounts, and databases are all
owned by your team. Nothing is shared with the Showroom infrastructure. This
ensures cost separation and independent lifecycle management.

**Use Managed Identity for all secret retrieval.**
No application in the Showroom ecosystem may use connection strings or shared
keys embedded in environment variables or configuration files at rest. All
secrets are fetched via Managed Identity from your Key Vault.

**Keep your hostname stable.**
Once you tell Showroom DevOps the URL of your application, do not change it.
If the URL changes, the Showroom platform stops working for your app until
DevOps re-wires it, which takes time. Use a deployment approach that lets you
push new versions without changing the URL — App Service deployment slots,
ACA revision pinning, and similar mechanisms achieve this on most cloud
platforms. If you genuinely need to change the hostname, notify DevOps well
in advance so they can schedule the re-wiring.


### Operations

**Propagate the correlation ID.**
The Showroom platform injects a correlation ID in the `traceparent` header
(W3C Trace Context) or `X-Request-ID`. Your application must read this header
on inbound requests and propagate it in all downstream calls and log entries.
This is the primary mechanism by which issues are traced across platform and
application boundaries.

**Provide an on-call contact.**
Supply Showroom DevOps with the name, email, and out-of-hours phone number of
at least two people who can respond to a production incident within 30
minutes. Update this list whenever personnel change.


## Phase 2 Additional Activities — External Audience (Prospects)

Phase 2 extends the Showroom to unauthenticated external visitors who sign in
via Google or Microsoft consumer accounts. The Showroom becomes the **sole
identity provider** for these users and hands your application a signed JWT.
Your application must trust that JWT and nothing else.

**All Phase 1 activities remain mandatory.** Phase 2 adds the following.


### JWT Verification

**Do not implement your own external OAuth flow.**
Your application must not initiate OAuth 2.0 / OIDC flows with Google,
Microsoft consumer, or any external IdP. The Showroom performs that exchange
and hands your application a signed assertion. Implementing your own external
OAuth flow creates two parallel trust chains and is a security defect.

**Fetch the Showroom JWKS document.**
On startup, retrieve the JSON Web Key Set from the URL supplied by Showroom
DevOps (see §4.2). This document contains the public keys your application
uses to verify the signature on every incoming Showroom JWT.

**Cache JWKS for 24 hours, keyed by key ID.**
Cache the key set locally, keyed by the `kid` (key identifier) field in each
key. When a signature verification fails, invalidate the cache entry for that
`kid` and refetch the JWKS once before returning an authentication error to
the caller. This ensures transparent handling of key rotation without service
interruption.

**Support a multi-key JWKS.**
The JWKS array may contain more than one key during a rotation window. Always
select the key whose `kid` matches the `kid` field in the incoming JWT header.
Never hardcode a specific key or assume a single-entry array.

**Verify all mandatory claims.**
For every request bearing a Showroom JWT, verify: RSA signature against the
matching JWKS key; `iss` matches the Showroom issuer URL supplied by DevOps;
`aud` matches the audience string supplied by DevOps (specific to your
demo); `exp` has not passed; `nbf` has been reached. Reject any token that
fails any of these checks with HTTP 401.

**Extract user identity from token claims only.**
Do not call external user-info endpoints, directory services, or databases to
look up the authenticated user. The JWT claims (`sub`, `email`, display name)
are the authoritative identity for the duration of the session. If additional
profile data is needed, design your own consent-based data-collection flow and
seek GDPR advice before collecting anything.


### HTTP Contract Additions

**Accept the signed launch hand-off.**
When the Showroom redirects a user to your demo, it attaches the Showroom JWT
in the `Authorization: Bearer` header of the initial launch request. Your
application must validate this token (per §3.1) before establishing a session.
Do not accept the hand-off without signature verification.

**Implement the usage callback.**
Your application must report message or interaction counts back to the Showroom
by POSTing to the usage-callback URL supplied by DevOps. The payload schema
and reporting cadence are defined in the Phase 2 runbook. Implement a retry
with exponential back-off if the callback endpoint is temporarily unreachable;
discard retries after 5 minutes to avoid unbounded queuing.

**Honour the callback shared secret header.**
Every POST to the usage-callback URL must include the `X-Demo-Callback-Secret`
header, set to the value supplied by Showroom DevOps. Rotate this value on
the DevOps-defined schedule (at minimum annually, or immediately upon
suspected exposure). Coordinate the rotation with Showroom DevOps in advance
to avoid a gap where the callback is rejected.

**Validate the Front Door origin header.**
The Showroom platform routes all external traffic through Azure Front Door.
Your application must validate the `X-Azure-FDID` header on every inbound
request and reject any request that does not carry the Front Door ID value
supplied by DevOps. This prevents direct-to-origin attacks that bypass the
WAF.

**Reject direct-origin traffic.**
In addition to header validation, configure your hosting layer (App Service
access restrictions, ACA ingress rules, or equivalent) to accept inbound
requests only from the Front Door service tag or IP ranges. Treat the header
check and the network-layer restriction as defence in depth — both must be
in place.

**Provide an admin subdomain exposure.**
Expose an admin-only path or subdomain restricted to PwC internal egress IPs
and requiring Phase 1 (internal SSO) authentication. This allows PwC
operators to manage the demo without using the external prospect flow. The
routing and IP restriction rules are configured by Showroom DevOps; you must
implement the application-level authorisation check.


### Operations Additions

**Rate-limit external users independently of internal users.**
Apply separate rate-limit counters for external (Phase 2 JWT) sessions and
internal (Entra) sessions. External prospect loads are less predictable and
must not degrade the experience for internal users.

**Log external identity claims separately for GDPR audit.**
When writing access logs for sessions established via the Showroom JWT,
record the `sub` claim and any `email` claim in a separate log stream with
the retention period specified by Showroom DevOps. Do not co-mingle these
records with application-logic logs. Seek your data-protection officer's
sign-off before the first external user reaches production.

**Alert on repeated JWT-verification failures.**
Configure an alert that fires when the JWKS-signature-verification failure
rate exceeds a threshold (suggested: more than 5 failures in a 5-minute
window). This indicates a key-rotation event the application did not catch,
a misconfigured audience value, or an active attack.


## Point of Contact with Showroom DevOps

This section governs all communication between your application team and the
Showroom DevOps team. Follow it exactly to avoid delays, security incidents
from mishandled secrets, or wiring errors caused by stale values.


### What You Send to Showroom DevOps

Deliver the following artefacts to Showroom DevOps before each milestone.
Never transmit secrets via email, Teams direct message, WhatsApp, or any
uncontrolled channel. Any secret transmitted outside approved paths must be
rotated immediately.

| Artefact | Format | Required for |
|---|---|---|
| Demo name and short URL slug | plain text | Kick-off |
| Public launch URL (FQDN) | URL | Phase 1 wiring |
| Entra redirect URI (callback URL) | URL | Phase 1 wiring |
| Demo Entra App Registration client ID | GUID | Phase 1 wiring |
| Expected user groups (Object IDs) | list of GUIDs | Phase 1 wiring |
| Liveness endpoint path | URL path | Phase 1 wiring |
| Usage callback endpoint | URL | Phase 2 wiring |
| Data-classification and GDPR note | short text | Phase 2 wiring |
| Break-glass contact rota | name, email, phone | Before go-live |
| Notification of any FQDN or port change | plain text | Whenever it changes |
| demo-map.json tile entry values (name, slug, thumbnail URL, auth groups) | plain text / JSON | Before Phase 1 wiring |


### What You Receive from Showroom DevOps

Showroom DevOps will supply the following values. Store each one in your Key
Vault; never in source control or plain-text configuration.

| Artefact | Format | Rotation schedule |
|---|---|---|
| Showroom JWKS URL | URL | Stable (notify on change) |
| JWT audience (`aud`) value for the demo | string | Stable |
| JWT issuer (`iss`) value | URL | Stable |
| `X-Demo-Callback-Secret` shared secret | string | At least annually |
| `X-Azure-FDID` Front Door identifier | GUID | On Front Door replacement |
| Usage-callback path and payload schema | URL + schema doc | On breaking change |
| Group Object IDs the demo app must authorise | list of GUIDs | On org change |
| Showroom origin URLs for CORS allow-list | list of URLs | Stable |
| Test-tenant credentials for dev validation | scoped credentials | Per test cycle |
| Showroom platform on-call contact rota | name, email, phone | Before Phase 1 go-live |


## Onboarding Sequence

Follow these steps in order. Do not attempt Phase 2 integration before Phase
1 is validated end-to-end.

1. Read this checklist in full. Identify any items that require decisions or
   procurement on your side (Key Vault, Managed Identity, App Registration).
2. Deliver the §4.1 artefacts for Phase 1 to Showroom DevOps.
3. Receive the §4.2 artefacts from Showroom DevOps.
4. Implement all Phase 1 activities (§2).
5. Perform end-to-end validation in the dev/test environment using the
   test-tenant credentials supplied by DevOps. Verify: authentication,
   group-based authorisation, health probe, correlation ID propagation.
6. Obtain Phase 1 go-live sign-off from Showroom DevOps.
7. Implement all Phase 2 activities (§3).
8. Deliver the additional §4.1 artefacts for Phase 2.
9. Perform end-to-end validation with the Phase 2 test tenant: JWT
   hand-off, usage callback, Front Door header enforcement, GDPR log
   separation, rate-limit behaviour.
10. Obtain Phase 2 go-live sign-off from Showroom DevOps.

\newpage

## Pre-flight Readiness Summary

Use this table as a final checklist before requesting go-live sign-off from
Showroom DevOps. Every row must be ticked.

### Phase 1 readiness

| Activity | Done |
|---|---|
| Entra App Registration created as Web (confidential client) | |
| Redirect URI registered and shared with DevOps | |
| Groups claim enabled in ID token | |
| Group Object IDs obtained from DevOps and enforced server-side | |
| Client secret stored in Key Vault, retrieved via Managed Identity | |
| OIDC Authorization Code + PKCE implemented in BFF; tokens not in browser | |
| Silent SSO verified; no spurious re-prompts | |
| Stable FQDN provided to DevOps | |
| Liveness endpoint returns HTTP 200 unauthenticated within 5 s | |
| `X-Forwarded-Proto` and `X-Forwarded-Host` honoured | |
| Session cookies carry Secure, HttpOnly, SameSite attributes | |
| CORS restricted to Showroom origin URLs from DevOps | |
| Managed Identity used for all secret retrieval | |
| Correlation ID propagated in all outbound calls and log entries | |
| On-call contact rota delivered to DevOps | |

### Phase 2 readiness (in addition to all Phase 1 rows)

| Activity | Done |
|---|---|
| No external OAuth flow implemented in your app | |
| JWKS URL fetched on startup and cached per §3.1 | |
| Multi-key JWKS support implemented (select by kid) | |
| All mandatory JWT claims verified (sig, iss, aud, exp, nbf) | |
| Showroom JWT accepted as sole launch hand-off mechanism | |
| Usage callback endpoint implemented with retry and back-off | |
| `X-Demo-Callback-Secret` header sent on every callback POST | |
| `X-Azure-FDID` header validated; requests without it rejected | |
| Network-layer restriction to Front Door origin in place | |
| Admin subdomain restricted to PwC egress IPs + internal SSO | |
| External JWT-verification failure alert configured | |
| External identity claims logged separately with correct retention | |
| Rate-limiting applied separately to external and internal sessions | |
| GDPR note delivered to DevOps; data-protection sign-off obtained | |
| Callback shared secret stored in Key Vault, rotation schedule agreed | |
