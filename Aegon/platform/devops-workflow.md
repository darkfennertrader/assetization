---
title: "PwC DevOps Guide: Pipelines and Environments on Aegon Launchpad"
---

## Purpose

This document describes the deployment model, pipeline split, environment
strategy, and operational responsibilities for a PwC DevOps engineer working
on the Aegon lighthouse programme. The central concept is the two-pipeline
model: Launchpad owns one pipeline, PwC owns another, and the two meet only
at a credentials handoff.

## Workflow diagram

![DevOps workflow](devops-workflow.png)

## The two-pipeline model

### Pipeline A -- Launchpad team (not PwC)

The Launchpad team owns a CodePipeline/CodeBuild pipeline that builds and
deploys blueprint infrastructure into LOB accounts via cross-account STS
roles. PwC has no access to this pipeline, its repository, or its deployment
credentials.

This pipeline provisions the Launchpad VPC inside our LOB account: the ALB,
the router Lambda, guardrail wiring, and optional Agent Core runtime. PwC
triggers this pipeline indirectly by asking the Tenant Admin to deploy a
blueprint from the web UI.

### Pipeline B -- PwC (our pipeline)

PwC owns a GitHub Actions pipeline that provisions and deploys everything
in the Business VPC. It has two jobs that run on every merge to main:

**Terraform job.** Runs `terraform apply` against the Business VPC. Manages
all PwC-owned infrastructure: DynamoDB tables, OpenSearch domains, S3 buckets,
ECS clusters, Lambda functions, EventBridge rules, SES identities, SQS queues,
CloudWatch log groups, and IAM roles for the application.

**Application job.** Builds the container image, pushes it to ECR, and
updates the ECS service task definition (or publishes a new Lambda version).
Injects runtime configuration from Secrets Manager as environment variables.

PwC's Terraform never provisions Bedrock, guardrails, router Lambdas, or Agent
Core runtimes. If any `aws_bedrock_*` resource appears in our Terraform, it
is a mistake.

## The credentials handoff

The bridge between the two pipelines is three values:

1. Router ALB hostname (internal DNS name of the Launchpad ALB).
2. API key (generated in the Launchpad web UI by the Tenant Admin).
3. HMAC secret (generated alongside the API key).

The DevOps engineer is responsible for:

- Receiving these values from the Tenant Admin after blueprint provisioning.
- Storing them in AWS Secrets Manager under a consistent naming convention,
  for example `launchpad/lh1/api-key`, `launchpad/lh1/hmac-secret`.
- Ensuring the application's IAM role has read access to those secrets.
- Never storing these values in Git, environment files, or CI/CD variables.

## Environment strategy

Aegon operates three environment tiers for each lighthouse: dev, test, and
prod. All three tiers call the same Launchpad production router endpoint.
There is no Launchpad dev or test instance for consumers to point at.

**Dev environment.** Synthetic data only. Used by developers for daily
iteration. Security controls match production-OU SCPs because all LOB
accounts sit in the production OU.

**Test environment.** Synthetic data only. Used for integration testing,
load testing, and evaluation runs before a release is promoted to production.

**Prod environment.** Real Aegon Finance data, subject to the data
governance workstream approval. Not activated until governance clears
each data source for each lighthouse.

Promoting a release from dev to test to prod means merging to the
appropriate branch (or using an environment protection rule in GitHub
Actions) and allowing the pipeline to deploy. There is no separate Terraform
workspace per environment -- use Terraform workspaces or separate state
backends, one per environment.

## Blueprint upgrade procedure

When the Launchpad team releases a new blueprint version, the upgrade
procedure is:

1. Tenant Admin deploys the new blueprint version from the web UI into the
   LOB account. This creates a new ALB endpoint alongside the existing one.
2. Tenant Admin generates a new API key bound to the new blueprint.
3. PwC DevOps updates Secrets Manager with the new API key, HMAC secret,
   and ALB hostname.
4. PwC runs the CI/CD pipeline. The application picks up the new secrets
   from Secrets Manager on next deploy (or on restart if using environment
   variable injection).
5. Verify the application calls the new blueprint successfully.
6. Tenant Admin deletes the old blueprint instance.

Never delete the old blueprint before the new one is confirmed working.

## Immutability rule

Blueprints cannot be modified in place. Any change to the router, guardrail,
or Agent Core configuration requires a new blueprint deployment. Treat
blueprint versions like container image tags: immutable once deployed.

The same principle applies to our own infrastructure. Prefer adding new
Terraform resources alongside existing ones and migrating traffic, rather
than modifying live resources that applications depend on.

## Observability

PwC owns all observability infrastructure in the Business VPC:

- CloudWatch log groups for ECS tasks and Lambda functions.
- CloudWatch metrics and alarms for error rates, latency, and queue depth.
- X-Ray traces through LangGraph execution (optional but recommended).
- Cost Explorer tags -- every PwC-owned resource must carry the lighthouse
  tag so per-lighthouse cost is attributable.

Launchpad maintains its own audit log of all router calls, keyed by
application ID (derived from the API key). This log is readable by the
Tenant Admin via the web UI. PwC cannot write to or delete this log.

To correlate a PwC application log entry with a Launchpad router log entry,
use the `x-request-id` header that the router echoes back in its response.
Log this header from the application side on every model call.

## Key rules for DevOps engineers

**Rule 1 -- Never Terraform the AI plumbing.**
The router, guardrail, agent runtime, and Bedrock model activations are
not PwC Terraform resources. Do not add them. If `terraform plan` shows
any Bedrock, guardrail, or Agent Core resources, remove them.

**Rule 2 -- Credentials flow from the web UI into Secrets Manager.**
The Tenant Admin generates API keys in the Launchpad web UI. The DevOps
engineer stores them in Secrets Manager. The pipeline reads them from
Secrets Manager. This is the only correct flow.

**Rule 3 -- All environments hit Launchpad production.**
Do not try to point dev or test at a different Launchpad endpoint. There
is no alternative endpoint. Every model call in every environment is
a production Bedrock call with real cost and real audit logging.

**Rule 4 -- Tag every resource with the lighthouse identifier.**
Use a consistent tagging scheme, for example `lighthouse=lh1`. This
enables per-lighthouse cost attribution in Cost Explorer and simplifies
cleanup when a lighthouse is decommissioned.

**Rule 5 -- Real data requires governance approval before it enters
any environment.**
Even in dev, loading real Aegon Finance data without governance approval
is a policy violation. Until the data governance workstream clears a
data source, use synthetic data only.

## When to escalate

| Situation | Who to contact |
|---|---|
| Landing zone not provisioned after 10 days | Provisioning lead |
| Blueprint deployment failing in web UI | Platform lead (Launchpad team) |
| Transit Gateway routing issue | Provisioning lead (network team) |
| New AWS service needed not in approved list | Architecture review lead |
| Real data approval needed | Data governance lead |
| Cost spike from unexpected Bedrock calls | Tenant Admin (check API key usage in web UI) |
