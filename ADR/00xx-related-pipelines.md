# Related Pipelines

* Date 2023-06-xx

## Status

Proposed

## Context

As an AppStudio user, I want to be able to build and test multiple coupled components which depend on each other. I want that process to be easy.

There are three use cases in scope for this document:

As an initial draft and to simplify comparison, these use cases are not changed from the content proposed in [PR#113](https://github.com/redhat-appstudio/book/pull/113).

* A user team has their own **intermediate base image**. When they propose an update to their base image with new content, they want to see if that’s going to break any of their Components that depend on it before merging. AppStudio should posit what rebuilds of those Components will look like and if they will pass their tests, and report that feedback back to the original pull request that updated content of the intermediate base image ([RHTAP-967](https://issues.redhat.com/browse/RHTAP-967)). A real example of this is in stolostron, where a [layered image component](https://github.com/stolostron/console/blob/main/Dockerfile.mce.prow#L20) refers to a [common parent image](https://github.com/stolostron/common-nodejs-parent).
  * In this case, the app images must be rebuilt for the intermediate image update to really be evaluated in a functional way.
  * This is a many-to-one dependency. Many component images depend on one intermediate base image.
* A user team has an **OLM operator**. When they propose an update to one of their operands with new code, they want to see if that’s going to break their operator. AppStudio should posit what a rebuild of the operator bundle will look like and if it passes its tests and report that feedback back to the original pull request that updated the code in one of the operand images ([RHTAP-992](https://issues.redhat.com/browse/RHTAP-992)). A real example of this is in [gatekeeper](https://github.com/gatekeeper/gatekeeper-operator) where the operator repo contains both the [controller code](https://github.com/gatekeeper/gatekeeper-operator/blob/main/controllers/gatekeeper_controller.go) and the [bundle metadata](https://github.com/gatekeeper/gatekeeper-operator/blob/main/config/manifests/bases/gatekeeper-operator.clusterserviceversion.yaml), which need to be built into separate images([1](https://github.com/gatekeeper/gatekeeper-operator/blob/main/Dockerfile) and [2](https://github.com/gatekeeper/gatekeeper-operator/blob/main/bundle.Dockerfile)), separate Components in AppStudio.

  * In this case, the bundle image must be rebuilt for the operand image update to be really be evaluated in a functional way.
  * This is a one-to-many dependency. One operator bundle depends on many operand images.
* A user team just has **two components that depend on each other in a functional way**. When they propose an update to one component, they want to submit a corresponding change to the second component, and have those tested together before merging both.
  * In this case, on any given day, component B’s PRs may or may not have dependencies on PRs from component A. Not all changes are linked.
  * This is a many-to-many dependency. The user may have lots of components that depend on lots of other components.

In theory **any combination of the cases above** could be present in an app. They could have one intermediate base image, many operand images that depend on that, and one or more operator bundles which depend on those.

Today, users work around how complicated it is to manage digests themselves by instead using *floating tags*, which have the benefit of being easy to use - no need to update - but have the problem of being unclear. It's not exactly clear what you're building against if you refer to it by tag. Potentially insecure. We want to make it easy for users to do better.

## Decision

In order to support linking of multiple components, any component dependency will be recorded as part of the Tekton definition to be run for pull request event types.

### User flow

Users will be able to specify dependencies between components by modifying the pull request Tekton definition or by adding configuration to the UI which will result in AppStudio representing the configuration in the Tekton definition. This definition will allow the specification of whether dependent components should be run in parallel or serially when combined.

### Pipelines as Code (PaC)

PaC will expand its design to include orchestration logic. This orchestrator will enable a plugable scheduler which is capable of identifying the dependent repositories and Tekton definitions (composing the metadata required to specify a component in AppStudio). When a component's Tekton definition indicates a dependency on another component, PaC will be able to combine the defined pipelines so that the resulting Pipeline definition builds images in the proper order.

When identifying the pipeline definitions to merge, PaC will first look at the linked components for the same branch where a build was triggered from. If no matching branches are found then the default branch will be used.

PaC will need to recursively expand the DAG to ensure that all dependent components are linked.

### Build service

The build service will be able to detect any component pull specs from earlier in a composite pipeline that differ from a previous Snapshot and replace all references of the previous pull spec with the new pull spec before building the component.

### Integration service

The integration service will be able to support updating multiple Component updates from a single PipelineRun such that all components built in a composite pipeline can be tested together as an Application in any configured integration tests.

### Eventual consistency

This flow of related changes as proposed in this ADR is limited to changes in the pull request Tekton definitions. It enables related components to be rebuilt as needed to ensure that image references are maintained and up to date. Once pull requests are merged for one component and the resulting container image is built, the resulting Snapshot will be "out of sync" in that some references in dependent images (i.e. RelatedImages in bundles or image references in a Dockerfile) will not match the latest artifact in the Snapshot. When build dependencies within the same Snapshot are enabled ([RHTAP-967](https://issues.redhat.com/browse/RHTAP-967)), this synchronization issue will be detected and relevant policies will fail.

After a new Snapshot is produced, a Renovatebot will be responsible to propogating the updated image references to all other Components within the Application. After these pull requests have all been merged, consistency should be achieved again and all relevant policies should pass. 

## Applied to Use Cases

Let's apply the architecture to some use cases, and see how it plays out:

### Common Parent Image

Scenario: an application image depends on a common parent image. The user has 1 Application, and 2 Components. One of them is the parent image. The other image is built FROM that image.

* The common parent image will register a dependency to all other Components
* After the parent image is built, all other dependent Component images will be rebuilt.
* If any of these dependent components are further dependent on images (i.e. a bundle image), then those images will also be rebuilt.
* Intermediate image references can be replaced either by digest or by full image reference as these are used within the same snapshot. The full pull spec should match in any dependent image.

### OLM Operators, with components in different repos

Scenario: the user has 5 components. One of them is a “bundle” image. It contains references to the other four images by digest. None of the images are in the same repo.

* Each non-bundle component declares that it depends on the bundle image.
* When a change is introduced into any of the non-bundle images, the pullspec will be replaced in the bundle image to enable the change to be tested.
* Since the pullspec location (i.e. registry and repository) might not be consistent with that in the snapshot due to the fact that the bundle image is targeting the _final_ location of the image, replacement will have to be performed by only finding and replacing the image digests.

### OLM Operators, with components in the same repo

Another OLM Operator Scenario: an operator git repo contains both the controller code and the bundle metadata.

* The bundle component will not indicate any dependency in its PR definition.
* The operator PR tekton definition will indicate a dependency on the bundle image.
* The bundle image will be rebuilt after the operator is built to replace the pullspec referenced in the bundle image.
* Since the pullspec location (i.e. registry and repository) might not be consistent with that in the snapshot due to the fact that the bundle image is targeting the _final_ location of the image, replacement will have to be performed by only finding and replacing the image digests.

## Consequences

* The creation and maintenance of PRs for builds running from AppStudio components remains unchanged (an alternative design that we considered involved creating PRs on other components to maintain the references). This means that the effect on the user managing multiple components in an application is reduced as there are fewer PRs to maintain and keep track of. 
* The user can pin their digest references in git. AppStudio will automate maintaining them. No magical resolution of tags in the buildsystem at build time, or worse at runtime.
* Changes will be required to multiple AppStudio components including a large change to PaC. This might be too much change across the various services to support this user flow.
* The composite pipelines generated have the potential to rebuild many container images that will always be "throw-away." This can result in an undesired increased cost of running builds.
* Users may have only a few Components, or they may have many (many dozens) of Components. Once they get past so many component dependencies, we suspect that users will likely change from checking that all dependent images work with the new parent image to "sharing" the verification load: building the image and pushing it out for other components/dependencies to update and test within their own PRs. With this design, the user can achieve this by deleting their dependent repositories. The parent image will be built and tested as normal. The user can still hypothetically construct their own "dependent PR" to test a particular layered component on an unmerged parent image change.

## Open Questions

* To reduce the time of inconsistency, can renovatebot create the PRs on dependent components immediately or should renovatebot always respect the configuration files? Does that still make sense if renovatebot is not being run on a cron basis?
* Would there be a way for a user to be able to issue a command in a PR to enable a one-off linking of multiple components or would this type of linking need to occur via a temporary modification to the Tekton pipeline definition in the same PR?
* Do we need to extend image signing support to all images produced in PR pipelines? This would primarily benefit users by reducing "false positives" in EC contract failures that would be expected to pass on normal builds. If so, we would need a solution to sign multiple images in a single Pipeline run (i.e. potentially keyless signing instead of Chains-based signing).