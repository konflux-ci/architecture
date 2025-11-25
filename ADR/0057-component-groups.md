# 57. ComponentGroups

Date: 2025-11019

## Status

Proposed

## References
ADR-0056

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
ability to implement test serialization. Because the current model does not
facilitate having a central place from which to define the test ordering, both
the user experience and the performance of test serialization would be poor. We
must make sure that the new Custom Resources support serialization.

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

We have decided to do away with the Application CR and replace it with a new CR
called ComponentGroup. The ComponentGroup spec will contain a Component/Branch
list which will tell the integration service how to generate snapshots. This is
the reverse of how the relationship is defined in the old model and will allow
for Components that are part of multiple ComponentGroups. The spec will also
include a field called `snapshotCreator`. For now this field will be unused
but in the future it may be used to allow the user to define custom snapshot
creation logic. To enable test serialization the ComponentGroup spec will also
include an optional field called `testGraph` which will contain a map that
defines the order of IntegrationTestScenarios to be run. Each node in the map
will be the name of an IntegrationTestScenario and it will contain a list of
other IntegrationTestScenarios. The scenario named in the node runs after those
in the list below it have completed. Each item in the list will contain the
name of another IntegrationTestScenario (required) and whether the parent
scenario should still be run if that scenario fails (optional). Finally, the
ComponentGroup spec will contain a list called `dependents` that contains the
names of other ComponentGroups for which snapshots should be created when the
parent ComponentGroup has a snapshot created.

### Example of ComponentGroup Spec

```
apiVersion: appstudio.redhat.com/v1alpha1
kind: ComponentGroup
metadata:
  name: sample-cg
  namespace: default
spec:
  components:
    - name: first-component
      componentBranch:
        name: "testing"
        lastPromotedImage: "quay.io/sampleorg/first-component@sha256:1b29..."
        lastPromotedCommit: "6a7c81802e785aa869f82301afe61f4e9775772b"
        lastBuildTime: "2025-08-13T12:00:00Z"
    - name: second-component
      componentBranch:
        name: v1
        lastPromotedImage: quay.io/sampleorg/second-component@sha256:ae32...
        lastPromotedCommit: 1359836353b8e249f2fbceba47d82751d7dab902
        lastBuiLdTime: "2025-08-13T05:13:25Z"
    - name python-component
      componentBranch:
        name: "3.12.4"
        lastPromotedImage: ''
        lastPromotedCommit: ''
        lastBuildTime: ''
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
  snapshotCreator: ''
```

### ComponentGroup Field Reference

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

* **spec.components**
  * Type: list
  * Required field
  * Contains a list of Components and their branches for whom new builds should trigger the creation of Snapshots for the given ComponentGroup

* **spec.components[].componentBranch**
  * Type: object
  * Required field
  * Information for the specific branch from that Component's git repository that will trigger the creation of a snapshot for this ComponentGroup

* **spec.components[].componentBranch.name**
  * Type: string
  * Required field
  * The name of the branch

* **spec.components[].componentBranch.lastPromotedImage**
  * Type: string
  * Optional field
  * The name of the last image that was promoted to the GCL. Updated by the integration service and used to create snapshots. Cannot be updated by the user

* **spec.components[].componentBranch.lastBuiltCommit**
  * Type: string
  * Optional field
  * The name of the last commit that was promoted to the GCL. Updated by the integration service and used to create snapshots. Cannot be updated by the user

* **spec.components[].componentBranch.lastBuildTime**
  * Type: string
  * Optional field
  * The timestamp of the build of lastBuiltCommit. Used by the integration service to prevent promotion regressions. Updated by the integration service and used to create snapshots. Cannot be updated by the user

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

* **spec.snapshotCreator**
  * Type: object
  * Optional field
  * Placeholder field. In the future this will be the home of custom snapshot creation logic if the user wishes to define any.

## Consequences

Once this is implemented users will be able to more easily test different
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
