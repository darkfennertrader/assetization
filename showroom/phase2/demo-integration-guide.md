---
title: "Attaching a Demo App to the PwC Showroom — Developer Guide"
---

Every demo app in the PwC Showroom ecosystem receives its prospects through the
same handoff mechanism: a signed JSON Web Token issued by the showroom BFF.
This document describes what each demo app must implement. No other
authentication is required.

## How the handoff works

When a prospect clicks a demo tile in the showroom catalog, the showroom:

1. Mints a short-lived JWT (60 s TTL) signed with an RSA-256 private key.
2. Returns a self-submitting HTML form that posts that token to your demo.

Your demo receives a `POST /` with a `token` form field. You must validate the
token, set your own session cookie, and then serve the demo UI. The prospect
sees no login screen.

## What you must implement

### 1. Accept `POST /` and extract the token

```python
# FastAPI example
@app.post("/")
async def handoff(token: str = Form(...)):
    claims = verify_showroom_token(token, expected_aud="your-demo-id")
    # set session cookie, redirect to GET /
```

```typescript
// Express example
app.post("/", express.urlencoded({ extended: false }),
  (req, res) => {
    const claims = verifyShowroomToken(
      req.body.token, "your-demo-id"
    );
    // set session cookie, redirect to GET /
  }
);
```

### 2. Fetch and cache the showroom public key (JWKS)

```
GET https://showroom.pwc.example/.well-known/jwks.json
```

Cache the response for **24 hours**, keyed by `kid`. On a
signature-verification failure, invalidate the cache entry for that `kid`
and refetch once before returning `401` — this handles key rotation without
downtime. The JWKS array may contain more than one key during a signing-key
rotation window; always select the entry whose `kid` matches the token
header's `kid`, do not assume a single key.

The showroom's `/.well-known/jwks.json` endpoint is Key Vault-backed: the
showroom-app derives the public JWKS document from the RSA-256 public key
material held in Azure Key Vault (via Managed Identity) and holds the result
in an in-process RAM cache with a 15-minute TTL. Private key material never
leaves Key Vault. No rotation pipeline or external JWKS store is needed.

### 3. Verify the token — required checks

| Check | Expected value |
|---|---|
| Signature algorithm | RS256 |
| `iss` | <https://showroom.pwc.example> (exact string match) |
| `aud` | your demo's ID string (e.g. `overwatch`) |
| `exp` | must be in the future |

Reject with `401 Unauthorized` if any check fails. Do not log the raw token.

### 4. Extract identity claims

After successful verification, read:

- `sub` — prospect email address (use this as the user identifier).
- `visitId` — UUID linking this session to the showroom's `demo_visits`
  record; include it in the usage callback (Step 5 below).

### 5. Set your own session cookie

```
Set-Cookie: demo_session=<encrypted payload>; HttpOnly; Secure;
            SameSite=Lax; Path=/; Max-Age=1800
```

Suggested payload: `{ email, visitId, exp: now + 30 min }`, encrypted with
a key you own. Redirect the browser to `GET /` after setting the cookie. The
one-use handoff JWT should be discarded at this point.

### 6. Report usage back to the showroom

When the prospect's session ends, or periodically, call:

```
POST https://showroom.pwc.example/api/internal/demo-usage
Content-Type: application/json
X-Demo-Callback-Secret: <shared secret — fetch from Key Vault>

{
  "email": "prospect@example.com",
  "demoId": "overwatch",
  "visitId": "<uuid from JWT claims>",
  "messageCount": 12,
  "closedAt": "2026-07-10T09:05:00Z"
}
```

The `X-Demo-Callback-Secret` value is a shared secret stored in Key Vault.
Retrieve it via Managed Identity at startup — never hard-code it.

## Token shape (reference)

```json
{
  "iss": "https://showroom.pwc.example",
  "aud": "overwatch",
  "sub": "prospect@example.com",
  "visitId": "a1b2c3d4-e5f6-...",
  "iat": 1752140700,
  "exp": 1752140760,
  "kid": "sr-2026-07"
}
```

TTL is **60 seconds**. Refuse any token with `exp` more than 5 minutes in
the future (clock-skew guard).

## What you must NOT do

- Do not implement your own Google, Microsoft, or Entra ID OAuth flow. The
  showroom handles all external authentication; your demo only needs to trust
  the showroom's signed assertion.
- Do not trust `email` from any source other than a verified showroom JWT.
- Do not persist the raw JWT.
- Do not accept a token whose `aud` does not exactly match your demo ID —
  even if the signature is valid, it was minted for a different demo.
- Do not skip the `exp` check. Expired tokens must be rejected.

## Phase 3 note

In Phase 3, APIM sits in front of every demo app and enforces JWT validation
at the gateway layer. Your in-app validation remains as defence-in-depth
but will no longer be the primary enforcement point. No code changes are
required when Phase 3 is deployed.

## Reference implementations

Minimal working implementations (30-45 lines each) are available in the
showroom repository under `docs/demo-templates/`:

- `node-express/` — uses the `jose` library (JWKS fetch + RS256 verify).
- `python-fastapi/` — uses `PyJWT[crypto]` (JWKS fetch + RS256 verify).

Copy the relevant template into your demo, set the `DEMO_ID` and
`SHOWROOM_JWKS_URL` environment variables, and the handoff is complete.
