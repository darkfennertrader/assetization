# showroom — PwC AI Showroom (L1)

Documents covering the **L1 Showroom** — the external-facing demo environment used by PwC salespersons to give prospects a scoped 1-hour AI experience via a QR code.

## Documents

| File | Description |
|---|---|
| `showroom-azure-architecture.md` / `.pdf` | Azure service topology: Front Door, WAF, APIM, ACA, Cosmos DB, Key Vault, ACR, App Insights, Event Hub, ADLS. Service selection rationale, networking model (private endpoints, VNet layout), Managed Identity assignments, scaling + cost profile, deployment topology, IaC + CI/CD, compliance posture. |
| `showroom-azure-architecture.dot` / `.png` | Graphviz source and rendered diagram — L1 Showroom + L4 Substrate services consumed |
| `showroom-qr-flow.md` / `.pdf` | Auth & session design: token model (self-signed RS256 JWT, 5-min TTL, no Redis), step-by-step walkthrough, APIM policy skeleton, full frontend guidance (Next.js + Fluent UI + TanStack Query + MSAL React) |
| `showroom-qr-flow.dot` / `.png` | Graphviz source and rendered diagram — three swimlanes: Presenter / Shared Substrate / Prospect |

## Build

```bash
bash showroom/build-pdf.sh
```

Renders both PNGs and builds both PDFs.

## Key design decisions

| Decision | Applied in |
|---|---|
| D3 — Self-signed RS256 JWT for 1-hour demo tokens | `showroom-qr-flow.md` |
| D8 — No Redis; short TTL (5 min) + Cosmos session status | `showroom-qr-flow.md` |
| D9 — APIM is the single enforcement point | Both documents |
| Option A — Single Next.js Container App (admin + prospect + BFF) | `showroom-azure-architecture.md` |

See `docs/auth-design-note.md` for the full D1-D9 decision log.

## Group-claim caveats (deferred from phase 1)

These items were removed from the phase-1 DevOps runbook and are tracked here
for phase-2 planning.

### Caveat 1 — Group overage limit

Entra ID injects the `groups` array directly into the ID token only when the
user's total Entra group membership count is below a threshold (roughly 150 for
JWT). When a user is in more groups than this limit, the token instead carries a
`_claim_names` / `_claim_sources` reference; the application must then call
Microsoft Graph (`/me/memberOf` or `getMemberGroups`) to resolve group membership
at runtime. In a large corporate tenant such as PwC's, typical users are members
of many distribution lists and security groups, making the overage scenario highly
likely.

Mitigations to evaluate before delivering credentials to the demo team:

- Enable the **"Emit groups as role claims"** option on the App Registration and
  filter to only the FinCrime-Showroom group. This emits only that single group
  in the claim regardless of the user's other memberships and is immune to the
  overage limit.
- Alternatively, switch to **App Role assignments** (see Caveat 2 below) and
  assign the security group to an App Role — the `roles` claim is per-application
  and never suffers overage.

Action item for the DevOps engineer: create a test user account that is a member
of many Entra groups (simulating a typical PwC employee), authenticate against the
App Registration, decode the resulting ID token, and confirm that the
FinCrime-Showroom Object ID is present in the `groups` array. Do this before
releasing any handoff credentials to a demo team.

### Caveat 2 — `groups` claim vs `roles` claim (App Roles)

The phase-1 design reads the raw `groups` claim from the ID token. This exposes
all of the user's Entra group Object IDs to any party that can inspect the token,
which is not application-scoped. Microsoft's best-practice guidance favours
**App Role assignments**: the App Registration defines named roles, the
FinCrime-Showroom group is assigned to one of those roles, and the app reads the
`roles` claim — which contains only roles defined for that specific application
and is never affected by the overage limit.

For phase 2, assess migrating to `roles`. The code change in the middleware is
minimal — one environment variable and one claim-name string.
