---
title: "PwC AI Platform Vision — Three-Tier Architecture"
author: "Raimondo Marino — Solution AI Architect"
date: "2026-07-09"
---

## The problem we are solving

In three years PwC will have fifteen or more AI applications. The only question is whether we build them fifteen times or once. Right now, every project that lands on someone's desk gets its own identity system, its own API gateway, its own observability stack, its own audit trail. That is not wrong for the first two apps — it is unavoidable. But it is a serious problem from the third app onwards, because every new project duplicates the same plumbing, requires its own maintenance, and multiplies the cost of every future security patch and compliance audit.

The architecture I want to walk you through is the answer to that problem.

## Three tiers — top to bottom

At the top, **Tier 1 — User Surfaces.** This is what people see. Two products live here. The **Showroom** is external-facing: a salesperson generates a QR code, a prospect scans it, and they get a live AI demo for one hour. No account created, no data retained. The **Marketplace** is internal: PwC employees browse a catalogue of certified AI assets, try them in a sandbox, and adopt them into their engagement in a few clicks. Both products call the same shared foundation underneath. Optional bespoke frontends for specific engagement apps also live at this tier, but most apps should aim to have no dedicated UI at all — more on that in a moment.

In the middle, **Tier 2 — Shared Control Plane.** This is the security and governance layer that every request passes through, no exceptions. Azure API Management is the gateway: it validates tokens, enforces rate limits, runs safety filters, tags every request with cost-centre metadata, and writes a tamper-proof audit log. Entra ID handles PwC staff authentication; Entra External ID handles external guests and clients. A fine-grained authorisation service — such as OpenFGA — enforces relationship-based permissions for complex multi-tenant scenarios. Key Vault holds all secrets. **This tier is built once and never duplicated per project.** Every future app inherits it for free.

At the bottom, **Tier 3 — Capabilities.** This is where the actual AI logic lives. Assets here are packaged as independent services and exposed through a uniform **MCP (Model Context Protocol) or A2A (Agent-to-Agent) interface contract**, so any consumer above can call them without knowing how they are built. Three runtime options exist. **Azure Container Apps** is the default: small containers, stateless orchestrators, and most MCP tool servers run here — scales to near-zero cost when idle. **Databricks** is for data-heavy workloads: agents that reason over a Data Lakehouse, run Spark queries, or serve fine-tuned models sit here, governed by Unity Catalog, with no data egress. **AKS** covers heavy workloads where ACA is not enough — GPU inference at scale, complex sidecar architectures. The runtime is an implementation detail; the MCP contract is the same regardless.

## Two audiences, two paths

**PwC employees** reach the Marketplace and its MCP tools through their existing dev tools — Copilot inside VS Code, Cursor, Claude Desktop, or internal LangGraph agents — over the PwC corporate network or VPN. Traffic never touches the public internet; it resolves to a private APIM endpoint through Entra ID SSO. The developer adds a two-line config pointing at the internal Marketplace URL and every certified tool appears inside their IDE.

**External clients** follow a completely different path. We do not give them access to the PwC Marketplace. Instead, when an engagement starts, the relevant Tier 3 assets are deployed **into the client's own Azure subscription** as signed, versioned containers pulled from the PwC registry. The MCP server runs inside their infrastructure. Their data never crosses into PwC, and once provisioned the client environment has no live connection back to us.

## What an MCP server actually is

An MCP server is a thin, protocol-compliant wrapper around a business logic component — roughly 50 to 150 lines of code using the official SDK. It advertises its tools via a standard discovery call and executes them when invoked. The wrapping represents about 10 to 15 percent of the total build effort; the business logic is the other 85 to 90 percent. That small tax converts a project-specific service into a Marketplace-shareable, portable, IDE-consumable asset that can be deployed either in PwC's own infrastructure for internal use or in a client's tenant as deployed infrastructure for engagement use — from the same signed container image, with no rebuild.

## Short-term, medium-term, and the honest trade-off

Short-term, existing projects ship on schedule. Nothing stops. In the medium term, we designate the first two apps as substrate-compatible and ring-fence roughly 20 percent of each project budget as a platform tax to build Tier 2 and the Tier 3 scaffolding once. The economics turn positive between the third and fifth application, because each new app contributes only its business logic — Tier 2 and Tier 3 are already there.

The honest trade-off: year-one cost is higher than building three siloed apps. The substrate pays back from year two and compounds every year after that. Two conditions must hold. First, the substrate must be self-service — IaC modules and certified images that a team deploys in a day, not a ticket queue that takes a week. Second, MCP is an interface bet: if the protocol evolves, we update the shim, not the business logic.

## The ask

Approve the first two apps as substrate-compatible. Fund the 20 percent platform tax on those two. Staff a small platform team — two or three people, six months to get the substrate to production quality. After that, every new engagement pulls from what already exists.

Two audiences. Three tiers. One MCP contract. Built once.
