# 19. Customize URLs Sent to GitHub

Created Date: 2023-03-29

## Status

Proposed

## Context

### Motivation

When we run builds and tests on PRs (see [STONE-134](https://issues.redhat.com/browse/STONE-134)),
developers need to be provided a link to the AppStudio UI so they can see the details of their
`PipelineRuns`. This is particularly important when a `PipelineRun` produces an error/failure.
The current implementation sends links back to the OpenShift developer console on the member
cluster, which should not be accessed by general public users.

### Background

Users can get a direct link to their PipelineRun which looks like this today:
https://console.redhat.com/beta/hac/stonesoup/workspaces/adkaplan/applications/adkaplan-demo/pipelineruns/devfile-sample-qtpn-ft8dh.
Adding `/logs` to the URL lets the user drill in the logs of a particular TaskRun. At present,
there is no bookmarkable URL which allows users to see the logs of a specific TaskRun. This feature
may be added in the near future (see [HAC-3370](https://issues.redhat.com/browse/HAC-3307)).

The following components in AppStudio send data/results back to GitHub via the Checks API:

- Pipelines as Code (PaC)
- Integration Service
- Other services which may run Pipelines in response to a GitHub event (ex - potentially Release Service).

An AppStudio workspace is associated with a Kubernetes namespace on a AppStudio “member cluster”,
which is not directly accessible by end users. The namespace name on the member cluster currently
correlates with the workspace name (a suffix is added). [ADR-0010](./0010-namespace-metadata.md)
specifies that a namespace label should exist which links the member cluster namespace back to the
AppStudio workspace.

Artifacts in AppStudio are organized into Applications and Components. A namespace can have more
than one `Application`, and an `Application` can have one or more `Components`. At present, each
`Component` has an associated PaC `Repository` object, though this may be subject to change in the future.

### Requirements

For a given PipelineRun in AppStudio, the following information must be identifiable based on
information in the AppStudio member cluster:

- Workspace ID
- Application ID
- Pipeline run ID

AppStudio components that report data back to GitHub must know the root URL for the AppStudio UI.
This URL must be configurable per AppStudio deployment (ex - staging, production in 
[infra-deployments](https://github.com/redhat-appstudio/infra-deployments)).
Workspace and application IDs should _not_ be added to PipelineRun YAML that is added to git
repositories for PaC. PaC PipelineRun templates should be transportable when a user forks someone
else’s git repo.

## Decision

AppStudio components that provide `PipelineRun` result links to GitHub or other source control
management systems must provide URLs that are accessible to registered end users who have
permission to view the requested `PipelineRun` resource.

## Consequences

### Dev Sandbox: Member Cluster Labels

Member cluster namespaces MUST have the `appstudio.redhat.com/workspace_name` label, in accordance
with [ADR-0010](./0010-namespace-metadata.md).

### Pipelines as Code: Customize URLs per Repository

Pipelines as Code's `Repository` custom resource will be extended to let users/service providers
customize the `PipelineRun` URL sent to SCM providers. This will take advantage of the upcoming
parameters feature in Pipelines as Code (see [SRVKP-2940](https://issues.redhat.com/browse/SRVKP-2940)).

Below is a proposed API, with an implementation for AppStudio:

```yaml
spec:
  params:
    - name: workspace
      type: string
      value: adkaplan-demo
    - name: application
      type: string
      value: demo-app
  customConsole:
    urlPRDetails: “{{rootURL}}/workspaces/{{workspace}}/applications/{{application}}/pipelineruns/{{pr}}”
    urlPRTaskLog: “{{rootURL}}/workspaces/{{workspace}}/applications/{{application}}/pipelineruns/{{pr}}/logs”
...
```

The API Fields are as follows:

- `params` - an array of parameters which can be propagated to PipelineRuns when they are created
  by Pipelines as Code. See [SRVKP-2940](https://issues.redhat.com/browse/SRVKP-2940) for the
  actual implementation.
- `customConsole` - provides a set of templatable URLs that are used when sending data back to an SCM provider.
  The following URLs can be templated with parameters:
  - `urlPRDetails` - a link to the PipelineRun details
  - `urlPRTaskLog` - a link to the log of a particular `TaskRun` within the `PipelineRun`.
- Documentation should highlight that the following parameters can be used in the console URL template:
  - `rootURL` - the root URL for the console, set in the PaC install configuration.
  - `namespace` - namespace of the `PipelineRun`
  - `pr` - name of the `PipelineRun`
  - `task` - name of the `TaskRun` within the PipelineRun (TaskLog URL only)
  - `pod` - name of the pod for the `TaskRun` (TaskLog URL only)
  - `firstFailedStep` - name of the first failed step (TaskLog URL only)

The proposed behavior is as follows:

- If `customConsole` is not specified, fall back to the current behavior (cluster-wide custom
  console or OpenShift/Tekton Dashboard defaults)
- When `customConsole` is specified, set the URL sent back to scm providers as follows:
  - Use `urlPRDetails` to send the pipeline run details link, applying the parameters in the
    `Repository` object in addition to the default parameters for the cluster. If not set, fall
    back to current behavior.
  - Use `urlPRTaskLog` to send the task log link, applying the parameters in the `Repository`
    object in addition to the default parameters for the cluster. If not set, fall back to current
    behavior.

See [SRVKP-2994](https://issues.redhat.com/browse/SRVKP-2944) for further details.

### Build Service: Propagate AppStudio Data to Repository CR

The AppStudio build service should be enhanced as follows:

- When the `Component` CR is created/reconciled, add the following to the respective `Repository`:
  - `params` - add parameter values for the RHTAP workspace (`appstudio.redhat.com/workspace_name`
    label on namespace) and the parent `Application`.
  - `customConsole` - provide the following template URLs:
    - `urlPRDetails`: `{{rootURL}}/workspaces/{{workspace}}/applications/{{application}}/pipelineruns/{{pr}}`
    - `urlPRTaskLog`: `{{rootURL}}/workspaces/{{workspace}}/applications/{{application}}/pipelineruns/{{pr}}/logs`

### Integration Test Service: Customize URLs

The Integration service should use similar mechanisms as Pipelines as Code to customize the URL
sent back to the respective SCM provider. Namely:

- Use the same custom console URL
- Use similar templating mechanisms for getting the PipelineRun URL - example by inferring the
  AppStudio workspace from the appropriate namespace and application via the parent Application
  for a respective component.

### Privacy Impact

Workspace names might contain identifying information (ex - usernames). This could be a privacy
concern if these identifiers are distributed publicly via URLs submitted to GitHub or other public
source control repositories. This potential disclosure of identifying information should be
presented to end users.
