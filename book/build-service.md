# Build Service


## Overview

The Build Service is composed of controllers that create and configure build pipelines. The main input for the Build Service is a Component CR managed by the [Hybrid Application Service (HAS)](hybrid-application-service.md).

![](../diagrams/build-service/build-service.drawio.svg)

### Dependencies

The Build Service is dependent on the following services:
- [Pipeline Service](./pipeline-service.md)
  - Pipeline execution, Pipeline logging
- [Hybrid Application Service](./hybrid-application-service.md)
  - Provides Component CR with annotations and `.status.devfile` which is used for PipelineRun configuration.
- [Image Controller](./image-controller.md)
  - Generation of a container image repository and robot account for Component CR which is used by PipelineRun

## Controllers

The Build Service contains these controllers:
- Component Build Controller
  - Monitors Component CRs and creates PipelineRuns - directly or via [Pipelines As Code (PaC)](https://pipelinesascode.com) provided by Pipeline Service.
- PaC PipelineRun Pruner Controller
  - Deletes PipelineRuns managed by Pipelines As Code for Components that were deleted.
- Git Tekton Resources Renovater
  - Provides updates for the .tekton directory in the user repository which has been created by Component Build Controller in Custom Mode.

### Component Build Controller

Component Build Controller is managed by Component CR changes. It's using Component CR annotations and `.status.devfile` for selecting a mode and configuration of the PipelineRuns.

#### Modes

Component Build Controller is working in two modes:
- Default Mode
  - Mode where PipelineRuns are created **directly** by the Build Service.
- Custom Mode
  - Integrates with Pipelines As Code, the Component Build Controller creates PipelineRuns definitions in the user code repository.
  - The prerequisite is to have installed GitHub App which is used by the Build Service in the user's repository.

Default mode:
1. Wait until the component has `.status.devfile` set
1. Get data from `.status.devfile` and use them for creating PipelineRun
1. Set annotation on the component - `appstudio.openshift.io/component-initial-build: processed`

Delete annotation `appstudio.openshift.io/component-initial-build` on Component to retrigger PipelineRun in Default mode.

For the selection of Custom mode the Component CR must have set annotation `appstudio.openshift.io/pac-provision` to `request`.

Custom Mode:
1. Wait until the component has `.status.devfile` set
1. Get data from `.status.devfile`, use them for creating `.tekton` folder in the user's repository and create Repository CR so that Pipelines as Code is configured to monitor the user's repository.
1. Change the value of `appstudio.openshift.io/pac-provision` annotation to `done` in case the previous step was successful, in case of an issue the annotation is set to `error` and annotation `appstudio.openshift.io/pac-provision-error` with more details about the error is added.

#### PipelineRun selection

The Build Service owns [BuildPipelineSelector CRD](https://redhat-appstudio.github.io/architecture/ref/build-service.html#buildpipelineselector) which defines which PipelineRun to select for the Component CR. By default global BuildPipelineSelector `build-pipeline-selector` in `build-service` namespace is used. BuildPipelineSelector CR contains selectors, the first matching selector is used for the Component CR. The list of selectors can be extended by creating BuildPipelineSelector CR with the same name as the Application CR in the user's namespace. This will ensure that it is applied to Component CRs under the corresponding Application CR. The list of selectors can be also extended for the whole user namespace by creating BuildPipelineSelector CR named `build-pipeline-selector` in the user's namespace.

Selectors are processed in this order:
- BuildPipelineSelector CR with the same name as Application CR in the user's namespace
- BuildPipelineSelector CR named `build-pipeline-selector` in the user's namespace
- BuildPipelineSelector CR named `build-pipeline-selector` in `build-service` namespace

If there is no match then the default pipeline hardcoded in the Build Service is used.

Example of BuildPipelineSelector:
```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: BuildPipelineSelector
metadata:
  name: build-pipeline-selector
  namespace: my-tenant
spec:
  selectors:
  - name: my-component
    pipelineRef:
      resolver: bundles
      params:
      - name: bundle
        value: quay.io/my-user/my-bundle:v1.0
      - name: name
        value: my-bundle
      - name: kind
        value: pipeline
    pipelineParams:
    - name: test
      value: fbc
    when:
      language: java
      componentName: my-component
      projectType: springboot
  - name: Label section
    pipelineRef:
      resolver: bundles
      params:
      - name: bundle
        value: quay.io/my-user/my-bundle:v1.0
      - name: name
        value: labelled
      - name: kind
        value: pipeline
    when:
      labels:
        mylabel: test
  - name: Docker build
    pipelineRef:
      resolver: bundles
      params:
      - name: bundle
        value: quay.io/redhat-appstudio-tekton-catalog/pipeline-docker-build:3649b8ca452e7f97e016310fccdfb815e4c0aa7e
      - name: name
        value: docker-build
      - name: kind
        value: pipeline
    when:
      dockerfile: true
  - name: NodeJS
    pipelineRef:
      resolver: bundles
      params:
      - name: bundle
        value: quay.io/redhat-appstudio-tekton-catalog/pipeline-nodejs-builder:3649b8ca452e7f97e016310fccdfb815e4c0aa7e
      - name: name
        value: nodejs-builder
      - name: kind
        value: pipeline
    when:
      language: nodejs,node
  - name: Fallback
    pipelineRef:
      resolver: bundles
      params:
      - name: bundle
        value: quay.io/my-user/my-fallback:v1.0
      - name: name
        value: fallback
      - name: kind
        value: pipeline
```

In the example the first selector will match only when the component CR name is `my-component` and it's defined in the devfile or detected with `language: java` and `projectType: springboot` if all requests are matching then PipelineRun is generated based on `pipelineRef` and pipelineRun parameters are set to pipelineParams. If any of `when` condition does not match then it's checking the next selector. The `Fallback` sector does not contain `when` so it will be processed in case previous selectors do not match.

`when` element could contain:
- language
  - Name of language from devfile .metadata.language, multiple languages can be defined: `java,nodejs,node`
- componentName
  - Name of Component CR
- projectType
  - projectType from devfile .metadata.projectType, can contain multiple values separated by a comma.
- dockerfile
  - if the Docker file is defined in generated devfile. Boolean value.
- annotations
  - match by Component CR annotations, expects map.
- labels
  - match by Component CR labels, expects map.

There are a few parameters that are set in PipelineRun created by the Build Service:
- git-url - taken from Component CR's spec.source.gitSource.url
- revision - taken from Component CR's spec.source.gitSource.revision when it's defined, otherwise it's using the default branch of the git repository
- output-image - generated by the Build Service the image repository is taken from Component CR's.
  - for Default mode, the tag is `initial-build-$TIMESTAMP-$RANDOM_NUMBER"`
  - for Custom mode, the tag is `{{ revision }}` which is evaluated by Pipelines As Code to commit SHA.
- docker-file - path to Dockerfile, only used when dockerfile is detected in Component's devfile
- path-context - context path for docker build, only used when dockerfile is detected in Component's devfile
- skip-checks - set to 'true' when Component contains annotation `skip-initial-checks: true`. This parameter is handled in pipelines so that when it's set to 'true' then testing task are skipped.

### PaC PipelineRun Pruner Controller

In Default mode the PipelineRuns are connected to Component CR using OwnerRef, which handles the deletion of the PipelineRun CR when Component CR is deleted.

In Custom mode the PipelineRuns creation is handled by Pipelines as Code and there is no cleanup of the PipelineRuns when the Repository CR which manages the git repository is deleted.

The purpose of the PaC PipelineRun Pruner Controller is to remove the PipelineRun CRs created for Component CR which is being deleted.

### Git Tekton Resources Renovater

In Custom mode the PipelineRun definition is created in the user's git repository under `.tekton` folder, this file is generated by Component Build Controller during Component CR creation. Git Tekton Resources Renovater is taking care of updating content of `.tekton` folder during the lifetime of the Component CR.

Git Tekton Resources Renovater triggers the creation of Job CRs when BuildPipelineSelector `build-pipeline-selector` in `build-service` namespace is updated.

Workflow:
1. Get repositories installed for the GitHub Application matching to Components CRs and get tokens to access them.
1. Split the workload into multiple jobs where each job:
    - Runs [renovate](https://www.mend.io/free-developer-tools/renovate/) for 20 GitHub users/organizations.

Renovate config is scoped only to `.tekton` folder.

When a new version of the task bundle or pipeline bundle is detected then a new pull-request is created in the user repository.
