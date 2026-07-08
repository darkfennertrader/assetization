---
title: "CI/CD Pipeline — Best Practices for a Three-Environment Azure Deployment"
---

# CI/CD Pipeline — Best Practices for a Three-Environment Azure Deployment

## Purpose

This document defines the standard CI/CD pipeline pattern adopted across all product
blocks — Showroom, Marketplace, and Knowledge Base — in the PwC AI Platform programme.
Standardising the pattern ensures that every team building on the shared Azure substrate
follows the same promotion discipline, can read each other's pipelines, and can trace any
running artefact back to a single source commit.

The pattern is deliberately simple: one codebase, one long-lived branch, one container
registry, three environments. Complexity is added only when a concrete business or
compliance requirement demands it.

## The Four Invariants

The following rules must hold for every product block deployed on the platform:

**One codebase, one long-lived branch.**
All production-bound changes flow through a single trunk branch (`main`). Feature work
is developed on short-lived branches and merged via pull request. Long-lived parallel
branches (e.g. a permanent `release` or `staging` branch) are not used, because they
require perpetual merge maintenance and make it impossible to guarantee that what was
tested is what was deployed.

**Three environments.**
Three identical stamps of the same infrastructure are provisioned: `dev` (for developer
integration), `tst` (for stakeholder acceptance), and `prod` (for live use). Each
environment runs in its own Azure resource group, with its own runtime configuration,
its own Key Vault, and its own system-assigned Managed Identity. The infrastructure
template is identical across all three — only the configuration values differ.

**One shared container registry.**
A single Azure Container Registry (ACR) is shared across all three environments and, where
architecturally appropriate, across product blocks. The registry is the canonical source
of truth for all built images. Per-environment registries are not used: they would require
copying images between environments, introducing the risk that what ran in `tst` is
not byte-for-byte identical to what was deployed to `prod`.

**Build once, promote by immutable tag.**
A container image is built exactly once per commit. It is tagged with an immutable build
identifier (a build number, a semantic version, or the short commit SHA). That same tag
is referenced by all three deployment stages. No rebuild occurs when promoting from `dev`
to `tst` or from `tst` to `prod` — the image is already in the registry.

## The Pipeline Lifecycle

The diagram in this directory (`cicd-pipeline-flow.png`) illustrates the following
five-stage lifecycle.

### Stage 1 — Build

Triggered on every merge to `main`, this stage checks out the source code, runs the
test suite, builds a single container image, and pushes it to the shared ACR with an
immutable tag. The image digest (a content-addressed SHA-256 hash) is recorded in the
pipeline run for later audit.

This stage runs exactly once per commit. If the build or tests fail, no image is pushed
and no deployment proceeds.

### Stage 2 — Deploy to Dev

Immediately after a successful build, the new image is deployed to the `dev` environment.
This stage is automatic — no human approval is required. The `dev` environment is
intentionally permissive: its purpose is to give developers fast feedback that the image
runs correctly in a real Azure environment before any stakeholder sees it.

The deployment mechanism is an in-place revision update on the Azure Container App: the
running revision is replaced by a new revision pointing at the newly pushed image tag.
Previous revisions are retained in the registry for rollback.

### Stage 3 — Approval Gate: Dev to Tst

Before the same image can be deployed to `tst`, a designated approver must explicitly
authorise the promotion. The pipeline pauses, notifies the approver (by email or Teams
message), and waits. The approver reviews the `dev` environment, confirms the image
behaves correctly, and clicks "Approve" in the pipeline UI.

This gate is the human checkpoint between a developer-facing and a stakeholder-facing
environment. It prevents unreviewed code from reaching the acceptance environment.

### Stage 4 — Deploy to Tst

After approval, the pipeline deploys the same image tag to the `tst` environment.
No new build occurs. The only change is the target Azure Container App. The runtime
configuration (environment variables, Key Vault URL, Managed Identity binding) is that of
the `tst` environment; the image bytes are identical to what ran in `dev`.

The `tst` environment is where stakeholder acceptance testing, security reviews, and
integration tests run. It is kept as production-like as possible in terms of
infrastructure sizing and configuration.

### Stage 5 — Approval Gate and Deploy to Prod

Promotion to `prod` requires a second, independent approval — typically from a different
person or a change-management board. The pipeline pauses again, notifies the approver,
and waits.

After approval, the image is deployed to the `prod` environment using the same mechanism
as `dev` and `tst`. The deployment is auditable: the pipeline run records which commit,
which image tag, which digest, which approver, and at what time each environment received
the change.

## What Differs Between Environments

The table below lists every category of difference between `dev`, `tst`, and `prod`.
The container image itself is not on this list, because it is identical across all three.

| Category | Where the difference lives |
|---|---|
| **Runtime configuration** | Environment variables on the ACA app (tenant IDs, group OIDs, feature flags) |
| **Secrets** | Each env has its own Key Vault; each Key Vault holds the credentials for that env only |
| **Identity** | Each ACA app has its own system-assigned Managed Identity; role assignments are per-env |
| **URL / hostname** | Each env has its own ACA-assigned FQDN; custom domains (phase 2) are per-env |
| **Approval gates** | `dev` is gate-free; `tst` and `prod` require explicit human approval |
| **Scaling rules** | `dev` may scale to zero outside business hours; `tst` and `prod` keep a minimum replica |
| **Container image** | Identical — same tag, same digest, same bytes |

## Why This Pattern

**Traceability.** Every deployment to every environment references the same build number.
When a production issue is reported, the build number visible in the Azure Portal traces
directly to the commit in version control. No "which build is this?" ambiguity.

**Reproducibility.** Because the image is built once and the registry tag is immutable,
it is possible to re-deploy any previous version of the application to any environment
in under two minutes by referencing the previous tag. This is the rollback story.

**Auditability.** The pipeline records every approval: who approved, when, and for which
image. This is a compliance requirement in regulated environments and a professional
standard for any production workload.

**Least privilege.** Per-environment Managed Identities mean that a compromised `dev`
identity cannot read `prod` secrets. Per-environment Key Vaults mean that a leaked `dev`
secret exposes only `dev` configuration.

**Simplicity.** One branch, one build, three deploy stages. Every engineer on any of the
product teams can understand the pipeline at a glance. There is no branch-merge overhead,
no per-environment build matrix, and no "hotfix lane" that bypasses testing.

## When to Deviate from This Pattern

The following are the only justified reasons to diverge:

- **Hard compliance or air-gap boundary.** If a regulatory requirement mandates that no
  artefact may cross an environment boundary without a formal re-build and re-sign process,
  a per-environment registry with a controlled import step (`az acr import`) may be
  required. The import step must be authenticated and audited.

- **Multi-team or multi-product ACR governance.** In a very large organisation where
  different product groups need independent lifecycle control of their registries (billing
  separation, independent geo-replication, different retention policies), a per-team ACR
  may be appropriate. This does not change the build-once principle — it only changes
  which registry the one image lands in.

- **Geo-distribution pull latency.** If the target ACA region is far from the ACR region
  and pull latency is a measured problem, ACR Geo-Replication can be enabled on the shared
  registry. The image remains logically single; the registry replicates it transparently
  to a nearby node.

In all other cases, the standard pattern applies. Complexity is a maintenance liability
and should be introduced only in response to a concrete, measured problem.
