---
title: "Front Door + WAF — Why Phase 2 Needs It and Phase 1 Did Not"
---

## The audience shift changes the threat model

Phase 1 was visible only to PwC employees who had to sign in with corporate
Entra ID before seeing a single page. Phase 2 publishes a URL in public DNS,
registers OAuth callback routes with Google and Microsoft, and hands the link
to people we do not manage. Those two things — a crawlable DNS record and
publicly registered callback paths — are all an automated scanner needs.

## Phase 1 vs. Phase 2 attack surface

| Property | Phase 1 | Phase 2 |
|---|---|---|
| Audience | PwC staff only | External prospects (anyone given the URL) |
| URL discovery | Intranet share, internal Slack | Email, business cards, decks, LinkedIn |
| Authentication | Entra ID corporate SSO + MFA + group claim | Google / MS consumer OAuth |
| Callback URLs | Internal; not registered externally | `/api/auth/callback/*` registered with Google and Microsoft — publicly known paths |
| Bot / scanner exposure | Minimal — URL not in public DNS | High — every new A-record is scanned within minutes |
| Catalog contents | Internal tooling list | Branded PwC demo names and thumbnails — competitive-intel value to scrapers |

## What Front Door + WAF blocks that nothing else does

| Threat | Edge mitigation |
|---|---|
| Credential stuffing / brute-force against OAuth callback URLs | WAF OWASP CRS 3.2 auth-endpoint abuse rules + edge rate-limit (e.g. 100 req/min per IP) |
| Automated catalog scraping (demo names, thumbnails, descriptions) | Front Door bot manager fingerprint + challenge; blocked before the request reaches ACA |
| Volumetric abuse inflating Cosmos DB RU consumption and ACA scale-out billing | Edge rate-limit absorbs spikes before any traffic enters the private network — no compute or DB cost incurred |
| DNS `TXT` and `.well-known` reconnaissance scans | WAF pattern rules drop standard scanning payloads at the PoP |
| Malformed OAuth `state` / `code` parameter injection | WAF payload-size and character-class rules; NextAuth validation is defence-in-depth, not first line |

## Monthly cost estimate (Azure West Europe, ~500 sessions/month)

| Component | Basis | Est. EUR / month |
|---|---|---|
| Front Door Standard profile — base fee | 1 profile | ~35 |
| WAF policy — OWASP CRS 3.2 managed ruleset | 1 policy | ~20 |
| Requests + data egress at Phase 2 volume | ~500 sessions, ~2 GB outbound | ~5 |
| **Total estimate** | | **~60** |

Bot Manager (advanced bot fingerprinting) requires Front Door **Premium**
(~+165 EUR/month). It can be added when and if measurable scraping appears in
the WAF logs. At Phase 2 volume it is not needed on day one.

For reference, a single cloud engineer hour resolving an abuse incident costs
more than the annual Front Door Standard bill. Attempting to retrofit WAF after
a scraping or DDoS event also requires a maintenance window, re-registration of
OAuth callback URLs, and DNS propagation time — all of which occur while the
Showroom is unavailable to live prospects.

## Bottom line

~60 EUR/month buys enterprise-grade edge protection from the moment
`showroom.pwc.example` appears in public DNS. Phase 3 (APIM gateway layer) does
not replace Front Door: the correct Phase 3 stack is
Front Door + WAF at edge → APIM at gateway → ACA at backend — each layer with a
distinct, non-overlapping responsibility. Front Door cost therefore persists and
is justified across all future phases.
