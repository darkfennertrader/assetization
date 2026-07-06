# docs/ — Index

> **Project:** PwC AI Assetization · Solution AI Architect: Raimondo Marino
>
> All documents are client-sanitized and suitable for internal and external use unless noted otherwise.

---

## Architecture documents

| File | What it is | Audience |
|---|---|---|
| **`ara-a-reference-architecture.md`** | Full reference architecture (ARA-A) — 6-layer Azure service map, two delivery profiles, phased sequencing, KPIs, trade-offs. The anchor document everything else references. | Architecture review board, engagement leads |
| **`ara-a-showroom-marketplace.md`** | One-page overview in Adrian's vocabulary (Marketplace / Showroom / Knowledge Base). Team-facing. Includes build-order timeline and team ownership split. | Full team, Adrian, client meetings |
| **`ara-a-showroom-marketplace.dot`** | Graphviz source for the architecture diagram. Edit and re-render to PNG with `dot -Tpng ara-a-showroom-marketplace.dot -o ara-a-showroom-marketplace.png` | Diagram maintainers |
| **`ara-a-showroom-marketplace.png`** | Rendered architecture diagram (auto-generated from `.dot`). Use in slides and Teams. | All |
| **`auth-design-note.md`** | Authentication & authorisation design note — Entra ID, Entra External ID, 1-hour QR-code credential flow, OpenFGA, APIM enforcement, decision log (D1–D9), open questions for Friday. | Michael (implementer), Raimondo, InfoSec review |
| **`friday-agenda.md`** | Agenda for Friday 2026-07-04 09:00–10:00 CET meeting. Includes pre-reads, two questions to send Adrian today, timebox per topic, and next-week deliverable table. | Raimondo, Michael |

---

## Research & playbook

| File | What it is |
|---|---|
| **`AI Assetization playbook.md`** | PwC AI Assetization & Acceleration Playbook v1.0 (May 2026). The method-as-product document. |
| **`agent-assetization-research.md`** | Agent Assetization on Azure & Databricks — architectural patterns research report (June 2026). Source for ARA-A service choices. |
| **`agent-assetization-research.pdf`** | PDF version of the research report. |

---

## Diagrams & tooling

| File | What it is |
|---|---|
| **`decision-tree.dot`** | Graphviz source for the research decision tree (Q1–Q6 architecture selector). |
| **`decision-tree.png`** | Rendered decision tree. |
| **`build_all.sh`** | Regenerates all PDFs and PNGs in this directory. Run: `bash docs/build_all.sh` |

**PDF styling assets** (pandoc defaults, LaTeX header, Lua filter, Mermaid config) have been
moved to `.clinerules/pdf-toolkit/` so they can be reused across repos.
See `.clinerules/pdf-toolkit/README.md` for installation instructions and the build template.

---

## Reading order (for new team members)

1. `AI Assetization playbook.md` — understand the *why* and the method
2. `agent-assetization-research.md` — understand the Azure/Databricks building blocks
3. `ara-a-reference-architecture.md` — the synthesised, opinionated architecture
4. `ara-a-showroom-marketplace.md` + `.png` — the team-facing view
5. `auth-design-note.md` — if you are working on auth / the showroom

---

## How to regenerate the diagram PNG

```bash
cd docs/
dot -Tpng ara-a-showroom-marketplace.dot -o ara-a-showroom-marketplace.png
dot -Tpng decision-tree.dot -o decision-tree.png
```

Requires `graphviz` (`sudo apt install graphviz` on Ubuntu/Debian).

---

*Last updated: 2026-07-01 · Owner: Raimondo Marino*
