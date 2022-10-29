# Pipeline Service

Pipeline Service provides Tekton APIs and services to kcp workspaces.
When a workspace binds to the Pipeline Service APIExport, it has access to the following Tekton APIs:

- `Task`
- `Pipeline`
- `PipelineRun`
- `Repository` (for [Pipelines as Code](https://pipelinesascode.com))

The following features are also provided:

- Signing and attestation of `TaskRuns` with [Tekton Chains](https://tekton.dev/docs/chains/)
- Archiving of `PipelineRuns` and `TaskRuns` with [Tekton Results](https://tekton.dev/docs/results/)
- Integrations with GitHub, Gitlab, and Bitbucket with [Pipelines as Code](https://pipelinesascode.com) (PaC).

## Architecture

Tekton controllers are deployed directly on the workload cluster.
The kcp syncer for the workload cluster is configured to sync `Pipeline`, `Task`, and `PipelineRun` objects.
When a `PipelineRun` is created on kcp, it is synced to the workload cluster whose controllers then create `TaskRun` objects and resulting `Pods`.
The Chains and Results controllers then work with the synced `PipelineRun` and generated `TaskRun` objects to perform their respective actions.

Like upstream Tekton, Pipelines as Code (PaC) also runs controllers directly on workload clusters.
Unlike other Tekton components, PaC also exposes a `Route`/`Ingress` that allows it to receive webhook events from source control repositories.
To sent traffic from kcp to the workload cluster, Pipeline Service will deploy a "gateway" service that acts as a proxy to PaC on the workload cluster.

Tekton Results will likewise use the gateway to forward requests to its service.
The apiserver will be patched to translate kcp workspaces/namespaces to the respective synced namespace on the workload cluster.
