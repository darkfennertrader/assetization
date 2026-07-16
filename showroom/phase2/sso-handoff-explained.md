---
title: "Single Sign-On to Demo Apps"
---

## The one-line summary

The customer logs in **once** at the showroom. The showroom then
**vouches** for the customer to each demo app using a short-lived signed
ticket. The customer never sees a second login screen.

## Why this matters

Every demo app in the PwC portfolio is built and deployed independently.
Each one could, in principle, ask the customer to authenticate separately —
creating a frustrating experience where clicking a demo tile triggers another
Google or Microsoft login prompt. That friction kills a live sales
presentation.

The design described here eliminates that friction entirely. From the
customer's perspective they click a tile and the demo opens. The entire
security exchange happens invisibly in the background, in under a second.

## The mental model — a museum with a ticket office

Imagine the showroom as the **ticket office** of a museum that has several
themed exhibition halls. Each hall is a demo app.

The customer arrives at the museum entrance — the showroom — and buys a
ticket by signing in with their personal Google or Microsoft account. The
ticket office does the hard work: it asks Google or Microsoft *"is this
person who they say they are?"*, receives the answer, and looks up the
customer in the guest list to check they are invited. That is the **only**
time credentials are checked.

When the customer wants to enter an exhibition hall, the ticket office
**stamps a small pass**. The pass says, in effect:

> *"The bearer is `prospect@example.com`, admitted to the Overwatch hall only,
> valid for the next 60 seconds. Signed: PwC Showroom."*

The hall's doorman inspects the stamp, confirms it is genuine, and waves the
customer in — no passport check, no second queue. The customer receives a
wristband at the door and can move freely around the hall for the rest of
their session.

## The four moves in the choreography

### Move 1 — The customer logs in once at the showroom

The customer navigates to `showroom.pwc.example` and clicks
**Sign in with Google** (or Microsoft). Google handles the authentication —
email address, password, and multi-factor if enabled. Google then tells the
showroom: *"This person owns `prospect@example.com` and they have just
authenticated."*

The showroom looks up the email in its guest list. If the customer is
invited and has available quota, the showroom sets a browser cookie. That
cookie remembers the customer for up to 7 days, so they do not have to
sign in again even if they close the browser and return later.

From this point on, Google and Microsoft are completely out of the picture.

### Move 2 — The customer clicks a demo tile

The showroom catalog shows only the demos the customer has been given
access to. When the customer clicks a tile (say, the *Overwatch* AI
assistant), the showroom:

1. Records the visit for usage tracking.
2. Mints a **signed ticket** — a JSON Web Token in technical terms —
   containing the customer's email address, the name of the demo, the
   current time, and an expiry 60 seconds in the future.
3. Signs the ticket with a private cryptographic key stored in Azure Key
   Vault. Only the showroom can produce this signature; no one can forge it.

The showroom does not hand the ticket to the customer to type in somewhere.
Instead, it sends the browser a tiny invisible form that automatically
submits the ticket to the demo app. The customer sees only a brief redirect.

### Move 3 — The demo app checks the ticket

The demo app has never met this customer before. It receives the ticket and
performs three checks:

- **Is the signature genuine?** The demo app holds a copy of the
  showroom's *public key* — the verification counterpart of the private key
  used to sign. It uses this to confirm the ticket really came from the
  showroom and has not been tampered with.
- **Is this ticket for me?** Every ticket names the specific demo it was
  minted for. A ticket for *Overwatch* is rejected at any other demo. This
  prevents a ticket from being reused across demos.
- **Has the ticket expired?** The 60-second lifetime means that even if a
  ticket were intercepted in transit, it would be useless by the time
  anyone could act on it.

If all three checks pass, the demo app accepts the customer as fully
authenticated — without ever contacting Google, Microsoft, or the showroom
directly.

### Move 4 — The demo app creates its own session

Because the ticket expires in 60 seconds, the demo app immediately creates
its own **session cookie** (typically valid for 30 minutes) so the
customer can navigate freely inside the demo without any further checks.
The short-lived ticket is discarded; it cannot be reused.

## Why this design?

### Single authentication point

Only the showroom speaks to Google and Microsoft. Demo apps never handle
passwords, never redirect to external login pages, and never go through a
new OAuth integration review. A new demo can be attached to the showroom in
an afternoon.

### No shared database between apps

The demo apps and the showroom do not share a session store, a cache, or a
database. The ticket is **self-contained**: the demo app extracts everything
it needs — who the customer is, which demo they are entering — from the
ticket itself. Each demo can live in its own Azure subscription, its own
repository, and its own release cycle.

### Short-lived tickets eliminate replay attacks

A ticket that is valid for only 60 seconds cannot be stolen and replayed.
By the time an attacker could intercept and present the ticket, it has
already expired.

### Scoped tickets prevent lateral movement

Each ticket names exactly one demo. If an attacker somehow obtained a valid
*Overwatch* ticket, they could not use it to access *UBO* or any other demo.
The scope is enforced cryptographically, not by policy alone.

### The customer sees nothing

From the customer's perspective they clicked a tile and the demo opened.
There is no second login screen, no loading spinner labelled *"Authenticating
with provider…"*, no pop-up, no copy-pasted code. That is the entire point.

## The everyday analogy — cast of characters

| Role in the story | Real component |
|---|---|
| Passport office | Google or Microsoft (proves identity) |
| Museum concierge / ticket office | PwC Showroom (authenticates the customer once) |
| Stamped pass (handwritten note) | Signed JWT (short-lived ticket) |
| Concierge's official seal | Showroom private key in Azure Key Vault |
| Photograph of the seal on every doorman's desk | JWKS public key endpoint |
| Exhibition hall doorman | Demo app's token validation logic |
| Wristband inside the hall | Demo app session cookie |

## Appendix A — technical terms for the curious

This section is for readers who want to connect the story above to the
technical documentation in `showroom-phase2-flow.md`.

| Plain-English term | Technical name | Where it lives |
|---|---|---|
| Signed ticket | JSON Web Token (JWT), RS256 algorithm | Minted by the showroom BFF on each tile click |
| Concierge's seal (private key) | RSA-256 private key | Azure Key Vault — never leaves Key Vault |
| Photograph of the seal (public key) | JWKS document at `/.well-known/jwks.json` | Served by showroom-app; cached 15 min in RAM |
| Ticket expiry | `exp` claim — 60 seconds from issue time | Enforced by every demo app on receipt |
| "Ticket is for this demo only" | `aud` claim — equals the demo's ID string | Enforced by every demo app on receipt |
| Guest list look-up | Cosmos DB `users` container | Read on every sign-in via Managed Identity |
| Customer's 7-day memory | NextAuth session cookie (`httpOnly`, `Secure`) | Browser — encrypted with `AUTH_SECRET` from Key Vault |
| Demo's 30-minute memory | Demo session cookie | Browser — set by the demo app after ticket validation |

For the full wire-level walkthrough — every HTTP request, every redirect,
every database write — see `showroom/phase2/showroom-phase2-flow.md`.
