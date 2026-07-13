---
title: "PwC Developer Guide: Working on Aegon Launchpad"
---

## Purpose

This document describes the day-to-day working model for a PwC software
developer building lighthouse applications on Aegon Launchpad. It covers
what a developer owns, what they must never touch, how the development loop
works, and the key rules that apply from day one.

## Workflow diagram

![Developer workflow](developer-workflow.png)

## What a developer owns

A PwC developer is responsible for everything that lives inside the
Business VPC and in the GitHub lighthouse repositories:

- LangGraph orchestration graphs and agent state machines.
- Tool functions (Python functions that query databases, retrieve documents,
  call external APIs).
- Application service code (ECS tasks, Lambda handlers, API Gateway routes).
- Data infrastructure definitions in Terraform (DynamoDB tables, OpenSearch
  domains, S3 buckets, SQS queues, EventBridge rules).
- Unit tests, integration tests, and evaluation harnesses.
- The HMAC signing helper used to sign every outbound model call.
- Prompt templates and system prompts.

## What a developer must never touch

The following are owned by the Launchpad team and are off-limits:

- The Launchpad VPC and any resource inside it.
- The router Lambda, the ALB, the guardrail configuration.
- Amazon Bedrock directly -- no `boto3.client("bedrock-runtime")` in
  application code.
- The Launchpad web UI (that is the Tenant Admin role, not the developer role).
- The Launchpad CI/CD account and its pipelines.

If a developer's code contains any of these, the design is wrong.

## The development loop

### Step 1 -- Local development

Clone the lighthouse repository and run LangGraph locally. For local
development, replace the Launchpad router with a lightweight HTTP stub
that returns canned model responses. This allows full local iteration
without incurring Bedrock costs and without requiring cloud credentials.

Keep all tool functions as plain Python functions with no cloud
dependencies wherever possible, so they run identically on a laptop
and in the cloud.

### Step 2 -- Branch and pull request

Push a feature branch and open a pull request. The standard GitHub PR
review process applies. Code review must cover:

- HMAC signing logic (any regression here breaks all model calls).
- Data access patterns (ensure no cross-VPC data movement is introduced
  inadvertently).
- Prompt changes (treat prompts as code; version them, review them,
  test them).

### Step 3 -- CI/CD pipeline

On merge to main, GitHub Actions triggers two jobs:

1. Terraform job -- applies any infrastructure changes to the Business VPC
   (new tables, new indexes, new queues, etc.).
2. Application job -- builds the container image, pushes to ECR, updates
   the ECS service or Lambda function.

The pipeline reads the router ALB hostname, API key, and HMAC secret
from Secrets Manager and injects them as environment variables into the
deployed service. The developer does not manage secrets manually.

### Step 4 -- Cloud testing

All cloud environments (dev, test, prod) point at the same Launchpad
production router. There is no Launchpad sandbox. Every model call is a
real Bedrock call with real cost.

Test with synthetic data in dev and test environments. Do not load real
production data into any environment until the data governance workstream
has cleared it.

### Step 5 -- Debugging

Application logs, LangGraph traces, and tool call timings all live in
the Business VPC CloudWatch log groups, which PwC controls. Launchpad
maintains a separate audit log of router calls (keyed by application ID
from the API key). To correlate a failed model call with the router log,
use the request ID that the router returns in the response header.

If a model call is rejected by the guardrail (HTTP 403), the issue is
either a prompt that triggers a guardrail rule or a misconfigured API key
binding. Contact the Tenant Admin role holder to check the guardrail
configuration -- the developer cannot change guardrails directly.

## Key rules for developers

**Rule 1 -- No direct Bedrock calls.**
All model invocations go through the router ALB using the HMAC-signed
HTTP call pattern. The router endpoint, API key, and HMAC secret come
from Secrets Manager. Never hard-code them.

**Rule 2 -- Keep all state in the Business VPC.**
Databases, caches, queues, and document stores live in the Business VPC.
Nothing persists in the Launchpad VPC. If an agent running in Agent Core
(optional pattern) needs data, it must reach back into the Business VPC
via a tool function.

**Rule 3 -- One API key per lighthouse.**
Each of the five lighthouses gets its own API key. Never share keys across
lighthouses. Separate keys give separate log streams and separate cost
attribution per lighthouse.

**Rule 4 -- Blueprints are immutable.**
Never attempt to modify a deployed router, guardrail, or agent runtime in
place. Changes to blueprints are handled by the Tenant Admin deploying a
new blueprint version alongside the existing one, then switching the
application to the new API key, then deleting the old blueprint.

**Rule 5 -- Use synthetic data until governance clears real data.**
The dev and test environments are real AWS accounts with production-level
security controls. Loading real Aegon finance data before the data
governance workstream has approved it violates Aegon policy and will
trigger an incident.

**Rule 6 -- Write the HMAC helper once, reuse across all lighthouses.**
HMAC signing is identical for every lighthouse. Build a shared Python
package for it in week 1, publish it to the internal package registry, and
import it from all five lighthouse repos. Do not copy-paste the signing
logic.

## When to escalate

| Situation | Who to contact |
|---|---|
| Router returns 401 or 403 unexpectedly | Tenant Admin role holder (check API key and guardrail binding) |
| Blueprint version needs upgrading | Tenant Admin role holder (web UI action) |
| New AWS component needed (not approved) | Architecture review lead (exception process) |
| Real data access required | Data governance lead |
| Landing zone or account issue | Provisioning lead |
| Platform mechanics unclear | Platform lead (Launchpad team) |

Developers should not contact the Launchpad platform lead directly for
debugging assistance. The Launchpad team provides training and occasional
guidance but does not debug application code.
