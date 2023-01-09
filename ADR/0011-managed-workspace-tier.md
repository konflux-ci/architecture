# 11. Managed Workspace Tier

Date: 2023-01-09

## Status

New

## Context

Stonesoup provides the ability to release content to privileged destinations.
For instance, to a production environment managed by a team that is not the same as the service team (as in the case of a centralized operations or centralized SRE team), or, for another example, to a production registry managed by a release engineering team (as in releasing to registry.redhat.io)

This is enabled via flexible release pipelines that are curated by the Stonesoup release team.
These pipelines include the ability to run tasks using secrets for an organization that are needed to access privileged destinations.

These pipelines are triggered by the Release Service based on instances of Release custom resources. They are configured to execute in managed workspaces. This workspace type is one that is managed in the sense that a dedicated team or organization (SRE or Software production) controls access to the workspace.
This restricted access is needed since this workspace type houses Production environments/services.

The diagram below shows the flow of custom resources and the orchestration of pipelines by the release service.

![](../diagrams/release-service/hacbs-release-service-data-flow.jpg)

Currently, Release pipelines are executed using organization specific service accounts with secrets that are required to
release content to privileged destinations.

At the moment, configuring those secrets cannot be performed by a regular user in a managed workspace.
They must be performed by a user with elevated privileges.

Examples of steps needed to configure secrets:

> cosign public-key --key k8s://tekton-chains/signing-secrets

- Needed to obtain the Tekton Chains public key from the tekton-chains namespace

> oc secrets link pipeline redhat-appstudio-registry-pull-secret --for=pull,mount -n dev-release-team

- Needed to link the pipeline service account using in the build service such that attestations can be uploaded by Tekton chains.

> oc secrets link release-service-account hacbs-release-tests-m5-robot-account-pull-secret --for=mount -n managed-release-team

- Needed to link the credentials to the release pipeline service account required to push content to privileged destinations.

## Decision

Users in managed workspaces need to configure their workspaces to be able to run release pipelines. It is not feasible to require Stonesoup administrators, with elevated permissions, to help facilitate that setup.

It shall be possible to provision namespace with additional permissions compared to the standard tier in dev sandbox.

This would require a new tier in the dev sandbox for a new type of workspace.

## Consequences

TBD
