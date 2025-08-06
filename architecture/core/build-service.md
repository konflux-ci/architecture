# Build Service


## Overview

The Build Service is composed of controllers that create and configure build pipelines. The main input for the Build Service is a Component CR managed by the Konflux UI or created manually via `kubectl`.

![](../diagrams/build-service/build-service-diagram.svg)

### Dependencies

The Build Service is dependent on the following services:
- [Pipeline Service](./core/pipeline-service.md)
  - Pipeline execution, Pipeline logging
- [Image Controller](./add-ons/image-controller.md)
  - Generation of a container image repository and robot account for Component CR which is used by PipelineRun

## Controllers

The Build Service contains these controllers:
- Component Build Controller
  - Monitors Component CRs and creates PipelineRun definitions which will be used by [Pipelines As Code (PaC)](https://pipelinesascode.com) provided by Pipeline Service.
- PaC PipelineRun Pruner Controller
  - Deletes PipelineRuns for Components that were deleted.
- Component dependency update (nudging) controller
  - Monitors push PipelineRuns and based on set relationships runs renovate which updates
    SHA for image from PipelineRun in user's repository.

### Component Build Controller

Component Build Controller is managed by Component CR changes (creation or update).
It's using Component CR annotations and configuration of the PipelineRuns.

#### Modes
The prerequisite is to have installed GitHub App which is used by the Build Service in the user's repository, or have gitlab/github secret created for usage via webhook
([creating GitLab secrets](https://konflux.pages.redhat.com/docs/users/building/creating-secrets.html#gitlab-source-secret)).

Component Build Controller is working in multiple ways based on a request annotation `build.appstudio.openshift.io/request`:
- PaC provision, annotation value `configure-pac` (default when request annotation isn't set)
    - Sets up webhook if GitHub App isn't used.
    - Integrates with Pipelines As Code, creates PipelineRun definitions in the user code repository.
- PaC provision without MR creation, annotation value `configure-pac-no-mr`
    - Sets up webhook if GitHub App isn't used.
    - Integrates with Pipelines As Code, doesn't create PipelineRun definitions in the user code repository.
- PaC unprovision, annotation value `unconfigure-pac`
    - Removes webhook created during provisioning if GitHub App wasn't used.
    - Creates PR removing PipelineRuns definitions from the user code repository.
- Trigger PaC build, annotation value `trigger-pac-build`
    - Re-runs push pipeline runs (used for re-running failed push pipelines).

All those requests first wait for `.spec.containerImage` to be set, either manually or
by image-controller via
[ImageRepository CR](https://github.com/konflux-ci/architecture/blob/main/architecture/add-ons/image-controller.md#to-create-an-image-repository-for-a-component-apply-this-yaml-code).

Controller will also create component specific service account `build-pipeline-$COMPONENT_NAME`
used for build pipelines.

PaC provision:
1. Sets up webhook in the respository if GitHub App isn't used.
1. Creates or reuses Repository CR (Component CR is set as the owner).
1. Creates merge request in the user code repository with PipelineRun definitions.
1. Sets `build.appstudio.openshift.io/status` annotation with either error, or state `enabled` and merge request link.
1. Sets finalizer `pac.component.appstudio.openshift.io/finalizer`.
1. Removes `build.appstudio.openshift.io/request` annotation.

PaC provision without MR creation:
1. Sets up webhook in the repository if GitHub App isn't used.
1. Creates or reuses Repository CR (Component CR is set as the owner).
1. Doesn't create merge request in the user code repository with PipelineRun definitions, that is up to user.
1. Sets `build.appstudio.openshift.io/status` annotation with either error, or state `enabled`.
1. Sets finalizer `pac.component.appstudio.openshift.io/finalizer`.
1. Removes `build.appstudio.openshift.io/request` annotation.

PaC unprovision:
1. Removes finalizer `pac.component.appstudio.openshift.io/finalizer`.
1. Removes webhook from repository if GitHub App isn't used and the repository isn't used in another component.
1. Creates merge request in the user code repository removing PipelineRun definitions.
1. Sets `build.appstudio.openshift.io/status` annotation with either error, or state `disabled` and merge request link.
1. Removes `build.appstudio.openshift.io/request` annotation.

Trigger PaC build:
1. Triggers push pipeline via PaC incoming webhook, requires pipeline run name to be the same as it was named during provisioning `$COMPONENT_NAME-on-push`.
1. Sets `build.appstudio.openshift.io/status` annotation when error occures.
1. Removes `build.appstudio.openshift.io/request` annotation.

#### PipelineRun selection
Available and default pipelines are in the config map present on the cluster in controller's namespace
[build pipelines config](https://github.com/redhat-appstudio/infra-deployments/blob/main/components/build-service/base/build-pipeline-config/build-pipeline-config.yaml).

Build pipeline is selected based on `build.appstudio.openshift.io/pipeline` annotation,
when annotation is missing, annotation with default pipeline (based on config map) will be added.

Annotation value is json in string eg. `'{"name":"docker-build","bundle":"latest"}`.
Name is the name of the pipeline, and the bundle is either `latest` which will use the tag from config map
or specific tag for the bundle (used mostly for testing).

When specified pipeline doesn't exist in config map, it will result with error.

#### PipelineRun parameters
There are a few parameters that are set in PipelineRun created by the Build Service:
- git-url - set to `'{{source_url}}'` (evaluated by PaC to git url)
- revision - set to `'{{revision}}'` (evaluated by PaC to git commit SHA)
- output-image - taken from Component CR's `spec.containerImage`,
  for push pipeline appended tag `:{{revision}}`
  and for pull pipeline appended tag `:on-pr-{{revision}}`
- image-expires-after - set only for pull pipelines, value hadcoded in the code or from ENV variable `IMAGE_TAG_ON_PR_EXPIRATION`
- dockerfile - path to Dockerfile, taken from Component CR's `spec.source.git.dockerfileUrl`,
  default is `Dockerfile`
- path-context - path to subdirectory with context, when used taken from Component CR's `spec.source.git.context`

Additionally in [build pipelines config](https://github.com/redhat-appstudio/infra-deployments/blob/main/components/build-service/base/build-pipeline-config/build-pipeline-config.yaml)
pipelines may have specified `additional-params` which will be added with default values from pipeline itself.

### PaC PipelineRun Pruner Controller
The purpose of the PaC PipelineRun Pruner Controller is to remove the PipelineRun CRs created for Component CR which is being deleted.

It will remove all PipelineRuns based on `appstudio.openshift.io/component` label in PipelineRun.

### Component dependency update controller (nudging)
Monitors push PipelineRuns and based on defined relationships runs renovate,
which updates SHA for the image produced by PipelineRun in user's repository.

Relationships can be set in a Component CR via `spec.build-nudges-ref` (list of components to be nudged)

1. When PipelineRun is for a component which has set `spec.build-nudges-ref`, it will add finalizer to it
`build.appstudio.openshift.io/build-nudge-finalizer`.
1. It will wait for PipelineRun to successfully finish.
1. When PipelineRun successfully finishes, it will run renovate on user's repositories
   (for components specified in `spec.build-nudges-ref`),
   updating files with SHA of the image which was built by PipelineRun.
1. Renovate will create merge request in user's repository if it finds matches.
1. Removes `build.appstudio.openshift.io/build-nudge-finalizer` finalizer from PipelineRun.

Default files which will be nudged are: `.*Dockerfile.*, .*.yaml, .*Containerfile.*`.

Users can modify list via:
- `build.appstudio.openshift.io/build-nudge-files` annotation in push PipelineRun definition.
- [custom nudging config map](https://konflux.pages.redhat.com/docs/users/building/component-nudges.html#customizing-nudging-prs) with `fileMatch` (takes precedence over annotation).
