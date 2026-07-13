---
title: "Aegon Launchpad Platform Architecture"
---

## Purpose

This document explains the Aegon Launchpad platform architecture from a PwC
engagement perspective. It describes the three-account topology, the two VPCs
inside the Line-of-Business account, and the runtime traffic model that governs
every AI call made by a lighthouse application.

Read this document first before reading any of the persona-specific workflow
documents in this folder.

## Architecture diagram

![Platform architecture](platform-architecture.png)

## Account topology

Launchpad is built on three AWS account tiers.

**CI/CD account (Launchpad-owned).** Owns the platform's own Git repository,
CodePipeline, CodeBuild, ECR, and security scanning (Snyk, SonarCube). This
account is entirely managed by the Launchpad team. PwC has no access and no
responsibilities here.

**Launchpad core account (Launchpad-owned).** Hosts the web UI (ECS Fargate
containers), model management, tenant management, and the blueprint catalogue.
Authentication uses Cognito federated to the corporate Azure AD. PwC engineers
with the Tenant Admin role log in here to provision blueprints and generate API
keys. This is the only Launchpad account PwC regularly interacts with.

**Line-of-Business (LOB) account (shared).** The account where lighthouse
applications actually run. It contains two physically separate VPCs.

## The two VPCs inside the LOB account

### Launchpad VPC (Launchpad-owned, immutable)

Provisioned and managed entirely by the Launchpad team via cross-account STS
deployment. PwC cannot modify anything in this VPC.

It contains:

- ALB with TLS termination -- the single entry point for all model calls.
- Router (Lambda) -- authorises every request using API key and HMAC signature.
- Guardrail (Bedrock) -- applies the guardrail policy bound to the API key.
- Amazon Bedrock -- the underlying model invocation service.
- Agent Core runtime (optional) -- an optional blueprint for use cases that
  require MCP tool wiring or agent-to-agent (A2A) communication.

**Hard rule: no data of any kind is permitted to reside in this VPC.** It is
designed to be stateless and immutable. Databases, documents, caches, queues --
all state lives in the Business VPC.

### Business VPC (PwC-owned)

Provisioned by PwC using Terraform via our own GitHub Actions pipeline. This is
where all lighthouse application code and data infrastructure live.

It contains everything PwC builds: the LangGraph orchestrator, tool functions,
databases (DynamoDB, OpenSearch, Aurora), document storage (S3), scheduled jobs
(EventBridge), notification services (SES/SNS), and the Secrets Manager entries
that hold API keys and HMAC secrets.

The two VPCs communicate through a Transit Gateway. PwC does not configure the
Transit Gateway -- that is Aegon's network team.

## Runtime traffic model

Every model call from a lighthouse follows this path:

1. The lighthouse application reads the router ALB hostname, API key, and HMAC
   secret from Secrets Manager.
2. The application signs the request payload with the HMAC secret and sends an
   HTTPS POST to the router ALB.
3. The router Lambda validates the API key and HMAC signature.
4. The router applies the guardrail policy bound to that API key.
5. Bedrock invokes the configured model and returns the completion.
6. The response travels back to the application along the same path.

**The application never calls Bedrock directly.** There is no boto3
bedrock-runtime client in PwC code. The router is the only permitted entry
point to any model.

## Blueprints

A blueprint is a versioned, ARB-approved, immutable deployable capability
managed by the Launchpad team. Current blueprints include:

- LLM router (the ALB + HMAC layer described above)
- Guardrail configuration wrapper
- Agent Core runtime (for MCP/A2A use cases)
- Model evaluation harness
- Guardrail evaluation harness

Blueprints are provisioned by a Tenant Admin logging into the web UI and
selecting from the catalogue. They are not provisioned via Terraform.
Blueprint upgrades create a new parallel instance; the old one is deleted only
after the application has been pointed at the new API key.

## What PwC owns vs what Launchpad owns

| Layer | Owner | How provisioned |
|---|---|---|
| Bedrock, guardrails, router, Agent Core | Launchpad team | Launchpad CI/CD + Web UI |
| ALB blueprints in LOB account | Launchpad team | Cross-account STS deploy |
| Transit Gateway, VPC endpoints | Aegon network team | Aegon governance process |
| Business VPC networking | Aegon provisioning lead | Aegon governance (10-day SLA) |
| All Business VPC services (DB, S3, app) | PwC | Our Terraform + GitHub Actions |
| LangGraph orchestration code | PwC | Our GitHub repos + CI/CD |
| Secrets Manager entries | PwC DevOps | Our Terraform |
| API keys and HMAC secrets (source) | Launchpad Tenant Admin | Web UI |

## Onboarding sequence

Before PwC can deploy any application, the following must happen in order:

1. Request the LOB account landing zone from the Aegon provisioning lead.
   Allow approximately 10 working days for the network team to provision the
   Business VPC and Launchpad VPC in the account.
2. Launchpad team connects the Launchpad VPC to the Transit Gateway.
3. PwC Tenant Admin logs into the web UI, provisions the router blueprint and
   guardrail blueprint, and generates one API key per lighthouse.
4. PwC DevOps stores API key and HMAC secret in Secrets Manager.
5. PwC CI/CD pipeline provisions Business VPC infrastructure (Terraform).
6. PwC CI/CD pipeline deploys lighthouse application code.
7. Application is live and calling models through the router.

The earliest realistic date for step 7 is approximately 1 August 2026, assuming
the landing zone request is submitted in the week of 14 July 2026.
