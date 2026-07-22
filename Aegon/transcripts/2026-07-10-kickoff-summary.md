---
title: "Aegon Kick-off Meeting Summary: Platform Architecture and Onboarding"
---

## Meeting Details

**Date:** 10 July 2026
**Format:** Video call (recorded)
**Duration:** approximately 60 minutes

**Attendees**

- Jan Helcl -- Lead ML/AI Engineer, PwC CZ (meeting facilitator)
- Raimundo -- Solution AI Architect, PwC
- Mark -- Aegon Group Finance (business sponsor, tenant admin role)
- Nathalie -- Aegon (programme lead)
- Stuart -- External consultant to Barrington, representing the Aegon
  Launchpad platform team

## Purpose

A technical deep-dive into the Aegon Launchpad platform -- the
infrastructure on which the five Finance AI lighthouses will be built.
The session was intended to give PwC (especially Raimundo, who had not
attended the prior IT discovery session) a full picture of the platform
before design work begins the following week.

## Programme Context Recap

Aegon and PwC will co-develop five AI lighthouses for Group Finance.
The project starts the week of 14 July 2026. The first few weeks are
dedicated to design and requirements refinement. From approximately
week 5, the plan is either to hand over to Aegon builders or to
co-develop. The five lighthouses are already scoped at a high level;
exact use-case scope is still being refined.

A key constraint raised early: Dean Holland's central technology team
(which owns the Launchpad platform) is fully committed for the rest of
the year. PwC is being brought in partly to accelerate delivery within
the existing AI guardrails and avoid duplication between Transamerica
Finance and Corporate Finance.

## Platform Overview: Aegon Launchpad

Stuart walked through the Launchpad platform architecture. All of the
following is AWS-native.

### Account structure

The platform is built across three separate AWS account types.

**CICD account** -- the management and orchestration account. Uses AWS
CodePipeline and CodeBuild with Snyk, SonarCube, and unit testing
integrated. This account drives deployments into all other accounts.

**Core (Launchpad) account** -- provisioned by the CICD account.
Contains the central web UI, model management, tenant management,
blueprint management, and the ALB-based AI router. All functions are
Lambda-based (serverless). The web UI runs on scalable ECS containers.
Authentication uses AWS Cognito backed by Azure Active Directory (the
Aegon internal IdP). JML (Joiners, Movers, Leavers) is managed through
internal AD groups.

**Line-of-business (BU) account** -- the account where lighthouse
applications actually live. The Launchpad team provisions a dedicated
Launchpad VPC inside this account (separate from the existing business
VPC) via a cross-account STS deployment triggered from the CICD account.

### Networking

Every account follows the same VPC template: routable and
non-routable subnets, account-specific VPC endpoints (centralised
endpoints are on the roadmap but not yet implemented). The Launchpad
VPC within the BU account is deliberately isolated from the business
VPC to prevent contamination.

Cross-account and cross-VPC communication is routed through a Transit
Gateway. Deep packet inspection is enforced at the Transit Gateway
boundary, which is why NLB endpoints cannot be used -- only ALB
endpoints are permitted (ALB traffic can be inspected; NLB traffic
cannot).

### Request flow

An application in the business VPC makes an HTTPS call to the
Launchpad ALB using:

- an API key (created by the tenant admin in the web UI)
- an HMAC signature (message data plus HMAC ID)

The router validates both. On success it applies the model and
guardrail configuration bound to that API key and forwards the request
to Amazon Bedrock. The response follows the same path back. No data is
stored inside the Launchpad VPC -- all databases and persistent storage
must reside in the business application VPC.

### Web UI roles

Four roles exist in the platform:

- **Platform Admin (Launchpad team)** -- sets up tenants and assigns
  accounts to tenants; cannot deploy blueprints.
- **Tenant Admin (business unit)** -- provisions blueprints, creates
  API keys, configures model and guardrail bindings; generates the
  credentials used by developers.
- **Tenant Reader** -- read-only view of the tenant configuration.
- **App Developer** -- deploys the lighthouse application and
  configures it to call the router using tenant-admin-supplied
  credentials.

### Blueprints

A blueprint is a versioned, immutable unit of infrastructure. The ALB
router is a blueprint. Guardrails are a blueprint. Deploying a new
version does not replace the old one -- both run in parallel until the
application is pointed at the new ALB and the old gateway is deleted.
This enables zero-downtime upgrades and safe rollback.

### Agents (released May 2026)

AWS Bedrock Agent Core and Agent Core Gateway have been integrated into
the Launchpad. Because Agent Core and Agent Core Gateway are only
supported in three of the six availability zones in US East 1, the
Launchpad team has fixed the zone assignments to guarantee reliable
deployment. Centralised VPC endpoints with a private hosted zone
redirect are used for agent-to-runtime calls.

Ten agent patterns are documented and approved through the Aegon
Architecture Review Board (ARB):

- Direct agent invocation
- Agent to agent (A2A)
- MCP (Model Context Protocol) -- internal and external
- Through Lambda functions
- Agent Core Gateway to containers
- And additional combinations of the above

All patterns have sample code available. Stuart confirmed that using
custom frameworks such as LangGraph is acceptable provided the
components are AWS-supported and, if not yet approved by Aegon, are
submitted through the standard component approval process. Nothing is
treated as a blocker -- new components can be approved by working with
Stephanie Reynolds in Dean's architecture team.

### Environment lifecycle

All environments (dev, test, QA, production) within BU accounts connect
to the Launchpad **production** environment. This is intentional: you
always want your application consuming stable, production-grade
Launchpad code regardless of which stage of your own SDLC you are in.

Data classification governs where an account sits in the AWS
Organisational Unit (OU) hierarchy, not the application's lifecycle
stage. If development or test work uses production-level data, that
account must sit in the production OU and be subject to production
security controls.

### Scale as of 10 July 2026

52 gateway VPC instances are currently deployed or in deployment across
Aegon. Use cases include two security applications, an internal chat
product (Luminar), multiple Spain-based applications, and several
Corporate Finance applications. The number of deployed gateways grew
from the thirties to 52 in roughly one month.

## Key Decisions and Action Items

### Onboarding: landing zone request

Before PwC or the Finance team can develop on the platform, Aegon must
provision a development environment (a Launchpad VPC inside a BU
account). Mark confirmed he will initiate this request the week of
14 July 2026 by contacting Steve Kiss, who manages the onboarding
process. The SLA for building the VPC is approximately 10 business
days (best case faster, depending on the network team). The Launchpad
team gave a target of 1 August 2026 for the environment to be ready,
trained, and fully operational.

Once the landing zone is ready, PwC colleagues can be added as users.
The Launchpad team will provide onboarding training covering tenant
admin operations, HMAC authentication, blueprint provisioning, and
troubleshooting.

### One environment for all five lighthouses

Raimundo asked how to structure the environment across five use cases
without duplicating resources. Stuart's recommendation: use a single
Launchpad gateway VPC for all five lighthouse applications in
development, with each lighthouse application using its own API key.
This keeps logs, billing, and configuration separated per application
while sharing the underlying infrastructure. Separate gateway
blueprints within the same VPC are only needed if traffic prioritisation
between applications becomes a requirement.

### Prototype and MVP path

The HTML demos already exist. To move them toward a more advanced
prototype (real LLM, mock data, no full MVP governance), all work
should start in the development environment. If real data is introduced,
the account must meet production-OU governance requirements even if the
application itself is still in development. Mark's team will help
navigate the data governance steps when that point is reached.

### Custom frameworks

LangGraph and similar low-level frameworks are acceptable. If a
component is not yet on the Aegon-approved list, the path is to work
with the architecture team (Stephanie Reynolds) to get it approved.
Stuart emphasised this is not a blocker -- it just adds a small amount
of process overhead.

### Support boundaries

The Launchpad team provides: platform training, onboarding support,
blueprint documentation, sample code, and warranty-period debugging
assistance. They do not provide: application code development, extended
debugging sessions on business application code, or Terraform/IaC
coaching. PwC (as the development partner) is expected to have
sufficient DevOps capability to build and deploy the lighthouse
applications independently.

## Architect's Reflections (PwC Perspective)

The following observations are relevant for the PwC team going into the
design phase.

**The platform is mature and permissive.** The Launchpad is further
along than a typical enterprise AI guardrail layer. It is genuinely
enabling -- the guardrail can be set to "none" in development, model
management is centralised, and the governance overhead is auditable
rather than blocking. This is a positive starting condition.

**The 10-day VPC onboarding SLA is the critical path.** If the landing
zone request is not submitted in the week of 14 July, the 1 August
target slips. PwC should treat this as the single most urgent
dependency to track in week 1.

**Separate API keys per lighthouse from day one.** Stuart's best
practice recommendation should be treated as a non-negotiable design
decision. Mixed logs will make debugging and cost attribution
impossible at scale.

**LangGraph is viable but needs early approval.** If the lighthouse
designs require fine-grained agent orchestration (which is likely for
Lighthouses 1, 2, and 4), a LangGraph approval request should be
submitted in parallel with design work, not after prototyping begins.

**Data governance will be the slower gating factor.** The platform
itself is ready relatively quickly. Access to real Aegon Finance data
(even for prototyping) requires a separate governance step. This needs
to be initiated in week 1 of design for every lighthouse, in parallel,
so it does not block prototype testing in weeks 4 to 5.

**No data inside the Launchpad VPC.** All databases, document stores,
and retrieval indexes for the lighthouses must live in the business
application VPC, not in the Launchpad gateway VPC. This is an
architectural constraint with implications for how RAG pipelines
(Lighthouses 2 and 4) and anomaly detection storage (Lighthouse 3)
are designed.

**Agent patterns are pre-approved and well-documented.** The ten ARB-
approved agent patterns with sample code reduce the design risk
significantly. PwC should map each lighthouse to one or more of these
patterns early in the design phase and only deviate where there is a
clear functional requirement that the patterns cannot satisfy.
