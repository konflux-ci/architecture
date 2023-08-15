# 28. Component Dependencies

* Date 2023-08-15

## Status

Accepted

## Context

As an AppStudio user, I want to be able to build and test multiple coupled components which depend on each other by digest reference. I want that process to be easy.

There are three use cases in scope for this document:

* A user team has their own **common parent image**. When they propose an update to their base image with new content, they want to see if that’s going to break any of their Components that depend on it before merging. AppStudio should posit what rebuilds of those Components will look like and if they will pass their tests, and report that feedback back to the original pull request that updated content of the common parent image ([RHTAP-967](https://issues.redhat.com/browse/RHTAP-967)). A real example of this is in stolostron, where a [layered image component](https://github.com/stolostron/console/blob/main/Dockerfile.mce.prow#L20) refers to a [common parent image](https://github.com/stolostron/common-nodejs-parent).
  * In this case, the dependent images must be rebuilt to include the common parent image update in order to determine the actual effect of the proposed change.
  * This is a many-to-one dependency. Many component images depend on one common parent image.
* A user team has an **OLM operator**. When they propose an update to one of their operands with new code, they want to see if that’s going to break their operator. In order to be fully tested, a single rebuilt image needs to be included as a reference in a bundle image in order to be tested as a whole unit when deployed via OLM, i.e. for integration tests ([RHTAP-992](https://issues.redhat.com/browse/RHTAP-992)). A real example of this is in [gatekeeper](https://github.com/gatekeeper/gatekeeper-operator) where the operator repo contains both the [controller code](https://github.com/gatekeeper/gatekeeper-operator/blob/main/controllers/gatekeeper_controller.go) and the [bundle metadata](https://github.com/gatekeeper/gatekeeper-operator/blob/main/config/manifests/bases/gatekeeper-operator.clusterserviceversion.yaml), which need to be built into separate images([1](https://github.com/gatekeeper/gatekeeper-operator/blob/main/Dockerfile) and [2](https://github.com/gatekeeper/gatekeeper-operator/blob/main/bundle.Dockerfile)), separate Components in AppStudio.
  * In this case, the bundle image must be rebuilt for the operand image update to be tested at all (assuming OLM is the strategy for deploying the operator).
  * This is a one-to-many dependency. One operator bundle depends on many operand images.
* A user team just has **two components that depend on each other in a functional way**. When they propose an update to one component, they want to submit a corresponding change to the second component, and have those tested together before merging both.
  * In this case, on any given day, component B’s PRs may or may not have dependencies on PRs from component A. Not all changes are linked.

In theory **any combination of the cases above** could be present in an app. They could have one common parent image, many operand images that depend on that, and one or more operator bundles which depend on those.

Today, users work around how complicated it is to manage digests themselves by instead using *floating tags*, which have the benefit of being easy to use - no need to update - but have the problem of being unclear. It's not exactly clear what you're building against if you refer to it by tag. Potentially insecure. We want to make it easy for users to do better.

## Decision

### Interface changes

**Declared Component Dependencies**: Introduce a new field on the `Component` resource called `depends on` that lets one Component declare that another Component **depends on it**.

* The `depends on` field is a list.
* We will call a Component which has a dependency on another Component: a **"dependant"** component.
* We will call a Component on which other Components have a dependency: a **"dependency"** component.
* [integration-service] will handle the testing and promotion of all **dependancy** components in a special way.
* [build-service] will use the `depends on` links to propose updates to users' **dependant** git repositories.
* The set of Components and their "depends on" links form a directed-acyclic-graph (DAG). Application-service is responsible for making sure that cycles are not introduced and for managing references in the lifecycle of all Components in the Application. Deleting a Component should be well-defined.
* As with Components in general, the "depends on" references are Application-scoped. Declared relationships between Components in different Applications are not to be considered valid. Declared relationships between Components in different namespaces are not to be considered valid.

**PR Groups**: Introduce a new convention for PRs that lets one PR declare that it is related to another PR.

* Treat the **source branch name** of the PR as a slash-delimited string, and use the first element of that
  list as the PR Group name.
* A new set of functionality for [integration-service] uses PR Groups to guide testing of related
  PRs.
* The set of PRs in a PR Group form a flat set.
* PR Groups are scoped to Component repos under a single Application. Even if PRs across different
  applications share the same **source branch name**, they shouldn't be considered part of the
  same PR Group.
* For example, if the source branch name for a PR is `my-feature/change-1`, then the PR Group
  name should be interpreted as `my-feature`.
* A source branch name with no slashes is the degenerate case. For example, if the source branch
  name for a PR is `my-feature`, then the PR Group name should be interpreted as `my-feature`.
* Since all PRs have a source branch name, all PRs are trivially members of a PR Group.

Important to understand: the declared dependencies as defined on the Components' `depends on` lists and PR Groups are two different things:

* Component dependencies are declarations about which Components' builds need each other. Automation uses this to create PRs in PR Groups.
  * You say in english: “Builds of Component A depend on builds of Component B.”
* PR Groups can be supplied by the user without any declared Component dependencies:
  * You say in english: “PR #1 and PR #2 are in the same PR Group.”

**Context directories** for [Pipelines as Code](https://pipelinesascode.com/)(PaC): introduce a new `spec.context` field in the `Repository` CR. When present, this field instructs PaC to only create a PipelineRun for events which include changes to the declared context directory in the git repository. This enables us to only run PipelineRuns that are relevant to Components that change in a given push or pull request event. By default, this is ".": the entire git repository.

* [build-service] is responsible for setting the context dir field on the Repository CR and for propagating changes to the context dir on the user's Component CRs to the Repository CR.

See also [RHTAP-371](https://issues.redhat.com/browse/RHTAP-371).

### Integration-service and Component dependencies

* When [integration-service] notices a build of a Component which is known to be a **dependency** component (where another Component declares that it depends on this one by way of a `depends on` reference), it always skips all testing (both pre-merge and post-merge). It always promotes the image to the global candidate list when the PR is merged, but it does not promote to dev environment (post-merge) and it does not create Releases (post-merge).
  * Builds of Components which are known to be **dependency** components never directly trigger tests, never trigger promotion, or Releases.
* When [integration-service] notices a build of a Component which is known to be a **dependant** component (one for which there is another Component that depends on it by way of a `depends on` reference on that other Component), it does testing as normal, promotes to global candidate list as normal, and it promotes to dev env as normal, and it creates Releases as normal.
* When [integration-service] notices a build of a Component that references no other components and no other components refer to it - then it proceeds like normal, runs tests, promotes, deploys, releases, etc.

### Build-service and Component dependencies

* [build-service] will propagate the digest from one Component to another as a PR – following the declared `depends on` references. This is a bit like renovatebot wrapped in a controller. The [build-service] acts when it sees that a build pipelinerun has completed successfully for a **dependency** component image (one on which others depend).
  * If this is the first time it has seen this **dependency** component updated in this way, it will file a new pull request on the **dependant** components supplying the pullspec and digest of the new **dependency** components, using the same branch name prefix as was used for the **dependency** component PR.
  * If a PR on that branch already exists, update that branch with an additional commit including the new **dependency** component digest.

The [build-service] will also update the PR it filed when the PRs that triggered it are merged or updated. It may update the description and/or it may rebase on the main branch and/or it may issue /retest. Need to figure out what we want here.

### Integration-service and PR Groups

* When [integration-service] notices a build from a PR (PR#2) that it detects is in the same group as a build from another PR (PR#1), it will perform testing but it will perform that process with some modifications. It will:
  * Construct the Snapshot for the test using the image from the triggering build pipeline of PR #2 as well as the image found on the latest build pipeline associated with PR#1. This lets a user test PR #2 including unmerged content from PR #1. It will construct the Snapshot from the latest builds of all PRs in the PR Group.
  * Post the test results back on PR#1 in addition to the results it would normally post to PR#2. It will post the test results back to all PRs in the PR Group.

### Build-service and PR Groups

* When [build-service] responds to the build of a PR (PR #1) and propagates the digest from one Component to another as a PR (PR#2). It follows the declared `depends on` references to know which other repos should receive an update PR. It marks the PR that it submits (PR #2) as being in the same PR Group (slash-prefixed name of the git source branch) as the triggering PR (PR #1). This enables pre-merge testing of both changes.
* When [build-service] submits PR #2:
  * It marks it as "Draft" and it includes a reference to the triggering PR (PR #1) in the description of the automatically submitted PR (PR #2), giving the user some indication that it should not be merged out of order.
  * It checks to see if the two Components (source and destination as determined by the `depends on` references) are in the same git repository (a monorepo) and if PR #1 contains any changes to the `context` directory for the destination Component. If it does, then it create a new commit copying the code changes from that context directory in PR #1 to that context directory in PR #2, and it bases the commit that updates the digest reference on top of this synthetic commit.

## Applied to Use Cases

Let's apply the architecture to some use cases, and see how it plays out:

### Common Parent Image

Scenario: an application image depends on a common parent image. The user has 1 Application, and 2 Components. One of them is the parent image. The other image is built FROM that image.

* The child image Component declares that it `depends on` the parent image Component, by way of the new field on the Component CR.
* [integration-service] will always skip testing for parent image update builds, will never promote them, or use them to initiate Releases, but it will promote them to the global candidate list.
* [build-service] will propagate digest references as a PR to the child image Component repo, by analyzing the `depends on` fields of all other Components in the Application. The PR that it files must be submitted in such a way that it appears in the same PR Group (the same slash-prefixed name of the git source branch) as the triggering PR submitted by a user.
* When the parent image PR is merged, [build-service] will update the PRs it originally filed to take them out of "Draft" to indicate that they are safe to merge now as long as there are no other unmerged triggering PRs in the same group. It may potentially rebase the PRs to trigger a new build or use `/retest`.

Think about branches:

* User team updates parent image with branch `update-2023-06-07` (or whatever).
* [build-service] uses that branch name as a prefix in the branch names that it chooses (`update-2023-06-07/<suffix>`) everywhere it propagates the digest to.

### OLM Operators, with components in different repos

Scenario: the user has 5 components. One of them is a “bundle” image. It contains references to the other four images by digest. None of the images are in the same repo.

* The bundle Component declares that it `depends on` all other operand image Components, by way of the new field on the Component CR.
* [integration-service] will always skip testing for all components except for the bundle image Component, because the bundle image Component declares that it depends on all other Components. (All other Components are **dependency** Components. The bundle is the only **dependant** Component.)
* [build-service] will propagate digest references as a PR to the bundle image, in the same PR Group
  as the originating PR. The PR will be marked as "Draft" to indicate they should not be merged.
* When the operand image PR is merged, [build-service] will update the PRs it originally filed to
  take them out of "Draft" to indicate that they are safe to merge now as long as there are no other
  unmerged triggering PRs in the same group.

Think about branches:

* User team updates their operand images with branch `feature-1234` (or whatever).
* [build-service] uses that same branch in its PR to the bundle repo.
* [build-service] uses that branch name as a prefix in the branch names that it chooses (`feature-1234/<suffix>`) to send to the bundle repo.
* If user submits three operand image PRs and uses the same branch name for all (`feature-1234`) – then the digests all pile up on the same bundle branch (`feature-1234/<suffix>`), the same bundle PR.
* If the user submits three operand image PRs and uses different branch names for all – then the digests are split among three different bundle branches, three different bundle PRs.

---

### OLM Operators, with components in the same repo

Another OLM Operator Scenario: an operator git repo contains both the controller code and the bundle metadata.

* The user has two Components, that both point to the same repo.
* The bundle Component declares that it `depends on` the controller image Component, by way of the new field on the Component CR.
* [integration-service] will always skip testing for the controller Component because it is known to be an **dependency** component.
* [build-service] will propagate the digest reference as a PR to the bundle image, which happens to be the same git repository as the controller Component.

Think about branches:

* The user submitted their controller image update on the `new-feature` branch.
* [build-service] pushes its commits with the new image digest references to a new feature branch that uses the triggering feature branch name as a prefix: `new-feature/<suffix>`.
  * This works like it does in most other cases. Let the user merge the original PR, and only after that will [integration-service] update the checks for `new-feature` to say “okay to merge now!”
  * When the user merges the original PR, [build-service] will update the PR it filed on the `new-feature/<suffix>` branch to take it out of "Draft", indicating that it is safe to merge now. It may potentially rebase the PR to trigger a new build or use `/retest`.

## Miscellany

* To give the user some control, should we make [build-service] respect [renovatebot
  configuration files](https://docs.renovatebot.com/configuration-options/)? Does that still make
  sense if renovatebot is not being run on a cron basis? (If the answer to the original question is
  yes, then that may inform whether how we implement the new functionality in [build-service]). No.
  Even though [build-service] here is acting _like_ renovatebot and even though we may use
  renovatebot as the implementation underneath, it likely does not make sense to let the user
  control this particular path of updates with a renovatebot configuration file. We want to update
  specific things (digests) at specific times (in response to other PRs).
* Since we don't have exclusive control over merging changes (or really, any control at all
  exclusive or not), we can't prevent the user from merging things out of order. This means they can
  get themselves into trouble. We try to provide clues like marking the PR as a Draft;
  but we can't stop it. How does the user recover from this situation? Are there any side-effects?

## Consequences

* The basics of AppStudio builds are unchanged with this design (an alternative design that we considered involved changing the way pull-request build pipelines were defined and processed by PaC). This means less change spidering out to other AppStudio systems to support this change.
* The user can pin their digest references in git. AppStudio will automate maintaining them. No magical resolution of tags in the buildsystem at build time, or worse at runtime.
* The user is going to get more PRs on their repo. Maybe too many PRs for a positive UX.
* Since more PRs will trigger more PipelineRuns, our current PVC quota issues (which limit how many PipelineRuns can be run at any one time) may be exacerbated.
* Users may have only a few Components, or they may have many (many dozens) of Components. Once they get past so many component dependencies, we suspect that users will likely change from checking that all dependent images work with the new parent image to "sharing" the verification load: building the image and pushing it out for other components/dependencies to update and test within their own PRs. With this design, the user can achieve this by purging the `depends on` field values from their Component CRs. The parent image will be built and tested as normal. [build-service] will not send PRs. The user can still hypothethically construct their own PR Group to test a particular layered component on an unmerged parent image change.

[build-service]: ../ref/build-service.md
[integration-service]: ../ref/integration-service.md
