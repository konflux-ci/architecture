# Internal Services

## Overview

The Internal Services system consists of a kubernetes controller (running on an internal, private cluster) that is capable of watching and reconciling custom resources on a remote, public cluster.
These custom resources describe which pipelines and parameters to use to execute internal jobs on an internal, private cluster.
The results and outcome of the pipeline are added as an update to the custom resources. The remote, public cluster watches these resources to determine the outcome.

## Goals

* The Internal Services system attempts to enable execution of internal jobs via a polling mechanism.
* The Internal Services system provides execution results back to the requesting cluster.

## System Context

The diagram below shows the interaction of the internal services controller and the [Release Service](./core/release-service.md) and shows the flow of custom resources

![](../diagrams/internal-services/internal-services-controller-overview.jpg)

## Terminology

* **InternalRequest** - The custom resource that describes the internal service to trigger the internal job on.
* **Remote Cluster** - A **public**, Konflux cluster residing outside a private network.
* **Internal, Private Cluster** - A cluster that is not externally addressable but which has access to a private network.

## Resources
Below is the list of CRs that the Internal Service is responsible for interacting with:

### CREATE

| Custom Resource | When?                                                                                                             | Why?                                          |
|-----------------|-------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| PipelineRun     | Once a InternalRequest has been reconciled and the Pipeline to run has been discovered and is ready for execution | To perform the steps in the Internal Pipeline |

### READ

| Custom Resource        | When?                                                       | Why?                                |
|------------------------|-------------------------------------------------------------|-------------------------------------|
| InternalServicesConfig | During controller startup and during each reconcile attempt | To obtain configuration information |

### UPDATE

| Custom Resource  | When?                                                              | Why?                                                                              |
|------------------|--------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| InternalRequest  | During the lifecycle of an attempt to complete an InternalRequest  | To provide status for the execution of the Pipeline to the remote, public cluster |

### WATCH

| Custom Resource  | When?                            | Why?                                                                                     |
|------------------|----------------------------------|------------------------------------------------------------------------------------------|
| InternalRequest  | Always                           | To provide an API to process an internal request                                         |
| PipelineRun      | Once the PipelineRun is created  | To relay the Internal PipelineRun status to the remote InternalRequest for viewing |

### Samples

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: InternalServicesConfig
metadata:
  name: config
  namespace: internal-services
spec:
  allowList:
    - managed-team-1-tenant
    - managed-team-2-tenant
  debug: false
  volumeClaim:
    name: pipeline
    size: 1Gi
```

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: InternalRequest
metadata:
  name: example
  namespace: default
spec:
    request: "internal-system-abc-pipeline"
    params:
        foo: quay.io/redhat-isv/operator-pipelines-images:released
        bar: sha256:dd517544390c4c9636a555081205115a2fd3e83c326e64026f17f391e24bd2e5
```

## Security Risk Mitigations

Enabling remote, public clusters the ability to run internal jobs carrying certain security risks:

* A user or a pipeline may attempt to run an internal job that it is not permitted to.
* A user or a pipeline may attempt to run an arbitrary job

The following list describes measures in places to mitigate those risks.

* The creation of an `InternalRequest` custom resource requires permission on the Remote Cluster.
* The Internal Services controller instance is configured to watch a specific cluster.
  * This cluster is provided to the controller as an argument to a secret that was added by the admin team.
  * The secret contains a KUBECONFIG file.
* Only `Pipelines` that are defined and exist within the controller's namespace can be executed on the internal, private cluster.
* The Internal Services controller only watches and acts on remote namespaces that are specifically allowed in the `Config` custom resource.

## Detailed Workflow

> The following bullet points are numbered to align with the diagram displayed in the [System Context](#system-context) section above.

1. A `InternalRequest` CR is created by a pipeline run by a service account on the remote, public cluster as part of a pipeline.
    * The `spec.request` should reference the pipeline to execute.
    * The `spec.params` should reference the parameters to pass to the pipeline.
2. The `InternalRequest` CR is noticed by the Internal Services controller and attempts to reconcile it.
3. The Internal Services controller verifies whether the remote namespace is allowed in the `InternalServicesConfig` CR.
    * If it is not allowed, the Internal Services controller updates the `InternalRequest` CR with an invalid `status` and a rejection message and stops reconciling.
    * If it is allowed, a `PipelineRun` is created based on the `Pipeline` name found in the `spec.request` and parameter values found in `spec.params` from the `InternalRequest` CR.
4. The remote `InternalRequest` CR is updated by the Internal Services controller to mark as in-progress.
5. The internal job encapsulated by the `Pipeline` completes.
6. The `PipelineRun` is watched by the Internal Services controller.
7. Upon completion, the Internal Services controller updates the `status` section of the remote `InternalRequest` CR
    * The remote, public cluster calling pipeline sees the update to the `status` of the `InternalRequest` CR and continues its execution.
    * By default, `PipelineRun` CRs are deleted once completed.
      * There are only preserved if an admin has set the `InternalServicesConfig` CR `spec.debug` to `true`
