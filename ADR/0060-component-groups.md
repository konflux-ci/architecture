# 60. ComponentGroups

Date: 2025-11019

## Status

Proposed

## References
To be implemented alongside [ADR-0056](./0056-revised-component-model.md)

## Context

The existing application/component model in Konflux limits our ability to
support different types of workflows. New versions of a particular Component
must be onboarded as a separate Component. Additionally, each Component can
belong to exactly one application. Both of these issues hinder reusability and
introduce additional work for users.

Furthermore, ownership of the current APIs is unclear. They were originally
owned by HAS (which is now deprecated) and exhibit excessive coupling across
multiple services.

The current application/component model also limits the integration service's
ability to implement test ordering. Because the current model does not
facilitate having a central place from which to define the test ordering, both
the user experience and the performance of test ordering would be poor. We
must make sure that the new Custom Resources support test ordering.

Users also want testing on one snapshot to trigger the creation and testing of
other snapshots with different groups of components. This too must be
accounted for in the new model.

Finally, Snapshot creation is hard-coded into the integration service.
Snapshots are always created from the full set of Components in an Application.
This is limiting for users with more complex test and release use-cases who may
want to aggregate subsets of these sets of Components for testing. While this
problem is out of the scope of the current design, we need to consider it when
desigining the ComponentGroup spec.

## Decision

We have decided to _deprecate_ and eventually _remove_ the Application CR and
replace it with a new CR called ComponentGroup.

The ComponentGroup spec will contain a Component/Branch list which will tell
the integration service how to generate snapshots. This is the reverse of how
the relationship is defined in the old model, in which the Component CR
contained a `spec.Application` field naming its parent Application. Defining
the relationship "top-down" from parent to child will allow Components to
belong to multiple ComponentGroups. To enable test ordering the ComponentGroup
spec will also include an optional field called `testGraph` which will contain
a map thatdefines the order of IntegrationTestScenarios to be run. Each node in
the map will be the name of an IntegrationTestScenario and will contain a list
of other IntegrationTestScenarios. The scenario named in the node runs after
those in the list below it have completed. Each item in the list will contain
the name of another IntegrationTestScenario (required) and whether the parent
scenario should still be run if that scenario fails (optional). Finally, the
ComponentGroup spec will contain a list called `dependents` that contains the
names of other ComponentGroups for which snapshots should be created when a
snapshot is created for the parent ComponentGroup.

### Example of ComponentGroup Spec

```
apiVersion: konflux-ci.dev/v1alpha1
kind: ComponentGroup
metadata:
  name: sample-cg
  namespace: default
spec:
  components:
    - name: first-component
      componentVersion:
        name: "testing"
    - name: second-component
      componentVersion:
        name: v1
    - name: python-component
      componentVersion:
        name: "3.12.4"
  dependents:
    - child-cg
  testGraph:
    verify:
      - name: clamav-scan
      - name: dast-tests
        onFail: skip
      - name: operator-scorecard
    e2e-test:
      - name: clamav-scan
        onFail: run
    operator-scorecard:
      - name: operator-deployment
        onFail: skip
status:
  globalCandidatelist:
  - component: "first-component"
    lastPromotedImage: "quay.io/sampleorg/first-component@sha256:1b29..."
    lastPromotedCommit: "6a7c81802e785aa869f82301afe61f4e9775772b"
    lastPromotionTime: "2025-08-13T12:00:00Z"
  - component: "second-component"
    lastPromotedImage: quay.io/sampleorg/second-component@sha256:ae32...
    lastPromotedCommit: 1359836353b8e249f2fbceba47d82751d7dab902
    lastPromotionTime: "2025-08-13T05:13:25Z"
  - component: "python-component"
    lastPromotedImage: ''
    lastPromotedCommit: 2910be1733dae5e941b3779290c2a11f0e088782
    lastPromotionTime: "2025-08-13T19:24:43Z"
```

### ComponentGroup Field Reference

* **apiVersion**
  * Type: string
  * Required field
  * Value: `appstudio.redhat.com/v1alpha1`.

* **kind**
  * Type: string
  * Required field
  * Value: `ComponentGroup`.

* **metadata.name**
  * Type: string
  * Required field

* **metadata.namespace**
  * Type: string
  * Required field

* **spec**
  * Type: object
  * Required field

* **spec.components**
  * Type: list
  * Required field
  * Contains a list of Components and their branches for whom new builds should trigger the creation of Snapshots for the given ComponentGroup

* **spec.components[].componentVersion**
  * Type: object
  * Required field
  * Information for the specific branch from that Component's git repository that will trigger the creation of a snapshot for this ComponentGroup

* **spec.components[].componentVersion.name**
  * Type: string
  * Required field
  * The name of the version. Matches the `appstudio.openshift.io/version` annotation

* **spec.dependents**
  * Type: list
  * Optional field
  * A list of ComponentGroups for which a snapshot will be created when a snapshot is created for the ComponentGroup being defined in the current yaml

* **spec.testGraph**
  * Type: object
  * Optional field
  * The dependency graph for serialized tests

* **spec.testGraph.{}**
  * Type: list
  * Optional field
  * A list of dependents for each item in the testGraph

* **spec.testGraph.{}.name**
  * Type: string
  * Required field
  * The name of an IntegrationTestScenario that must complete before the parent scenario in the map can begin. 

* **spec.testGraph.{}.onFail**
  * Type: string
  * Optional field
  * Denotes whether a failure in the IntegrationTestScenario should prevent the next scenario from running. Can be set to `run` or `skip`. Defaults to `run`

* **status.globalCandidateList**
  * Type: map
  * Auto-populated field
  * Contains information about the most recently built and promoted versions of each image

* **status.componentStates.[].lastPromotedImage
  * Type: string
  * Auto-populated field
  * The name of the last image that was promoted to the GCL. Updated by the integration service and used to create snapshots. Cannot be updated by the user

* **status.componentStates.[].lastPromotedCommit
  * Type: string
  * Auto-populated field
  * The name of the last commit that was promoted to the GCL. Updated by the integration service and used to create snapshots. Cannot be updated by the user

* **status.componentStates.[].lastPromotionTime
  * Type: string
  * Auto-populated field
  * The timestamp of the build of lastPromotedCommit. Used by the integration service to prevent promotion regressions. Cannot be updated by the user

## Consequences

Once this is implemented developers will be able to more easily test different
configurations of their applications. Duplication of applications and
components will be significantly reduced. There will still be some duplication
due to the fact that a ComponentGroup cannot contain two alternative branches
for a single Component. This may be resolved in the future if Konflux supports
custom Snapshot creation logic.

Additionally, users can order their tests to ensure that expensive tests are
not being run unecessarily and that tests which rely on other tests are run
in the correct order. In addition to improving the user experience, this has
the potential to improve resource utilization on the clusters by running fewer
unecessary tests.

Migrating from Applications to ComponentGroups will further Konflux's goal of
decoupling its respective services. The ComponentGroup CR will be owned by the
Integration Service. ComponentGroups also do not rely on the Component CR in
any way; all information about Components that the the Integration Service
needs to create and test Snapshots will be found in the build PipelineRuns and
stored in the ComponentGroups themselves.

The release service will need to make minor changes in order to support the new
model. The Release CRD contains a `spec.application` field that names the
Application to which the Snapshot triggering the release belongs. The CRD will
need to be updated to support ComponentGroups or Applications.  A Release
should not have values for both fields. The ReleasePlan and
ReleasePlanAdmission CRD's should be updated accordingly.

## Future Enhancements

### Custom Snapshot Creation

Users have requested more control over the way in which snapshots are created.
They may want to be able to included resources that are not built in Konflux or
conditionally create snapshots containing a subset of the Components in the
ComponentGroup. This will not be part of the initial ComponentGroup
implementation. However, it may be included in the future. If snapshot creation
logic is defined in the integration service CRDs rather than the build pipeline
then the integration team will add a new field called `snapshotCreator` to the
ComponentGroup CRD. This will contain a reference to a task or pipeline which,
when run, will create a Snapshot for that ComponentGroupa

### Multiple Versions per Component

The current ComponentGroup spec only allows users to include a single
`componentVersion` per Component. The possibility of supporting multiple
versions was investigated but it would require support for custom Snapshot
creation.

In the example below, the integration service would have to decide which images
from Component `compA` to include in the Snapshot. The integration service
could include the image for version `v1` or `v2`, it could include both, or it
could create two separate snapshots - one with each version. Rather than making
a choice for the users, we are chosing to support this only once custom Snapshot
creation is implemented so that users can determine how these complex Snapshots
should be constructed.

```
components:
  - name: "compA"
    componentVersion:
      - name: "v1"
      - name: "v2"
  - name: "compB"
    componentVersion:
      - name: "v1"
```

There is a workaround for users who want multiple versions of the same
Component in their ComponentGroups. The integration service does not check
whether a Component has been added to the ComponentGroup multiple times. If a
user adds the same Component with different versions twice then both images
will be included in the Snapshot.

```
components:
  - name: "compA"
    componentVersion:
      name: "v1"
  - name: "compA"
    componentVersion:
      name: "v2"
  - name: "compB"
    componentVersion:
      name: "v1"
```
