# 0009 Pipeline Service via Operator

Created: 2022-12-01
Last Updated: 2022-12-06

## Status

Proposed

## Context

kcp is no longer being used as a control plane for StoneSoup. This means that
"Pipeline Service" cannot be deployed as an independent service. For our
initial MVP, all Tekton APIs need to be deployed onto a standard OpenShift
cluster (specifically OpenShift Dedicated).

## Decision

All Tekton APIs will be provided using the stock OpenShift Pipelines operator.
In the spirit of developing in a "service first" manner, StoneSoup will deploy
a candidate "nightly" release of the operator. The service will be defined in
the [pipeline-service](https://github.com/openshift/pipeline-service)
repository, which is then imported into
[infra-deployments](https://github.com/redhat-appstudio/infra-deployments) as
an ArgoCD application.

Configurations that are specific to StoneSoup must be made available through
the Pipelines operator CRDs. The following changes are specific to StoneSoup:

- Disable Tekton Triggers. Pipelines as Code will be the favored mechanism for
  event-based triggering of pipelines for now. This decision can be revisited
  in the future based on need.
- Disable the pruner that comes with the operator. Tekton Results will be used
  to prune `PipelineRun` and `TaskRun` data off cluster, thereby ensuring data
  is archived before removal.
- Direct Pipelines as Code to use a URL pattern that displays the `PipelineRun`
  or `TaskRun` info from the Hybrid Application Console (HAC). This ensures
  end users do not need access to the underlying compute cluster(s).

## Consequences

- StoneSoup will need to provide a cohesive experience for building and
  releasing operators. Until this is complete, Pipeline components in StoneSoup
  may need to be deployed in the following fashion:
  - Use the OpenShift Pipelines operator to deploy the core Pipeline controllers.
  - Deploy Tekton Chains, Tekton Results, and Pipelines as Code using ArgoCD.
    StoneSoup should be used to build these components and apply updates.
  - Eventually onboard core Tekton components to StoneSoup, with the goal of
    building the operator in StoneSoup.
- Tekton Results will need to be productized and incorporated into the
OpenShift Pipelines operator.
- Tekton Triggers should be disabled in StoneSoup using appropriate operator
  configuration.
- The Tekton Pruner needs to be disabled in StoneSoup using appropriate
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
  This is not available yet, but may be possible through projects like
  [rukpak](https://github.com/operator-framework/rukpak).
