# 1. Pipeline Service Phase 1

Created: 2022-10-13
Last Updated: 2023-09-29

## Status

Replaced

Superceded by [ADR-0009](./0009-pipeline-service-via-operator.md)

## Context

App Studio initially ran on a single cluster and provisioned [Tekton](https://tekton.dev) controllers.
With the migration to [kcp](https://github.com/kcp-dev/kcp), controllers need to either a) be made "kcp aware", or b) run on all workload clusters, targeting the same kcp `APIExport`.
App Studio could build this on their own, however other services and teams beyond App Studio need the ability to run Tekton pipelines.

Tekton code utilizes libraries that are not simple to refactor and make "kcp aware."
Furthermore, Tekton is an upstream project with a wide, active community.
Adding kcp-aware changes would require upstream acceptance, or require us to fork Tekton and apply our "kcp aware" patches.

## Decision

Tekton APIs and services will be provided through a separate, independent service - Pipeline Service.
App Studio and HACBS will be "customer 0" for Pipeline Service.
Future managed services which rely on Tekton APIs can bind to the Pipeline Service and start running pipelines right away.

Pipeline Service will deploy and manage Tekton controllers directly on workload clusters.
kcp syncers will be used to generate APIExports from the workload cluster.
We will utilize the OpenShift Pipelines Operator to deploy Tekton controllers to the furthest extent possible, whose configuration will be controlled via ArgoCD.
Otherwise, other Tekton controllers will be deployed with direct manifests.

Arch Diagram: https://miro.com/app/board/uXjVOVEW0IM=/

## Consequences

- Other services use an APIBinding to execute `PipelineRuns` (and access Tekton APIs) in kcp.
- `TaskRun` objects cannot be synced to KCP.
  App Studio and HACBS components may only interact with `PipelineRun` objects directly.
- Workload clusters for Pipeline Service need to be directly managed by the Pipeline Service team.
  We cannot rely on general "compute as a service" from kcp Control Plane Service (CPS).
- Pipelines as Code (PaC) needs a separate ingress and service configured on KCP, which forwards traffic to PaC on the workload cluster.
  - `Ingress` support on kcp comes from an add-on capability - the [kcp Global Load Balancer Controller](https://github.com/kcp-dev/kcp-glbc).
  - `PipelineRun` objects created by PaC are not visible on kcp.
  - We are limited to one workload cluster - the gateway cannot load balance traffic across clusters.
- Tekton Results can only be accessed on workload clusters. It would require additional changes/patches to make it accessible from kcp.
