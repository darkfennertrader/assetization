---
title: "Assetization: Showroom Phase 2 — DevOps Infrastructure Runbook (Delta)"
---

## Prerequisite

This document is a **delta on top of the Phase 1 runbook**
(`showroom/phase1/devops-runbook.md`, 2026-07-07). Everything described there
remains in force unless a section below is explicitly marked **REPLACES**. Read
Phase 1 first; this document only describes what changes.

## Scope of Phase 2

Phase 1 delivered a showroom for **internal PwC employees** authenticated via
PwC Entra ID. Phase 2 extends the same platform to serve **both audiences**
simultaneously:

- **Internal PwC employees** (unchanged path) — sign in via PwC Entra ID at
  `admin.showroom.pwc.example`. Presenter and admin functions live here.
- **External prospects** (new path) — sign in via Google OAuth or Microsoft
  consumer OAuth at `showroom.pwc.example`. Prospect-facing catalog and
  demo-launch live here.

The two audiences share the same ACA showroom container, Key Vault, Cosmos DB,
App Insights, and ACR. They are separated by **subdomain routing** enforced at
the Front Door layer: the external prospect subdomain (`showroom.pwc.example`)
accepts only Google/Microsoft-consumer tokens; the admin subdomain
(`admin.showroom.pwc.example`) accepts only PwC Entra ID tokens.

## §1 — Naming convention

No change from Phase 1. New resource-type tokens used in this phase:

| Token | Resource type |
|---|---|
| `afd` | Azure Front Door profile |
| `waf` | WAF policy (linked to Front Door) |
| `cosmos` | Azure Cosmos DB account |
| `appi` | Application Insights component |

Full pattern: `<type>-pwc-showroom-<env>-<region>`.

## §2 — Azure resources

### §2.1 Shared services — no change

The shared Container Registry (`crpwcshowroom<region>`) is unchanged.

### §2.2 Showroom platform (per environment) — delta

The following resources are **added** to each environment resource group
(`rg-pwc-showroom-<env>-<region>`). All Phase 1 resources remain.

#### New resources

| Resource | Name pattern | Notes |
|---|---|---|
| Front Door profile | `afd-pwc-showroom-<e>-<r>` | Standard tier. Two origin groups: `showroom.pwc.example` and `admin.showroom.pwc.example`, both pointing at the ACA showroom-app over HTTPS (see origin-protection note below). No Private Link or VNet in Phase 2. |
| WAF policy | `waf-pwc-showroom-<e>-<r>` | Prevention mode, OWASP CRS 3.2, bot-manager ruleset. Attached to the Front Door profile. |
| Cosmos DB account | `cosmos-pwc-showroom-<e>-<r>` | Serverless capacity mode. Three containers: `users`, `connection_events`, `demo_visits` (see §10). Geo-redundancy and multi-region writes: off in Phase 2. Soft-delete (PITR): 7 days. |
| Application Insights | `appi-pwc-showroom-<e>-<r>` | Workspace-based, linked to `log-pwc-showroom-<e>-<r>` (Phase 1). Receives three custom events only: `ProspectLoggedIn`, `DemoOpened`, `UsageReported`. Sampling: none (low volume). Data cap: 1 GB/day. Retention: 31 days (default free window). |
| DNS records | `showroom.pwc.example`, `admin.showroom.pwc.example` | CNAME to Front Door endpoint. TLS certificates managed by Front Door (auto-renewed). |

#### Origin protection (Front Door Standard hardening)

Because Front Door Standard cannot use Private Link, the ACA origin is protected
by two software-layer controls that together prevent direct access to the raw ACA
FQDN:

1. **ACA ingress IP allowlist** — the ACA app's ingress rule accepts source IPs
   only from the `AzureFrontDoor.Backend` service tag. Traffic arriving from any
   other IP (including a developer's machine) is dropped at the network layer.
2. **Front Door ID header check** — the showroom BFF middleware reads the
   `X-Azure-FDID` request header and returns `403 Forbidden` if the value does
   not match the `FRONT_DOOR_ID` environment variable (the provisioned Front Door
   instance GUID). Every request forwarded by Front Door carries this header with
   the correct GUID; requests that bypass Front Door do not.

The DevOps engineer must configure item (1) on the ACA environment ingress and
set `FRONT_DOOR_ID` (see §3.4) to the GUID shown in the Azure Portal under the
Front Door profile's **Overview** blade. Refer to §11.5 for the complete
origin-protection runbook.

#### ACA showroom-app — changed settings

The existing ACA app (`ca-pwc-showroom-<env>-<region>`) gains:

- **Custom ingress hostname**: `showroom.pwc.example` (external) and
  `admin.showroom.pwc.example` (internal admin). The ACA-assigned default FQDN
  remains active as a fallback for the warmer function.
- **New Managed Identity role assignments** (in addition to Phase 1):
  - `Cosmos DB Built-in Data Contributor` scoped to
    `cosmos-pwc-showroom-<env>-<region>` — allows the BFF to read/write all
    three Cosmos containers.
  - `Monitoring Metrics Publisher` scoped to `appi-pwc-showroom-<env>-<region>`
    — allows the BFF to push custom events to App Insights.

### §2.3 Demo apps — scope boundary

**REPLACES §2.3 of Phase 1** for the external-prospect authentication path.

For external prospects the showroom mints a **signed handoff JWT** and the demo
app validates it. The demo app no longer needs a PwC Entra ID App Registration
or a group-claim check on the external-prospect code path.

The internal Entra SSO path (Phase 1 §3.2) **remains in force for internal
employees** accessing demos via `admin.showroom.pwc.example`.


## §2.4 — DNS and custom-domain provisioning (new)

**Owner:** DevOps engineer. This is a one-time activity per environment,
performed before the showroom is opened to external prospects. Domain
registration of the parent zone is the responsibility of PwC's
domain-management / IT team and is out of scope for this runbook.

**Steps:**

1. **Create an Azure DNS zone** in the shared resource group:

   ```bash
   az network dns zone create \
     --resource-group rg-pwc-shared-<region> \
     --name <domain>
   ```

   Substitute `<domain>` with the parent domain name allocated by PwC
   (e.g. `pwc.example`).

2. **Delegate NS records at the registrar.** After creation, Azure assigns
   four nameservers. Retrieve them:

   ```bash
   az network dns zone show \
     --resource-group rg-pwc-shared-<region> \
     --name <domain> \
     --query nameServers -o tsv
   ```

   Provide these four nameserver names to PwC's domain-management team.
   They create the NS records at the registrar delegating the zone to Azure.
   Allow 15-60 minutes for propagation.

3. **Create CNAME records** for the two showroom subdomains, both pointing
   at the Front Door endpoint hostname
   (`afd-pwc-showroom-<env>-<region>.azurefd.net`):

   ```bash
   FD_HOST="afd-pwc-showroom-<env>-<region>.azurefd.net"

   az network dns record-set cname set-record \
     --resource-group rg-pwc-shared-<region> \
     --zone-name <domain> \
     --record-set-name showroom \
     --cname "$FD_HOST"

   az network dns record-set cname set-record \
     --resource-group rg-pwc-shared-<region> \
     --zone-name <domain> \
     --record-set-name admin.showroom \
     --cname "$FD_HOST"
   ```

4. **Add both custom domains to the Front Door profile.** For each domain,
   Front Door emits a domain-validation TXT record. Create it in the DNS
   zone before Front Door can issue the TLS certificate:

   ```bash
   # Example for showroom.<domain>
   az afd custom-domain create \
     --profile-name afd-pwc-showroom-<env>-<region> \
     --resource-group rg-pwc-showroom-<env>-<region> \
     --custom-domain-name showroom-external \
     --host-name showroom.<domain> \
     --certificate-type ManagedCertificate \
     --minimum-tls-version TLS12
   ```

   Retrieve the validation token:

   ```bash
   az afd custom-domain show \
     --profile-name afd-pwc-showroom-<env>-<region> \
     --resource-group rg-pwc-showroom-<env>-<region> \
     --custom-domain-name showroom-external \
     --query validationProperties
   ```

   Create the TXT record returned by the command above:

   ```bash
   az network dns record-set txt add-record \
     --resource-group rg-pwc-shared-<region> \
     --zone-name <domain> \
     --record-set-name _dnsauth.showroom \
     --value "<validation-token>"
   ```

   Repeat for `admin.showroom.<domain>` (custom-domain-name:
   `showroom-admin`).

5. **Wait for TLS certificate issuance.** Front Door automatically
   requests a managed certificate from DigiCert once the TXT record
   propagates. This takes 5-15 minutes. Monitor status:

   ```bash
   az afd custom-domain show \
     --profile-name afd-pwc-showroom-<env>-<region> \
     --resource-group rg-pwc-showroom-<env>-<region> \
     --custom-domain-name showroom-external \
     --query domainValidationState
   ```

   The value transitions from `Pending` to `Approved` to `Issuing` to
   `Approved`. No manual certificate management is required; Front Door
   auto-renews before expiry.

6. **Bind each custom domain to its Front Door route:**
   - `showroom.<domain>` bound to the external-prospect route.
   - `admin.showroom.<domain>` bound to the admin route.

7. **Update OAuth redirect URIs** in both provider consoles (§3.1a and
   §3.1b) to use the confirmed FQDNs. Remove any temporary ACA-FQDN URIs
   used during development.

**Verification checklist (before handing off to the showroom developer):**

- `[ ]` `dig showroom.<domain>` returns the Front Door CNAME target.
- `[ ]` `dig admin.showroom.<domain>` returns the Front Door CNAME target.
- `[ ]` HTTPS `GET showroom.<domain>/api/health` returns `200 OK`.
- `[ ]` HTTPS `GET admin.showroom.<domain>/api/health` returns `200 OK`.
- `[ ]` TLS certificate is a DigiCert-issued managed cert, not self-signed.
- `[ ]` OAuth sign-in via Google and Microsoft completes without redirect
  URI mismatch error.

## §3 — Entra ID configuration

### §3.1 Showroom App Registration

No change. The existing `app-pwc-showroom` App Registration continues to serve
the internal admin path at `admin.showroom.pwc.example`.

One additional redirect URI must be registered under the **Web** platform:

```
https://admin.showroom.pwc.example/api/auth/callback/azure-ad
```

(Phase 1 registered the ACA default FQDN; Phase 2 adds the custom subdomain.)

### §3.1a — Google OAuth 2.0 client registration (new, one-time per environment)

**Prerequisite:** access to a PwC Google Cloud project. If none exists,
a Google Workspace or Cloud Identity admin must create one (one-off,
no ongoing cost for this use case).

**Steps:**

1. In Google Cloud Console, open the project and navigate to
   **APIs & Services** → **Enabled APIs**. Enable the
   **Google Identity Services** API if not already enabled.
2. Navigate to **APIs & Services** → **Credentials** →
   **Create Credentials** → **OAuth 2.0 Client ID**.
   Application type: **Web application**. Name: `pwc-showroom`.
3. Under **Authorized redirect URIs** add one URI per environment:
   - <https://showroom.pwc.example/api/auth/callback/google>
   - <https://showroom-dev.pwc.example/api/auth/callback/google>
4. Click **Create**. Copy the **Client ID** and **Client Secret**
   (shown once at creation).
5. Navigate to **APIs & Services** → **OAuth consent screen**.
   - User type: **External** (allows any Google account holder).
   - App name: `PwC AI Showroom`. Support email: DevOps contact.
   - Scopes: add `openid`, `email`, `profile`.
   - Publishing status: **In production** (so external users are not
     blocked by the "unverified app" warning).
6. Store values:
   - `Client ID` → `GOOGLE_CLIENT_ID` environment variable (§3.4).
   - `Client Secret` → Key Vault secret `google-oauth-client-secret`
     (§3.5).
7. Rotation: no fixed expiry imposed by Google. Rotate on a 12-month
   schedule or when the Console flags the credential as old. Procedure
   is the same as Phase 1 §3.5.

### §3.1b — Microsoft consumer OAuth client registration (new, one-time per environment)

This is a **second App Registration**, separate from the existing
`app-pwc-showroom` registration (which is for PwC Entra ID employees
only). It covers external prospects signing in with personal Microsoft
accounts.

**Steps:**

1. In the Azure Portal → **App registrations** → **New registration**.
   - Name: `app-pwc-showroom-consumer`.
   - Supported account types:
     **Accounts in any organizational directory and personal
     Microsoft accounts (e.g. Skype, Xbox)**.
   - Redirect URI: **Web** platform:
     <https://showroom.pwc.example/api/auth/callback/microsoft-consumer>
2. After creation, under **Authentication** add a second redirect URI
   for the dev environment:
   <https://showroom-dev.pwc.example/api/auth/callback/microsoft-consumer>
3. Under **API permissions** → **Add a permission** →
   **Microsoft Graph** → **Delegated permissions**. Add:
   `openid`, `email`, `profile`.
   Click **Grant admin consent for PwC** to pre-approve the scopes.
4. Under **Certificates & secrets** → **New client secret**.
   Expiry: 24 months (Azure maximum). Copy the secret value immediately
   (only visible at creation).
5. Store values:
   - **Application (client) ID** → `MICROSOFT_CLIENT_ID` env var
     (§3.4).
   - Client secret → Key Vault secret `microsoft-oauth-client-secret`
     (§3.5).
6. Rotation: every 24 months (Azure enforces the expiry). Procedure:
   create a new secret, update Key Vault, rotate the ACA revision.
   The old secret is valid until its own expiry, so rotation is
   zero-downtime.

**Important:** the `app-pwc-showroom-consumer` registration is
**PwC-owned infrastructure**, not a per-customer configuration.
No customer or prospect ever interacts with it. Each new external
prospect just authenticates against their own existing Microsoft
account.

### §3.2 Per-demo App Registration — REPLACES (external-prospect path)

**For the external-prospect path only:** demo apps do **not** need an Entra App
Registration for prospect sign-in. The showroom issues a signed JWT; the demo
app validates it using the showroom's public JWKS endpoint. See §7 for the full
on-boarding contract.

The Phase 1 App Registration and group-claim requirement remain in force for
internal employees using the demo via the admin path.

### §3.3 Security group

No change for the internal admin path. External prospects are controlled by the
Cosmos DB allow-list (`users.status`) managed by the presenter via the admin
panel — there is no security group involved.

### §3.4 ACA app environment variables — delta

The following variables are added to the showroom ACA app revision. No secret
values are stored in environment variables; all secrets are retrieved from Key
Vault via Managed Identity at startup.

| Variable | Value type | Description |
|---|---|---|
| `COSMOS_ENDPOINT` | URL | <https://cosmos-pwc-showroom-env-region.documents.azure.com:443/> (substitute env and region tokens) |
| `COSMOS_DB` | String | `showroom` (Cosmos DB database name) |
| `GOOGLE_CLIENT_ID` | GUID / string | Google OAuth 2.0 client ID (non-secret). Obtained from Google Cloud Console. |
| `MICROSOFT_CLIENT_ID` | GUID | Microsoft consumer OAuth app client ID (non-secret). |
| `APPINSIGHTS_CONNECTION_STRING` | String | App Insights connection string (not instrumentation key). Copied from the `appi-pwc-showroom-<e>-<r>` resource. Non-secret. |
| `PROSPECT_ORIGIN` | URL | Origin value for the external prospect subdomain — set as a plain environment variable. |
| `ADMIN_ORIGIN` | URL | Origin value for the admin subdomain — set as a plain environment variable. |
| `AUTH_SECRET_NAME` | String | `auth-secret` (Key Vault secret name for `AUTH_SECRET`) |
| `GOOGLE_SECRET_NAME` | String | `google-oauth-client-secret` |
| `MICROSOFT_SECRET_NAME` | String | `ms-oauth-client-secret` |
| `HANDOFF_KEY_NAME` | String | `demo-handoff-key` (Key Vault **Key** name, not a Secret — the BFF calls the Key Vault Sign API) |
| `FRONT_DOOR_ID` | GUID | Front Door instance GUID. The BFF middleware compares this to the `X-Azure-FDID` header on every incoming request and returns `403 Forbidden` if the values do not match. Copy from the Front Door profile Overview blade. |
| `DEMO_CALLBACK_SECRET_NAME` | String | `demo-callback-shared-secret` |

Phase 1 variables (`AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `FINCRIME_GROUP_OID`,
`KEY_VAULT_URL`, `CLIENT_SECRET_NAME`) remain unchanged.

### §3.5 Key Vault secrets — delta

The following secrets are added to `kv-pwc-showroom-<env>-<region>`:

| Secret name | Content | Rotation |
|---|---|---|
| `auth-secret` | 32-byte random hex string; used by NextAuth to encrypt session cookies. | Rotate by generating a new value, updating Key Vault, restarting the ACA revision. All existing sessions are invalidated (users must re-authenticate). |
| `google-oauth-client-secret` | Google OAuth 2.0 client secret. Obtained from Google Cloud Console. | No fixed expiry; rotate when the Google Console UI flags the credential as old or on a 12-month schedule. Same procedure as Phase 1 §3.5. |
| `ms-oauth-client-secret` | Microsoft consumer OAuth client secret. Generated in the Azure Portal App Registration (separate from the PwC Entra tenant — this is a personal-account app in the Microsoft identity platform). | Same 12-month expiry and rotation procedure as Phase 1 §3.5. |
| `demo-callback-shared-secret` | 32-byte random hex string; the `X-Demo-Callback-Secret` header value shared with each demo app. | Rotate by: (1) generating a new value; (2) updating Key Vault; (3) distributing the new value to every demo team's Key Vault; (4) restarting the showroom ACA app and all demo ACA apps. |

The Phase 1 `showroom-client-secret` remains.

## §4 — CI/CD pipelines

No new pipeline. The existing showroom pipeline (Phase 1 §4.1) is extended:

- **Schema-init step** (runs once, idempotent): after image push, a pipeline
  task runs a one-shot container that calls the Cosmos DB data-plane API to
  create the three containers (`users`, `connection_events`, `demo_visits`) with
  their index policies if they do not yet exist. The task uses the service
  connection's Managed Identity, which must be granted `Cosmos DB Built-in Data
  Contributor` on the Cosmos account. Safe to re-run — Cosmos returns HTTP 200
  if the container already exists.
- **Front Door purge step** (optional, when `demo-map.json` changes): the
  pipeline can call `az afd endpoint purge` to invalidate the Front Door cache
  for the catalog API response.

## §5 — Team roles

No change from Phase 1. Cosmos DB and App Insights inherit resource-group RBAC.
The `Cosmos DB Built-in Data Contributor` role assignment (full name:
`Cosmos DB Built-in Data Contributor`, definition ID
`00000000-0000-0000-0000-000000000002`) for the showroom ACA app's Managed
Identity is provisioned by the DevOps engineer during initial setup.

**OAuth client registrations (§3.1a and §3.1b) are PwC DevOps responsibilities.**
They are one-time-per-environment setup steps. Customers and prospects never
configure, touch, or even know about these registrations. A prospect signs in
with their own existing Google or Microsoft account; the PwC registration is
transparent to them.

**DNS and custom-domain provisioning (§2.4) is a DevOps engineer responsibility.**
All seven steps in §2.4 — DNS zone creation, NS delegation, CNAME records, Front
Door custom-domain binding, TLS certificate validation, route binding, and OAuth
redirect-URI updates — are performed by the DevOps engineer before the showroom
is opened to external prospects.

**Reporting workbook (§14) responsibilities:**

- **Full-Stack Developer** — builds and maintains the workbook.
  Writes the SQL queries and defines the chart panels. Executes on the dev
  environment first, then clones the workbook to prod.
- **DevOps Engineer** — provisions Cosmos DB Reader RBAC for presenter
  accounts, pins the workbook to the Azure Dashboard, and adds the shortcut
  URL to `showroom/phase2/README.md`.

## §6 — Handoff outputs — required by the showroom developer

In addition to the Phase 1 outputs, the Full-Stack Developer needs:

- Front Door **endpoint hostname** (e.g. `afd-pwc-showroom-dev-xxx.azurefd.net`)
  and the two **custom FQDNs** once DNS is validated.
- Cosmos DB **account endpoint** and **database name** (`showroom`).
- App Insights **connection string** (non-secret; can be shared openly).
- **JWKS URL**: <https://showroom.pwc.example/.well-known/jwks.json> — published
  by the showroom app; demo teams consume this.
- New Key Vault **secret names** listed in §3.5.
- Google Cloud Console project name (for the developer to set up the OAuth
  consent screen during development).

Pre-handoff verification checklist (in addition to Phase 1):

- `[ ]` DNS and custom domains provisioned and verified per §2.4 checklist.
- `[ ]` `GET` <https://showroom.pwc.example/api/health> returns `200 OK`.
- `[ ]` `GET` <https://admin.showroom.pwc.example/api/health> returns `200 OK`.
- `[ ]` A Google test account in the Cosmos `users` allow-list can sign in,
  see the catalog, and launch a demo.
- `[ ]` A Google test account **not** in the allow-list receives the
  access-denied page.
- `[ ]` A PwC Entra test account reaches `admin.showroom.pwc.example` and is
  not offered Google/Microsoft consumer login.
- `[ ]` `GET` <https://showroom.pwc.example/.well-known/jwks.json> returns a
  valid JWKS JSON document.
- `[ ]` App Insights receives a `ProspectLoggedIn` event within 60 s of the
  test sign-in.

## §7 — Handoff outputs — required by demo teams joining the external-prospect catalog

**REPLACES §7 of Phase 1** for the external-prospect code path.

The showroom team provides the demo team with:

- **JWKS URL**: <https://showroom.pwc.example/.well-known/jwks.json>.
- **Issuer claim** (`iss`): the exact value <https://showroom.pwc.example> — demo apps must check this claim precisely.
- **Audience claim** (`aud`): the demo's `demoId` string (agreed at on-boarding,
  e.g. `overwatch`). Only tokens carrying this exact `aud` are valid at that
  demo.
- **Demo-callback shared secret**: the value of `demo-callback-shared-secret`
  from Key Vault. Delivered to the demo team via a time-limited Key Vault
  secret-sharing URL or equivalent secure channel. Never via email, Teams, or
  any repository. The demo team stores the received value directly in their own
  Key Vault secret.
- **Callback URL** the demo should POST to:
  <https://showroom.pwc.example/api/internal/demo-usage>.

The demo team must implement:

1. Accept `POST /` with `token=<JWT>` in the POST body.
2. Fetch the JWKS document from the JWKS URL; cache for 24 hours keyed by
   `kid`; re-fetch on signature-verification failure.
3. Verify signature (RSA-256), `iss`, `aud` (must equal the demo's own
   `demoId`), and `exp`.
4. On success: create a session cookie from `sub` (prospect email) and
   `visitId`; redirect to `GET /`.
5. On failure: respond `401 Unauthorized`.
6. After each usage session: `POST /api/internal/demo-usage` with
   `X-Demo-Callback-Secret` header and the JSON body described in
   `sso-handoff-explained.md`.

Pre-handoff verification (replaces Phase 1 group-claim check):

- `[ ]` Demo app accepts a test handoff JWT (minted manually with a valid TTL,
  correct `aud`, signed with the current Key Vault key) and creates a session.
- `[ ]` Demo app rejects a JWT with an incorrect `aud`.
- `[ ]` Demo app rejects an expired JWT (TTL past).
- `[ ]` Demo app POSTs a usage callback to the showroom after the test session
  and receives `200 OK`.
- `[ ]` Demo app exposes an unauthenticated health endpoint
  (`GET /api/health`, `200 OK`) for the warmer function.

The Phase 1 §7 Entra group-claim check still applies for demo apps reached via
the internal admin path (`admin.showroom.pwc.example`).

## §8 — Cold-start mitigation — keep-warm ping

No change to the warmer function design. Update the targets table:

| Target | URL | Notes |
|---|---|---|
| Showroom (external) | <https://showroom.pwc.example/api/health> | Replaces the ACA default FQDN from Phase 1 once Front Door and custom domain are active. |
| Showroom (admin) | <https://admin.showroom.pwc.example/api/health> | New target. Same container; separate hostname. |
| Overwatch | replace with real FQDN — e.g. `overwatch.aca.io/api/health` | Unchanged from Phase 1. Full example: overwatch.azurecontainerapps.io/api/health |
| UBO | replace with real FQDN — e.g. `ubo.aca.io/api/health` | Unchanged from Phase 1. Full example: ubo.azurecontainerapps.io/api/health |

## §9 — Demos in scope

No change to the demo list. The Phase 1 table gains one column:

| Demo | launchUrl | Handoff JWT verified | Internal Entra path active |
|---|---|---|---|
| Overwatch | `xxx (to be defined)` | `[ ]` | `[ ]` |
| UBO | `xxx (to be defined)` | `[ ]` | `[ ]` |

## §10 — Cosmos DB operational model (new)

### Containers and index policy

| Container | Partition key | Purpose |
|---|---|---|
| `users` | `/email` | Allow-list of external prospects. Fields: `email`, `status` (`active`/`banned`/`quota_exhausted`), `allowedDemoIds[]`, `messageQuotaRemaining`, `totalConnections`, `lastSeenAt`. |
| `connection_events` | `/email` | One document per sign-in. Fields: `email`, `connectionAt`, `ip`, `userAgent`. Append-only; never updated. |
| `demo_visits` | `/email` | One document per demo-launch. Fields: `visitId`, `email`, `demoId`, `openedAt`, `messageCount`, `closedAt`. `messageCount` and `closedAt` are back-filled by the usage callback. |

Default index policy (all paths) is sufficient for Phase 2. If query latency
on `SELECT * FROM c WHERE c.email = @e` degrades, add a single-field index on
`/email` for each container.

### Capacity

Serverless mode: no provisioned throughput. Serverless does not support
multi-region writes — acceptable for the current scale.

### Backup and recovery

Continuous backup is enabled by default in Serverless mode (7-day PITR
window). No action required. For a data-loss event: restore via the Azure
Portal "Restore account" flow to a new account; update `COSMOS_ENDPOINT`
in the ACA revision environment; restart.

## §11 — Front Door and WAF operational model (new)

### WAF ruleset

OWASP CRS 3.2 in **Prevention** mode. Bot-manager ruleset enabled. No custom
geographic restrictions in Phase 2. Review ruleset version at each Phase
upgrade.

### Health probes

Front Door sends HTTP HEAD to the health endpoint
(`/api/health`) every 30 seconds from three PoPs. If the origin fails two
consecutive probes it is marked degraded and Front Door holds traffic until
recovery. The health endpoint must return `200 OK` without authentication.

### TLS and certificate renewal

TLS certificates for `showroom.pwc.example` and `admin.showroom.pwc.example`
are provisioned and auto-renewed by Front Door (no manual certificate
management). The CNAME records must be in place before certificate issuance;
do not remove them.

### Cache

Front Door caches the `/.well-known/jwks.json` response (short TTL — set
`Cache-Control: max-age=900` on the response). Run `az afd endpoint purge`
after a key rotation to clear the JWKS cache across all PoPs immediately.

### §11.5 — Origin protection contract

This section collects every enforcement rule that prevents the raw ACA FQDN
from being used as a bypass route around Front Door and the WAF.

**Rule 1 — ACA ingress IP allowlist (Azure network layer)**

In the ACA environment ingress configuration, add an IP restriction rule:

- **Action:** Allow
- **IP range / service tag:** `AzureFrontDoor.Backend`
- **Default action (all other sources):** Deny

This is set on the ACA **environment**, not on the individual app revision.
Microsoft publishes the `AzureFrontDoor.Backend` IP ranges and updates them
automatically; no manual maintenance is required.

**Rule 2 — BFF middleware FDID header check (application layer)**

The showroom BFF must implement a middleware that runs on every request before
any routing or authentication logic:

- Read the `X-Azure-FDID` request header.
- Compare it with the `FRONT_DOOR_ID` environment variable using a constant-time
  string comparison.
- If the header is absent or the values differ: return `403 Forbidden`
  immediately. Log the source IP and the received header value for auditing.
- If the values match: pass the request to the next middleware.

The Front Door instance GUID is visible in the Azure Portal under
`afd-pwc-showroom-<env>-<region>` → **Overview**. Copy it into the
`FRONT_DOOR_ID` environment variable on the ACA revision (see §3.4).

**The warmer function exception**

The keep-warm timer function (Phase 1 §8) calls the ACA health endpoint on the
raw ACA FQDN, not through Front Door. Its source IP is not in the
`AzureFrontDoor.Backend` range. Two options:

- Option A (recommended): route the warmer through Front Door too — update the
  warmer's target URLs to <https://showroom.pwc.example/api/health> and
  <https://admin.showroom.pwc.example/api/health>. The warmer then carries a
  valid `X-Azure-FDID` header automatically.
- Option B (fallback): add the warmer function's outbound IP to the ACA ingress
  allowlist as a second rule and add an exception for the warmer's client IP in
  the FDID middleware (check `User-Agent` or a shared internal header).

Option A is simpler and eliminates a separate allowlist entry to maintain.


## §12 — App Insights operational model (new)

### What is collected

Three backend custom events only: `ProspectLoggedIn`, `DemoOpened`,
`UsageReported`. No browser SDK, no page-view telemetry. Email is always
SHA-256-hashed in the payload; raw email is never sent to App Insights.

### Viewing data

Open `appi-pwc-showroom-<env>-<region>` in the Azure Portal. The **Usage**
blade shows pre-built funnels for custom events. The **Logs** blade accepts
KQL queries against the `customEvents` table. The **Workbooks** blade hosts
the operational usage report (to be built alongside the showroom app).

### Alert rules (recommended minimum)

- `ProspectLoggedIn` count drops to zero for 24 hours during business days.
- `UsageReported` average `messageCount` exceeds 200 (potential quota abuse).

Configure in the App Insights **Alerts** blade; route to an email action group
containing the Solution Architect and the DevOps engineer.

## §13 — Handoff-key operational model (new)

### Key generation

The demo-handoff signing key is generated **inside Key Vault** using Key
Vault's native RSA key-generation (RSA 2048). The private key material never
leaves Key Vault; the showroom BFF calls the Key Vault Sign API and Key Vault
performs the RSA operation internally.

The DevOps engineer creates the key:

```bash
az keyvault key create \
  --vault-name kv-pwc-showroom-<env>-<region> \
  --name demo-handoff-key \
  --kty RSA --size 2048 \
  --ops sign verify
```

The `kid` used in JWTs is derived from the Key Vault key version string
(e.g. `4a7b3c9d...`). The showroom app reads the current key version at
startup and refreshes it every 15 minutes.

### JWKS publication

The showroom app's `/api/health` and `/.well-known/jwks.json` handlers derive
the public projection of the key from the public components returned by the Key
Vault Get Key API. The private key material never appears in the JWKS document.

### Key rotation procedure

Key rotation is zero-downtime because the JWKS endpoint can serve multiple
key versions simultaneously:

1. Generate a new key version in Key Vault:
   `az keyvault key rotate --vault-name ... --name demo-handoff-key`.
2. The showroom app's 15-minute cache refresh will pick up the new version
   automatically. During the overlap window both the old and new public keys
   appear in the JWKS document.
3. Demo apps hold the JWKS for 24 hours. Tokens signed with the new key are
   valid immediately. Tokens signed with the old key remain valid until they
   expire (60-second TTL) — in practice the overlap window is irrelevant.
4. After 48 hours (one full JWKS cache cycle for all demo apps plus a safety
   margin), disable the old key version in Key Vault.
5. Purge the Front Door JWKS cache: `az afd endpoint purge ...`.

No code changes, no container image rebuild, and no demo-team action are
required for a key rotation.

**Recommended annual rotation cadence:** schedule a full key rotation at least
once per year even in the absence of a suspected compromise. Add a calendar
reminder at provisioning time. The 48-hour overlap window (step 4 above) means
the rotation causes no interruption to live sessions; communicate the planned
date to all demo team leads at least one week in advance so they can verify
their JWKS cache logic.

### Revocation

If the private key is compromised: disable the key version immediately in Key
Vault. The showroom app will fail to sign new JWTs until a new version is
created (step 1 above). In-flight tokens are 60 seconds TTL; after 60 seconds
no valid tokens remain in circulation.

## §14 — Reporting workbook (new)

### Purpose

The reporting workbook is the primary **business reporting surface** for the
showroom. It shows PwC presenters and managers which prospects have connected,
which demos are popular, and how quota is being consumed — directly from Cosmos
DB, with no hashing and no manual SQL required.

App Insights is **not** used for business reporting. It receives only
operational telemetry (three hashed-email custom events) and is the surface for
alerting on application health. The Cosmos DB containers are the single source
of truth for prospect-level reporting because they hold plain email addresses
and the full usage record.

### Workbook name and location

| Property | Value |
|---|---|
| Resource name | `wb-pwc-showroom-usage` |
| Resource group | `rg-pwc-showroom-<e>-<r>` |
| Azure Monitor Workbooks type | **Standard workbook** (no gallery required) |
| Data source | Cosmos DB `showroom` database |

### Panels

The Full-Stack Developer builds and maintains these three panels.

**Panel 1 — Prospect summary table**

Data source: `users` container.

Columns: email, displayName, status, lastSeenAt, totalConnections,
messageQuotaRemaining, allowedDemoIds.

Sort: `lastSeenAt` descending. Filters: status dropdown (all / active /
banned / quota exhausted), date-range picker for `lastSeenAt`.

Sample query:

```sql
SELECT c.email, c.displayName, c.status,
       c.lastSeenAt, c.totalConnections,
       c.messageQuotaRemaining,
       ARRAY_LENGTH(c.allowedDemoIds) AS demoCount
FROM c
ORDER BY c.lastSeenAt DESC
```

**Panel 2 — Sign-ins over time (time chart)**

Data source: `connection_events` container.

Chart: daily bar chart of sign-in count for the last 30 days.

Sample query (group by date prefix):

```sql
SELECT SUBSTRING(c.connectionAt, 0, 10) AS day,
       COUNT(1) AS signIns
FROM c
GROUP BY SUBSTRING(c.connectionAt, 0, 10)
```

**Panel 3 — Demo popularity (bar chart)**

Data source: `demo_visits` container.

Chart: horizontal bar chart, one bar per `demoId`, count of visits.

Sample query:

```sql
SELECT c.demoId, COUNT(1) AS visits
FROM c
GROUP BY c.demoId
```

### Access — RBAC

| Role | Resource | Assigned to |
|---|---|---|
| `CosmosDB Data Reader` | `cosmos-pwc-showroom-<e>-<r>` | Presenter accounts (email-based Entra assignment). Full role name: Cosmos DB Built-in Data Reader. |
| `Reader` | `rg-pwc-showroom-<e>-<r>` | Same presenters (needed to open the workbook resource in the Portal) |

**DevOps engineer action:** after build, run:

```bash
az cosmosdb sql role assignment create \
  --account-name cosmos-pwc-showroom-<env>-<region> \
  --resource-group rg-pwc-showroom-<env>-<region> \
  --role-definition-name "Cosmos DB Built-in Data Reader" \
  --scope "/" \
  --principal-id <presenter-object-id>
```

Repeat for each presenter who needs workbook access.

### Dashboard shortcut

Pin the workbook to the resource-group Azure Dashboard:

1. Open the workbook in the Portal.
2. Click **Pin** (top-right toolbar) → select the shared dashboard
   `dash-pwc-showroom-<env>`.
3. DevOps engineer adds the workbook URL to `showroom/phase2/README.md`
   under the **Quick links** section.

### Escalation path

If PwC managers later require scheduled email reports or joins to CRM/Salesforce
data, the Cosmos DB containers and the three SQL queries defined above are
directly compatible with the Power BI native Cosmos DB connector — no schema
changes would be required.
