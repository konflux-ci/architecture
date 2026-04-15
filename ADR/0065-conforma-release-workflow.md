# ADR-65: Unified Conforma Release Workflow

## Status

Proposed

## Date

2026-04-15

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

### New Conforma Release Workflow

A [new workflow](https://github.com/conforma/infra-deployments-ci/blob/main/.github/workflows/konflux-policy.yaml) has been introduced that:

1. Pulls the latest policy, task definition and CLI changes.
2. Tests them by running both the release pipeline Conforma task and the integration pipeline Conforma task.
3. Tags the CLI and policy bundles with the `konflux` tag.
4. Pushes the tested task definitions to the `konflux` branch in the tekton-catalog repo. These task definitions also contain a pinned version of the CLI for the step image.

### Rollback

If a release introduces a regression, any member of the Conforma team can roll back by running a GitHub workflow in the [conforma/infra-deployments-ci](https://github.com/conforma/infra-deployments-ci) repository. The workflow re-tags the CLI, policy bundles, and task definitions to a known-good prior version.

### What We Are Changing

We are updating both the Conforma integration pipeline in build-definitions and the Conforma release pipeline task to use the floating `konflux` tag. This ensures the CLI, policies, and task definitions are tested and released together.

## Consequences

### Positive

- Eliminates version skew between the CLI, policies, and task definitions
- All three components are tested together before the `konflux` tag is updated
- Removes dependency on the slow build-definitions and infra-deployments merge process for Conforma updates
- Step images use pinned CLI versions instead of `latest`

### Negative

- We don't yet have a workflow that includes development and staging environments.
- By referencing task definitions via tag-based Tekton resolvers, we bypass Tekton's built-in caching, which relies on digest references.

## References

- [conforma/cli](https://github.com/conforma/cli) — CLI tool for verifying software supply chain artifacts against Conforma policies
- [conforma/policy](https://github.com/conforma/policy) — OPA/Rego policy rules used to validate attestations and pipeline definitions
- [conforma/infra-deployments-ci](https://github.com/conforma/infra-deployments-ci) — CI workflows and acceptance tests for Conforma's deployment in Konflux, including the unified release and rollback workflows
