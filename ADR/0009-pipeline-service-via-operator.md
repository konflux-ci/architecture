# 9. Pipeline Service via Operator

Created: 2023-09-29
Last Updated: 2023-09-29

## Status

Proposed

## Context

kcp is no longer being used as a control plane for RHTAP. This means that
"Pipeline Service" cannot be deployed as an independent service. For our
initial MVP, all Tekton APIs need to be deployed onto a standard OpenShift
cluster (specifically OpenShift Dedicated).

## Decision

All Tekton APIs will be provided using the stock OpenShift Pipelines operator (OSP).
In the spirit of developing in a "Service First" manner, RHTAP will deploy
a candidate "nightly" release of the operator. The service will be defined in
the [pipeline-service](https://github.com/openshift-pipelines/pipeline-service)
repository, which is then imported into
[infra-deployments](https://github.com/redhat-appstudio/infra-deployments) as
an ArgoCD application.

Not all metrics required for operating the service are exposed natively by the
controllers. The `pipeline-metrics-exporter` controller is to be used as a test
bed to expose new metrics, with the goal of upstreaming those metrics as they
mature and prove their value.

Configurations that are specific to RHTAP must be made available through
the OSP CRDs. The following changes are specific to RHTAP:

- Disable Tekton Triggers. Pipelines as Code will be the favored mechanism for
  event-based triggering of pipelines for now. This decision can be revisited
  in the future based on need.
- Disable the pruner that comes with the operator. Tekton Results will be used
  to prune `PipelineRun` and `TaskRun` data off cluster, thereby ensuring data
  is archived before removal.
- Direct Pipelines as Code to use a URL pattern that displays the `PipelineRun`
  or `TaskRun` info from the Konflux UI. This ensures
  end users do not need access to the underlying compute cluster(s).
- The Pipelines as Code application name must match the GitHub Application name, so that users understand which GitHubApplication is responsible for triggering the pipelines.
- The GitHub Application secret value, deployed using an ExternalSecret.
- Any configuration related to performance.

Furthermore, as the service will be accessed through CodeReadyToolchain (CRT), the
following changes are also specific to RHTAP:
- Deploying a proxy (known as `SprayProxy`) on the CRT host cluster that redirects
  incoming PaC requests to the member clusters. More on SprayProxy [here](0031-sprayproxy.md).
- Providing a plugin to the CRT Proxy so Tekton Results requests are redirected
  to the appropriate member cluster.

## Consequences

- Tekton Triggers should be disabled in RHTAP using the appropriate operator
  configuration.
- The Tekton Pruner needs to be disabled in RHTAP using the appropriate
  operator configuration. This is done under the assumption that Results will
  be responsible for pruning resources. Eventually the operator should automate
  this setting if `Results` is deployed and configured to prune resources.
- Pipelines as Code should use an appropriate URL to HAC when interacting with
  SCM services, such as the GitHub
  [Checks API](https://docs.github.com/en/rest/guides/getting-started-with-the-checks-api?apiVersion=2022-11-28).
- Changes to Pipeline components need to be baked into the operator and built
  rapidly.
- Hot fixes need to be provided on a "roll forward" basis. OLM Operators do not
  support "rollback" mechanisms today. Mean time to revert an offending change,
  rebuild, and deploy needs to be measured in hours.
- The version of the deployed operator needs to be configurable via ArgoCD.
  This is should be doable by using `kustomize` to patch the `CatalogSource` and `ImageContentSourcePolicy`.
