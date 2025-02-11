# 43. Creating Artifacts from Snapshots for testing and release

Date: 2024-10-21

## Status

Proposed

## Authors

- Krunoslav Pavic
- Andrew McNamara

## Context

This ADR aims to cover the proposed functionality for creating additional Artifacts as part of the Konflux build/test/release process.
These artifacts would vary in type and would cover use cases where either the single built image or entire sets of images
from the user's application are needed to generate one or more artifacts.

Some limitations with our current approach that can be mitigated with this ADR:
* The ability to produce multiple artifacts with a single PipelineRun
* Reduced need for in-PR nudging (one of the common use cases for this is the operator bundle builds as mentioned below)


## Use Cases in Detail

* A team produces operands and operators. When integration service creates a Snapshot, it uses a constructor that
  actually builds a bundle. When releasing, the team releases that single bundle artifact. That constructor also has an extract
  operation to list all related images that are referenced, and that extraction generates the list for release service to operate on
* A team produces a set of images with ko. The build task generates/pushes all images with ko and then produces a "build artifact"
  OCI manifest which includes an immutable reference to each of the ko-built artifacts. When integration service creates a Snapshot,
  it uses a constructor that doesn't need to create a new artifact. When releasing, the team releases that single artifact.
  The constructor also has an extract operation to list all the ko-built artifacts and that extraction generates the list for release service to operate on.
* A team produces a set of images that are just a group of artifacts that should be released together.
  The artifacts are built via separate PipelineRuns. When integration service creates a Snapshot, it uses a constructor
  that saves the Snapshot CR as an OCI blob. When releasing, the team releases that single artifact.
  The constructor also has an extract operation to list all artifacts that were in the Snapshot and that extraction
  generates the list for release service to operate on.


## Decision

A new API will be introduced which instructs the Integration service to create a Tekton pipeline which will generate the
artifact.
Once built, the artifact reference will be added to the Snapshot's metadata so it can be discovered during testing or release process.
Additionally, the integration service will wait for the artifact constructor to finish before starting the integration testing pipelines
in order to enable users to run tests using the new artifacts.

### The ArtifactConstructor API

The proposal here is to introduce the new ArtifactConstructor API which will define Tekton pipelines that will generate individual artifacts.
These pipelines would be executed after a Snapshot is generated and before the integration test pipelines start.

When each artifact generation pipelineRun is completed, the reference to the artifact is extracted and added to the original Snapshot.
After that, the integration testing pipelines castart, and since the artifacts are referenced by the Snapshot,
it is possible to fetch them and run tests on them.

```yaml
apiVersion: appstudio.redhat.com/v2alpha1
kind: ArtifactConstructor
metadata:
    name: example--artifact-constructor
spec:
    selectors:
        - expression: ‘metadata.labels["konflux-ci.dev/application"] == "integration-service" && metadata.annotations["test.pac.appstudio.openshift.io/event-type"] == "pull_request"’
          description: “Selects only PR Snapshots associated with integration-service”
    params:
      - name: source
        value: https://github.com/konflux-ci/integration-service
    resolverRef:
      resolver: git
      params:
        - name: url
          value: https://github.com/konflux-ci/integration-examples
        - name: revision
          value: main
        - name: pathInRepo
          value: pipelines/bundle_generator_pipeline.yaml
    extractors:
      - ref: 'status.results.filter(result,result.name == "IMAGE_URL")[0].value'
        name: ‘metadata.labels["appstudio.openshift.io/component"]’

```

Don't take the fields literally. The details will likely change after the ADR has settled. It is
here for illustration purposes.

The `selector` field will be used to identify resources that should trigger the construction of new Artifacts. This will be done using CEL expressions.

The `resolverRef` resource will be used to define the Tekton pipeline definition which can be used to run the artifact pipelineRun.

The `extractor` resource will use CEL expressions to extract the individual field values from the artifact pipelineRun.
The individual artifacts are expected to use a reference that can be used to fetch it, like an image pullSpec or similar URL.
Since the `extractor` resource is a list, it can take multiple extractor entries if the artifact pipeline is expected to provide multiple artifacts.
Each extracted resource will be added to the Snapshot's metadata.

## Consequences

- [integration-service] now executes additional Tekton pipelineRuns which are expected to generate artifacts which
  can then be associated with the Snapshot.
- [integration-service] waits for the artifact pipelineRuns to finish before starting the integration testing pipelines
  for a given Snapshot.
- this will have implications for the [release service] as it will further remove coupling around an Application and an Application Snapshot
- Potential decrease of a reliance on an Application, which will have implications on [build-service] and the Konflux UI
