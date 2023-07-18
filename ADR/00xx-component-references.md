# XX. Component References

* Date 2023-06-xx

## Status

Proposed

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
  * This is a many-to-many dependency. The user may have lots of components that depend on lots of other components.

In theory **any combination of the cases above** could be present in an app. They could have one common parent image, many operand images that depend on that, and one or more operator bundles which depend on those.

Today, users work around how complicated it is to manage digests themselves by instead using *floating tags*, which have the benefit of being easy to use - no need to update - but have the problem of being unclear. It's not exactly clear what you're building against if you refer to it by tag. Potentially insecure. We want to make it easy for users to do better.

## Decision

### API

* Introduce a new CustomResource called `ComponentReference` that lets one Component declare that another Component **embeds a reference** to it.
  * A `ComponentReference` spec contains two fields: a referent, and a referer
  * [integration-service] handles the testing and promotion of all referents in a special way.
  * A new set of functionality for [build-service] uses the `ComponentReference` links to propose updates to users git repositories.
* Introduce a new convention for PRs that lets one PR declare that it depends on another PR.
* Important to understand: the declared reference embeddings as defined in the `ComponentReferences` and PR dependencies are two different things.
  * `ComponentReferences` are declarations about which Components we should expect to see PR dependencies for.
    * You say in english: “Component A references Component B.”
  * PR dependencies can be supplied by the user without any declared `ComponentReferences` on the respective Components.
    * You say in english: “PR #1 depends on PR #2.”

### Integration-service

* When [integration-service] notices a build of a *referent* Component (where another Component declares that it embeds a reference to this one), it always skips all testing (both pre-merge and post-merge). It always promotes the image to the global candidate list when the PR is merged, but it does not promote to dev environment (post-merge) and it does not create Releases (post-merge).
  * Builds of *referent* Components never directly trigger tests, never trigger promotion, or Releases.
* When [integration-service] notices a build of a *referer* Component (one that declares that it embeds references to others), it does testing as normal, promotes to global candidate list as normal, and it promotes to dev env as normal, and it creates Releases as normal.
* When [integration-service] notices a build of a Component that references no other components and no other components refer to it - then it proceeds like normal, runs tests, promotes, deploys, releases, etc.

### Build-service

* [build-service] will propagate the digest from one Component to another as a PR – following the declared `ComponentReferences`. This is a bit like renovatebot wrapped in a controller. The [build-service] acts when it sees that a build pipelinerun has completed successfully for a *referent* image.
  * If this is the first time it has seen this *referent* updated in this way, it will file a new pull request on the *referer* supplying the pullspec and digest of the new referent, using the same branch name as was used for the *referent* PR.
  * If a PR on that branch already exists, update that branch with an additional commit including the new *referent* digest.

The [build-service] will also update the PR it filed when the PRs that triggered it are merged or updated. It may update the description and/or it may rebase on the main branch and/or it may issue /retest. Need to figure out what we want here.

### “PR dependency”

TODO - describe exactly how the user specifies that one PR depends on another. PaC will have to pass this through to the PipelineRun as an annotation. For now, just assume it is possible and defined.

* When [integration-service] notices a build from a PR (PR#2) that declares it depends on another PR (PR#1), it will do testing but it will also:
  * Construct the Snapshot for the test using the image from the triggering build pipeline of PR #2 as well as image found on the latest build pipeline associated with PR#1. This lets a user test PR #2 including unmerged content from PR #1.
  * Post the test results back on PR#1 in addition to the results it would normally post to PR#2.
  * Post a special followup check result on PR#2 that “fails” saying, “don’t merge this. It still depends on another.”
* When [integration-service] notices a build from a PR (PR#2) that declares it depends on another PR (PR#1) but that other PR (PR#1) is merged, it will do testing and it will post a followup check result that “succeeds” saying “this is mergeable, all other PRs that it depends on are merged.”
  * If PR #2 depends on two or more other PRs (not just 1), then [integration-service] should perform testing and post *distinct* followup check results on PR#2 reporting the merge status of all PRs it depends on. As they merge, those distinct check results turn from failing to passing. When all have passed, then PR#2 will appear as mergeable to the user.
  * If PR #1 is closed without merging, then PR #2 could languish. [build-service] should check this for this situation on a periodic basis (for want of an event to trigger it) and either update or close PR #2.

## Applied to Use Cases

Let's apply the architecture to some use cases, and see how it plays out:

### Common Parent Image

Scenario: an application image depends on a common parent image. The user has 1 Application, and 2 Components. One of them is the parent image. The other image is built FROM that image.

* The child image Component declares that it embeds a reference to the parent image Component, by way of a new `ComponentReference` CR.
* [integration-service] will always skip testing for parent image update builds, will never promote them, or use them to initiate Releases, but it will promote them to the global candidate list.
* [build-service] will propagate digest references as a PR to the child image Component repo, by analyzing the available `ComponentReference` CRs in the workspace.
* [integration-service] will post followup checks on the normal component PRs saying “don’t merge this” until the parent image update is merged.
* When the parent image PR is merged, [build-service] will update the PRs it originally filed to say “no more dependency here” and potentially rebase the PRs to trigger a new build (or use /retest).

Think about branches:

* User team updates parent image with branch update-2023-06-07 (or whatever).
* [build-service] uses that same branch (update-2023-06-07) everywhere it propagates the digest to.
* The branch doesn't have much effect in this scenario.

### OLM Operators, with components in different repos

Scenario: the user has 5 components. One of them is a “bundle” image. It contains references to the other four images by digest. None of the images are in the same repo.

* The bundle Component declares that it embeds references to all other operand image Components, by way of the new `ComponentReference` CR.
* [integration-service] will always skip testing for all components except for the bundle image Component, because the bundle image Component declares that it embeds references to all other Components.
* [build-service] will propagate digest references as a PR to the bundle image
* [integration-service] will post followup checks on the bundle PR saying “don’t merge this” until all operand PRs are merged.

Think about branches:

* User team updates their operand images with branch feature-1234 (or whatever).
* [build-service] uses that same branch in its PR to the bundle repo.
* If user submits three operand image PRs and uses the same branch name for all – then the digests all pile up on the same bundle branch, the same bundle PR.
* If the user submits three operand image PRs and uses different branch names for all – then the digests are split among three different bundle branches, three different bundle PRs.

---

### OLM Operators, with components in the same repo

Another OLM Operator Scenario: an operator git repo contains both the controller code and the bundle metadata.

* The user has two Components, that both point to the same repo.
* The bundle Component declares that it embeds references to the controller image Component, by way of a new `ComponentReference` CR.
* [integration-service] will always skip testing for the controller component because it is a *referent* Component.
* [build-service] will propagate the digest reference as a PR to the bundle image, which happens to be the same git repository as the controller Component.
  * The user submitted their controller image update on the `new-feature` branch.
  * [build-service] could do one of the following:
    * ❌ Push its commits with the new image digest references to the same feature branch.
      * Will [build-service] -- acting as the TAP github App -- have rights to push to that branch? Probably not.
    * 🤔 Submit its commits as a suggestion on the original PR, which the user can accept or not.
      * This would be “odd” for build service, but maybe nice from the user’s point of view. Just one PR to work with.
    * ❌ Push its commits with the new image digest references to a new feature branch based on the original feature branch, called `new-feature-build-service`
      * This could be nice, but the PR will trigger new builds of the original image since it contains code changes for the controller (here, I am assuming that we can limit builds in PaC based on contextDirectories for multi-Component repos; we don’t have this today, but assume that we do).
    * ✅ Push its commits with the new image digest references to a new feature branch that is not based on the original feature branch, called `new-feature-from-build-service`
      * This works like it does in most other cases. Let the user merge the original PR, and only after that will [integration-service] update the checks for `new-feature-from-build-service` to say “okay to merge now!”

## Open Questions

* To give the user some control, should we make [build-service] respect [renovatebot
  configuration files](https://docs.renovatebot.com/configuration-options/)? Does that still make
  sense if renovatebot is not being run on a cron basis? (If the answer to the original question is
  yes, then that may inform whether how we implement the new functionality in [build-service].
* Since we don't have exclusive control over merging changes (or really, any control at all
  exclusive or not), we can't prevent the user from merging things out of order. This means they can
  get themselves into trouble. We try to provide feedback via github checks to help prevent this;
  but we can't stop it. How does the user recover from this situation? Are there any side-effects?

## Consequences

* The basics of AppStudio builds are unchanged with this design (an alternative design that we considered involved changing the way pull-request build pipelines were defined and processed by PaC). This means less change spidering out to other AppStudio systems to support this change.
* The user can pin their digest references in git. AppStudio will automate maintaining them. No magical resolution of tags in the buildsystem at build time, or worse at runtime.
* The user is going to get more PRs on their repo. Maybe too many PRs.
* Users may have only a few Components, or they may have many (many dozens) of Components. Once they get past so many component dependencies, we suspect that users will likely change from checking that all dependent images work with the new parent image to "sharing" the verification load: building the image and pushing it out for other components/dependencies to update and test within their own PRs. With this design, the user can achieve this by deleting their `ComponentReference` CRs. The parent image will be built and tested as normal. [build-service] will not send PRs. The user can still hypothethically construct their own "dependent PR" to test a particular layered component on an unmerged parent image change.

[build-service]: ../ref/build-service.md
[integration-service]: ../ref/integration-service.md
