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
