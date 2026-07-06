---
title: "Showroom Phase 1 — DevOps Infrastructure Runbook"
---

# Showroom Phase 1 — DevOps Infrastructure Runbook

This document describes the target infrastructure state for the showroom platform in
phase 1. It is intentionally **app-agnostic**: the showroom itself has a fixed set of
Azure resources; each demo app that joins the catalog follows the generic per-demo
procedure described here. The demos currently in scope are listed in §9.

## 1. Azure resources

### 1.1 Showroom platform (fixed)

| Resource | Name | Notes |
|---|---|---|
| Resource group | `rg-pwc-showroom-dev-we` | West Europe; tags: `customer=pwc`, `workload=showroom`, `env=dev` |
| Subscription | WARNING: To be confirmed | Use existing shared subscription or request a dedicated one |
| Log Analytics workspace | `log-pwc-showroom-dev-we` | Linked to the ACA environment for automatic log forwarding |
| ACA environment | `cae-pwc-showroom-dev-we` | Consumption plan, West Europe, no VNet. Shared by the showroom and all demo ACA apps |
| ACA app — showroom | `ca-pwc-showroom-dev-we` | External HTTPS ingress, port 3000, scale-to-zero (min 0, max 5). Kept warm during business hours by `func-pwc-showroom-warmer-dev-we` — see §8. Pulls image from ACR via system-assigned Managed Identity. The IMDS endpoint (169.254.169.254) is accessible from the container by default on the Consumption plan, enabling `DefaultAzureCredential` to acquire MI tokens at runtime. |
| Container Registry | `crpwcshowroomdev` | Standard SKU; admin credentials disabled; ACR pull via Managed Identity for the showroom and all demo ACA apps. No hyphens — Azure registry name rule |
| Key Vault | `kv-pwc-showroom-dev-we` | Standard SKU, RBAC authorization mode (not access policies), soft-delete and purge-protection enabled. Holds the showroom and all demo App Registration client secrets, each as a named secret (e.g. `showroom-client-secret`, `overwatch-client-secret`). One shared vault — each ACA app's MI is granted `Key Vault Secrets User` scoped to its own secret only. |
| App Registration — showroom | `app-pwc-showroom-dev` | PwC Entra ID tenant, **Web (confidential client)**, groups claim enabled (Security Group OIDs). Region omitted — Entra is tenant-global |
| Security group | `FinCrime-Showroom` | WARNING: Use existing group or create new one; obtain the Object ID. Applied to the showroom App Registration and to every demo App Registration |
| Managed Identity | System-assigned on each ACA app | Every ACA app (showroom + all demos) must have: (1) `AcrPull` role on `crpwcshowroomdev`, and (2) `Key Vault Secrets User` role on `kv-pwc-showroom-dev-we` scoped to that app's own secret only. |

### 1.2 Per-demo resources (one set per demo in the catalog)

| Resource | Name pattern | Notes |
|---|---|---|
| ACA app — demo | `ca-pwc-<demo>-dev-we` | External HTTPS ingress on the demo's container port (confirm with demo team). Same ACA environment. Outbound internet as required by the demo. Scale-to-zero demo apps are kept warm by `func-pwc-showroom-warmer-dev-we` — see §8. Pulls image from the shared ACR via system-assigned Managed Identity |
| App Registration — demo | `app-pwc-<demo>-dev` | PwC Entra ID tenant, **Web (confidential client)**, groups claim enabled. Same `FinCrime-Showroom` group enforced in-app. Region omitted — Entra is tenant-global |
| Key Vault secret — demo | `<demo>-client-secret` in `kv-pwc-showroom-dev-we` | Holds the demo's App Registration client secret. RBAC `Key Vault Secrets User` assignment scoped to this secret, granted to the demo ACA app's system-assigned MI only. |

Replace `<demo>` with the lower-case workload name (e.g. `overwatch`, `ubo`).

## 2. Naming convention

All Azure resources in the assetization program follow the pattern:

```
<type>-<customer>-<workload>-<env>-<region>
```

| Token | Meaning | Phase 1 value |
|---|---|---|
| `type` | CAF-standard[^caf] resource-type abbreviation | `rg`, `cae`, `ca`, `log`, `kv`, ... |
| `customer` | Customer / tenant umbrella | `pwc` |
| `workload` | Solution inside the customer program | `showroom`, or the demo name |
| `env` | Environment | `dev` |
| `region` | 2-letter Azure region code | `we` (West Europe) |

Lowercase, hyphen-separated. For resource types that forbid hyphens (Container
Registry, Storage Account) drop the hyphens and keep the token order. If the
length cap is hit, truncate `customer` or drop `env` for globally-scoped
resources.

For Entra ID App Registrations, `region` is omitted — Entra is tenant-global.

Rationale: predictable names make cost analysis, RBAC scoping, and diagnostic
log filtering trivial — slice by customer, workload, or environment with a
single `startswith()` or tag filter.

[^caf]: **CAF** = Microsoft's **Cloud Adoption Framework**, published at
    [learn.microsoft.com/azure/cloud-adoption-framework/](https://learn.microsoft.com/azure/cloud-adoption-framework/).
    The runbook's `type` tokens come from CAF's
    [recommended abbreviations for Azure resource types](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-abbreviations)
    — the industry-standard prefix set (e.g. `rg`, `aks`, `cr`, `kv`, `st`,
    `vnet`, `nsg`) used by Bicep AVM and Terraform CAF modules.

## 3. Entra ID configuration

### 3.1 Showroom App Registration (`app-pwc-showroom-dev`)

Register the application in the PwC Entra ID tenant as a **Web (confidential
client)** application — not a Single-Page Application. This type is required
because the BFF performs the OAuth authorization-code exchange server-side,
using a client secret. The redirect URI must be registered under the **Web**
platform in the App Registration (not under SPA), pointing to the showroom
ACA FQDN callback route (`/api/auth/callback/azure-ad`). Add a second redirect
URI for local development (<http://localhost:3000/api/auth/callback/azure-ad>).
Enable the `groups` claim (Security Group Object IDs) in the ID token. Generate
a client secret (12-month expiry) and store it in the shared Key Vault under
the name `showroom-client-secret`. The raw value is **never** delivered to
the developer and **never** placed in the ACA app's environment variables; the
BFF retrieves it at container startup from Key Vault using its Managed Identity.

### 3.2 Per-demo App Registration (one per demo in the catalog)

For each demo being added to the showroom catalog, register a new application in
the PwC Entra ID tenant as a **Web (confidential client)** application. Add
the demo's ACA FQDN as the redirect URI under the **Web** platform (plus a
local development URI if the demo team requires it). Enable the `groups` claim.
The demo App Registration enforces the same `FinCrime-Showroom` group. Generate
a client secret (12-month expiry) and store it in the shared Key Vault under
the name `<demo>-client-secret`. Silent SSO works because both the showroom and
every demo app share the same Entra ID tenant — when the user arrives at a demo
after being redirected from the showroom, Entra already holds their session
cookie and issues the authorization code without re-prompting.

### 3.3 Security group

Identify or create the `FinCrime-Showroom` security group and add initial test
members (at minimum the Solution Architect, the Full-Stack Developer, and the
DevOps engineer). Note the group Object ID — it is needed in the showroom app and
in every demo app as the `FINCRIME_GROUP_OID` environment variable.

### 3.4 Group-claim caveats — verify before phase-1 sign-off

**Caveat 1 — Group overage limit.** Entra ID injects the `groups` array directly
into the ID token only when the user's total Entra group membership count is below
a threshold (roughly 150 for JWT). When a user is in more groups than this limit,
the token instead carries a `_claim_names` / `_claim_sources` reference; the
application must then call Microsoft Graph (`/me/memberOf` or `getMemberGroups`)
to resolve group membership at runtime. In a large corporate tenant such as PwC's,
typical users are members of many distribution lists and security groups, making
the overage scenario highly likely.

Mitigations to evaluate before delivering credentials to the demo team:

- Enable the **"Emit groups as role claims"** option on the App Registration and
  filter to only the `FinCrime-Showroom` group. This emits only that single group
  in the claim regardless of the user's other memberships and is immune to the
  overage limit.
- Alternatively, switch to **App Role assignments** (see Caveat 2 below) and
  assign the security group to an App Role — the `roles` claim is per-application
  and never suffers overage.

Action item for the DevOps engineer: create a test user account that is a member
of many Entra groups (simulating a typical PwC employee), authenticate against the
App Registration, decode the resulting ID token, and confirm that the
`FinCrime-Showroom` Object ID is present in the `groups` array. Do this before
releasing any handoff credentials to a demo team.

**Caveat 2 — `groups` claim vs `roles` claim (App Roles).** The current design
reads the raw `groups` claim from the ID token. This exposes all of the user's
Entra group Object IDs to any party that can inspect the token, which is not
application-scoped. Microsoft's best-practice guidance favours **App Role
assignments**: the App Registration defines named roles, the `FinCrime-Showroom`
group is assigned to one of those roles, and the app reads the `roles` claim —
which contains only roles defined for that specific application and is never
affected by the overage limit.

For phase 1 the `groups` approach stands (fastest to implement, centrally managed
via a single group). The trade-off is recorded here so the migration to `roles`
can be assessed at phase-2 planning. The code change in the middleware is
minimal — one environment variable and one claim-name string.

### 3.5 ACA app environment variables

Every ACA app (showroom and each demo) receives the following environment
variables on its revision. **No secret values are stored in environment
variables**; secrets are retrieved at runtime from Key Vault by the BFF.

| Variable | Value type | Description |
|---|---|---|
| `AZURE_TENANT_ID` | GUID | PwC Entra ID tenant identifier |
| `AZURE_CLIENT_ID` | GUID | The app's own App Registration client ID |
| `FINCRIME_GROUP_OID` | GUID | Object ID of the `FinCrime-Showroom` security group — used for the coarse group-membership check |
| `KEY_VAULT_URL` | URL | <https://kv-pwc-showroom-dev-we.vault.azure.net/> — same value for all apps |
| `CLIENT_SECRET_NAME` | String | Name of this app's secret in Key Vault, e.g. `showroom-client-secret` or `overwatch-client-secret` |

The BFF reads `KEY_VAULT_URL` and `CLIENT_SECRET_NAME` at startup, authenticates
to Key Vault using `DefaultAzureCredential` (which picks up the container's
system-assigned Managed Identity automatically), and holds the resolved secret
value in memory for the lifetime of the process.

### 3.6 Client secret rotation

1. Generate a new credential in the App Registration (leave the old one active).
2. Update the corresponding Key Vault secret to the new value (Azure creates a
   new version automatically; the previous version remains accessible during
   transition).
3. Restart the ACA revision:
   `az containerapp revision restart --name ca-pwc-<app>-dev-we --resource-group rg-pwc-showroom-dev-we --revision <revision-name>`
4. The BFF fetches the new secret from Key Vault on startup.
5. Monitor logs for 24 hours, then delete the old App Registration credential
   and, if required, expire the previous Key Vault secret version.

No code changes and no container image rebuild are required for a secret rotation.

## 4. CI/CD pipelines

Provision an Azure DevOps project and private Git repositories (names to be
confirmed with the Solution Architect and the Full-Stack Developer). Create a
service connection to the Azure subscription using **Workload Identity Federation**
(no client secret to rotate), scoped to the resource group.

### 4.1 Showroom pipeline

Triggers on every push to `main` of the showroom repository. Stage 1 builds the
showroom Docker image and pushes to ACR tagged with the build ID; stage 2 updates
`ca-pwc-showroom-dev-we` to run that image.

### 4.2 Per-demo pipeline (one per demo)

Each demo team owns and maintains its own pipeline. The pattern is identical to
the showroom pipeline: push to `main` → build Docker image → push to ACR →
update the demo's ACA app. Only the target ACA app name and image name differ.
The same Workload Identity Federation service connection and ACR are reused.

IaC choice (Bicep or Terraform) is left to the implementer — the Solution
Architect confirmed in the 2026-07-03 standup: *"use whatever you feel
comfortable with."*

No approval gates in phase 1.

## 5. Team roles on the Azure subscription

| Role | Azure RBAC |
|---|---|
| DevOps engineer | Owner (can create and assign resources) |
| Solution Architect | Contributor |
| Full-Stack Developer | Contributor |

Owner access confirmed in the 2026-07-03 standup. Contributor access for the
Solution Architect and the Full-Stack Developer to be granted by the DevOps
engineer once subscription access is confirmed.

## 6. Handoff outputs — required by the showroom developer

Before the Full-Stack Developer can start on the showroom:

- Showroom App Registration **Client ID** (Application ID)
- PwC Entra **Tenant ID**
- Key Vault **URL** (<https://kv-pwc-showroom-dev-we.vault.azure.net/>) and **secret name** (`showroom-client-secret`) — the BFF retrieves the client secret at runtime using its Managed Identity; the raw value never leaves Key Vault and is never transmitted to the developer
- `FinCrime-Showroom` security group **Object ID**
- Showroom ACA **FQDN**, for example:
  ```
  ca-pwc-showroom-dev-we.<hash>.westeurope.azurecontainerapps.io
  ```
- Container Registry **login server**, for example:
  `crpwcshowroomdev.azurecr.io`
- Azure DevOps **showroom repository clone URL**
- **Subscription ID** and **resource group name**
- `[ ]` Showroom container exposes `GET /api/health` returning `200 OK`, no auth, no BFF traversal.

## 7. Handoff outputs — required by any demo team joining the catalog

For each demo being on-boarded into the showroom, the DevOps engineer delivers:

- `<demo>` App Registration **Client ID**
- PwC Entra **Tenant ID** (same for all demos)
- Key Vault **URL** (<https://kv-pwc-showroom-dev-we.vault.azure.net/>) and **secret name** (`<demo>-client-secret`) — same pattern as the showroom; the raw value never leaves Key Vault and is never transmitted to the demo team
- `FinCrime-Showroom` security group **Object ID** (same for all demos)
- `<demo>` ACA **FQDN**, for example:
  ```
  ca-pwc-<demo>-dev-we.<hash>.westeurope.azurecontainerapps.io
  ```
- Container Registry **login server** (same for all demos)
- Azure DevOps `<demo>` **repository clone URL**
- **Subscription ID** and **resource group name** (same for all demos)

Pre-handoff verification (mandatory): the DevOps engineer must confirm — using a
test account representative of a typical PwC employee — that the ID token issued
by the App Registration contains the `FinCrime-Showroom` Object ID in the `groups`
claim (or `roles` claim if App Roles are used). See §3.4. Do not release
credentials until this test passes.

- `[ ]` Demo container exposes an unauthenticated health endpoint (default `GET /api/health`, `200 OK`) so it can be added to the warmer target list — see §8.

## 8. Cold-start mitigation — keep-warm ping

ACA Consumption scales to zero when idle. The first request after a period of
inactivity triggers a cold start: the platform allocates compute, the container
runtime starts, and the application boots — typically 10–30 seconds. During a
live client demonstration this is unacceptable. The mitigation adopted is
Mitigation 2 from the
[ACA vs App Service decision document](aca-vs-appservice-decision.md):
an Azure Function (timer trigger) issues one HTTPS GET every 5 minutes during
business hours to each customer-facing ACA app's health endpoint. This is
sufficient to keep one replica warm. Scale-to-zero still applies outside the
window.

### 8.1 Warmer function resources

| Resource | Name | Notes |
|---|---|---|
| Azure Function (warmer) | `func-pwc-showroom-warmer-dev-we` | Consumption plan; runtime is DevOps's choice |
| Timezone setting | `WEBSITE_TIME_ZONE` = `W. Europe Standard Time` | CRON evaluates in CET |
| Schedule | `0 */5 9-18 * * 1-5` | Every 5 min, 09:00–18:59 CET, Mon–Fri |
| Target — showroom | ca-pwc-showroom-dev-we.\<hash\>.westeurope.azurecontainerapps.io/api/health | HTTPS GET, no auth. Replace \<hash\> with the real ACA FQDN once provisioned |
| Target — overwatch | ca-pwc-overwatch-dev-we.\<hash\>.westeurope.azurecontainerapps.io/api/health | HTTPS GET, no auth. Replace \<hash\> with the real ACA FQDN once provisioned |
| Response contract | `200 OK` within 200 ms | Endpoint must not traverse BFF or demo-map logic |
| Expected cost | ~EUR 1.75/month | Function Consumption free tier covers execution; ACA compute dominates |

Add a row to the targets table each time a new scale-to-zero demo is on-boarded.

## 9. Demos currently in scope for phase 1

| Demo | ACA app name | App Registration name | Repository | Pipeline owner |
|---|---|---|---|---|
| Overwatch | `ca-pwc-overwatch-dev-we` | `app-pwc-overwatch-dev` | TBC | TBC |
| UBO | `ca-pwc-ubo-dev-we` | `app-pwc-ubo-dev` | TBC | TBC |

Add a row to this table each time a new demo is on-boarded into the showroom
catalog. The full on-boarding procedure is described in §§1.2, 3.2, 4.2, and 7.
Remember to add the demo's health endpoint as a new target row in §8.1.
