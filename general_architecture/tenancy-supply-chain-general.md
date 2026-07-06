---
title: "PwC AI Platform — Generalised Tenancy Supply Chain"
author: "Raimondo Marino — Solution AI Architect"
date: "2026-07-02"
---

# Generalised Tenancy Supply Chain

The platform separates two concerns that must never mix: **supply** (what PwC builds and certifies) and **runtime** (what executes inside the client's environment). The diagram captures this as three zones: PwC tenant on the left, a deploy-time-only pipeline in the middle, and the client tenant on the right.

## Supply side — PwC Marketplace

The PwC Marketplace CI/CD pipeline builds, signs, scans, and publishes six categories of artefact:

- **Bicep / Terraform modules** — infrastructure-as-code for the full substrate: identity, gateway, agent runtime, observability, and the optional Databricks module.
- **Signed container images** — LangGraph runtime, Showroom BFF, Marketplace portal, MCP tool servers, Knowledge Base UI.
- **Private PyPI packages** — shared Python libraries: `pwc-mcp-tools`, `pwc-agent-sdk`, `pwc-langgraph-common`, `pwc-observability`.
- **APIM Policy Library and Prompt Library** — versioned gateway policies, HITL configuration, system prompts.
- **Databricks Asset Bundles (DAB)** — Unity Catalog seed definitions, DLT pipeline templates, Vector Search index definitions, MLflow model bundle configurations.
- **MLflow baseline models** — signed foundation models published via Delta Sharing for deploy-time pull into the client's MLflow Model Registry.

Nothing is pushed into a client tenant. Everything is pulled by the deployment pipeline.

## Deploy time — the only crossing point

A PwC engineer activates the deployment pipeline with JIT B2B access, federated Entra ID identity, and MFA. The pipeline pulls artefacts from all six sources and provisions them into the client's subscription. This is the only moment anything crosses the tenant boundary. After provisioning completes, the access is revoked. There is no persistent connection between PwC and the client tenant at runtime.

## Client tenant — runtime side

The client tenant contains two independently deployable layers:

**Shared Substrate (always deployed):** Azure Front Door and WAF as the edge, APIM enforcing the PwC-supplied policies, LangGraph runtime on Azure Container Apps for lightweight orchestration agents (Showroom demos, workflow, chat), MCP Tool Servers providing specific capabilities (/rag, /extract, /anomaly, /notify), Entra ID for staff SSO and Entra External ID for guest access, and Observability (App Insights, LangSmith, Event Hub → ADLS audit log, Key Vault). All runtime traffic stays entirely within the client subscription.

**Databricks module (optional — lakehouse-native tenants):** Unity Catalog as the governance plane with per-client catalog isolation, Delta Lake with Lakehouse Federation for governed access to existing client systems (SQL Server, SAP, Oracle, Snowflake), Databricks Vector Search for RAG over client documents (governed by Unity Catalog permissions), MLflow Model Registry for custom and fine-tuned models, and Databricks Model Serving hosting data-heavy agents that run next to the data with no egress. APIM routes data-heavy agent requests directly to Databricks Model Serving; the Azure-native LangGraph runtime handles all other agent classes. For tenants not on Databricks, Azure AI Search and Azure ML Endpoints are used in place of the Databricks components — the architecture is identical, the implementations are pluggable.

## The runtime boundary rule

**No client data ever crosses into the PwC tenant.** Client data is accessed read-only by MCP tools (Azure-native path) or via Unity-Catalog-governed queries by Databricks Model Serving (Databricks path) — always inside the client's own subscription. The only artefacts that cross the boundary are signed, versioned, and pulled at deploy time, never pushed at runtime.
