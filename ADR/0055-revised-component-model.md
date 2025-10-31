# 55. Revised Component Model

## Status

Proposed
[//]: # (One of: Proposed, Withdrawn, Deferred, Accepted, Implementable, Implemented, Replaced)

## References

* [Konflux Community Call, 2025-03-11](https://www.youtube.com/watch?v=IwNFRNjRC_Q)
* [Konflux Community Call, 2025-03-25](https://www.youtube.com/watch?v=VwzDbUH_vjU)

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

* **Component Branch**: A component can have one or more component branches,
  which are a combination of a component and a specific branch or tag. A single
  component branch can be referenced by multiple component groups.
  build-service owns the Component API going forwards and the spec changes
  for branches.
* **Component Group**: A component group can contain other component groups or
  component branches, forming a Directed Acyclic Graph (DAG) that represents
  the release structure. This allows for greater flexibility and reusability,
  as a component can be used in multiple groups without re-registration.
  integration-service owns the new Group API and the eventual decommissioning
  of the old Application API.

The implementation will be phased, starting with the core build team and
gradually migrating services and users over time, with the final goal of
decommissioning the old model once the migration is complete.

### Detail of new Component CR spec

```
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  name: example
  namespace: example

spec: # Required field
  # specific actions will be processed and then removed
  actions:
    # specify names of component versions to restart the push build for
    # both can be specified at same time, but eliminate duplicates
    trigger-push-build: Test
    trigger-push-builds:
      - Test
      - Different pipeline

    # Only for build pipeline configuration PR explicit creation,
    # otherwise if version exists in the .spec.source.versions
    # and status doesn't have it, do onboarding without PR.
    # When create-pipeline-configuration-pr is specified,
    # at least one of 'all_versions', 'version', 'versions' has to be specified.
    # 'all_versions' has precedence.
    # When both 'version' and 'versions' will be specified use all versions from them
    # but eliminate duplicates.
    create-pipeline-configuration-pr:
      # when specified it will do onboarding for all versions and also create PRs
      all-versions: true
      # will do onboarding only for specific versions and also create PRs
      # all_versions has precedence if 'version' or 'versions' specified
      version: some-verision
      versions:
        - version-name1
        - version-name2

  # when offboarding is performed, cleaning PR will be created based on this
  # optional, default: false
  skip-offboarding-pr: true

  # either will be set by IR, or explicitly specified with custom repo, without tag
  containerImage: quay.io/org/tenant/component

  # Pipeline used for all versions, unless explicitly specified in 'source' for specific version.
  # Optional. If missing here, it has to be specified in all versions, BUT only if explicit onboarding is required, otherwise neither has to be specified.
  # pipelines should allow also custom pipelines based on (by name & git resolver) https://issues.redhat.com/browse/KONFLUX-10117
  # can have specified ONLY either pull-and-push, or both push & pull
  default-build-pipeline: used only for explicit onboarding
    # can have specified just one of:  pipelinespec-from-bundle,
    # pipelineref-by-name, pipelineref-by-git-resolver
    pull-and-push:
      # will be used to fetch bundle and fill out PipelineSpec in pipeline runs
      # name the pipeline is based on build-pipeline-config CM in build-service NS
      # when 'latest' bundle is specified, bundle image will be used from CM
      # when bundle is specified to specific image bundle, then that one will be used
      # and pipeline name will be used to fetch pipeline from that bundle
      # this is the same how specified pipeline works now
      # build service does validation if wrong name or bundle is specified
      pipelinespec-from-bundle:
        name: docker-build-oci-ta
        bundle: latest

      # will be used to fill out PipelineRef in pipeline runs to user specific pipeline
      # such pipeline definition has to be in .tekton
      # build service doesn't do any validation about correct pipeline name
      pipelineref-by-name: custom-pipeline

      # will be used to fill out PipelineRef in pipeline runs to user specific pipeline via git resolver, specifying repository with a pipeline definition
      # build service doesn't do any validation about correct url,revision,PathInRepo
      pipelineref-by-git-resolver:
        url: https://github.com/custom-pipelines/pipelines.git
        revision: main
        pathInRepo: pipeline/push.yaml

    # can have specified just one of:  pipelinespec-from-bundle,
    # pipelineref-by-name, pipelineref-by-git-resolver
    push:
      pipelinespec-from-bundle:
        name: docker-build-oci-ta
        bundle: latest
      pipelineref-by-name: custom-pipeline
      pipelineref-by-git-resolver:
        url: https://github.com/custom-pipelines/pipelines.git
        revision: main
        pathInRepo: pipeline/push.yaml

    # can have specified just one of:  pipelinespec-from-bundle,
    # pipelineref-by-name, pipelineref-by-git-resolver
    pull:
      pipelinespec-from-bundle:
        name: docker-build-oci-ta
        bundle: latest
      pipelineref-by-name: custom-pipeline
      pipelineref-by-git-resolver:
        url: https://github.com/custom-pipelines/pipelines.git
        revision: main
        pathInRepo: pipeline/pull.yaml

  source: Required field
    # git repo url
    url: https://github.com/user/repo # prevent modify webhook Required field

    # used for all branches unless explicitly specified per version
    # optional, default: Dockerfile
    dockerfileUri: Dockerfile used only for explicit onboarding

    # list of all versions
    versions: # Required field (but can have also nothing inside in that case it is just empty shell of component, and we have nothing to do)
      # context (default: "") used only for explicit onboarding
      # dockerfileUri (default: Dockerfile) used only for explicit onboarding
      # skip-builds (default: false)
      # build-nudges-ref optional
      # pipeline optional, unless 'default-pipeline' not specified, BUT only if explicit onboarding is required used only for explicit onboarding

      - name: Version 1.0 # user defined name for a version
        revision: ver-1.0 # mandatory (we won't support anymore default branch), protected by webhook

      - name: Test # user defined name for a version
        revision: test # mandatory (we won't support anymore default branch), protected by webhook
        context: ./test used only for explicit onboarding
        dockerfileUri: test.Dockerfile used only for explicit onboarding
        # when true it will disable builds for a revision
        # react on change and update Repository CR and than update it in per version status
        skip-builds: true
        # nudging refs, both component and branch are mandatory
        build-nudges-ref: # react on change and add to status in nudged component
          - component: component1 # mandatory
            version: test_some # mandatory
          - component: component2 # mandatory
            version: test_some2 # mandatory

      - name: Different pipeline # user defined name for a version
        revision: different_branch # mandatory (we won't support anymore default branch), protected by webhook
        # different pipeline used for the version than specified in default-build-pipeline
        build-pipeline: used only for explicit onboarding
          pull-and-push: # just example, can be also just pull & push
            pipelinespec-from-bundle: # just example, can be one of pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver
              name: pipeline_name_in_bundle_image
              bundle: specific_bundle_image

# status will be updated by build service after onboarding,
# or in some cases also if something changes in the spec, like:
# skip-builds, build-nudged-by (but that spec change might be also in different component)
status:
  # general error message, not specific to any version (those are in versions)
  message: Spec.ContainerImage is not set / GitHub App is not installed
  # name of Repository CR for the component
  pac-repository: repository-cr-name
  containerImage: quay.io/org/tenant/component # updated only during onboarding explicit/implicit, if containerImage is modified after onboarding, just do nothing, not even add anything in status.message like we do now

  # all versions which were processed by onboarding (implicit/explicit)
  # also if version is removed from the spec, offboarding will remove it from the status
  versions:
    - name: Version 1.0
      # onboarding status will be either succeeded or failed (disable won't be there because we will just remove specific version section)
      onboarding-status: succeeded
      configuration-merge-url: https://github.com/user/repo/pull/1 # only present if onboarding was successful
      onboarding-time: 29 May 2024 15:11:16 UTC # only present if onboarding was successful
      revision: ver-1.0
      skip-builds: false # updated when skip-builds changes in the spec for the version
      build-nudged-by: # set when other version/component specifies this version in build-nudges-ref
        - component: component3
          version: test_some3
        - component: component4
          version: test_some4

    - name: Test
      onboarding-status: succeeded
      configuration-merge-url: https://github.com/user/repo/pull/1 # only present if onboarding was successful
      onboarding-time: 29 May 2024 15:11:16 UTC # only present if onboarding was successful
      revision: test
      skip-builds: true # updated when skip-builds changes in the spec for the version
      build-nudges-ref: # updated when build-nudges-ref changes in the spec for the version
        - component: component1 # mandatory
          version: test_some # mandatory
        - component: component2 # mandatory
          version: test_some2 # mandatory

    - name: Different pipeline
      # error occurred during provisioning
      onboarding-status: failed
      revision: different_branch
      # version specific error message
      message: pipeline for Different pipeline branch doesn't exist
      skip-builds: false # updated when skip-builds changes in the spec for the version

```

### Component CR Spec Field Reference

* **apiVersion** (string)
  * Type: string
  * Value: `appstudio.redhat.com/v1alpha1`

* **kind** (string)
  * Type: string
  * Value: `Component`

* **metadata.name** (string)
  * Type: string
  * Required field

* **metadata.namespace** (string)
  * Type: string
  * Required field

* **spec** (object)
  * Type: object
  * Required field

* **spec.actions** (object)
  * Type: object
  * Specific actions will be processed and then removed

* **spec.actions.trigger-push-build** (string)
  * Type: string
  * Specify name of component version to restart the push build for
  * Can be specified at same time as trigger-push-builds, but eliminate duplicates

* **spec.actions.trigger-push-builds** (array)
  * Type: array of strings
  * Specify names of component versions to restart the push build for
  * Can be specified at same time as trigger-push-build, but eliminate duplicates

* **spec.actions.create-pipeline-configuration-pr** (object)
  * Type: object
  * Only for build pipeline configuration PR explicit creation, otherwise if version exists in .spec.source.versions and status doesn't have it, do onboarding without PR
  * When create-pipeline-configuration-pr is specified, at least one of 'all-versions', 'version', 'versions' has to be specified
  * 'all-versions' has precedence
  * When both 'version' and 'versions' are specified, use 'all-versions' from them but eliminate duplicates

* **spec.actions.create-pipeline-configuration-pr.all-versions** (boolean)
  * Type: boolean
  * When specified it will do onboarding for all versions and also create PRs

* **spec.actions.create-pipeline-configuration-pr.version** (string)
  * Type: string
  * Will do onboarding only for specific version and also create PR
  * all-versions has precedence if 'version' or 'versions' specified

* **spec.actions.create-pipeline-configuration-pr.versions** (array)
  * Type: array of strings
  * Will do onboarding only for specific versions and also create PRs
  * all-versions has precedence if 'version' or 'versions' specified

* **spec.skip-offboarding-pr** (boolean)
  * Type: boolean
  * When offboarding is performed, cleaning PR will be created based on this
  * Optional, default: false

* **spec.containerImage** (string)
  * Type: string
  * Either will be set by IR, or explicitly specified with custom repo, without tag

* **spec.default-build-pipeline** (object)
  * Type: object
  * Pipeline used for all versions, unless explicitly specified in 'source' for specific version
  * Optional. If missing here, it has to be specified in all versions, BUT only if explicit onboarding is required, otherwise neither has to be specified
  * Pipelines should allow also custom pipelines based on (by name & git resolver) https://issues.redhat.com/browse/KONFLUX-10117
  * Can have specified ONLY either pull-and-push, or both push & pull
  * Used only for explicit onboarding

* **spec.default-build-pipeline.pull-and-push** (object)
  * Type: object
  * Can have specified just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver

* **spec.default-build-pipeline.pull-and-push.pipelinespec-from-bundle** (object)
  * Type: object
  * Will be used to fetch bundle and fill out PipelineSpec in pipeline runs
  * Name the pipeline is based on build-pipeline-config CM in build-service NS
  * When 'latest' bundle is specified, bundle image will be used from CM
  * When bundle is specified to specific image bundle, then that one will be used and pipeline name will be used to fetch pipeline from that bundle
  * This is the same how specified pipeline works now
  * build-service does validation if wrong name or bundle is specified

* **spec.default-build-pipeline.pull-and-push.pipelinespec-from-bundle.name** (string)
  * Type: string

* **spec.default-build-pipeline.pull-and-push.pipelinespec-from-bundle.bundle** (string)
  * Type: string

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-name** (string)
  * Type: string
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline
  * Such pipeline definition has to be in .tekton
  * build-service doesn't do any validation about correct pipeline name

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-git-resolver** (object)
  * Type: object
  * Will be used to fill out PipelineRef in pipeline runs to user specific pipeline via git resolver, specifying repository with a pipeline definition
  * build-service doesn't do any validation about correct url, revision, pathInRepo

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-git-resolver.url** (string)
  * Type: string

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-git-resolver.revision** (string)
  * Type: string

* **spec.default-build-pipeline.pull-and-push.pipelineref-by-git-resolver.pathInRepo** (string)
  * Type: string

* **spec.default-build-pipeline.push** (object)
  * Type: object
  * Can have specified just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver

* **spec.default-build-pipeline.push.pipelinespec-from-bundle** (object)
  * Type: object

* **spec.default-build-pipeline.push.pipelinespec-from-bundle.name** (string)
  * Type: string

* **spec.default-build-pipeline.push.pipelinespec-from-bundle.bundle** (string)
  * Type: string

* **spec.default-build-pipeline.push.pipelineref-by-name** (string)
  * Type: string

* **spec.default-build-pipeline.push.pipelineref-by-git-resolver** (object)
  * Type: object

* **spec.default-build-pipeline.push.pipelineref-by-git-resolver.url** (string)
  * Type: string

* **spec.default-build-pipeline.push.pipelineref-by-git-resolver.revision** (string)
  * Type: string

* **spec.default-build-pipeline.push.pipelineref-by-git-resolver.pathInRepo** (string)
  * Type: string

* **spec.default-build-pipeline.pull** (object)
  * Type: object
  * Can have specified just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver

* **spec.default-build-pipeline.pull.pipelinespec-from-bundle** (object)
  * Type: object

* **spec.default-build-pipeline.pull.pipelinespec-from-bundle.name** (string)
  * Type: string

* **spec.default-build-pipeline.pull.pipelinespec-from-bundle.bundle** (string)
  * Type: string

* **spec.default-build-pipeline.pull.pipelineref-by-name** (string)
  * Type: string

* **spec.default-build-pipeline.pull.pipelineref-by-git-resolver** (object)
  * Type: object

* **spec.default-build-pipeline.pull.pipelineref-by-git-resolver.url** (string)
  * Type: string

* **spec.default-build-pipeline.pull.pipelineref-by-git-resolver.revision** (string)
  * Type: string

* **spec.default-build-pipeline.pull.pipelineref-by-git-resolver.pathInRepo** (string)
  * Type: string

* **spec.source** (object)
  * Type: object
  * Required field

* **spec.source.url** (string)
  * Type: string
  * Git repo url
  * Prevent modify webhook
  * Required field

* **spec.source.dockerfileUri** (string)
  * Type: string
  * Used for all branches unless explicitly specified per version
  * Optional, default: Dockerfile
  * Used only for explicit onboarding

* **spec.source.versions** (array)
  * Type: array of objects
  * List of all versions
  * Required field (but can have nothing inside, in that case it is just empty shell of component, and we have nothing to do)
  * Each version can have: context (default: ""), dockerfileUri (default: Dockerfile), skip-builds (default: false), build-nudges-ref (optional), pipeline (optional, unless 'default-build-pipeline' not specified, BUT only if explicit onboarding is required)
  * Used only for explicit onboarding

* **spec.source.versions[].name** (string)
  * Type: string
  * User defined name for a version

* **spec.source.versions[].revision** (string)
  * Type: string
  * Mandatory (we won't support anymore default branch)
  * Protected by webhook

* **spec.source.versions[].context** (string)
  * Type: string
  * Default: "" (empty string)
  * Used only for explicit onboarding

* **spec.source.versions[].dockerfileUri** (string)
  * Type: string
  * Default: Dockerfile
  * Used only for explicit onboarding

* **spec.source.versions[].skip-builds** (boolean)
  * Type: boolean
  * When true it will disable builds for a revision
  * React on change and update Repository CR and then update it in per version status

* **spec.source.versions[].build-nudges-ref** (array)
  * Type: array of objects
  * Nudging refs, both component and version are mandatory
  * React on change and add to status in nudged component

* **spec.source.versions[].build-nudges-ref[].component** (string)
  * Type: string
  * Mandatory

* **spec.source.versions[].build-nudges-ref[].version** (string)
  * Type: string
  * Mandatory

* **spec.source.versions[].build-pipeline** (object)
  * Type: object
  * Different pipeline used for the version than specified in default-build-pipeline
  * Used only for explicit onboarding

* **spec.source.versions[].build-pipeline.pull-and-push** (object)
  * Type: object
  * Can have specified just one of: pipelinespec-from-bundle, pipelineref-by-name, pipelineref-by-git-resolver

* **spec.source.versions[].build-pipeline.pull-and-push.pipelinespec-from-bundle** (object)
  * Type: object

* **spec.source.versions[].build-pipeline.pull-and-push.pipelinespec-from-bundle.name** (string)
  * Type: string

* **spec.source.versions[].build-pipeline.pull-and-push.pipelinespec-from-bundle.bundle** (string)
  * Type: string

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-name** (string)
  * Type: string

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-git-resolver** (object)
  * Type: object

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-git-resolver.url** (string)
  * Type: string

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-git-resolver.revision** (string)
  * Type: string

* **spec.source.versions[].build-pipeline.pull-and-push.pipelineref-by-git-resolver.pathInRepo** (string)
  * Type: string

* **spec.source.versions[].build-pipeline.push** (object)
  * Type: object

* **spec.source.versions[].build-pipeline.pull** (object)
  * Type: object

* **status** (object)
  * Type: object
  * Status will be updated by build-service after onboarding, or in some cases also if something changes in the spec, like: skip-builds, build-nudged-by (but that spec change might be also in different component)

* **status.message** (string)
  * Type: string
  * General error message, not specific to any version (those are in versions)

* **status.pac-repository** (string)
  * Type: string
  * Name of Repository CR for the component

* **status.containerImage** (string)
  * Type: string
  * Updated only during onboarding explicit/implicit
  * If containerImage is modified after onboarding, just do nothing, not even add anything in status.message like we do now

* **status.versions** (array)
  * Type: array of objects
  * All versions which were processed by onboarding (implicit/explicit)
  * If version is removed from the spec, offboarding will remove it from the status

* **status.versions[].name** (string)
  * Type: string

* **status.versions[].onboarding-status** (string)
  * Type: string
  * Onboarding status will be either succeeded or failed (disable won't be there because we will just remove specific version section)

* **status.versions[].configuration-merge-url** (string)
  * Type: string
  * Only present if onboarding was successful

* **status.versions[].onboarding-time** (string)
  * Type: string
  * Only present if onboarding was successful

* **status.versions[].revision** (string)
  * Type: string

* **status.versions[].skip-builds** (boolean)
  * Type: boolean
  * Updated when skip-builds changes in the spec for the version

* **status.versions[].build-nudged-by** (array)
  * Type: array of objects
  * Set when other version/component specifies this version in build-nudges-ref

* **status.versions[].build-nudged-by[].component** (string)
  * Type: string

* **status.versions[].build-nudged-by[].version** (string)
  * Type: string

* **status.versions[].build-nudges-ref** (array)
  * Type: array of objects
  * Updated when build-nudges-ref changes in the spec for the version

* **status.versions[].build-nudges-ref[].component** (string)
  * Type: string
  * Mandatory

* **status.versions[].build-nudges-ref[].version** (string)
  * Type: string
  * Mandatory

* **status.versions[].message** (string)
  * Type: string
  * Version specific error message

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
* Nudging: The "nudging" feature will need design changes. There is some idea
  to nudge the same component branch (by name) across components with ability
  to configure/override the behavior - but at this time not yet clearly
  defined.

## Roadmap

At the time of this writing, we have a low level of detail about the particular spec of the
new Component API and the Group API. The following is an ordered roadmap of
activities to move that forwards.

* The build team designs and implements a new component object with component branches.
* The build team updates the build service so it supports components with the branches.
* The build team updates the documentation to mention components with component branches.
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
* The UI team makes the new model the primary one for the Konflux UI.
* The old component/application model is decommissioned.
  * The build and integration teams automatically migrate existing users that are using the old model to the new one.
    * The build team is responsible for migration of the components.
    * The integration team is responsible for migration of the groups-applications.
  * The feature owner deletes the documentation connected to the old mode.
  * The UI team removes the support for the old model from the UI.
  * The build and integration teams  remove CDR connected to the old model from clusters.
  * Konflux teams responsible for the Konflux services and functionality remove support for the old mode.
