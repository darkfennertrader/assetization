# Aegon Platform Working Documents

This folder contains PwC's internal reference documentation for the Aegon
Launchpad platform. It is written for the PwC delivery team and covers the
platform architecture, and the working model for each role on the engagement.

These are **internal PwC working documents**, not client deliverables. Role
names are generic so the material can be genericised for reuse on other
accounts.

## One-line summary of the platform

Launchpad is a paved road: it provides a versioned, immutable router blueprint
(ALB + HMAC authentication + guardrails + Bedrock model access), provisioned
via a web UI into a dedicated VPC in our AWS account. PwC builds lighthouse
applications in a separate Business VPC and calls the router over HMAC for
every LLM inference. The router is the only permitted path to any model.
Everything else -- orchestration, data, tools, UI -- is ours to design and
build.

## Documents in this folder

| File | Audience | What it covers |
|---|---|---|
| `business-view.md` | PwC partners, engagement leads, business audience | Platform overview in plain language, five ownership zones, two speeds of delivery |
| `platform-architecture.md` | Everyone | Account topology, two-VPC model, blueprints, onboarding sequence |
| `developer-workflow.md` | Software developers | What to own, what to never touch, the dev loop, key rules |
| `devops-workflow.md` | DevOps engineers | Two-pipeline model, credentials handoff, environment strategy, blueprint upgrades |
| `architect-workflow.md` | Solution architects | Design decisions, orchestration patterns, exception process, stakeholder routing |

Each document has a companion `.dot` diagram rendered to `.png` by
`build_all.sh`.

## Diagrams in this folder

| File | What it shows |
|---|---|
| `business-view.dot` | Five ownership zones and nine-step request flow (business audience) |
| `data-governance.dot` | Synthetic data fast lane vs real data governed lane |
| `platform-architecture.dot` | Full account topology and runtime traffic flow |
| `developer-workflow.dot` | Developer's local loop, CI/CD, and cloud runtime |
| `devops-workflow.dot` | Two-pipeline model and environment lifecycle |
| `architect-workflow.dot` | Design phase, decision gates, and stakeholder routing |
| `decision-tree.dot` | LangGraph vs Agent Core orchestration decision |

## How to regenerate PDFs and PNGs

Run from the repo root:

```bash
bash Aegon/platform/build_all.sh
```

This renders all `.dot` files to `.png` and all `.md` files (except this
README) to `.pdf` using the shared pdf-toolkit.

## Key principles (one line each)

- Every LLM call goes through the router blueprint. No exceptions.
- All data lives in the Business VPC. The Launchpad VPC is stateless.
- Blueprints are immutable. Upgrades deploy a new version alongside the old.
- Credentials (API key + HMAC secret) flow from the web UI into Secrets Manager.
- All environments (dev, test, prod) call the same Launchpad production router.
- Default orchestration pattern is LangGraph in the Business VPC.
- Agent Core is selective: use only when MCP or A2A is genuinely required.
- Ask before building: unknown components go through the exception process.
- Synthetic data first: real data requires governance approval per data source.
- One API key per lighthouse: separate logs, separate cost attribution.
