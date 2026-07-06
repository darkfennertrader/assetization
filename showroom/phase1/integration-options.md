---
title: "Showroom Phase 1 — Demo Integration Patterns: Options, Trade-offs, and the PwC Choice"
---

# Purpose

This document records the architectural decision behind how the PwC AI Showroom
launches its portfolio of demos. It covers every realistic integration pattern in
use across the industry, evaluates each from both the technical and end-user
perspectives, and explains why **Redirect + Silent SSO** was chosen as the primary
model.

The audience is the Phase-1 delivery team and any architect joining the programme
after the decision has been made. The document is intended to survive as a durable
design record — not a recommendation to revisit the choice, but a transparent
account of why it was made.


# 1. The Problem Space

The PwC AI Showroom is a **catalog** — a single, authenticated entry point that
presents a portfolio of independently built, independently deployed AI demos to
client visitors.

The key constraints that shape the integration choice are:

- **Heterogeneous tech stacks.** Each demo is built by a different team and may use
  React, Streamlit, Angular, plain Python/Flask, or a future framework not yet known.
  Any pattern requiring all demos to share a runtime or framework is ruled out.

- **Independent deploy cycles.** Demo teams ship on their own cadence. The showroom
  must not require a coordinated release to add or update a demo.

- **Full browser capabilities per demo.** Demos may need file upload, clipboard
  access, camera, PDF rendering, WebSocket connections, and third-party cookies.
  Any pattern that applies a cross-origin security restriction is ruled out.

- **Silent, frictionless authentication.** A client visitor who signs in once to the
  showroom must not be asked to sign in again when entering a demo.

- **Low integration cost per new demo.** Adding a new demo should be a catalog
  configuration change, not a proxy-rule change or an iframe-wiring change.

- **Authentic demo experience.** The demo must run exactly as it would when a client
  eventually buys the product — not in a constrained shell.


# 2. The Full Landscape — 13 Integration Patterns

The patterns below progress from tightest to loosest coupling between the showroom
and its demos.

## 2.1 Baseline: Single SPA Monorepo

**What it is.** All demos and the showroom shell are modules within one codebase and
one deployment unit. A single Webpack/Vite bundle is served from one ACA container.

**What Anna (the visitor) sees.** A seamless single-page app. No handoffs, no
reloads. Demo UIs appear in-place as the shell routes to them.

**Pros.** Maximum UX coherence. Shared design system, auth state, telemetry, and
error boundaries — all for free.

**Cons.** Every demo team must commit to the same codebase, the same framework, the
same release train. The showroom team becomes a gatekeeper for every demo change.
Absolutely rules out demos from partner organisations or external vendors. One noisy
dependency upgrade can affect all demos simultaneously.

**Verdict for PwC showroom.** Not applicable. The program has multiple independent
teams and demos with heterogeneous stacks.


## 2.2 Reverse-Proxy (Path Rewriting)

**What it is.** The showroom's ACA container fronts Overwatch (and every other demo)
via an Nginx or YARP reverse proxy. Requests to
`showroom.pwc.com/demos/overwatch/…` are rewritten and forwarded to
`overwatch-internal.azurecontainerapps.io/…`. The browser always sees one origin.

**What Anna sees.** One URL in the address bar throughout. The showroom's header
and footer wrap Overwatch's UI. The tab title and favicon stay under the showroom's
control.

**Pros.** Feels like a single product. Bookmarkable deep-links. Back button works.
No cross-origin restrictions.

**Cons.** Any URL or redirect that Overwatch generates internally (API calls,
OAuth callbacks, `window.location.href`, absolute asset paths) may reference the
demo's real internal hostname and break through the proxy rewrite. Path collision
between demos is a constant operational risk. Adding a new demo requires new proxy
rules and regression testing across all existing rules. CSP/HSTS/CORS headers from
each demo's backend must be audited and rewritten.

**Verdict for PwC showroom.** High coupling, high per-demo integration cost. Does
not meet the "low integration cost per new demo" constraint. Ruled out as primary
model.


## 2.3 Redirect + Silent SSO ← **Chosen**

**What it is.** The showroom is a catalog application. When Anna clicks the Overwatch
tile, the showroom issues a short (typically under 500 ms) redirect to
`overwatch.pwc.com`. Both the showroom and Overwatch are registered as applications
in the same Entra ID tenant. Overwatch's OIDC middleware accepts Anna's existing SSO
session and issues its own session cookie without prompting her to sign in again.

**What Anna sees.** A brief branded interstitial — "Launching Overwatch…" — then
Overwatch loads in the same tab as its own standalone application. The URL bar
changes to `overwatch.pwc.com`. The tab title and favicon become Overwatch's.
Overwatch occupies the entire viewport exactly as it would if a client accessed it
directly.

**What Anna can do.** Everything a user of the real product can do. Bookmark any
deep link inside Overwatch, share it with a colleague (who will be silently
authenticated if already in the tenant, or prompted for a one-click Entra ID login
if not). Use browser back to return to the showroom catalog. Right-click any element
or link as expected. Use clipboard, file upload, PDF export, WebSocket-backed live
charts — no restrictions.

**Pros.** Zero cross-origin restrictions. Every demo runs as the real product, giving
an authentic experience. Adding a new demo is a catalog registration (one JSON entry)
with no changes to proxy rules or iframes. Demo teams retain full architectural
autonomy. Entra ID silent-SSO eliminates re-authentication friction in the
overwhelming majority of visits.

**Cons.** The origin changes on launch — Anna briefly experiences a
"leaving the showroom" transition. The showroom loses contextual wrapping around the
demo (no persistent header, no breadcrumb trail back). If a client's browser has SSO
session expired, they see an Entra ID login page from Overwatch's domain rather than
the showroom's domain on re-entry.

**Verdict for PwC showroom.** Best fit. Meets all five key constraints. Selected as
the primary integration model.


## 2.4 iframe Embedding

**What it is.** The showroom page renders an `<iframe>` containing the demo
application. The showroom's chrome surrounds the iframe. Anna never leaves the
showroom's origin.

**What Anna sees.** The showroom header and footer remain. Inside the bounded
rectangle of the iframe, Overwatch's UI is displayed. If Overwatch's own UI has a
header, Anna sees two stacked headers. Overwatch's internal navigation (routing) is
trapped inside the iframe — the browser address bar and back button do not reflect
it.

**What Anna can do — and cannot.**

Anna cannot bookmark a specific Overwatch page; the showroom URL is the only stable
address. She cannot use the browser back button to navigate inside the demo;
pressing back exits the demo entirely. She cannot copy links to specific demo views
and share them meaningfully.

Modern browsers (Chrome, Safari, Firefox) block third-party cookies inside iframes
by default (Chrome's CHIPS, Safari ITP, Firefox Total Cookie Protection). Overwatch's
Entra ID sign-in flow requires setting a session cookie from its own origin; inside
an iframe that cookie is blocked. Anna sees an "unable to sign you in" error.
Clipboard access, camera, microphone, file downloads, notifications, and popup
windows are each subject to a per-permission `allow` attribute on the iframe element
and may be blocked by enterprise browser policies regardless.

If Overwatch's server responds with `X-Frame-Options: DENY` or a `Content-Security-
Policy: frame-ancestors 'none'` header, the iframe renders a blank white rectangle.

**Pros.** Preserves the showroom chrome around the demo. One URL for the whole
session (useful for analytics that track a single session across all demos).

**Cons.** Third-party cookie blocking breaks Entra ID SSO in all major modern
browsers. Browser permissions are restricted. Back button is broken. Deep-linking
is not possible. Full-screen charts and modals are confined to the iframe rectangle.
The experience feels constrained to the visitor.

**Verdict for PwC showroom.** Ruled out. SSO breakage alone is disqualifying.


## 2.5 Module Federation (Webpack 5 / Vite Federation)

**What it is.** The showroom is a "host" SPA. Each demo exposes a set of React
(or Vue/Angular) components as a remotely loaded bundle via Webpack Module
Federation or the Vite-Federation plugin. At runtime the host imports the remote
bundle and mounts its components in the showroom's component tree.

**What Anna sees.** A single-page application. Demo UIs render inside the showroom
with no reloads. Shared design tokens and auth state flow naturally between shell and
demo.

**Pros.** Best-in-class UX continuity. Independent deployments once the protocol is
established. Shared dependencies (React, design system) are loaded once.

**Cons.** All demos must export compatible module graphs. Version mismatches in
shared packages (React 18 vs 18.2, different Zustand versions) cause silent runtime
bugs or hard crashes. Requires all demo teams to adopt a specific build toolchain
and module-federation plugin. Any unhandled error in a remote module can bring down
the host SPA. Incompatible with non-JavaScript demos (Streamlit, static HTML
micro-sites, legacy Angular-1 apps).

**Verdict for PwC showroom.** Not applicable. Tech stack heterogeneity rules it out.


## 2.6 Web Components / Custom Elements

**What it is.** Each demo team compiles their application to a self-contained custom
HTML element (e.g. `<demo-overwatch>`), registered via the browser's
`customElements.define` API with a Shadow DOM for style isolation. The showroom
page loads the demo's JS bundle and places the element tag in the page.

**What Anna sees.** The demo renders inline within the showroom page, visually
integrated but with style isolation via Shadow DOM.

**Pros.** Framework-agnostic — React, Vue, Svelte, Angular Elements, and plain JS
can all compile to Custom Elements. Better style isolation than a raw iframe.
Accessibility and keyboard focus work properly.

**Cons.** All demos must provide a Custom Element build — a non-trivial engineering
investment for each team. Shadow DOM has well-known limitations with forms, portals,
and focus management. The custom element shares the showroom's origin and JavaScript
global scope — a bug or security issue in any demo element can affect the host.
Third-party-cookie restrictions still apply for any API calls the element makes to
its own backend.

**Verdict for PwC showroom.** Interesting for a future "embedded widget" model
(e.g. embedding a demo's KPI tile in a client-facing report), but not appropriate
as the primary launch mechanism for full-application demos.


## 2.7 Backend-for-Frontend (BFF) with Server-Side Composition

**What it is.** The showroom's server fetches each demo's HTML fragment from an
internal API and stitches the fragments together into a composed page before
streaming it to the browser. Historically implemented via Edge-Side Includes (ESI),
Tailor (Zalando), Podium (Finn.no), or Next.js server-components with data from
third-party backends.

**What Anna sees.** A fully composed HTML page — one URL, one visual experience.
Fastest possible Time-to-First-Byte.

**Pros.** Full SEO control. Zero client-side JS coupling. Each demo can be any stack
as long as it exposes an HTML-fragment API.

**Cons.** Requires every demo to expose an HTTP fragment API that the showroom's BFF
can call — a significant, non-standard architectural contract to impose on
independent teams. Any dynamic interactivity requires reconciling multiple JS
runtimes on the client, which eventually reduces to the Module Federation or Custom
Elements problems. Session propagation across BFF-to-demo service calls requires
careful JWT forwarding design.

**Verdict for PwC showroom.** Architecturally interesting but the "expose an HTML
fragment API" requirement is too large an imposition on independent demo teams.
Ruled out.


## 2.8 New-Tab Launch (`target="_blank"`)

**What it is.** Demo tiles are plain `<a>` links with `target="_blank"
rel="noopener"`. Clicking opens the demo in a new browser tab. The showroom catalog
remains in the original tab.

**What Anna sees.** Two open tabs. The catalog is still accessible by switching
tabs. The demo runs in its own tab with its own full viewport.

**Pros.** Zero technical integration beyond an anchor tag. Silent SSO still works
(same Entra ID tenant, new tab is a first-party context). Anna can open multiple
demos in parallel and compare them side-by-side.

**Cons.** Tab proliferation after several demos. Some enterprise browser policies
or popup blockers prevent new-tab opens. No "return to catalog" affordance built in.

**Verdict for PwC showroom.** Excellent as a **secondary option** — surfaced as
a Ctrl/Cmd-click behaviour on any tile, or an explicit "open in new tab" icon
alongside the primary launch button. Not the default.


## 2.9 Deep-Link Handoff with Signed Token (LTI-style)

**What it is.** Before redirecting, the showroom mints a short-lived, signed JWT
(similar to Learning Tools Interoperability 1.3 or SAML deep-link) carrying the
user's identity and optional launch context (demo tier, sales-pitch dataset,
feature flags). The redirect URL includes the token as a query parameter. The demo's
backend validates the token, establishes its own session, and strips the token from
the URL.

**What Anna sees.** Identical to plain redirect — a brief interstitial, then the
demo loads, authenticated and contextualised.

**Pros.** Decouples identity from Entra ID — demos hosted in partner tenants or
external SaaS platforms can be launched without being registered in PwC's tenant.
The token can carry rich context: "show Anna the retail-loyalty dataset", "hide
the admin panel in demo mode", "grant read-only access".

**Cons.** Requires a token validation endpoint on every demo that uses this model.
Token expiry and replay-protection need care. More moving parts than a bare OIDC
redirect.

**Verdict for PwC showroom.** Reserved for **partner-hosted demos** — i.e., any
demo that lives outside the PwC Entra ID tenant. Should be designed as an optional
extension to the catalog registry entry, not a change to the core launch flow.


## 2.10 Screencast / Video Walkthrough

**What it is.** The demo tile plays a pre-recorded screen-capture video (typically
60–180 seconds) with voice-over and on-screen annotations. No live application runs.

**What Anna sees.** A video player inline in the catalog. She watches the demo but
cannot interact with it.

**Pros.** Zero infrastructure cost. No "demo down" incidents. Ideal for demos that
require real customer data or expensive compute resources that cannot be shared
publicly.

**Cons.** No hands-on experience. Feels like marketing material rather than a live
capability. Date-stamps quickly (UI changes make the video stale).

**Verdict for PwC showroom.** Retained as a **fallback tile type** in the catalog
registry. A tile whose `launchType` is `"video"` plays an MP4 rather than
redirecting. Valuable for demos where live access is not feasible.


## 2.11 Static Screenshots + Narrative

**What it is.** A catalog entry links to a static page of annotated screenshots,
architecture diagrams, and a written case study. No application runs.

**Pros.** Zero infrastructure. Communicates the design intent and results of a demo
that may no longer be deployed.

**Cons.** No experiential value.

**Verdict for PwC showroom.** Useful for demos that have concluded (phase wrap-up
pages, past client deliveries) but are still worth referencing in the catalog.


## 2.12 Sandbox Tenant / Read-Only Replica

**What it is.** This is not a launch mechanism but a **data isolation strategy**
used alongside any of the above. The demo's live deployment runs against a
pre-seeded synthetic dataset. Visitors can mutate data freely without affecting any
real dataset or any other visitor's session. Resetting the sandbox is a scheduled
job (daily or after each session).

**What Anna sees.** The real application. She can click "adjust loyalty scoring" or
"delete cohort" without hesitation — the data is synthetic.

**Verdict for PwC showroom.** Mandatory for any demo that allows write operations.
Implemented as a separate ACA environment (or isolated database) per demo, not a
change to the launch pattern.


## 2.13 Live-Piloted Screen-Share (Presales Motion)

**What it is.** The demo tile triggers a WebRTC screen-share session in which a PwC
salesperson (or a controlled AI agent) drives the demo live while the visitor
watches and directs. The visitor never touches the application directly.

**Pros.** Ideal for high-touch enterprise sales where the demo is complex and requires
guided narrative. Eliminates the risk of a visitor reaching a blank state or error.

**Cons.** Requires a human (or orchestrated agent) to be available. Does not scale
to a self-serve catalog.

**Verdict for PwC showroom.** Out of scope for the self-serve showroom. Remains a
valid presales motion in parallel (PwC's traditional sales methodology), but the
showroom is explicitly designed to complement it by providing unguided, 24/7 access.


# 3. UX Comparison — The Three Finalists

The three patterns with the strongest technical case were evaluated in detail.
The following table compares them from the visitor's perspective.

| Dimension | Reverse-Proxy | Redirect + Silent SSO | iframe |
|---|---|---|---|
| URL stays under showroom domain | Yes | No (switches to demo domain) | Yes |
| URL changes reflect demo-internal navigation | Yes | Yes | No — URL is frozen |
| Bookmarkable deep links inside demo | Yes | Yes | No |
| Browser back button navigates demo | Yes | Yes | Often exits demo entirely |
| SSO — third-party cookie restrictions | Not affected | Not affected | Breaks in Chrome, Safari, Firefox |
| Full browser permissions (clipboard, file upload, camera) | Full | Full | Restricted / blocked by policies |
| Full-screen / responsive viewport | Full | Full | Confined to iframe rectangle |
| Demo CSS / JS loaded without rewrites | Risk of breakage from path rewriting | Full fidelity | Full fidelity inside iframe |
| Security isolation (bug in demo cannot affect showroom) | No (same process, same origin) | Yes (separate origin) | Partial (shared origin, nested) |
| Integration cost per new demo | High — new proxy rules per demo | Low — one catalog entry | Medium — iframe wiring, sandbox flags |
| Demo team architectural autonomy | Low | High | Low |
| Risk of surprise breakage from demo change | High (rewrites cascade) | Low | Medium |


# 4. The PwC Choice — Reasoning

The showroom is a **catalog**, not a **shell**. Its job is to authenticate the
visitor, present a curated portfolio, and hand the visitor off to each demo as a
genuine, standalone product. The design intent is that visiting a demo in the
showroom should feel indistinguishable from visiting that demo as a paying client.

That framing directly determines the right model:

- **iframe** was ruled out because modern browser cookie policies make Entra ID SSO
  unreliable inside an iframe. The demo experience degrades in ways Anna cannot
  understand or work around. Non-negotiable disqualifier.

- **Reverse-proxy** was ruled out because path-rewriting is tightly coupled to each
  demo's internal URL structure. A minor internal refactor in Overwatch (changing a
  route from `/dashboard` to `/app/dashboard`) breaks the proxy rules silently for
  all visitors. Adding a new demo requires proxy engineering. The integration cost
  does not meet the "low cost per new demo" constraint.

- **Redirect + Silent SSO** meets every constraint:
  - Heterogeneous stacks — irrelevant; the showroom only needs the demo's launch URL.
  - Independent deploy cycles — adding a demo is a JSON entry in the catalog registry.
  - Full browser capabilities — the demo runs on its own origin with no restrictions.
  - Silent authentication — Entra ID issues a new session cookie silently if Anna is
    already signed in to the tenant.
  - Authentic experience — Anna is using the real product.

The perceptive cost — the brief transition as the origin changes — is acceptable
and can be further softened with a branded interstitial page. It aligns with the
mental model PwC wants to convey: *"Here is a portfolio of real products. I am
now going to show you the first one."*

## Secondary patterns retained

The core model is redirect + silent SSO, complemented by:

- **New-tab launch** — available on every tile via Ctrl/Cmd-click, or via an
  explicit icon. Useful for visitors who want to compare two demos side-by-side.

- **Deep-link with signed token** — used for any future demo hosted outside PwC's
  Entra ID tenant (partner demos, third-party SaaS integrations).

- **Sandbox tenant** — mandatory for any demo that allows data mutation. The
  synthetic dataset is pre-seeded and reset daily.

- **Video fallback tile** — used when a demo cannot run live (expensive compute,
  sensitive data, demo decommissioned). The catalog tile type changes to `"video"`;
  no other change to the launch infrastructure.


# 5. User Journey — Anna Visits Three Times

The same visit, told through each of the three finalist models.

## 5.1 Redirect + Silent SSO (the actual experience)

Anna navigates to `showroom.pwc.com`. She signs in once via Entra ID. She browses the
catalog, sees the Overwatch tile, and clicks it. A branded page appears briefly:
"Launching Overwatch — Retail Loyalty Intelligence." Two seconds later Overwatch's
dashboard fills the tab. The URL bar now reads `overwatch.pwc.com`. Anna explores
the demo for twenty minutes, bookmarks the churn-cohort view, shares it with a
colleague. She clicks the browser back button once and is back on the showroom
catalog. She clicks the next tile.

Her colleague follows the bookmark. Entra ID recognises her existing sign-in and
issues an Overwatch session silently. She lands on the exact dashboard view Anna
bookmarked. She closes the tab and continues her day.

## 5.2 Reverse-Proxy (not chosen — illustrated for contrast)

Anna clicks the Overwatch tile. The URL bar changes to
`showroom.pwc.com/demos/overwatch/`. Overwatch's UI appears below the showroom's
header. She clicks "Generate Churn Report." Overwatch's frontend issues a POST to
`/api/reports` — the proxy rewrites it to the internal host. It works. She tries to
download the report PDF. The PDF URL is hardcoded to the internal hostname in the
response headers; the download fails with a 404. Anna calls support.

## 5.3 iframe (not chosen — illustrated for contrast)

Anna clicks the Overwatch tile. The showroom's header and footer stay visible. An
embedded rectangle below the header shows "Sign in with Microsoft." She clicks it.
A popup window opens (Entra ID needs a popup because it cannot set cookies in a
third-party iframe context). Her browser's popup blocker may have blocked it. If it
opened, she signs in. The popup closes. Overwatch now loads in the iframe. She
tries to maximise a chart. It fills the iframe rectangle but not the screen. She
finds the "Download CSV" button. The browser blocks the download (iframe `sandbox`
attribute did not include `allow-downloads`). She copies a URL from Overwatch's
own navigation bar — it points to `overwatch.pwc.com/dashboard`, which works when
pasted in a new tab but is invisible to the showroom's analytics.


# Appendix — Decision Matrix

| Pattern | Heterogeneous stacks | Independent deploy | Full browser capabilities | Silent SSO | Low cost per demo | Fit |
|---|---|---|---|---|---|---|
| Single SPA monorepo | No | No | Yes | Yes | No | Not applicable |
| Reverse-proxy | Yes | No (proxy rules) | Yes | Yes | No | No |
| Redirect + silent SSO | Yes | Yes | Yes | Yes | Yes | **Primary** |
| iframe | Yes | Yes | No | No | Yes | No |
| Module Federation | No | Yes | Yes | Yes | No | Not applicable |
| Web Components | Partial | Yes | Partial | Partial | No | Future widget use |
| BFF server-side composition | Yes | No (fragment API) | Yes | Partial | No | No |
| New-tab launch | Yes | Yes | Yes | Yes | Yes | Secondary |
| Deep-link with signed token | Yes | Yes | Yes | Yes | Medium | Future (partners) |
| Screencast / video | Yes | Yes | n/a | n/a | Yes | Fallback tile |
| Static screenshots | Yes | Yes | n/a | n/a | Yes | Legacy archive tile |
| Sandbox tenant | Yes | Yes | Yes | Yes | Medium | Companion strategy |
| Live-piloted screen-share | Yes | Yes | n/a | n/a | No | Out of scope |
