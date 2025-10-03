---
title: Pipeline Service
eleventyNavigation:
  key: Pipeline Service
  parent: Core Services
  order: 5
toc: true
---

# Pipeline Service

Pipeline Service provides Tekton APIs and services to Konflux.

## Architecture Evolution

The Pipeline Service architecture has evolved from a specialized service to a simplified deployment model:

- **Upstream Installations** (e.g., [konflux-ci installer](https://github.com/konflux-ci/konflux-ci)): Deploy upstream Tekton directly
- **Downstream Installations** (e.g., [Fedora Konflux cluster](https://gitlab.com/fedora/infrastructure/konflux/infra-deployments)): Deploy the OpenShift Pipelines distribution of Tekton via OLM operator subscription

### Historical Context

See [ADR-0001](../../ADR/0001-pipeline-service-phase-1.md) (Replaced) and [ADR-0009](../../ADR/0009-pipeline-service-via-operator.md) (Implemented) for the evolution from the initial kcp-based architecture to the current operator-based deployment model.

![Pipelines operator deployment](../diagrams/pipeline-service.drawio.svg)

## APIs and Services

Pipeline Service provides the following:

- Tekton APIs directly through its custom resource definitions.
- Container image signing and provenance attestations through Tekton Chains.
- Archiving of `PipelineRuns`, `TaskRuns`, and associated logs through Tekton
  Results.

Pipeline Service also exposes the following ingress points:

- Pipelines as Code controller: this is a `Route` that receives webhook events
  from source code repositories.
- Tekton Results API: this is an `Ingress` that serves Tekton Results data
  over a RESTful API. Clients authenticate with the same `Bearer` token used to
  authenticate Kubernetes requests.

## Deployment Configuration

For downstream installations using the OpenShift Pipelines operator, the deployment includes the following notable configurations (see [ADR-0009](../../ADR/0009-pipeline-service-via-operator.md)):

- Tekton Triggers will be disabled entirely.
- The pruner (provided by the Pipelines operator) will be disabled in favor of
  pruning via Tekton Results.
- Pipelines as Code will link the results of pipeline tasks to an appropriate
  [Konflux UI](./core/konflux-ui.md) URL.

## Architecture

### Diagram

Legend:
* Blue: managed by Pipeline Service
* Yellow: not managed by Pipeline Service

![Architecture diagram](../diagrams/pipeline-service/architecture.jpg)

### Tekton Pipelines

#### Trusted Artifacts

Tasks in Konflux build pipelines use Trusted Artifacts to securely share files between tasks (see [ADR-0036](../../ADR/0036-trusted-artifacts.md)). This allows users to include custom Tekton Tasks in build pipelines without jeopardizing build integrity. Trusted Artifacts wrap files into archives stored in OCI registries, with checksums recorded as task results to ensure artifacts are not tampered with between tasks.

#### Partner and Custom Tasks

Konflux supports partner-contributed and custom Tekton Tasks in build/test pipelines (see [ADR-0021](../../ADR/0021-partner-tasks.md)). Tasks are validated through CI checks before being accepted into the [build-definitions repository](https://github.com/konflux-ci/build-definitions). Task results follow standardized naming conventions (see [ADR-0030](../../ADR/0030-tekton-results-naming-convention.md)) including `TEST_OUTPUT` for test-like tasks and `SCAN_OUTPUT` for scan-like tasks.

#### appstudio-pipeline Service Account

The service should offer users a service account for running pipelines (see [ADR-0025](../../ADR/0025-appstudio-pipeline-serviceaccount.md)).
However, the automatic generation of a 'pipeline' service account within namespaces has been disabled in the component because it was found that the permissions granted to that account were overly broad.

The Pipeline Service component creates the `appstudio-pipelines-scc` ClusterRole, but does not bind this role to any service account.

The [CodeReadyToolchain](https://github.com/codeready-toolchain) platform (CRT) creates the `appstudio-pipelines-runner` ClusterRole on each tenant/member cluster. It also creates the `appstudio-pipeline` ServiceAccount on every tenant namespace as well as the role bindings for the `appstudio-pipeline` service account within the namespace.

### Tekton Chains

#### Signing Secret

The signing secret is unique to each cluster, and is a long lived secret.
Rotating the secret is extremely disruptive, as it invalidates any artifact that was built using that secret.

Moving to keyless signing would solve the issue and would be the long-term solution.

The public-key is stored in `openshift-pipelines` namespace as a Secret named `public-key`. The secret is readable by all authenticated users to allow them to verify signed artifacts.

### Tekton Results

#### Storage

AWS RDS and S3 are used to handle the storage needs of Tekton Results.

### Pipeline as Code

#### Webhook Configuration

As of the workspace deprecation decision (see [ADR-0039](../../ADR/0039-workspace-deprecation.md)), Konflux follows a single-cluster design. Organizations operating multiple Konflux clusters should register a separate GitHub Application for each cluster. Each cluster's Pipelines as Code controller receives webhooks directly from its dedicated GitHub Application.

**Historical Note**: Previously, multi-cluster deployments used Sprayproxy ([ADR-0031](../../ADR/0031-sprayproxy.md), now Replaced) to fan out webhook requests from a single GitHub Application to multiple member clusters. This is no longer used.

#### Secret management

The secrets for the GitHub Application are stored in Vault, and synchronized as an ExternalSecret. The refresh rate for the synchronization is aggressive so that rotating the secrets do not generate too long of an outage.

## Repositories

As of August 2024, Konflux no longer uses the [deprecated Pipeline Service repository](https://github.com/openshift-pipelines/pipeline-service/) as a base for Tekton-related configuration.

Konflux now deploys Tekton components directly from their respective upstream repositories:
- [Tekton Pipelines](https://github.com/tektoncd/pipeline)
- [Tekton Chains](https://github.com/tektoncd/chains)
- [Tekton Results](https://github.com/tektoncd/results)
- [Pipelines as Code](https://github.com/openshift-pipelines/pipelines-as-code)

For downstream installations using OpenShift Pipelines, the operator is deployed via OLM subscription rather than through a centralized pipeline-service repository.
