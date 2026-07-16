---
title: "Showroom Platform Build Checklist"
---

## Purpose and Audience

This document is addressed to the Showroom platform team — the full-stack
developers and DevOps engineers who build and operate the Showroom portal
itself. It lists every activity your team must perform to make the Showroom
ready for both phases of operation.

**Phase 1** covers the internal catalog: PwC employees log in with their
corporate Entra ID credentials, browse the catalog, and launch demo
applications. **Phase 2** extends the platform to external prospects who
authenticate via Google or Microsoft consumer accounts, routes all external
traffic through Azure Front Door and WAF, and introduces a JWKS-signed JWT
hand-off to each demo application.

This document is **platform-focused**: it specifies what the Showroom team
builds and operates, not what each demo team builds.

**Out of scope:** everything owned by individual demo application teams —
their App Registrations, their Key Vaults, their container images, their
Log Analytics workspaces, their PKCE flows, and their JWT-verification code.
That scope is fully described in `developer-integration-checklist.md` in this
directory. Both documents reference each other's handoff tables; keep them
in sync whenever a table row changes.


## Phase 1 Activities — Internal Showroom for PwC Employees

All activities in this section are **mandatory** before Phase 1 go-live.
Full details for each item are in `showroom/phase1/devops-runbook.md`.
Section numbers below refer to that runbook.


### Authentication and Identity

**Register the Showroom's own App Registration.**
Create `app-pwc-showroom` in the PwC Entra ID tenant as a **Web (confidential
client)** application (runbook §3.1). This is the Showroom's own identity — not
to be confused with the separate App Registration that each demo team creates
for their own application. Register it in the Web platform section with two
redirect URIs: the ACA default FQDN path `/api/auth/callback/azure-ad` and
<http://localhost:3000/api/auth/callback/azure-ad> for local development.
Agree the App Registration name and configuration with the Entra tenant admin
before provisioning (see §5.1 for the wider-DevOps coordination checklist).

**Enable the groups claim.**
In the App Registration's Token configuration, add the `groups` optional claim
to the ID token and select "Security groups" so that security group Object IDs
are included. This is mandatory: the Layer-1 group check (see below) reads
this claim. Also request the `GroupMember.Read.All` delegated permission from the
Entra tenant admin and obtain admin consent before Phase 1 go-live (runbook §3.1).
Without it the BFF cannot resolve group memberships for users with more than 200
group assignments.

**Store the Showroom client secret in the Showroom Key Vault.**
The Showroom has its own Key Vault (`kv-pwc-showroom-<env>-<region>`). Store
the App Registration client secret there. At runtime, the BFF retrieves it via
the ACA app's system-assigned Managed Identity. Never place the secret in
environment variables at rest, configuration files, or any source repository.
Rotate at least annually or immediately upon any suspected exposure.

**Implement the OIDC Authorization Code + PKCE flow in the Showroom BFF.**
The BFF generates a `code_verifier` and `code_challenge` on every unauthenticated
request, stores the verifier in an encrypted HttpOnly cookie, and redirects the
browser to the Entra `/authorize` endpoint. On the callback the BFF exchanges
the code at the Entra `/token` endpoint using both the PKCE verifier and the
client secret, stores the resulting ID token in an encrypted server-side
session, and never exposes tokens to the browser.

**Enforce Layer-1 authorisation: FinCrime Showroom group check.**
On every authenticated request, the BFF reads the `groups` claim from the
session token and checks whether it contains the `FINCRIME_GROUP_OID` value
(runbook §3.3 and §3.4). If the user is not a member, return a friendly HTML page with
HTTP 200 — do not use 401 or 403. The Group Object ID is supplied by the Entra
tenant admin and stored in the BFF configuration.

**Enforce Layer-2 authorisation: per-demo tile filtering via demo-map.json.**
The BFF reads `demo-map.json`, which is baked into the container image at build
time. This file defines, for each demo, the tile metadata (title, thumbnail URL,
`launchUrl`) and the authorization entries (which user `oid`s and group OIDs may
see that demo). The BFF intersects the authenticated user's `oid` and `groups`
with those entries and returns only the tiles the user is authorized to see
(runbook §7 and §9). Phase 1 starts with all tiles granted to `FINCRIME_GROUP_OID`;
the mechanism exists so future per-partner filtering requires only a
`demo-map.json` edit and a container revision update — no code change.


### HTTP Contract

**Publish a stable default FQDN.**
In Phase 1 the Showroom uses the ACA-assigned default FQDN (a custom domain
is deferred to Phase 2). Communicate this FQDN to the demo teams as the
Showroom origin URL they must allow in their CORS policy (see
`developer-integration-checklist.md` §2.2).

**Expose an unauthenticated health endpoint.**
Implement `/api/health` returning HTTP 200 with a short JSON body. This endpoint
must not require authentication and must respond within 5 seconds. It is called
by the Timer Function cold-start mitigator (see §2.4) and by ACA health probes.

**Implement the catalog page and tile launch.**
Render the authorized demo tiles as HTML. Each tile includes a thumbnail, title,
and description. When the user clicks a tile, the page executes a top-level
browser navigation (`window.location.href = demo.launchUrl`) — do not use an
iframe or a server-side proxy route. This is a hard design constraint: each demo
runs in its own process and manages its own session (runbook §7).

**Inject correlation IDs on all outbound requests.**
Insert a `traceparent` header (W3C Trace Context) or `X-Request-ID` on every
outbound call from the BFF. Log the same value in all BFF log entries for that
request cycle. This is the primary mechanism by which incidents are traced across
the Showroom and demo-app boundaries.


### Deployment

**Deploy the ACA environment and the Showroom ACA app.**
Environment: `cae-pwc-showroom-<env>-<region>`, Consumption plan, no VNet in
Phase 1. App: `ca-pwc-showroom-<env>-<region>`, external HTTPS ingress on
port 3000, scale-to-zero (min 0, max 5 replicas). Pull the container image
from the shared ACR using the ACA app's system-assigned Managed Identity — no
Docker credentials in any environment variable (runbook §2.2).

**Provision the shared Azure Container Registry.**
Create `crpwcshowroom<region>.azurecr.io`. Assign `AcrPull` to the Showroom
ACA app's Managed Identity. All demo teams that elect to share the ACR also
receive `AcrPull` on their own Managed Identities; teams using their own
registry do not. Coordinate ACR provisioning with the wider-DevOps function
before any team attempts an image push (see §5.1).

**Provision the Showroom Key Vault.**
Create `kv-pwc-showroom-<env>-<region>`. Store the App Registration client
secret, the `FINCRIME_GROUP_OID` value, and any future secrets here. Grant the
Showroom ACA app's Managed Identity the `Key Vault Secrets User` role.

**Provision the Showroom Log Analytics workspace.**
Create `log-pwc-showroom-<env>-<region>`. Link the ACA environment to it so
that `stdout`/`stderr` from the Showroom container is shipped automatically.
Each demo team owns and pays for its own workspace — do not co-mingle their
log streams with the Showroom's.

**Deploy the cold-start Timer Function.**
Create `func-pwc-showroom-<env>-<region>` with a Timer trigger (CRON
`0 */5 9-18 * * 1-5`, `WEBSITE_TIME_ZONE=W. Europe Standard Time`). The
function issues a GET to `/api/health` every 5 minutes on weekdays during
business hours to keep the ACA replica alive and eliminate cold-start latency
for the first user of the day. The full cost/complexity rationale is documented
in `aca-vs-appservice-decision.md`.


### Operations

**Publish the Phase 1 handoff outputs to each demo team.**
Before wiring any demo, deliver the values listed in §4.2 of this document.
Do not allow a demo team to begin integration work until they have received
all Phase 1 handoff outputs.

**Maintain the demo-map.json manifest.**
`demo-map.json` is the single configuration file that controls which demos
appear in the catalog and who may see them. When a new demo is onboarded or
an authorization entry changes, update the file and release a new container
revision. Keep the schema stable — any breaking schema change must be
communicated to demo teams before deployment.

**On-call rota.**
Maintain an on-call rota for the Showroom platform covering business hours
and the agreed out-of-hours escalation path. Share this rota with the wider
DevOps function and with each demo team lead.


## Phase 2 Additional Activities — External Prospects

Phase 2 opens the Showroom to external visitors who are not PwC employees.
The Showroom becomes the **sole identity provider** for external sessions and
issues signed JWTs to each demo application in lieu of an Entra token.

**All Phase 1 activities remain mandatory.** Phase 2 adds the following.
Full details are in `showroom/phase2/devops-runbook.md`.


### External Identity Provider Integration

**Configure the external OAuth providers (Google, Microsoft consumer).**
Integrate Google OAuth 2.0 and Microsoft consumer (personal account) OIDC into
the Showroom BFF. External sessions are routed via the
`showroom.pwc.example` subdomain; internal (Entra) sessions remain on
`admin.showroom.pwc.example`. The subdomain routing is enforced at Front Door
(see §3.2); the BFF must check the incoming host header to select the
correct authentication path.

**Store external-IdP client credentials in the Showroom Key Vault.**
The client ID and secret for Google OAuth and the Microsoft consumer OIDC app
registration must be stored in the Showroom Key Vault and retrieved at runtime
via Managed Identity. Rotate on the same schedule as internal credentials.

**Do not forward external user credentials to demo apps.**
Once the Showroom has authenticated an external user, it issues a Showroom-signed
JWT. Demo apps verify that JWT and derive identity from it. The Showroom never
shares the raw Google or Microsoft token with any downstream application.


### JWT Issuance to Demo Applications

**Generate and publish an RSA key pair for JWT signing.**
Create an RS256 signing key pair. Assign a unique `kid` (key identifier) to
each key. Store the private key in the Showroom Key Vault. Publish the
corresponding public key in the JWKS document at a stable URL (for example,
<https://showroom.pwc.example/.well-known/jwks.json>). The JWKS endpoint must
be publicly accessible without authentication and must return within 5 seconds.

**Maintain at least two keys in the JWKS document during rotation.**
When rotating the signing key, add the new key to the JWKS document and keep
the old key for at least 24 hours before removing it. This allows demo apps
that have cached the JWKS to pick up the new key without an authentication
outage. Never remove a key from the JWKS while any unexpired token signed by
it may still be in circulation.

**Issue JWTs with all mandatory claims.**
For every external session, issue a short-lived JWT containing: `iss`
(Showroom issuer URL), `aud` (the per-demo audience string supplied to that
demo team), `sub` (stable user identifier), `email` (from the external IdP),
`exp` (not more than the session duration), and `nbf`. Sign with the current
RS256 private key and include the matching `kid` in the JWT header.

**Rotate signing keys at least annually.**
Schedule key rotation and communicate the rotation schedule to all demo teams
in advance. A rotation must not break any live demo session — follow the two-key
window rule above. After rotation, deliver the updated JWKS URL and any changed
issuer or audience values to every demo team before removing the old key.

**Deliver the JWKS and JWT parameters to each demo team.**
See the handoff table in §4.2.


### Front Door and WAF

**Deploy Azure Front Door (Standard tier).**
Create `afd-pwc-showroom-<env>-<region>`. Configure two origin groups both
pointing to the Showroom ACA app over HTTPS — one for `showroom.pwc.example`
(external path) and one for `admin.showroom.pwc.example` (internal path). No
Private Link or VNet in Phase 2.

**Configure the WAF policy in Prevention mode.**
Create `waf-pwc-showroom-<env>-<region>`, OWASP CRS 3.2, bot-manager ruleset,
attached to the Front Door profile. Prevention mode means the WAF blocks
matching requests rather than just logging them.

**Configure custom domains and TLS.**
Use DigiCert ManagedCertificate provisioned by Front Door. Minimum TLS version
1.2. Domain validation is via TXT record in the DNS zone owned by the wider
DevOps function (coordinate per §5.1). Auto-renewal is handled by Front Door;
no manual certificate management is required.

**Enforce the X-Azure-FDID header.**
Configure the ACA app's ingress to require the `X-Azure-FDID` header matching
the Front Door profile identifier. This prevents external traffic from reaching
the ACA origin directly, bypassing the WAF. Deliver the `X-Azure-FDID` value
to every demo team so they can enforce the same check in their own origin
(see `developer-integration-checklist.md` §3.2).

**Do not allow direct-to-origin traffic in production.**
Apply an ACA access restriction to accept inbound requests only from the
Azure Front Door service tag. This is network-layer enforcement; the header
check is application-layer enforcement. Both must be in place.


### APIM Ingress

**Deploy Azure API Management.**
Place APIM between Front Door and the ACA origin for the external path. Configure
a `validate-jwt` policy that checks the external-user JWT issued by the Showroom's
own token endpoint. For the internal path, the `validate-jwt` policy checks the
Entra ID JWT, replacing the in-app middleware check from Phase 1.

**Rate-limit at APIM.**
Configure separate rate-limit counters for external (Phase 2 JWT) and internal
(Entra) sessions. External prospect traffic is less predictable; it must not
consume quota that would degrade internal users.


### Usage Callback Receiver

**Implement the usage-callback POST endpoint.**
Expose an endpoint that demo apps POST to when reporting message or interaction
counts. Validate the `X-Demo-Callback-Secret` header on every inbound POST;
reject requests without it or with an invalid value. Store callback events in
Cosmos DB. Define the payload schema and deliver it to each demo team as part
of the Phase 2 handoff (see §4.2).

**Provision Cosmos DB for demo metadata and callback storage.**
Create the Cosmos DB account for the allow-list of registered demos and for
usage-callback event storage. Grant the Showroom ACA app's Managed Identity
the `Cosmos DB Built-in Data Contributor` role. No demo team has direct access
to this database.

**Deliver the callback secret to each demo team via Key Vault.**
Generate a unique `X-Demo-Callback-Secret` per demo. Store it in the Showroom
Key Vault and transmit it to the demo team only via a mechanism they can store
directly in their own Key Vault (for example, a time-limited shared-access URL
or an Azure Key Vault secret-sharing facility). Never transmit via email,
Teams, or any uncontrolled channel.


### Operations Additions

**GDPR and data-classification handling.**
External user identity data (`sub`, `email`) from Google and Microsoft consumer
IdPs must be logged in a separate, restricted log stream with the retention
period aligned to your GDPR data-protection officer's guidance. Do not
co-mingle external identity data with application-logic logs. Obtain
data-protection sign-off before the first external user reaches production.

**Alert on JWKS and callback anomalies.**
Configure alerts for: (a) JWKS endpoint returning non-200 for more than
2 consecutive health probes; (b) elevated JWT-verification failure rate on the
APIM `validate-jwt` policy; (c) usage-callback rejection rate exceeding a
threshold. These alert on platform failures before demo teams notice them.

**On-call rota update.**
Update the on-call rota to include Phase 2 components (Front Door, WAF, APIM,
external IdP). Ensure the wider DevOps function has emergency contacts for
Front Door and Cosmos DB incidents.


## Point of Contact with Demo Teams

These tables are the mirror of §4 in `developer-integration-checklist.md`.
Every row in §4.1 corresponds to a row in that document's §4.1 (What You Send
to DevOps). Every row in §4.2 corresponds to a row in that document's §4.2
(What You Receive from DevOps). Keep both tables in sync when either changes.


### What You Receive from Each Demo Team

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


### What You Provide to Each Demo Team

Never transmit secret values via email, Teams direct message, or any
uncontrolled channel. Rotate any value that is transmitted outside the approved
path immediately.

| Artefact | Format | Rotation schedule |
|---|---|---|
| Showroom JWKS URL | URL | Stable (notify on change) |
| JWT audience (`aud`) value for this demo | string | Stable |
| JWT issuer (`iss`) value | URL | Stable |
| `X-Demo-Callback-Secret` shared secret | string | At least annually |
| `X-Azure-FDID` Front Door identifier | GUID | On Front Door replacement |
| Usage-callback path and payload schema | URL + schema doc | On breaking change |
| Group Object IDs the demo app must authorise | list of GUIDs | On org change |
| Showroom origin URLs for CORS allow-list | list of URLs | Stable |
| Test-tenant credentials for dev validation | scoped credentials | Per test cycle |
| Showroom platform on-call contact rota | name, email, phone | Before Phase 1 go-live |


## Point of Contact with the Wider DevOps Function

The Showroom platform depends on infrastructure owned by the wider PwC DevOps
function. Coordinate the items below before beginning either phase.


### What You Request from the Wider DevOps Function

| Action required | Timing |
|---|---|
| Entra tenant admin creates `app-pwc-showroom` App Registration | Before Phase 1 provisioning |
| Entra admin grants `GroupMember.Read.All` admin consent | Before Phase 1 provisioning |
| Entra admin provisions `FINCRIME_GROUP_OID` security group | Before Phase 1 go-live |
| DNS subdomain delegation for `showroom.pwc.example` and `admin.showroom.pwc.example` | Before Phase 2 Front Door setup |
| DNS TXT record for DigiCert certificate domain validation | Before Phase 2 Front Door setup |
| CAA record authorising DigiCert in the DNS zone | Before Phase 2 Front Door setup |
| Budget alert thresholds and FinOps tags agreed for the Showroom resource group | Before any provisioning |
| Log Analytics parent workspace or retention policy confirmation | Before Phase 1 provisioning |


### What You Provide to the Wider DevOps Function

| Artefact | Timing |
|---|---|
| Resource group naming (`rg-pwc-showroom-<env>-<region>`) and tag values | At provisioning start |
| List of Managed Identity principal IDs needing ACR pull access | Before first image push |
| List of Managed Identity principal IDs needing Key Vault access | Before first deployment |
| Estimated Cosmos DB throughput and storage for Phase 2 | Before Phase 2 provisioning |
| Data-classification label for external user identity log stream | Before Phase 2 go-live |


## Onboarding Sequence

Follow these steps in order. Phase 2 must not begin before Phase 1 is
validated end-to-end.

1. Read `showroom/phase1/devops-runbook.md` in full. Identify decisions that
   need Entra tenant admin involvement or DNS changes (both require lead time).
2. Submit the §5.1 requests to the wider DevOps function for Phase 1 items.
3. Provision the resource group, Key Vault, ACR, and Log Analytics workspace.
4. Create the App Registration, enable the groups claim, store the client
   secret in Key Vault.
5. Build the BFF container image and push to ACR.
6. Deploy the ACA environment + app and the Timer Function.
7. Deliver the Phase 1 handoff outputs (§4.2) to the first demo team.
8. Perform end-to-end validation with one demo (authentication, Layer-1 authz,
   Layer-2 tile filter, tile launch, health probe, correlation ID propagation).
9. Obtain Phase 1 go-live sign-off.
10. Read `showroom/phase2/devops-runbook.md` in full. Submit Phase 2 DNS and
    certificate requests to the wider DevOps function.
11. Provision Front Door, WAF, APIM, Cosmos DB, and external-IdP credentials.
12. Generate the RS256 signing key pair, publish the JWKS endpoint, and
    deliver Phase 2 handoff outputs (§4.2) to each demo team.
13. Perform end-to-end validation with an external test user through the JWT
    hand-off, usage callback, and Front Door header enforcement.
14. Obtain Phase 2 go-live sign-off.

\newpage

## Pre-flight Readiness Summary

Use this table as a final check before requesting go-live sign-off from
the wider DevOps function. Every row must be ticked.

### Phase 1 readiness

| Activity | Done |
|---|---|
| App Registration `app-pwc-showroom` created as Web (confidential client) | |
| Redirect URIs registered (ACA FQDN + localhost) | |
| Groups claim enabled; GroupMember.Read.All admin-consented | |
| Client secret stored in Key Vault, retrieved via Managed Identity | |
| OIDC Authorization Code + PKCE implemented in BFF; tokens not in browser | |
| Layer-1 authz: FINCRIME_GROUP_OID checked on every request | |
| Layer-2 authz: demo-map.json loaded; tiles filtered per user oid/groups | |
| ACA environment + app deployed; external HTTPS ingress on port 3000 | |
| Scale configured (min 0, max 5); cold-start Timer Function deployed | |
| ACR provisioned; Managed Identity image pull working | |
| Key Vault provisioned; Managed Identity secret access verified | |
| Log Analytics workspace provisioned; ACA stdout/stderr flowing | |
| `/api/health` returns HTTP 200 unauthenticated within 5 s | |
| Correlation IDs injected on all outbound BFF requests | |
| Phase 1 handoff outputs delivered to first demo team | |
| demo-map.json schema documented and shared with demo teams | |
| On-call rota published to wider DevOps function and demo team leads | |

### Phase 2 readiness (in addition to all Phase 1 rows)

| Activity | Done |
|---|---|
| Google OAuth and Microsoft consumer OIDC configured and tested | |
| External-IdP client credentials stored in Key Vault | |
| RS256 signing key pair generated; private key in Key Vault | |
| JWKS endpoint published and publicly accessible without auth | |
| Two-key JWKS maintained; rotation procedure documented | |
| JWTs issued with all mandatory claims (iss, aud, sub, email, exp, nbf) | |
| Front Door (Standard) + WAF (Prevention, OWASP CRS 3.2) deployed | |
| Custom domains + DigiCert ManagedCertificate active; TLS 1.2 minimum | |
| X-Azure-FDID ACA ingress restriction enforced; direct-origin traffic blocked | |
| APIM deployed with validate-jwt policy for both external and internal paths | |
| Rate-limiting per-session-type configured at APIM | |
| Usage-callback POST endpoint implemented; X-Demo-Callback-Secret validated | |
| Cosmos DB provisioned; allow-list and callback storage working | |
| Per-demo callback secret generated and delivered via approved channel | |
| GDPR log stream separated; data-protection sign-off obtained | |
| Phase 2 handoff outputs (JWKS URL, aud, iss, X-Azure-FDID, callback schema, test creds) delivered to all demo teams | |
| Alerts configured for JWKS health, JWT-failure rate, callback rejection rate | |
