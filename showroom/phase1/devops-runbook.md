---
title-meta: "Assetization: Showroom Phase 1 - DevOps Infrastructure Runbook"
---

\thispagestyle{empty}
\vspace*{\fill}
\begin{center}
{\LARGE\bfseries Assetization: Showroom Phase 1\par}
\vspace{0.8em}
{\large DevOps Infrastructure Runbook\par}
\vspace{1.5em}
{\normalsize 2026-07-07\par}
\end{center}
\vspace*{\fill}
\newpage

## Introduction

This document describes the target infrastructure state for the showroom platform in
phase 1. It covers two scopes:

- **Showroom** — the catalog web app that PwC FinCrime staff uses to browse and
  launch demos. This is the scope of the Fixed platform resources in §2.
- **Demo apps** — independently owned products (Overwatch, UBO, etc.) that have
  their own teams, repositories, pipelines, and Azure resources. This runbook
  documents only the minimal on-boarding contract between the showroom and each
  demo team. **Demo app infrastructure is entirely out of scope** — each demo team
  provisions their own resources; the showroom team has no visibility or
  responsibility for them beyond the items listed in §7.

The demos currently expected in phase 1 are listed in §9.

### Environments

Phase 1 uses **three environments** — `dev`, `tst`, and `prod` — hosted in a
**single Azure subscription** (`PZI-GX-E-SUB397`). Each environment is a
separate resource group containing an isolated copy of the showroom platform
resources listed in §2.2. Resource names carry the environment token so that
resource-graph queries and cost reports slice cleanly by environment
(e.g. `rg-pwc-showroom-dev-<region>`, `rg-pwc-showroom-tst-<region>`,
`rg-pwc-showroom-prod-<region>`).

**Access model:**

- **`dev`** — the Solution Architect and the Full-Stack Developer have Contributor
  access. They can create, modify, and destroy resources at will. This is the
  integration and iteration environment.
- **`tst`** and **`prod`** — owned and administered **exclusively by the DevOps
  engineer**. Developers have no direct write access. Promotion from `dev` to `tst`
  and from `tst` to `prod` happens through the CI/CD pipeline only (image tag
  promotion in ACR; ACA revision update).

**Deferred to phase 2:** Microsoft's best-practice recommendation is one Azure
subscription per environment (separate billing, hard blast-radius boundary,
distinct RBAC and policy scopes). Phase 2 will migrate `tst` and `prod` to their
own subscriptions once the APIM and VNet substrate is in place.

## 1. Naming convention

All Azure resources in the assetization program follow the pattern:

```
<type>-<customer>-<workload>-<env>-<region>
```

| Token | Meaning | Phase 1 value |
|---|---|---|
| `type` | CAF-standard[^caf] resource-type abbreviation | `rg`, `cae`, `ca`, `log`, `kv`, `func`, ... |
| `customer` | Customer / tenant umbrella | `pwc` |
| `workload` | Solution inside the customer program | `showroom` |
| `env` | Environment | `dev`, `tst`, or `prod` |
| `region` | 2-letter Azure region code | `xxx (to be defined)` |

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

## 2. Azure resources

### 2.1 Shared services (one instance, across all environments)

These resources are provisioned once and used by all environments and all
demo teams. They are not replicated per env.

| Resource | Name | Notes |
|---|---|---|
| Container Registry | `crpwcshowroom<region>` | Standard SKU. No hyphens — Azure registry name rule. Admin credentials disabled. ACR pull granted via Managed Identity to every ACA app (showroom and any demo app joining the catalog). One shared registry for all envs — images are promoted by tag from `dev` to `tst` to `prod`. |
| Entra ID tenant | PwC corporate tenant | Tenant-global. All App Registrations live here. Not a deployable resource. |

### 2.2 Showroom platform (per environment)

One resource group per environment: `rg-pwc-showroom-<env>-<region>`.
Tags on every resource in the group: `customer=pwc`, `workload=showroom`,
`env=<env>`.

| Resource | Name pattern | Notes |
|---|---|---|
| Resource group | `rg-pwc-showroom-<env>-<region>` | Container for all showroom resources in this env. |
| Log Analytics workspace | `log-pwc-showroom-<env>-<region>` | Part of Azure Monitor. Receives ACA container `stdout`/`stderr` automatically via the ACA environment link. |
| ACA environment | `cae-pwc-showroom-<env>-<region>` | Consumption plan, no VNet. Hosts the showroom ACA app only. Linked to the Log Analytics workspace above. |
| ACA app — showroom | `ca-pwc-showroom-<env>-<region>` | External HTTPS ingress, port 3000, scale-to-zero (min 0, max 5). Kept warm during business hours by the warmer function (see §8). Pulls image from the shared ACR (§2.1) via system-assigned Managed Identity. The IMDS endpoint (169.254.169.254) is accessible from the container by default on the Consumption plan, enabling `DefaultAzureCredential` to acquire MI tokens at runtime. Phase 1 uses the ACA-assigned default FQDN; a custom domain is deferred to phase 2. |
| Key Vault | `kv-pwc-showroom-<env>-<region>` | Standard SKU, RBAC authorization mode, soft-delete and purge-protection enabled. Holds **only** the showroom App Registration client secret (`showroom-client-secret`). The showroom ACA app's system-assigned MI is granted `Key Vault Secrets User` scoped to this secret. |
| Azure Function — warmer | `func-pwc-showroom-<env>-<region>` | Consumption plan. Timer trigger: every 5 min during business hours. See §8. |
| App Registration — showroom | `app-pwc-showroom` | PwC Entra ID tenant, **Web (confidential client)**, groups claim enabled. Region omitted — Entra is tenant-global. |
| Security group | `xxx (to be defined)` | Use existing group or create new one; obtain the Object ID. This is the coarse-grained gate: membership = "can see the Showroom at all". |
| Managed Identity | System-assigned on the showroom ACA app | Must be granted: (1) `AcrPull` on the shared ACR (§2.1), and (2) `Key Vault Secrets User` on `kv-pwc-showroom-<env>-<region>` scoped to `showroom-client-secret`. |

### 2.3 Demo apps — scope boundary

Each demo app (Overwatch, UBO, etc.) is an **independent product** owned by its
own team. Demo app infrastructure — resource groups, ACA environments, ACA apps,
Key Vaults, Log Analytics workspaces, App Registrations — is entirely the
responsibility of each demo team and is **out of scope** for this runbook.

The only shared resource a demo team uses from the showroom platform is the
**Container Registry** (§2.1). The DevOps engineer grants the demo ACA app's
system-assigned Managed Identity the `AcrPull` role on the shared ACR at
on-boarding time (see §7).

## 3. Entra ID configuration

### 3.1 Showroom App Registration

Register the application in the PwC Entra ID tenant as a **Web (confidential
client)** application — not a Single-Page Application. This type is required
because the BFF performs the OAuth authorization-code exchange server-side,
using a client secret. The redirect URI must be registered under the **Web**
platform in the App Registration (not under SPA), pointing to the showroom
ACA FQDN callback route (`/api/auth/callback/azure-ad`). Add a second redirect
URI for local development (<http://localhost:3000/api/auth/callback/azure-ad>).
Enable the `groups` claim (Security Group Object IDs) in the ID token. Also
add the `GroupMember.Read.All` delegated permission and request admin consent
from the Entra tenant admin — without this permission the BFF cannot resolve
group memberships for users who belong to more than 200 groups (Microsoft's
transitive-membership overage threshold). Generate
a client secret (12-month expiry) and store it in the showroom's Key Vault
(`kv-pwc-showroom-<env>-<region>`) under the name `showroom-client-secret`. The
raw value is **never** delivered to the developer and **never** placed in the
ACA app's environment variables; the BFF retrieves it at container startup from
Key Vault using its Managed Identity.

### 3.2 Per-demo App Registration (one per demo in the catalog)

Each demo team registers their own application in the PwC Entra ID tenant as a
**Web (confidential client)** application and stores the client secret in their
own Key Vault. This runbook does not prescribe the demo team's infrastructure.
The showroom's only requirement of a demo App Registration is:

- Redirect URI registered under the **Web** platform, pointing to the demo's
  ACA FQDN callback route (`/api/auth/callback/azure-ad`).
- The `groups` claim enabled.
- The same security group (§3.3) enforced in-app so the group-check in the
  demo BFF uses the same `FINCRIME_GROUP_OID` as the showroom.

Silent SSO works because both the showroom and every demo app share the same
PwC Entra ID tenant — when the user arrives at a demo after being redirected
from the showroom, Entra already holds their session cookie and issues the
authorization code without re-prompting.

### 3.3 Security group

Identify or create the security group and add initial test
members (at minimum the Solution Architect, the Full-Stack Developer, and the
DevOps engineer). Note the group Object ID — it is needed in the showroom app and
in every demo app as the `FINCRIME_GROUP_OID` environment variable.

**Note:** Group-claim overage limits and the `groups` vs `roles` (App Roles) decision
are deferred to phase-2 planning and are out of scope here. See the phase-2 planning
notes for the full caveat analysis.

### 3.4 ACA app environment variables

The showroom ACA app receives the following environment variables on its
revision. **No secret values are stored in environment variables**; secrets are
retrieved at runtime from Key Vault by the BFF.

| Variable | Value type | Description |
|---|---|---|
| `AZURE_TENANT_ID` | GUID | PwC Entra ID tenant identifier |
| `AZURE_CLIENT_ID` | GUID | Showroom App Registration client ID |
| `FINCRIME_GROUP_OID` | GUID | Object ID of the security group — Layer-1 (coarse-grained) group-membership check |
| `KEY_VAULT_URL` | URL | <https://kv-pwc-showroom-\<env\>-\<region\>.vault.azure.net/> |
| `CLIENT_SECRET_NAME` | String | `showroom-client-secret` |

The BFF reads `KEY_VAULT_URL` and `CLIENT_SECRET_NAME` at startup, authenticates
to Key Vault using `DefaultAzureCredential` (which picks up the container's
system-assigned Managed Identity automatically), and holds the resolved secret
value in memory for the lifetime of the process.

Demo teams configure analogous environment variables on their own ACA apps,
pointing to their own Key Vault. This is out of scope for this runbook.

### 3.5 Client secret rotation

A client secret is the shared string that lets an App Registration prove its
identity to Entra ID during the OAuth authorization-code exchange. Entra allows a
maximum lifetime of 24 months; Microsoft recommends 12. When a secret expires,
every user login and every downstream token call fails with `AADSTS7000215` until
the secret is replaced.

**Phase 1 timing:** with secrets created at a 12-month expiry, the first rotation
is due roughly 12 months from provisioning — well beyond the phase 1 delivery
window. The procedure below is documented for operational continuity; it will
not actually run during phase 1. Automation of the rotation (scheduled pipeline,
Managed Identity Federated Credentials, or certificate auto-rotation via Key
Vault) is deferred to phase 2.

**Procedure (when needed):**

1. Generate a new credential in the App Registration (leave the old one active).
2. Update the corresponding Key Vault secret to the new value (Key Vault creates
   a new version automatically; the previous version remains accessible during
   transition).
3. Restart the ACA revision:
   `az containerapp revision restart --name xxx --resource-group xxx --revision xxx`
4. The BFF fetches the new secret from Key Vault on startup.
5. Monitor logs for 24 hours, then delete the old App Registration credential
   and, if required, expire the previous Key Vault secret version.

No code changes and no container image rebuild are required for a secret rotation.

## 4. CI/CD pipelines

Provision an Azure DevOps project and private Git repositories (names to be
confirmed with the Solution Architect and the Full-Stack Developer). Create a
service connection to the Azure subscription using **Workload Identity Federation**
(no client secret to rotate), scoped to the showroom resource group.

### 4.1 Showroom pipeline

Triggers on every push to `main` of the showroom repository. Stage 1 builds the
showroom Docker image and pushes to the shared ACR tagged with the build ID;
stage 2 updates the showroom ACA app to run that image.

## 5. Team roles on the Azure subscription

| Role | `dev` resource group | `tst` resource group | `prod` resource group |
|---|---|---|---|
| DevOps engineer | Owner | Owner | Owner |
| Solution Architect | Contributor | Reader | Reader |
| Full-Stack Developer | Contributor | Reader | Reader |

Owner access confirmed in the 2026-07-03 standup. Contributor/Reader access for
the Solution Architect and the Full-Stack Developer to be granted by the DevOps
engineer once subscription access is confirmed.

## 6. Handoff outputs — required by the showroom developer

Before the Full-Stack Developer can start on the showroom:

- Showroom App Registration **Client ID** (Application ID)
- PwC Entra **Tenant ID**
- Key Vault **URL** (<https://kv-pwc-showroom-\<env\>-\<region\>.vault.azure.net/>) and
  **secret name** (`showroom-client-secret`) — the BFF retrieves the client secret
  at runtime using its Managed Identity; the raw value never leaves Key Vault and
  is never transmitted to the developer
- Security group **Object ID** (`FINCRIME_GROUP_OID`)
- Showroom ACA **default FQDN** (`xxx (to be defined once provisioned)`)
- Container Registry **login server** (`crpwcshowroom<region>.azurecr.io`)
- Azure DevOps **showroom repository clone URL**
- **Subscription** `PZI-GX-E-SUB397` and **resource group name**
  (`rg-pwc-showroom-<env>-<region>`)

Pre-handoff verification checklist:

- `[ ]` Showroom ACA app is running and reachable at its default FQDN.
- `[ ]` Showroom container exposes `GET /api/health` returning `200 OK`, no auth,
  no BFF traversal.
- `[ ]` On group-check failure the BFF returns a plain HTML page with HTTP **200**
  and a human-readable message (e.g. *"You do not have access to the PwC AI
  Showroom. Please contact your line manager."*). Do **not** return 401 or 403.
- `[ ]` A test account in the security group can log in, see the catalog, and click
  through to a demo.
- `[ ]` A test account **not** in the security group reaches the "no access" page.

## 7. Handoff outputs — required by any demo team joining the catalog

The showroom team's only on-boarding deliverable to a demo team is:

- Container Registry **login server** (`crpwcshowroom<region>.azurecr.io`) — the
  demo team's ACA app's system-assigned Managed Identity must be granted `AcrPull`
  on this registry by the DevOps engineer
- Security group **Object ID** (`FINCRIME_GROUP_OID`) — the demo team enforces the
  same group in their own BFF
- PwC Entra **Tenant ID**

Everything else a demo team needs (resource group, ACA FQDN, Key Vault, App
Registration, pipeline, etc.) is their own responsibility.

The showroom team additionally needs one item **from** the demo team before the
demo tile can be added to `demo-map.json`:

- The demo's public ACA **FQDN** (`launchUrl`) — the URL the browser navigates to
  when the user clicks the tile

Pre-handoff verification (mandatory): confirm — using a test account
representative of a typical PwC employee — that the demo's ID token contains
the security group Object ID in the `groups` claim. Do not add the tile to
`demo-map.json` until this test passes.

- `[ ]` Demo container exposes an unauthenticated health endpoint
  (`GET /api/health`, `200 OK`) — this is the warmer ping target (see §8).

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

The warmer function lives in the showroom's per-env resource group
(`rg-pwc-showroom-<env>-<region>`) and is owned by the DevOps engineer.
It pings the showroom ACA app plus any demo ACA apps whose teams have provided
a health endpoint FQDN. Because ACA ingress is public HTTPS, the function can
reach demo apps in any resource group or subscription.

### 8.1 Warmer function resources

| Resource | Name | Notes |
|---|---|---|
| Azure Function (warmer) | `func-pwc-showroom-<env>-<region>` | Consumption plan; runtime is DevOps's choice. Lives in `rg-pwc-showroom-<env>-<region>`. |
| Timezone setting | `WEBSITE_TIME_ZONE` = `W. Europe Standard Time` | CRON evaluates in CET |
| Schedule | `0 */5 9-18 * * 1-5` | Every 5 min, 09:00–18:59 CET, Mon–Fri |
| Target — showroom | `<showroom-FQDN>/api/health` | HTTPS GET, no auth. Replace with the real FQDN once provisioned. |
| Target — overwatch | `<overwatch-FQDN>/api/health` | HTTPS GET, no auth. Replace with the real FQDN once the demo team provides it. |
| Response contract | `200 OK` within 200 ms | Endpoint must not traverse BFF or demo-map logic |
| Expected cost | ~EUR 1.75/month | Function Consumption free tier covers execution; ACA compute dominates |

Add a row to the targets table each time a new scale-to-zero demo is on-boarded.

## 9. Demos currently in scope for phase 1

| Demo | Demo team ACA FQDN (launchUrl) | App Registration name | Repository | Pipeline owner |
|---|---|---|---|---|
| Overwatch | `TBD — Overwatch team to provide` | `TBD` | TBC | Demo team |
| UBO | `TBD — UBO team to provide` | `TBD` | TBC | Demo team |

Add a row to this table each time a new demo is on-boarded into the showroom
catalog. The on-boarding steps are: (1) demo team provides `launchUrl`; (2) DevOps
engineer adds demo's MI to the shared ACR `AcrPull` role assignment; (3) demo tile
is added to `demo-map.json` and the showroom is redeployed; (4) demo FQDN is added
as a target row in §8.1.
