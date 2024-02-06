# 35. Artifact Streams

Date started: 2024-02-05

## Status

Proposed

Relates to:

<!-- ... a lot ... -->

Supercedes:

<!-- ... a lot ... -->

## Authors

- Andrew M

## Context

Since the beginning of AppStudio, we have had a dependency on the [Component] and [Application] model that
originated in the Hybrid Application Service. A [Component] is a single containerized artifact that has
information on how to build and deploy recorded in a linked [Devfile]. Multiple [Components] can be grouped
together into a single [Application] to indicate that the should be deployed together via GitOps.

Along with the [gitops-service] which was decided to stop deploying in [ADR 32. Decoupling Deployment],
the controllers' APIs and the UI for AppStudio have been tightly coupled with the concept of [Application]s
and [Component]s. For example, 

- PipelineRuns triggered by PipelinesAsCode produced a single image that is tied to a specific [Component]
  which is assumed to be an OCI artifact.
- The AppStudio UI (HAC) display PipelineRuns for all [Component]s in a single [Application] together.
- [Component]s are tied to artifacts produced from a single a git repository and branch.

This model presented multiple challenges including:

- If a user wants to build a new branch of an already onboarded git repository, they would need to create
  a new [Component] (with a workspace-unique name).
- [Component]s can be members of only one [Application].
- As the number of related [Component]s increases, it becomes much harder to visualize all of the currently
  or previously running PipelineRuns since all [Component]s are included together. This has resulted in users
  creating multiple [Application]s that are related to each other just to resolve the visual representation
  challenges.
- Since a PipelineRun produces a single [Component], it becomes harder to support build strategies that produce
  multiple artifacts, i.e [ko].
- [Component]s are only defined in the context of an [Application] and cannot be moved. When a user wants to
  start building a Component, they need to either add it to a current [Application] and have its builds affecting
  the IntegrationTestScenarios results of the generated Snapshots or the component needs to be created in its
  own temporary   Application only to be deleted and recreated in the appropriate one once the builds are
  properly functioning.

## Decision

We are going to abstract the concepts of the built artifacts and their relationships to each other outside of
any other controller within AppStudio. If a controller wants to maintain complete separation from others (i.e.
in order to be fully deployable on its own), it may use an adapter pattern to convert this abstraction to its
own relevant internal data model.

### ArtifactConfig

An `ArtifactConfig` describes the metadata which is used to define an `Artifact`, an `ArtifactStream`, and
how `Artifact`s produced update that stream.

`Artifact`s do not exist in isolation to other `Artifact`s in the system, however, there are both explicit
and implicit relationships that exist between them, for example:

- (implicit) Multiple `ArtifactConfig`s can be created for the same repository and branch combinations. These
  configurations would be allowed as long as the name of the produced artifact is unique. This supports use
  cases like `ko` where multiple `Artifact`s would be produced from a single build
- (explicit) A single `ArtifactConfig` can describe the configuration for producing the "same" `Artifact"
  from multiple branches in the same git repository. As an `ArtifactConfig` also controls the creation of
  an `ArtifactStream`, `Artifact`s produced on any one of the branches would update the corresponding
  `ArtifactStream`.
- (explicit) A single repository and branch may produce different `Artifact`s under different conditions.
  When artifacts are produced as part of a pull request, for example, the controller will still need to
  generate `Artifact` resources, but these should not be able to update any `ArtifactStream`s for the 
  on-push build events

### Artifact

An `Artifact` represents a single object (binary or non-binary artifacts) produced as part of a software
supply chain. It not only defines the storage location of the object itself but also the location of any
additional supporting metadata like produced SBOMs, provenance, and signatures (and the public gpg keys).

Since the concept of an `Artifact` exists outside of any other controller, the object may either be manually
created based on known artifacts or a constructor may be leveraged to watch for specific actions (i.e. within
the kubernetes cluster or new artifacts being pushed to an external location) in order to produce the resulting
`Artifact`. An example of this constructor can resemble the `TestSubjectConstructor` as proposed in
[Upstreaming integration-service].

`Artifact`s can also store references to the process which created the object (i.e. PipelineRun). As soon as a
PipelineRun is created, an `Artifact` should be created to enable visibility into the ongoing process if
an `ArtifactStream` is used for tracking or visualization.

### ArtifactStream

All `Artifact`s have an owner reference to a single `ArtifactStream`. The `ArtifactStream` keeps track of the latest
produced `Artifact` that has been created owned by that stream (i.e. similar to a floating tag reference).

A validation webhook will prevent an `Artifact` from being created unless its configuration matches that of its owning
`ArtifactStream`.

### ArtifactCollection

An `ArtifactCollection` is a set of `Artifact`s that are grouped together. An `ArtifactCollection` can include
references to other `ArtifactCollection`s to enable intermediate logical separation and aggregated groupings.
Additionally, there are no restrictions around how many `ArtifactCollection`s a given `Artifact` may belong to.

### ArtifactCollectionStream

All `ArtifactCollection`s have an owner reference to a single `ArtifactCollectionStream`. The `ArtifactCollectionStream`
defines the set of `ArtifactStream`s and `ArtifactCollectionStream`s that are allowed in the owned `ArtifactCollection`s.
The `ArtifactCollectionStream` also defines whether any individual update to a contained stream results in the automatic
generation of a new owned `ArtifactCollection`. The `ArtifactCollectionStream` keeps track of the latest produced
`ArtifactCollection` owned by that stream.

A validation webhook will prevent an `ArtifactCollection` from being created unless all contained `Artifact`s and
`ArtifactCollection`s match its owning `ArtifactCollectionStream`.

## Consequences

- If any controller does not want to interface with the `Artifact*` CRs directly (i.e. to achieve independence
  from other controllers within AppStudio), they will need to create an adapter pattern between the relevant
  APIs and their own internal data model.
- We should now have native ability to describe built artifact and their various supply chain related attestations.
  This ability holds whether the artifact is built within the kubernetes cluster or outside of it.
- We lose the simplification of having a common [Component] and [Application] data model requirement between
  all controllers as the relationships with `Artifact`s and related resources are loose couplings
- We will have to produce multiple adapters for the various controllers in order to achieve data model independence
- While each of the controllers that compose AppStudio should be able to exist on their own, they can all
  "come together" around a common description of produced artifacts in order to create a unified build, test,
  and delivery pipeline.
- The owning references of `ArtifactStream`s and `ArtifactCollectionStream`s can be used for grouping and visualizing
  related `Artifact`s and `ArtifactCollection`s.
- Some `Artifact` types can have custom uniqueness requirements which would enable the prevention of `Artifact` creation
  if the uniqueness failed. For example, an RPM-typed `Artifact` may require global uniqueness of `name`, `version`, and
  `release` properties.


[ADR 32. Decoupling Deployment]: 0032-decoupling-deployment.md
[Application]: ../ref/application-environment-api.md#application
[Applications]: ../ref/application-environment-api.md#application
[Component]: ../ref/application-environment-api.md#component
[Components]: ../ref/application-environment-api.md#component
[Devfile]: https://devfile.io/
[gitops-service]: ../ref/gitops-service.md
[ko]: https://github.com/ko-build/ko
[Upstreaming integration-service]: https://github.com/redhat-appstudio/architecture/pull/148/files