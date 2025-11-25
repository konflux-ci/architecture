# 56. Revised Component Model

## Status

Implementable

[//]: # (One of: Proposed, Withdrawn, Deferred, Accepted, Implementable, Implemented, Replaced)

## References

* [Konflux Community Call, 2024-08-27](https://www.youtube.com/watch?v=2-IlGvRw6iQ)
* [Konflux Community Call, 2025-03-11](https://www.youtube.com/watch?v=IwNFRNjRC_Q)
* [Konflux Community Call, 2025-03-25](https://www.youtube.com/watch?v=VwzDbUH_vjU)
* [Konflux Community Call, 2025-10-23](https://www.youtube.com/watch?v=1HgBlG-ykP8)
* [Konflux Community Call, 2025-11-06](https://www.youtube.com/watch?v=duyCp_JEaZM)

## Context

The existing application and component model in Konflux presents several
limitations that hinder our ability to scale and support flexible workflows.
Specifically, the current model requires a new component to be registered for
each use case, even when the same underlying code is being used in multiple
release scenarios. This creates unnecessary overhead and complexity, while also
limiting the reusability of our components.

Furthermore, ownership of the current APIs is unclear. They were originally
owned by HAS (which is now deprecated) and exhibit excessive coupling across
multiple services.

## Decision

We have decided to adopt a revised component model that replaces the concept of
an "application" with a "component group." The key elements of this new model
are:

* **Component Version**: A component can have none or more component versions,
  which are a combination of a component and a specific branch or tag. A single
  component version can be referenced by multiple component groups.
  build-service owns the Component API going forwards and the spec changes
  for branches.
* **Component Group**: A component group can contain component versions
  forming a Directed Acyclic Graph (DAG) that represents
  the release structure. This allows for greater flexibility and reusability,
  as a component can be used in multiple groups without re-registration.
  integration-service owns the new Group API and the eventual decommissioning
  of the old Application API.

The implementation will be phased, starting with the core build team and
gradually migrating services and users over time, with the final goal of
decommissioning the old model once the migration is complete.

### Example of new Component CR spec

```
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  name: example
  namespace: example

spec:
  actions:
    trigger-push-build: Test
    trigger-push-builds:
      - Test
      - Different pipeline

    create-pipeline-configuration-pr:
      all-versions: true
      version: some-verision
      versions:
        - version-name1
        - version-name2

  skip-offboarding-pr: true

  containerImage: quay.io/org/tenant/component

  repository-settings:
    comment-strategy: disable_all

  default-build-pipeline:
    pull-and-push:
      pipelinespec-from-bundle:
        name: docker-build-oci-ta
        bundle: latest

      pipelineref-by-name: custom-pipeline

      pipelineref-by-git-resolver:
        url: https://github.com/custom-pipelines/pipelines.git
        revision: main
        pathInRepo: pipeline/push.yaml

    push:
      pipelinespec-from-bundle:
        name: docker-build-oci-ta
        bundle: latest
      pipelineref-by-name: custom-pipeline
      pipelineref-by-git-resolver:
        url: https://github.com/custom-pipelines/pipelines.git
        revision: main
        pathInRepo: pipeline/push.yaml

    pull:
      pipelinespec-from-bundle:
        name: docker-build-oci-ta
        bundle: latest
      pipelineref-by-name: custom-pipeline
      pipelineref-by-git-resolver:
        url: https://github.com/custom-pipelines/pipelines.git
        revision: main
        pathInRepo: pipeline/pull.yaml

  source:
    url: https://github.com/user/repo

    dockerfileUri: Dockerfile

    versions:
      - name: Version 1.0
        revision: ver-1.0

      - name: Test
        revision: test
        context: ./test
        dockerfileUri: test.Dockerfile
        skip-builds: true

      - name: Different pipeline
        revision: different_branch
        build-pipeline:
          pull-and-push:
            pipelinespec-from-bundle:
              name: pipeline_name_in_bundle_image
              bundle: specific_bundle_image

status:
  message: Spec.ContainerImage is not set / GitHub App is not installed
  pac-repository: repository-cr-name
  containerImage: quay.io/org/tenant/component
  repository-settings:
    comment-strategy: disable_all

  versions:
    - name: Version 1.0
      onboarding-status: succeeded
      configuration-merge-url: https://github.com/user/repo/pull/1
      onboarding-time: 29 May 2024 15:11:16 UTC
      revision: ver-1.0
      skip-builds: false

    - name: Test
      onboarding-status: succeeded
      configuration-merge-url: https://github.com/user/repo/pull/1
      onboarding-time: 29 May 2024 15:11:16 UTC
      revision: test
      skip-builds: true

    - name: Different pipeline
      onboarding-status: failed
      revision: different_branch
      message: pipeline for Different pipeline branch doesn't exist
      skip-builds: false

```

### Component CR Spec Field Reference

* **apiVersion**
  * Type: string
  * Required field
  * Value: `appstudio.redhat.com/v1alpha1`.

* **kind**
  * Type: string
  * Required field
  * Value: `Component`.

* **metadata.name**
  * Type: string
  * Required field

* **metadata.namespace**
  * Type: string
  * Required field

* **spec**
  * Type: object
  * Required field

* **spec.actions**
  * Type: object
  * Optional field
  * Specific actions that will be processed by the controller and then removed from `spec.actions`.

* **spec.actions.trigger-push-build**
  * Type: string
  * Optional field
  * Specify name of component version to restart the push build for.
  * Can be specified together with trigger-push-builds and any duplicates will be removed.

* **spec.actions.trigger-push-builds**
  * Type: array of strings
  * Optional field
  * Specify names of component versions to restart the push build for.
  * Can be specified together with trigger-push-build and any duplicates will be removed.

* **spec.actions.create-pipeline-configuration-pr**
  * Type: object
  * Optional field
  * Send a PR with build pipeline configuration proposal for Component version(s).
  * If not set, version onboarding will be done without pipeline configuration PR.
  * Could be used after onboarding to create / renew build pipeline definition.

* **spec.actions.create-pipeline-configuration-pr.all-versions**
  * Type: boolean
  * Optional field
  * When specified it will send a PR with build pipeline configuration proposal for all Component versions.
  * Has precedence over `spec.actions.create-pipeline-configuration-pr.version` and `spec.actions.create-pipeline-configuration-pr.versions`.

* **spec.actions.create-pipeline-configuration-pr.version**
  * Type: string
  * Optional field
  * When specified it will send a PR with build pipeline configuration proposal for the Component version.
  * Can be specified together with `spec.actions.create-pipeline-configuration-pr.versions` and any duplicates will be removed.

* **spec.actions.create-pipeline-configuration-pr.versions**
  * Type: array of strings
  * Optional field
  * When specified it will send a PR with build pipeline configuration proposal for Component versions.
  * Can be specified together with `spec.actions.create-pipeline-configuration-pr.version` and any duplicates will be removed.

* **spec.skip-offboarding-pr**
  * Type: boolean
  * Optional field, default: false
  * When `true`, during offboarding, a cleaning PR won't be created.

* **spec.containerImage**
  * Type: string
  * Optional field
  * Will be set by controller when ImageRepository for a specific component is created, or is explicitly specified with a custom repository without tag.

* **spec.repository-settings**
  * Type: object
  * Optional field
  * Used for setting additional settings for the Repository CR.

* **spec.repository-settings.comment-strategy**
  * Type: string
  * Optional field
  * When specified, will set value of `comment_strategy` in the Repository CR.

* **spec.default-build-pipeline**
  * Type: object
  * Optional field
  * Used only when sending a PR with build pipeline configuration was requested via `spec.actions.create-pipeline-configuration-pr`.
  * Pipeline used for all versions, unless explicitly specified for a specific version.
  * Pipelines should also allow custom pipelines based on (by name & git resolver) https://issues.redhat.com/browse/KONFLUX-10117.
  * Can specify either only pull-and-push, or both push & pull.
  * When omitted it has to be specified in all versions.

* **spec.default-build-pipeline.pull-and-push**
  * Type: object
  * Optional field
  * Pipeline used for pull and push pipeline runs.
  * Can specify just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver.

* **spec.default-build-pipeline.pull-and-push.pipelinespec-from-bundle**
  * Type: object
  * Optional field
  * Will be used to fetch bundle and fill out PipelineSpec in pipeline runs.
  * The pipeline name is based on build-pipeline-config CM in build-service NS.
  * When 'latest' bundle is specified, bundle image will be used from CM.
  * When bundle is specified to specific image bundle, then that one will be used and pipeline name will be used to fetch pipeline from that bundle.
  * This is how the specified pipeline works now.
  * build-service does validation if wrong name or bundle is specified.

* **spec.default-build-pipeline.pull-and-push.pipelinespec-from-bundle.name**
  * Type: string
  * Required field

* **spec.default-build-pipeline.pull-and-push.pipelinespec-from-bundle.bundle**
  * Type: string
  * Required field

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-name**
  * Type: string
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline.
  * Such pipeline definition has to be in .tekton.
  * build-service doesn't do any validation about correct pipeline name.

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-git-resolver**
  * Type: object
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline via git resolver, specifying repository with a pipeline definition.
  * build-service doesn't do any validation about correct url, revision, pathInRepo.

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-git-resolver.url**
  * Type: string
  * Required field

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-git-resolver.revision**
  * Type: string
  * Required field

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-git-resolver.pathInRepo**
  * Type: string
  * Required field

* **spec.default-build-pipeline.push**
  * Type: object
  * Optional field
  * Pipeline used for push pipeline run.
  * Can specify just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver.

* **spec.default-build-pipeline.push.pipelinespec-from-bundle**
  * Type: object
  * Optional field
  * Will be used to fetch bundle and fill out PipelineSpec in pipeline runs.
  * The pipeline name is based on build-pipeline-config CM in build-service NS.
  * When 'latest' bundle is specified, bundle image will be used from CM.
  * When bundle is specified to specific image bundle, then that one will be used and pipeline name will be used to fetch pipeline from that bundle.
  * This is how the specified pipeline works now.
  * build-service does validation if wrong name or bundle is specified.

* **spec.default-build-pipeline.push.pipelinespec-from-bundle.name**
  * Type: string
  * Required field

* **spec.default-build-pipeline.push.pipelinespec-from-bundle.bundle**
  * Type: string
  * Required field

* **spec.default-build-pipeline.push.pipelineref-by-name**
  * Type: string
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline.
  * Such pipeline definition has to be in .tekton.
  * build-service doesn't do any validation about correct pipeline name.

* **spec.default-build-pipeline.push.pipelineref-by-git-resolver**
  * Type: object
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline via git resolver, specifying repository with a pipeline definition.
  * build-service doesn't do any validation about correct url, revision, pathInRepo.

* **spec.default-build-pipeline.push.pipelineref-by-git-resolver.url**
  * Type: string
  * Required field

* **spec.default-build-pipeline.push.pipelineref-by-git-resolver.revision**
  * Type: string
  * Required field

* **spec.default-build-pipeline.push.pipelineref-by-git-resolver.pathInRepo**
  * Type: string
  * Required field

* **spec.default-build-pipeline.pull**
  * Type: object
  * Optional field
  * Pipeline used for pull pipeline run.
  * Can specify just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver.

* **spec.default-build-pipeline.pull.pipelinespec-from-bundle**
  * Type: object
  * Optional field
  * Will be used to fetch bundle and fill out PipelineSpec in pipeline runs.
  * The pipeline name is based on build-pipeline-config CM in build-service NS.
  * When 'latest' bundle is specified, bundle image will be used from CM.
  * When bundle is specified to specific image bundle, then that one will be used and pipeline name will be used to fetch pipeline from that bundle.
  * This is how the specified pipeline works now.
  * build-service does validation if wrong name or bundle is specified.

* **spec.default-build-pipeline.pull.pipelinespec-from-bundle.name**
  * Type: string
  * Required field

* **spec.default-build-pipeline.pull.pipelinespec-from-bundle.bundle**
  * Type: string
  * Required field

* **spec.default-build-pipeline.pull.pipelineref-by-name**
  * Type: string
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline.
  * Such pipeline definition has to be in .tekton.
  * build-service doesn't do any validation about correct pipeline name.

* **spec.default-build-pipeline.pull.pipelineref-by-git-resolver**
  * Type: object
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline via git resolver, specifying repository with a pipeline definition.
  * build-service doesn't do any validation about correct url, revision, pathInRepo.

* **spec.default-build-pipeline.pull.pipelineref-by-git-resolver.url**
  * Type: string
  * Required field

* **spec.default-build-pipeline.pull.pipelineref-by-git-resolver.revision**
  * Type: string
  * Required field

* **spec.default-build-pipeline.pull.pipelineref-by-git-resolver.pathInRepo**
  * Type: string
  * Required field

* **spec.source**
  * Type: object
  * Required field

* **spec.source.url**
  * Type: string
  * Required field
  * Git repository url.
  * Modifications prevented by a webhook.

* **spec.source.dockerfileUri**
  * Type: string
  * Optional field, default: Dockerfile
  * Dockerfile path for all versions, unless explicitly specified for a version.
  * Used only when sending a PR with build pipeline configuration was requested via `spec.actions.create-pipeline-configuration-pr`.

* **spec.source.versions**
  * Type: array of objects
  * Required field (but can be an empty array, in that case it is just empty shell of component)
  * List of all versions.

* **spec.source.versions[].name**
  * Type: string
  * Required field
  * User defined name for a version.

* **spec.source.versions[].revision**
  * Type: string
  * Required field (we won't support the default branch anymore)
  * Branch name for the version.
  * Modifications prevented by a webhook.

* **spec.source.versions[].context**
  * Type: string
  * Optional field, default: "" (empty string)
  * Context directory for the version.
  * Used only when sending a PR with build pipeline configuration was requested via `spec.actions.create-pipeline-configuration-pr`.

* **spec.source.versions[].dockerfileUri**
  * Type: string
  * Optional field, default: Dockerfile
  * Dockerfile path for the version.
  * Used only when sending a PR with build pipeline configuration was requested via `spec.actions.create-pipeline-configuration-pr`.

* **spec.source.versions[].skip-builds**
  * Type: boolean
  * Optional field, default: false
  * When true it will disable builds for a revision.
  * Reacts to changes and updates Repository CR and then updates it in per version status.

* **spec.source.versions[].build-pipeline**
  * Type: object
  * Optional field
  * Used only when sending a PR with build pipeline configuration was requested via `spec.actions.create-pipeline-configuration-pr`.
  * Pipeline used for the version; when omitted, the default pipeline will be used from `spec.default-build-pipeline`.
  * Pipelines should also allow custom pipelines based on (by name & git resolver) https://issues.redhat.com/browse/KONFLUX-10117.
  * Can specify either only pull-and-push, or both push & pull.

* **spec.source.versions[].build-pipeline.pull-and-push**
  * Type: object
  * Optional field
  * Pipeline used for pull and push pipeline runs.
  * Can specify just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver.

* **spec.source.versions[].build-pipeline.pull-and-push.pipelinespec-from-bundle**
  * Type: object
  * Optional field
  * Will be used to fetch bundle and fill out PipelineSpec in pipeline runs.
  * The pipeline name is based on build-pipeline-config CM in build-service NS.
  * When 'latest' bundle is specified, bundle image will be used from CM.
  * When bundle is specified to specific image bundle, then that one will be used and pipeline name will be used to fetch pipeline from that bundle.
  * This is how the specified pipeline works now.
  * build-service does validation if wrong name or bundle is specified.

* **spec.source.versions[].build-pipeline.pull-and-push.pipelinespec-from-bundle.name**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.pull-and-push.pipelinespec-from-bundle.bundle**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-name**
  * Type: string
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline.
  * Such pipeline definition has to be in .tekton.
  * build-service doesn't do any validation about correct pipeline name.

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-git-resolver**
  * Type: object
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline via git resolver, specifying repository with a pipeline definition.
  * build-service doesn't do any validation about correct url, revision, pathInRepo.

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-git-resolver.url**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-git-resolver.revision**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-git-resolver.pathInRepo**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.push**
  * Type: object
  * Optional field
  * Pipeline used for push pipeline run.
  * Can specify just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver.

* **spec.source.versions[].build-pipeline.push.pipelinespec-from-bundle**
  * Type: object
  * Optional field
  * Will be used to fetch bundle and fill out PipelineSpec in pipeline runs.
  * The pipeline name is based on build-pipeline-config CM in build-service NS.
  * When 'latest' bundle is specified, bundle image will be used from CM.
  * When bundle is specified to specific image bundle, then that one will be used and pipeline name will be used to fetch pipeline from that bundle.
  * This is how the specified pipeline works now.
  * build-service does validation if wrong name or bundle is specified.

* **spec.source.versions[].build-pipeline.push.pipelinespec-from-bundle.name**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.push.pipelinespec-from-bundle.bundle**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.push.pipelineref-by-name**
  * Type: string
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline.
  * Such pipeline definition has to be in .tekton.
  * build-service doesn't do any validation about correct pipeline name.

* **spec.source.versions[].build-pipeline.push.pipelineref-by-git-resolver**
  * Type: object
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline via git resolver, specifying repository with a pipeline definition.
  * build-service doesn't do any validation about correct url, revision, pathInRepo.

* **spec.source.versions[].build-pipeline.push.pipelineref-by-git-resolver.url**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.push.pipelineref-by-git-resolver.revision**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.push.pipelineref-by-git-resolver.pathInRepo**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.pull**
  * Type: object
  * Optional field
  * Pipeline used for pull pipeline run.
  * Can specify just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver.

* **spec.source.versions[].build-pipeline.pull.pipelinespec-from-bundle**
  * Type: object
  * Optional field
  * Will be used to fetch bundle and fill out PipelineSpec in pipeline runs.
  * The pipeline name is based on build-pipeline-config CM in build-service NS.
  * When 'latest' bundle is specified, bundle image will be used from CM.
  * When bundle is specified to specific image bundle, then that one will be used and pipeline name will be used to fetch pipeline from that bundle.
  * This is how the specified pipeline works now.
  * build-service does validation if wrong name or bundle is specified.

* **spec.source.versions[].build-pipeline.pull.pipelinespec-from-bundle.name**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.pull.pipelinespec-from-bundle.bundle**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.pull.pipelineref-by-name**
  * Type: string
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline.
  * Such pipeline definition has to be in .tekton.
  * build-service doesn't do any validation about correct pipeline name.

* **spec.source.versions[].build-pipeline.pull.pipelineref-by-git-resolver**
  * Type: object
  * Optional field
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline via git resolver, specifying repository with a pipeline definition.
  * build-service doesn't do any validation about correct url, revision, pathInRepo.

* **spec.source.versions[].build-pipeline.pull.pipelineref-by-git-resolver.url**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.pull.pipelineref-by-git-resolver.revision**
  * Type: string
  * Required field

* **spec.source.versions[].build-pipeline.pull.pipelineref-by-git-resolver.pathInRepo**
  * Type: string
  * Required field

* **status**
  * Type: object
  * Optional field
  * Status will be updated by build-service after onboarding.
  * Status will also be updated upon certain changes in the `spec` after onboarding, like skip-builds.

* **status.message**
  * Type: string
  * Optional field
  * General error message, not specific to any version (those are in versions).

* **status.pac-repository**
  * Type: string
  * Optional field
  * Name of Repository CR for the component.

* **status.containerImage**
  * Type: string
  * Optional field
  * Updated only during onboarding.
  * If containerImage is modified after onboarding, just do nothing, not even add anything in status.message like we do now.

* **status.repository-settings**
  * Type: object
  * Optional field
  * Identifies which additional settings are used for the Repository CR.
  * Updated when repository-settings changes in the spec.

* **status.repository-settings.comment-strategy**
  * Type: string
  * Optional field
  * Identifies value of `comment_strategy` in the Repository CR.
  * Updated when comment-strategy changes in the spec.

* **status.versions**
  * Type: array of objects
  * Optional field
  * All versions which were processed by onboarding.
  * If version is removed from the spec, offboarding will remove it from the status.

* **status.versions[].name**
  * Type: string
  * Optional field
  * Name for the version.

* **status.versions[].onboarding-status**
  * Type: string
  * Optional field
  * Onboarding status will be either succeeded or failed (`disabled` won't be there because we will just remove specific version section).

* **status.versions[].configuration-merge-url**
  * Type: string
  * Optional field
  * Link with onboarding PR if requested by `spec.actions.create-pipeline-configuration-pr`.
  * Only present if onboarding was successful.

* **status.versions[].onboarding-time**
  * Type: string
  * Optional field
  * Timestamp for when onboarding happened.
  * Only present if onboarding was successful.

* **status.versions[].revision**
  * Type: string
  * Optional field
  * Branch name for the version.

* **status.versions[].skip-builds**
  * Type: boolean
  * Optional field
  * Identifies that builds for the versions are disabled.
  * Updated when skip-builds changes in the spec for the version.

* **status.versions[].message**
  * Type: string
  * Optional field
  * Version specific error message.

## Consequences

* Improved Reusability: Component branches can be easily reused across multiple
  component groups and release plans.
* Simplified Model: The new structure is more flexible and intuitive, reducing
  complexity for users.
* Clear Ownership: The Group and Component resources will be clearly associated
  by their controllers (integration-service and build-service respectively).
* Migration Effort: A significant effort is required to design, implement, and
  migrate all existing users and components to the new model.
* UI/UX Changes: The user interface and experience will need to be completely
  updated to reflect the new component group model.
* Documentation Updates: All existing documentation related to components and
  applications must be revised to reflect the new concepts and workflows.
* Partial decoupling: This should give us some progress towards decoupling, but
  the Snapshot resource will remain a common resource referenced by both
  integration service and release service.
* Nudging: The "nudging" feature will be moved to integration test pipeline (based on community meeting).

## Roadmap

The following is an ordered roadmap of
activities to move that forwards.

* The build team designs and implements a new component object with component versions.
* The build team updates the build service so it supports components with the versions.
* The build team updates the documentation to mention components with component versions.
* The UI team adds support for the new components with components into branches into the UI.
  * The old model stays the primary model for the UI. Users can switch to the UI for the new model by toggling options in the UI.
* The MintMaker team updates MintMaker so it provides dependency management for the new components.
* The feature owner announces the new model as a tech preview to the users.
* The integration team designs and implements a new group object.
* The integration team updates the Snapshot creation to also support creating snapshots from groups.
* The integration team updates the integration service so it supports integration testing for groups and group snapshots.
* The integration team updates documentation to mention groups.
* The UI team adds support for the groups into the UI.
  * Features *Status Reporting* and *Run Visualization* do not block changes to releases.
* The feature owner announces Groups to the users.
* The release team updates the release service so it supports releases of groups and group snapshots.
* The feature owner announces the ability to release group-based snapshots to the users.
* Konflux implores the users to start migrating to the new model.
* The UI team makes the new model the primary one for the Konflux UI, changes made should take into consideration the change required for gitops in order to avoid duplicated work.
* The old component/application model is decommissioned.
  * The build and integration teams automatically migrate existing users that are using the old model to the new one.
    * The build team is responsible for migration of the components.
    * The integration team is responsible for migration of the groups-applications.
  * The feature owner deletes the documentation connected to the old mode.
  * The UI team removes the support for the old model from the UI.
  * The build and integration teams  remove CDR connected to the old model from clusters.
  * Konflux teams responsible for the Konflux services and functionality remove support for the old mode.
