# Integration Service


## Overview

The Integration Service is composed of controllers that facilitate automated testing of content produced by the build pipelines. It is mainly responsible for integration testing capabilities.

The Integration service uses the pipeline, snapshot, and component controllers to watch for Component builds, trigger and manage testing Tekton Pipelines, and create releases based on the testing outcome(s).

### Goals

- The Integration service should be able to update one component image at a time in order to test and deploy individual component builds.
- The Integration service need to be able to test a specific set of images and record the results of integration testing.
- Given a specific set of images, Integration service should be able to tell if they passed application validation tests.
- The Integration service should have a capability to automatically promote sets of passed images.
- To be SLSA compliant, Integration service should also be able to tell what version of the build and test pipelines were used to create each component image.

### High Level Workflow

- When a build pipeline completes, Integration service creates a Snapshot CR representing a new collection of components that should be tested together.
- When Integration Service sees a new Snapshot CR (created either by itself or by a user), it coordinates testing of that Snapshot.
- Integration Service tests and validates the application according to user-provided configuration. It does this by executing Tekton PipelineRuns based on user-defined Integration Test Scenarios.
- When all the required test Tekton PipelineRuns have passed and if any automatic ReleasePlans have been created by the user in the workspace, it will create a Release CR signalling intent to release the tested content, to be carried out by the [release-service](./release-service.md).

The diagram below shows the interaction of the integration service and other services.

![](../diagrams/integration-service/integration-service-data-flow.jpg)

### Dependencies

The [Integration Service](./integration-service.md) is dependent on the following services:
- [Pipeline Service](./pipeline-service.md)
  - Pipeline execution, Pipeline logging
- [Hybrid Application Service](./core/hybrid-application-service.md)
  - Validates the Application and Component CRs. Integration Service updates the pullspec reference on the Component CR when a snapshot is created for the built image.
- [Release Service](./release-service.md)
  - Provides the ReleasePlan that will be used to determine if integration-service should create a Release
- [Enterprise Contract Service](./enterprise-contract.md)
  - Provides facilities to validate whether content has passed the Enterprise Contract.


## Terminology

**Component Pipeline** - This is the test pipeline run for the Component of an Application that gets triggered by a completed Build pipeline.

**Composite Pipeline** - This is the pipeline run that runs if two or more Components have completed and passed their Component pipeline concurrently so that they should be tested together.

**Global Candidate List** - The list of all Component digest that is updated after snapshot is created for an image built by build pipelineRun. This can be retrieved from the Application to see what Components it is made of and then querying each of the Components `Status.LastPromotedImage`.

**Snapshot** -  The custom resource that contains the list of all Components of an Application with their Component Image digests. Once created, the list of Components with their images is immutable. The Integration service updates the status of the resource to reflect the testing outcome.

**IntegrationTestScenario** - The custom resource that describes separate PipelineRuns that are supposed to be run by the snapshot controller. The IntegrationTestScenarios can be marked as optional, in which case they will not be taken into account when determining if the Snapshot has passed testing. Any number of IntegrationTestScenarios can be set by the user and also the user can specify the contexts where they will be applied (Component or Composite stage - or both).

**SLSA** - [SLSA](http://slsa.dev/) is a new PSSC initiative. Current goal is to reach [SLSA](http://slsa.dev/) level 4 or above for all services.

## Outdated Terminology

**Prelim Pipeline** - This is the same as the Component pipeline. Going forward the Preliminary Pipeline will be referred as Component Pipeline.

**Final Pipeline** -  This is the same as the Composite Pipeline. Going forward the Final Pipeline will be referred as Composite Pipeline.

## Resources
Below are the list of CRs that the integration service is responsible for interacting and performing operations:

### CREATE

| Custom Resource | When? | Why? |
|---|---|---|
| Snapshot | Post Component build PipelineRun completes.  | Used as the source input for the test gate pipeline |
| PipelineRuns | Post Snapshot creation  | To test the Snapshot  |
| Release | Post PipelineRun if there is a ReleasePlan for the Application, if the auto-release flag is set on the ReleasePlan | To signal to the Release Service to automatically push the Snapshot to the Production Environment |

### READ

| Custom Resources | When? | Why? |
|---|---|---|
| Application & Component | Before creating the Snapshots | To know which ImageSpecs to use in the Snapshot |
| IntegrationTestScenario | Before creating the Component/Composite PipelineRun(s) | To get the information for the PipelineRun |
| ReleasePlan | Before creating the Release | To signal the Release Service for next environment promotion (prod) |

### UPDATE

| Custom Resource | When? | Why? |
|---|---|---|
| Snapshot | Post Test PipelineRun | To mark the snapshot validated so that it can be promoted to the next environment |
| Component | Post Build PipelineRun | To update the Component with the image spec, in order to update the global candidates list |

### WATCH

| Custom Resource | When? | Why? |
|---|---|---|
| PipelineRun | Post Build PipelineRun | Read the component and the output image to create the Snapshot and start the Preliminary PipelineRun |
| PipelineRun | Post Component PipelineRun | Check the result of all Component PipelineRuns and mark the linked Snapshot as it either passed all tests or failed them |
| PipelineRun | Post Composite PipelineRun | Check the result of all Composite PipelineRuns and mark the linked Snapshot as it either passed all tests or failed them |
| Snapshot | Upon Snapshot creation | Check the Snapshot details and start running Integration PipelineRuns for it |
| Snapshot | Upon Snapshot status being updated as passed all tests | Follow up on the global candidate list state to possibly create the Composite Snapshot. Otherwise check ReleasePlan and create a Release.|

### Pipeline

The test pipeline will consist of a single definition that could be executed as two logically distinct pipeline runs by the Integration Service. The logical pipeline runs are:

- Component pipeline run
- Composite pipeline run

The Component pipeline run is always triggered for each Component of an Application and is triggered by a completed build of a component.

The Composite pipeline run is only triggered when it has been determined by the Integration Service that two or more Components of an Application have been successfully built concurrently by their respective Component pipeline and need to be tested together.

### PipelineRun

The Integration Service will generate a PipelineRun that can reference the user provided tekton pipeline.

#### Pipeline Reference
The pipeline reference identifies the target Tekton Pipeline that the PipelineRun will run. An application team should be able to offer its Tekton bundle at a well-known place, according to the pipeline reference. The pipeline packaging will be retrieved when the IntegrationTestScenario is executed by the Integration service.

#### Annotations/Labels

Following the [annotation guidelines](https://docs.google.com/document/d/1gyXM3pkKFFfxHZnopBi_53vREFWhwA0pFUuIhopDuEo/edit#), the Integration Service sets the below annotations on PipelineRuns.
```
“pipelines.appstudio.openshift.io/type": "test",
"test.appstudio.openshift.io/test":      “<component|composite>”
“test.appstudio.openshift.io/scenario":  “<IntegrationTestScenario name>”
“test.appstudio.openshift.io/kind":      “<enterprise-contract|...>”
"appstudio.openshift.io/snapshot":       “<snapshot name>”
“appstudio.openshift.io/component":      “<component name>”
“appstudio.openshift.io/application":    “<Application name>”
```
The Integration service will copy the annotations and labels from the Build PipelineRun and append those to the Test PipelineRuns for traceability across the system per [Labels and Annotations for Konflux pipelines](https://docs.google.com/document/d/1fJq4LDakLfcAPvOOoxxZNWJ_cuQ1ew9jfBjWa-fEGLE/edit#) and [Konflux builds and tests PRs](https://docs.google.com/document/d/113XTplEWRM63aIzk7WwgLruUBu2O7xVy-Zd_U6yjYr0/edit#)

The "test.appstudio.openshift.io/optional" Label provides users an option whether the result of a pipelineRun created according to the IntegrationTestScenario will be taken into account when determining if the Snapshot has passed all required testing. In another word, the label is used to specify if an IntegrationTestScenario is allowed to fail. If the label is not defined in an IntegrationTestScenario, integration service will consider it as "false".
```
"test.appstudio.openshift.io/optional":	"false"|"true"
```
The label will be copied to the subsequent Test PipelineRuns.

The `test.appstudio.openshift.io/kind` annotation is an optional annotation that can be used to filter on the kinds of `IntegrationTestScenario`s. The first recognized kind is the `enterprise-contract`. It will be copied to the `PipelineRun`s resulting from the `IntegrationTestScenario`.

## Detailed Workflow
1. Watch for Build PipelineRuns of `type: build`
    - Extract  Component Name, Application Name, and Image from pipeline annotations
2. Query the Application
    - for each Component extract the `Status.LastPromotedImage`
3. Create a Snapshot
    - Populate the `spec.components` list with the component name and the `Status.LastPromotedImage` with information from Step 1 and 2, replacing the container image for the built component with the one from the build PipelineRun
    - If a component does not have a container image associated with it then the component will not be added to the snapshot
4. Update the Component's `Status.LastPromotedImage` field, which updates the Global Candidate List.
5. Create PipelineRuns for each IntegrationTestScenario
    - Fetch the IntegrationTestScenario for the application/component to get the Tekton reference information
    - Assign annotations of
        ```
        "test.appstudio.openshift.io/test":   component
        "test.appstudio.openshift.io/snapshot":   “<snapshot name>”
        “test.appstudio.openshift.io/component":   “<component name>”
        “test.appstudio.openshift.io/application":   “<Application name>”
        ```
    - Pass in the Snapshot json representation as a parameter
6. Watch the PipelineRun of `test: component` and `component: <component name>`
    - When all required PipelineRuns complete
        - Check if all the required PipelineRuns associated with the snapshot have passed successfully
        - If all required PipelineRuns passed, mark the Snapshot as validated by setting its status condition `HACBSTestsSucceeded` as true
        - If not all required PipelineRuns passed, mark the Snapshot as not validated by setting its status condition `HACBSTestsSucceeded` as false, end the Integration testing process
    - Note: Users are allowed to mark an Integration Test Scenario as optional. In this case results of testing are ignored for the optional scenario and don't block further processing of the Snapshot.
7. Query the Application and find all of its components
    - For each Component extract the `Status.LastPromotedImage`
8. Prepare a new Snapshot
    - Populate the `spec.components` list and the `Status.LastPromotedImage` with information from Step 5.
9. Compare new Snapshot from step 8 to step 3
    - If determined the same, proceed to step 10
    - If determined not the same, proceed to step 14
10. Query ReleasePlan `spec.application` for the specific application in question
    - Check the auto-release flag on the ReleasePlan too
    - If ReleasePlan for Application found proceed to step 12
    - If ReleasePlan for Application NOT found proceed to step 13
11. Create a Release with the `spec.ReleasPlan` and `spec.Snapshot`
12. Done - Repeat from Step 1 again
13. If not the same, repeat step 4
    - Assign the same annotations except
        Test: composite
        Snapshot: name from step 8
    - Pass in the Snapshot name as a parameter
14. Watch the PipelineRun of `test: composite` and `snapshot: <snapshot name>`
    - When PipelineRuns complete
        - If all PipelineRuns passed, mark the Snapshot as validated by setting its status condition HACBSTestsSucceeded as true
15. Repeat step 11-12

### Image extraction details

Integration service is getting specific information about the image that's being built by the RHTAP build pipeline by parsing the expected Tekton results for the pipeline. All of them are required to be present in order to correctly construct a Snapshot.

<ins>Results are following:</ins>
 - IMAGE_URL
    - Represents image repository where the built image was pushed. Used to construct the component image reference.
 - IMAGE_DIGEST
    - Digest of the image that was built. Used to construct the component image reference.
 - CHAINS-GIT_URL
    - Git url of the source repository. Added to the source section of the component within the Snapshot.
 - CHAINS-GIT_COMMIT
    - The precise commit SHA that was fetched by git-clone task. Added to the source section of the component within the Snapshot.

>All those results contributes to a snapshot preparation for a pipelinerun


## Appendix

- [Konflux Promotion & Environment API](https://docs.google.com/document/d/14LaXAmQEW73kIr3a6TvPswT-zSdBsuaaxLF77HJ3gX4/edit#)
- [Konflux builds and tests PRs](https://docs.google.com/document/d/113XTplEWRM63aIzk7WwgLruUBu2O7xVy-Zd_U6yjYr0/edit#)
- [Labels and Annotations for Konflux pipelines](https://docs.google.com/document/d/1fJq4LDakLfcAPvOOoxxZNWJ_cuQ1ew9jfBjWa-fEGLE/edit#)
- [Implementation design and rules for pipeline customization](https://docs.google.com/document/d/1PXkpFHKrnq1Sg1giTgeXdYzNVf7CTRgwowykr7YPM2I/edit#)


## References

Originally drafted in a [google document](https://docs.google.com/document/d/1ZggNV3wTcZBFkbMs49eeQUG3vdJJXDDH3fIvfjhVPS8/edit#)
