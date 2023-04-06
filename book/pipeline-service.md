# Pipeline Service

Pipeline Service provides a SaaS for pipelines. It leverages:

- Kubernetes / OpenShift for the compute
- Tekton Pipelines, Results and friends for the core of the service
- OpenShift GitOps / Argo CD, Pipelines as Code for managing the infrastructure

The following features are provided:

- Signing and attestation of `TaskRuns` with [Tekton Chains](https://tekton.dev/docs/chains/)
- Archiving/Pruning of `PipelineRuns` and `TaskRuns` with [Tekton Results](https://tekton.dev/docs/results/)
- Integrations with GitHub, Gitlab, and Bitbucket with [Pipelines as Code](https://pipelinesascode.com) (PaC).

## Architecture

Pipeline Service is deployed onto the cluster alongside other AppStudio components. The following form the core architecture of Pipeline Service:

1. _OpenShift Pipelines:_ It enables the creation and management of Pipelines for user [Applications](https://redhat-appstudio.github.io/book/ref/application-environment-api.html#application).
2. _Pipelines as Code (PaC):_ An OpenShift Pipelines component that enables receiving webhook events from version control systems. The user would have to install a [GitHub App](https://pipelinesascode.com/docs/install/github_apps/) with the required permissions in order to forward events to the PaC endpoint exposed by the platform.
3. _Spray Proxy:_ Forwards requests to all clusters in the environment once an event is received on PaC. It is a reverse proxy that broadcasts to multiple backends.
4. _Tekton Results:_ Responsible for storing logs and pruning PipelineRuns. Utilises AWS RDS as the backend database for our production instance.
5. _Tekton Chains:_ Provides PipelineRun attestation capabilities, ensuring that all PipelineRuns are verified and can be traced back to their source.

## Repository

The official repository for the Pipeline Service can be found at https://github.com/openshift-pipelines/pipeline-service. This repository contains the source code, configuration files, and documentation needed to deploy and consume the service.
