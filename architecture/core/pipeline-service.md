# Pipeline Service

Pipeline Service provides Tekton APIs and services to RHTAP.
In the initial phase of RHTAP, Pipeline Service will be provided by a stock
installation of the OpenShift Pipelines operator.
This deployed version will be the a candidate build of the OpenShift Pipelines
operator from a Red Hat build system.

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

The deployment of the OpenShift Pipelines operator will have the following
notable configurations:

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

#### appstudio-pipeline Service Account

The service should offer users a service account for running pipelines.
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

#### Secret management

The secrets for the GitHub Application are stored in Vault, and synchronized as an ExternalSecret. The refresh rate for the synchronization is aggressive so that rotating the secrets do not generate too long of an outage.

## Repository

The official repository for the Pipeline Service can be found at https://github.com/openshift-pipelines/pipeline-service. This repository contains the source code, configuration files, and documentation needed to deploy and consume the service.
