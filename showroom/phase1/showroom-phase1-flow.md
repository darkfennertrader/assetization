---
title: "Showroom Phase 1 — Runtime Flow Explained"
---

Companion to `showroom-phase1-flow.png`. Each numbered step in the
sequence diagram maps to one section below.

![Showroom Phase 1 runtime flow](showroom-phase1-flow.png)

## Step 1 — Browser → Showroom BFF: `GET /`

A PwC FinCrime staff member opens the showroom URL in their browser.
In phase 1 this is the Azure Container Apps default FQDN (no custom domain
is registered in phase 1; a custom domain is deferred to phase 2):

```
xxx (to be defined once provisioned)
```

The browser sends a plain HTTPS GET to the root path. There is no session
cookie yet, so the BFF cannot identify who this person is.

## Step 2 — Showroom BFF → Browser: `302 → Entra /authorize (PKCE)`

The BFF detects the missing session and redirects the browser to the
PwC Entra ID authorization endpoint. It generates a `code_verifier`,
computes `code_challenge = SHA-256(code_verifier)`, stores the
verifier in an encrypted HttpOnly cookie, and includes the challenge
in the redirect URL. This is the standard Authorization Code + PKCE
flow. No client secret is sent to the browser.

## Step 3 — Browser → Entra ID: `/authorize + code_challenge`

The browser follows the redirect and sends the authorization request
to Entra ID, including the `code_challenge` and the showroom's
`client_id`.

## Step 4 — Entra ID → Browser: login form

Entra ID returns the PwC corporate login form. The user enters their
`@pwc.com` credentials.

## Step 5 — Browser → Entra ID: submit credentials

The user submits their email and password (and MFA if enabled for the tenant).

## Step 6 — Entra ID → Browser: `302 → /api/auth/callback?code=…`

Entra ID validates the credentials, sets an Entra session cookie in the
browser, and redirects back to the showroom callback URL with a
short-lived authorization code.

## Step 7 — Browser → Showroom BFF: `/api/auth/callback?code=…`

The browser follows the redirect back to the showroom BFF. The BFF
receives the authorization code and the encrypted `code_verifier` cookie.

## Step 8 — Showroom BFF → Entra ID: `POST /token`

The BFF sends the authorization code and the plaintext `code_verifier`
to the Entra ID token endpoint. Entra ID re-computes `SHA-256(verifier)` and
checks it against the `code_challenge` it stored earlier, proving that
the party exchanging the code is the same one that initiated the request.

## Step 9 — Entra ID → Showroom BFF: ID token

Entra ID returns an ID token containing the user's `oid` (Object ID)
and `groups` claim (list of Entra ID security group OIDs the user belongs to).
The BFF stores this in an encrypted server-side session cookie.

## Step 10 — Layer-1 AuthZ (coarse-grained group check)

The BFF checks whether the user's `groups` claim contains the
`FINCRIME_GROUP_OID` security group Object ID.

**If not a member:** the BFF returns a plain HTML page with HTTP **200**:
*"You do not have access to the PwC AI Showroom. Please contact your line
manager."* No 401 or 403 status code. The flow ends here.

**If a member:** the user passes Layer-1 and proceeds to Step 11.

## Steps 11–13 — Authorized: catalog loaded and tile clicked

If the user passes Layer-1 AuthZ:

**Step 11 — Layer-2 AuthZ (fine-grained via demo-map.json):**
The BFF uses a two-layer authorization model. Both layers always run on every
catalog request.

- **Layer 1 (coarse-grained) — step 10 above** — answers *"can this person see
  the Showroom at all?"* by checking the Entra ID `groups` claim against
  `FINCRIME_GROUP_OID`.
- **Layer 2 (fine-grained) — this step** — answers *"which demo tiles may this
  specific user see?"* The BFF reads `demo-map.json` (baked into the container
  image). This single file holds both the authorization entries (which `oid`s
  and group OIDs may see which demo IDs) and the tile metadata (title,
  thumbnail URL, `launchUrl`) for each demo. The BFF intersects the user's
  `oid` and `groups` claim against the authorization entries to produce the
  list of demo tiles this user may see.

The Layer-2 code path always runs. The **effect** depends on the map contents:
if every demo is granted to `FINCRIME_GROUP_OID`, every authorized user sees
every tile (Layer 2 is a no-op for that configuration). If specific demos are
granted only to specific `oid`s or sub-groups, the catalog is filtered per
user. Phase 1 will start with the no-op configuration; the mechanism is in
place so a future "show this demo only to these three partners" request is a
`demo-map.json` edit + container revision update, not a code change.

**Step 12 — /catalog HTML returned:** The BFF renders the catalog page with
the authorized demo tiles. Each tile displays a thumbnail, a title, and a
description. Only demos the user is authorized to see are shown.

**Step 13 — Tile click:** The user clicks the Overwatch tile. The catalog
page executes:

```typescript
window.location.href = demo.launchUrl;
// "xxx (to be defined — overwatch ACA FQDN)"
```

This is a **top-level browser navigation**, not a fetch, not an iframe. The
browser leaves the showroom URL entirely and navigates to Overwatch's own URL.
There is no BFF proxy route. There is no iframe element.

## Step 14 — Browser → Overwatch ACA: `GET /`

The browser sends a fresh HTTPS GET to the Overwatch ACA app. The
Overwatch app is an **independently deployed ACA container** running in
the same ACA environment as the showroom. It has its own Entra ID App
Registration (`xxx (to be defined)`) and its own session middleware.

## Step 15 — Overwatch → Browser: `302 → Entra /authorize (PKCE)`

Overwatch detects no session and redirects to Entra ID with its own
`client_id` and a new `code_challenge`. Same PKCE flow, different
application.

## Step 16 — Browser → Entra ID: `/authorize + code_challenge` (silent SSO)

The browser sends the authorization request to Entra ID. At this point
the user's browser already holds the Entra ID session cookie established
during the showroom login (steps 5–6). Entra ID recognizes the existing
session and does **not** show the login form again. It immediately issues
the authorization code without user interaction. This is called **silent SSO**
(Single Sign-On via session cookie within the same tenant). From the user's
perspective: a brief redirect flash, then Overwatch loads.

## Step 17 — Entra ID → Browser: `302 → Overwatch /api/auth/callback?code=…`

Entra ID redirects back to the Overwatch callback URL with the authorization code.
No login form was shown.

## Steps 18–19 — Overwatch token exchange

Same as steps 7–9 but for the Overwatch app: the browser delivers the code
to Overwatch's BFF, Overwatch exchanges it for an ID token, and stores the
session.

## Step 20 — Overwatch group check: not authorized

If somehow the user is not in the security group (impossible via the showroom
catalog since the showroom already checked the same group, but defensive
coding requires it), Overwatch shows its own "no access" page with HTTP **200**.
The flow ends.

## Step 21 — Overwatch UI loaded

The user sees the Overwatch application. The browser URL bar now shows the
Overwatch FQDN. The showroom is no longer in the picture. Overwatch's container
has outbound HTTPS access to Azure OpenAI and Azure Cognitive Services endpoints.

## Infrastructure notes

- The showroom and each demo app pull their container images from the **shared
  ACR** (`crpwcshowroom<region>.azurecr.io`) via system-assigned Managed
  Identity. No Docker credentials are stored in environment variables.
- The showroom ACA app sends container `stdout`/`stderr` to its own Log
  Analytics workspace (`log-pwc-showroom-<env>-<region>`) automatically via
  the ACA environment link.
- Each demo app sends logs to its **own** Log Analytics workspace — demo
  observability is the demo team's responsibility.
- The showroom's ACA environment (`cae-pwc-showroom-<env>-<region>`) hosts the
  showroom only. Each demo app runs in its own ACA environment owned by the
  demo team. No VNet is configured in phase 1 for any of these environments.

## Phase-2 upgrade path

When APIM is introduced in phase 2 it sits in front of both the showroom
and Overwatch. It will support two access paths simultaneously:

1. **Entra ID group path** (unchanged from phase 1): the security group
   check moves from in-app middleware to an APIM `validate-jwt` policy.
2. **QR session path**: a short-lived RS256 JWT issued by the showroom when
   a presenter generates a QR code. APIM validates the JWT and forwards a
   principal header to the demo app. No application-side code changes are
   required in Overwatch or any other demo app.
