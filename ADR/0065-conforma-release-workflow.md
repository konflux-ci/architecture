---
title: "65. Unified Conforma Release Workflow"
status: Proposed
applies_to:
  - enterprise-contract
  - release-service
topics:
  - release
  - conforma
  - deployment
---

# ADR-65: Unified Conforma Release Workflow

## Status

Proposed

## Date

2026-04-30

## Context

Conforma's deployment in Konflux involves three components that must stay in sync: the CLI, the policy bundles, and the Tekton task definitions. The current approach updates and deploys each independently, which causes problems in three areas.

### Task Definition Deployment

The release pipeline pulls its task definition version from a ConfigMap deployed via infra-deployments. A scheduled job updates this task definition weekly, but:

1. The only testing it undergoes is in the CLI repo.
2. The step images use the `latest` tag rather than pinned versions.

Reference: [verify-conforma-konflux-ta.yaml](https://github.com/conforma/cli/blob/main/tasks/verify-conforma-konflux-ta/0.1/verify-conforma-konflux-ta.yaml#L331)

### Policy Version Skew

The Conforma policy configs in konflux-release-data all reference a single policy bundle containing all Conforma release policies. Rather than submitting a separate MR for each policy config when a new version is released, they all use the `konflux` floating tag, which is updated weekly.

However, the policy configs pick up new policies as soon as the tag is updated, while the CLI and task definitions must go through the pull request process in build-definitions and infra-deployments before being deployed — a process that sometimes takes multiple weeks to merge. This means the deployed policies can end up being newer than the CLI, which is an issue when policies use built-in commands that the CLI does not yet support.

Reference: [Example build-definitions update](https://github.com/konflux-ci/build-definitions/pull/3053)

### Lack of Unified Testing

There is no mechanism to test all three components together before deployment. The CLI has its own tests, but the task definitions and policy bundles are not validated as a combined unit before being rolled out to production.

## Decision

We will introduce a unified release workflow that tests the CLI, policy bundles, and task definitions together before publishing them. All resolver references will then be pinned to the exact versions that were tested, eliminating version skew between components.

### Release Workflow

A [new workflow](https://github.com/conforma/infra-deployments-ci/blob/main/.github/workflows/konflux-policy.yaml) has been introduced that:

1. Pulls the latest policy, task definition, and CLI changes.
2. Tests them by running both the release pipeline Conforma task and the integration pipeline Conforma task.
3. Tags the CLI and policy bundles with the `konflux` tag.
4. Pushes the tested task definitions to the `konflux` branch in the tekton-catalog repo, with pinned CLI versions for the step images.

Once the workflow completes, pull requests are submitted to build-definitions and release-service-catalog to update the resolver references: bundle resolvers are pinned to the digest of the `konflux` tag, and git resolvers are pinned to the corresponding git SHA.

### Task-Level Policy Bundle Override

The `verify-enterprise-contract` and `verify-conforma-konflux-ta` tasks will accept a new `POLICY_BUNDLE_SOURCE` parameter. A new step in each task will replace the policy bundle referenced in the EnterpriseContractPolicy (policy.yaml) with the bundle specified by this parameter. This allows the release workflow to pin the exact policy bundle version that was tested, rather than relying on whatever bundle the ECP happens to reference at evaluation time.

### Rollback

If a release introduces a regression, rollback is performed by reverting the resolver reference update in the affected repository (build-definitions for the integration pipeline, release-service-catalog for the release task). This restores the previous pinned digest or git SHA, returning that pipeline to the last known-good version of the Conforma components.

## Consequences

### Positive

- Eliminates version skew between the CLI, policies, and task definitions
- All three components are tested together before resolver references are updated
- Digest-pinned bundle resolvers and SHA-pinned git resolvers preserve Tekton's built-in caching
- Step images use pinned CLI versions instead of `latest`

### Negative

- Updating the pinned digests and git SHAs in build-definitions and release-service-catalog still requires pull requests, so Conforma updates can be delayed by the review and approval process in those repositories.
- The Conforma integration pipeline (build-definitions) and the Conforma release task (release-service-catalog) are updated via separate pull requests, so version drift can occur if one merges significantly before the other.

## References

- [conforma/cli](https://github.com/conforma/cli) — CLI tool for verifying software supply chain artifacts against Conforma policies
- [conforma/policy](https://github.com/conforma/policy) — OPA/Rego policy rules used to validate attestations and pipeline definitions
- [conforma/infra-deployments-ci](https://github.com/conforma/infra-deployments-ci) — CI workflows and acceptance tests for Conforma's deployment in Konflux, including the unified release and rollback workflows
