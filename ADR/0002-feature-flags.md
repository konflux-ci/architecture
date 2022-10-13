# 2. Feature Flags

Date: 2022-06-01

## Status

Accepted

## Context

We know we need some way for processes to recognize that they’re working in a HACBS context or in an
App Studio context. We’ve been referring to this need loosely throughout the first half of 2022 as
“feature flags”.

Some examples:

- [hac] needs to know whether or not to render different screens
  for HACBS views and to direct the user to those views instead of App Studio views.
- [build-service] needs to know whether or not to install normal App Studio
  webhooks in the git repo of the user in order to trigger builds, or whether it should execute the
  setup logic necessary for HACBS [customized pipelines]
  (submitting a PR to the repo providing the default pipeline as source).
- [build-service] needs to know whether or not to promote a built image pullspec
  directly to the [Component] CR after it is built,
  or whether to wait and let the [integration-service] test things first.
- Build Service needs to know whether or not to create an [ApplicationSnapshot] after the
  [Component] CR is updated, or whether it should defer to the [integration-service] to create new
  [ApplicationSnapshots].

We have been thinking about this flag as a HACBS-wide flag. We had assumed that the *workspace
itself* would be HACBS enabled, or not. Perhaps the workspace would have an explicit type that
would let us know we are looking at or operating in a HACBS workspace, and not an App Studio
workspace.

**Problem**: workspaces don’t have a type useful for anything beyond initialization and they’re not
going to have one. Features and APIs should be composable in a single workspace. A user might use
a single workspace for *lots* of different activities - beyond just App Studio or HACBS. A workspace
type is too restrictive and single-purpose.

We had also been considering that the “flag” could be inferred from the organizational hierarchy of
the workspace - where, if the workspace was owned by an org that was owned by a tenant that was in
some pre-configured list of HACBS-enabled tenants, then this workspace should be considered
HACBS-enabled, workspace-wide.

**Problem**: we likely need to support the co-existence of HACBS-enabled workspaces and non-HACBS App
Studio workspaces in the same tenant. Tenants are big enterprises, with lots of teams, and those
teams have different adoption patterns. Some will want to be on App Studio, while others will want
to be on HACBS. Although we don’t have real customer input on this, it is reasonable to expect that
a single customer team may want to work on some projects in the HACBS feature set, and others in an
App Studio feature set. Much more realistically, imagine the path for “turning on HACBS” at the
tenant level. If you flip the switch at the tenant level, do all workspaces for all teams in the
tenant suddenly change behavior? A tenant-wide setting is too coarse and disruptive to tenant teams
that would appreciate independence.

## Decision

Use “api discovery” to control the enablement of *individual* features in *individual* workspaces.

[KCP] provides the [APIBinding] resource as a way of letting the user declare that a particular API
(read: CRD) should be made available in a single workspace. The user installs something in their
workspace by creating an [APIBinding]. Our processes (controllers and [hac]) should query for the
availability of a particular API they care about, and let their behavior be influenced by the
existence or non-existence of that API.

**Example**: if the [IntegrationTestScenario] API is present in KCP for a workspace, then a process
can know that the [integration-service] features of HACBS are enabled in the workspace.

- When onboarding a new [Component], [build-service] should consult the discovery API for
  [IntegrationTestScenario], and if it exists it should not install App Studio webhooks but should
  instead submit a PR prompting the HACBS onboarding process.
- When a build completes, [build-service] should consult the discovery API for
  [IntegrationTestScenario], and if it exists it should not promote the built image pullspec to the
  [Component] CR. [integration-service] will handle that flow instead.

**Example**: if the [ReleasePlan] API is present in the workspace, then a process can know that the
[release-service] features of HACBS are enabled in the workspace.

- After testing a new [ApplicationSnapshot], the [integration-service] should consult the existence
  of the [ReleasePlan] via the discovery API before it checks for the existence of any [ReleasePlan]
  resources. If the API is present then the [integration-service] should proceed as normal. If the
  API is *not present*, then the [integration-service] should silently ignore its codepath to
  inspect [ReleasePlans] and trigger automated [Releases].
  - If the API is *not present,* that means the user is in a configuration where they have installed
    the [integration-service] but they have *not installed the [release service]*. We don’t have
    a concrete reason to support this configuration today - but explicitly checking for the API
    before checking for [ReleasePlan] makes a cleaner interface between the two services. They’re
    now composable, rather than being part of a monolithic “HACBS feature set”.

**Example**: In [hac], we’re implementing HACBS screens as part of the [hac-dev] plugin.

- When generating a list of workspaces, [hac] could describe those workspaces as HACBS-enabled or
  not if one or more HACBS APIs are available via kubernetes API discovery in kcp. Those APIs will
  be present if [APIBinding] objects are present in the workspace and have been handled by KCP.
- When viewing an App Studio workspace, the [hac-dev] plugin should present the user with the
  corresponding HACBS view if one or more HACBS APIs are present in the workspace, which again will
  be present if corresponding [APIBinding] objects have been created in the workspace and handled by
  fulfilled by KCP.

## Open Questions

- How should [hac] decide whether or not to render the topology view for pipelines? It is reasonable
  to check for the existence of an API from the build side of the house, but we don’t have an API
  today that could signal this. It’s just PipelineRuns.
  - Use the [IntegrationTestScenario] API today, which is not a perfect fit, but will let us move
    forwards.

## Consequences

- We should experience a cleaner API - composable services, more aligned with a larger App Cloud API
  being developed by multiple teams.
- We may find ourselves forced into creating a CRD (and corresponding [APIBinding]) just so that we
  can influence the behavior of another service, just so we can give it a feature flag to check.
- Services that change their behavior based on the existence or non-existence of APIs that they do
  not own need to take special care if they manage some off-cluster state.
  - For example, [build-service] manages git webhooks when users onboard with a [Component] CR.
    However, the details of that webhook may change depending on whether or not the
    [IntegrationTestScenario] API is present or not. If the [IntegrationTestScenario] is installed
    or uninstalled, [has] should properly handle transitioning off-cluster state to align to the
    currently available APIs in the workspace; it should reconcile the webhooks with the intended
    state in the workspace which includes both Component CRs as well as the existence of
    [IntegrationTestScenario] APIs (CRDs).

## References

Originally drafted in a [google document](https://docs.google.com/document/d/1KcXWZ8VGUg_iR0RjdGuDYedP8ZW63XCgF26KZUNgpeQ/edit)

[hac]: ../book/hybrid-application-console.md
[hac-dev]: https://github.com/openshift/hac-dev
[has]: ../book/application-service.md
[build-service]: ../book/build-service.md
[integration-service]: ../book/integration-service.md
[customized pipelines]: https://issues.redhat.com/browse/HACBS-9
[KCP]: ../ref/kcp.md
[APIBinding]: ../ref/kcp.md#apibinding
[Component]: ../ref/application-environment-api.md#component
[ApplicationSnapshot]: ../ref/application-environment-api.md#applicationsnapshot
[ApplicationSnapshots]: ref/application-environment-api.md#applicationsnapshot
[ReleasePlan]: ../ref/release-service-api.md#releaseplan
[ReleasePlans]: ../ref/release-service-api.md#releaseplan
[IntegrationTestScenario]: ../ref/integration-service-api.md#integrationtestscenario
