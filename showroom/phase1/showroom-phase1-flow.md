---
title: "Showroom Phase 1 — Runtime Flow Explained"
---

# Showroom Phase 1 — Runtime Flow Explained

Companion to `showroom-phase1-flow.png`. Each numbered step in the
sequence diagram maps to one section below.

![Showroom Phase 1 runtime flow](showroom-phase1-flow.png)

---

## Step 1 — Browser → Showroom BFF: `GET /`

A PwC FinCrime staff member opens the showroom URL in their browser.
In phase 1 this is the Azure Container Apps default FQDN:
```
https://ca-pwc-showroom-dev-we.<hash>.westeurope.azurecontainerapps.io
```

No custom domain is registered yet. The browser sends a plain HTTPS GET
to the root path. There is no session cookie yet, so the BFF cannot
identify who this person is.

---

## Step 2 — Showroom BFF → Browser: `302 → Entra /authorize (PKCE)`

The BFF detects the missing session and redirects the browser to the
PwC Entra ID authorization endpoint. It generates a `code_verifier`,
computes `code_challenge = SHA-256(code_verifier)`, stores the
verifier in an encrypted HttpOnly cookie, and includes the challenge
in the redirect URL. This is the standard Authorization Code + PKCE
flow. No client secret is sent to the browser.

---

## Step 3 — Browser → Entra ID: `/authorize + code_challenge`

The browser follows the redirect and sends the authorization request
to Entra ID, including the `code_challenge` and the showroom's
`client_id`.

---

## Step 4 — Entra ID → Browser: login form

Entra ID returns the PwC corporate login form. The user enters their
`@pwc.com` credentials.

---

## Step 5 — Browser → Entra ID: submit credentials

The user submits their email and password (and MFA if enabled for the tenant).

---

## Step 6 — Entra ID → Browser: `302 → /api/auth/callback?code=…`

Entra ID validates the credentials and redirects the browser back to
the showroom callback URL with a short-lived authorization code.

---

## Step 7 — Browser → Showroom BFF: `/api/auth/callback?code=…`

The browser follows the redirect back to the showroom BFF. The BFF
receives the authorization code and the encrypted `code_verifier` cookie.

---

## Step 8 — Showroom BFF → Entra ID: `POST /token`

The BFF sends the authorization code and the plaintext `code_verifier`
to the Entra ID token endpoint. Entra ID re-computes `SHA-256(verifier)` and
checks it against the `code_challenge` it stored earlier, proving that
the party exchanging the code is the same one that initiated the request.

---

## Step 9 — Entra ID → Showroom BFF: ID token

Entra ID returns an ID token containing the user's `oid` (Object ID)
and `groups` claim (list of Entra ID security group OIDs the user belongs to).
The BFF stores this in an encrypted server-side session cookie.

---

## Step 10 — Group check: not authorized

If the user's `groups` claim does not include the `FinCrime-Showroom`
group OID, the BFF returns a friendly HTML page: *"You do not have
access to the PwC AI Showroom. Please contact your line manager."*
No 401 or 403 status code — just a clear, human-readable message.

The flow ends here for unauthorized users.

---

## Steps 11–13 — Authorized: catalog loaded and tile clicked

If the user is in `FinCrime-Showroom`:

**Step 11 — Load demo-map.json:** The BFF reads the static authorization
map. It intersects the user's `oid` and `groups` claim against the map to
produce the list of demo IDs this user may see. It then looks up each demo
ID in `demo-registry.json` to get the tile title, thumbnail, and `launchUrl`.

**Step 12 — /catalog HTML returned:** The BFF renders the catalog page with
the authorized demo tiles. Each tile displays a thumbnail, a title, and a
description. Only demos the user is authorized to see are shown.

**Step 13 — Tile click:** The user clicks the Overwatch tile. The catalog
page executes:

```typescript
window.location.href = demo.launchUrl;
// "https://ca-pwc-overwatch-dev-we.<hash>.westeurope.azurecontainerapps.io/"
```

This is a **top-level browser navigation**, not a fetch, not an iframe. The
browser leaves the showroom URL entirely and navigates to Overwatch's own URL.
There is no BFF proxy route. There is no iframe element.

---

## Step 14 — Browser → Overwatch ACA: `GET /`

The browser sends a fresh HTTPS GET to the Overwatch ACA app. The
Overwatch app is an **independently deployed ACA container** running in
the same ACA environment as the showroom. It has its own Entra ID App
Registration (`app-pwc-overwatch-dev`) and its own session middleware.

---

## Step 15 — Overwatch → Browser: `302 → Entra /authorize (PKCE)`

Overwatch detects no session and redirects to Entra ID with its own
`client_id` and a new `code_challenge`. Same PKCE flow, different
application.

---

## Step 16 — Browser → Entra ID: `/authorize + code_challenge` (silent SSO)

The browser sends the authorization request to Entra ID. At this point
the user's browser already holds the Entra ID session cookie from step 5
(the showroom login). Entra ID recognizes the existing session and does
**not** show the login form again. It immediately issues the authorization
code without user interaction. This is called **silent SSO** (Single Sign-On
via session cookie within the same tenant). From the user's perspective: a
brief redirect flash, then Overwatch loads.

---

## Step 17 — Entra ID → Browser: `302 → Overwatch /api/auth/callback?code=…`

Entra ID redirects back to the Overwatch callback URL with the authorization code.
No login form was shown.

---

## Steps 18–19 — Overwatch token exchange

Same as steps 7–9 but for the Overwatch app: the browser delivers the code
to Overwatch's BFF, Overwatch exchanges it for an ID token, and stores the
session.

---

## Step 20 — Overwatch group check: not authorized

If somehow the user is not in `FinCrime-Showroom` (impossible via the showroom
catalog since the showroom already checked the same group, but defensive
coding requires it), Overwatch shows its own "no access" page. The flow ends.

---

## Step 21 — Overwatch UI loaded

The user sees the Overwatch application. The browser URL bar now shows the
Overwatch FQDN. The showroom is no longer in the picture. Overwatch's container
has outbound HTTPS access to Azure OpenAI and Azure Cognitive Services endpoints.

---

## Infrastructure notes

- Both ACA apps pull their container images from the same ACR
  (`crpwcshowroomdev`) via system-assigned Managed Identity. No Docker
  credentials are stored in environment variables.
- Both ACA apps send container `stdout`/`stderr` to the shared Log Analytics
  workspace (`log-pwc-showroom-dev-we`) automatically.
- The ACA environment (`cae-pwc-showroom-dev-we`) provides the shared
  networking plane. No VNet is configured in phase 1.

---

## Phase-2 upgrade path

When APIM is introduced in phase 2 it sits in front of both the showroom
and Overwatch. It will support two access paths simultaneously:

1. **Entra ID group path** (unchanged from phase 1): the `FinCrime-Showroom`
   group check moves from in-app middleware to an APIM `validate-jwt` policy.
2. **QR session path**: a short-lived RS256 JWT issued by the showroom when
   a presenter generates a QR code. APIM validates the JWT and forwards a
   principal header to the demo app. No application-side code changes are
   required in Overwatch or any other demo app.
