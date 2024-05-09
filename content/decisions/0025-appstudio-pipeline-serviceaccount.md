---
date: 2023-05-30T00:00:00Z
title: appstudio-pipeline Service Account
number: 25
---
# appstudio-pipeline Service Account

## Status

Accepted

## Context

A default service account must be provided to allow Konflux components to run pipelines.
While OpenShift Pipelines has the option to automatically create a `pipeline` ServiceAccount on any namespace, the permissions granted to the account are overly broad and the solution was rejected after a security review.
Therefore Konflux must manage this default service account.

## Decision

Konflux will provide a service account named `appstudio-pipeline`.

### Ownership

The Pipeline Service component owns the `appstudio-pipeline-scc` ClusterRole.

The CodeReadyToolchain is in charge of:
* creating the `appstudio-pipeline` ServiceAccount on all tenant namespaces,
* creating the `appstudio-pipeline-runner` ClusterRole,
* granting the `appstudio-pipeline-runner` and `appstudio-pipeline-scc` ClusterRoles to the `appstudio-pipeline` ServiceAccount.

### ClusterRoles

#### appstudio-pipeline-runner

The resource is defined [here](https://github.com/codeready-toolchain/member-operator/blob/master/config/appstudio-pipelines-runner/base/appstudio_pipelines_runner_role.yaml).

#### appstudio-pipeline-scc

The resource is defined [here](https://github.com/openshift-pipelines/pipeline-service/blob/main/operator/gitops/argocd/pipeline-service/openshift-pipelines/appstudio-pipelines-scc.yaml).

## Consequences

* Tekton Pipelines users using the `pipeline` service account must migrate to the new `appstudio-pipeline` ServiceAccount.
