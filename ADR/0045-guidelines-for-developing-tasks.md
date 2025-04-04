# 45. Guidelines for developing tasks

* Date: 2024-11-06

## Status

Proposed

## Context

One of the architectural goals for Konflux is extensibility. The core system provides opinionated [build pipelines]
and [release pipelines], but lets users extend those and/or create their own. Beyond this goal, however, there has
not been any clear guidance about where contributions should be added or the types of functionality that are typical
for the stages of software development.

## Decision

* If any process is required to modify artifacts themselves, it should be done in [build pipelines]. This will ensure
  that Konflux users can appropriately test and verify these artifacts before triggering releases with them.
* Any tasks which need to be included in the artifacts' provenance (enabling verification with EC policies) must be
  included in the [build pipelines].
* Whenever possible, a task that just changes the format of an artifact (for example creating a tar from a container image)
  should be performed in the same pipeline that produced the artifact. These modified artifacts should be attached using
  the referrer's API and the blob digest reported via results to enable verification that the artifacts were produced
  from a trusted task.
* Artifact-modifying steps should generally be avoided in [release pipelines]. When interacting with produced artifacts,
  the release pipeline should be limited to extracting artifacts from storage (i.e. an OCI registry), copying/pushing
  artifacts to target locations, and updating metadata associated with the artifacts.
* Reusable tasks or pipelines that are intended to be used in IntegrationTestScenarios should be contributed to
  [pipeline samples].

## Consequences

* All artifacts produced in Konflux should have provenance attestations. These attestations will include information
  about which tests have run.
* Whenever possible, the provenance attestations should be made available with the released artifacts. It may be
  necessary to update this metadata during the release process (for example, signing provenance with a different key
  or updating the provenance to indicate that a build was hermetic). If it is not possible to publish the provenance
  as-is, a summary attestation can be used instead.
* It should be possible to test any artifact that is going to be released.

## Footnotes

* It is not currently possible to produce trusted build-time tasks without pushing them to the [build definitions]
  repository. Once the process for trusting tasks from various locations has been established, a new ADR should be
  created to update the recommendations presented here.
* Once it is possible to generate attestations for integration tests, the requirement to add all gating tasks to the
  [build definitions] can be relaxed. This will, of course, require that the tasks and their results can be
  appropriately trusted.

[build pipelines]: https://github.com/konflux-ci/build-definitions/
[build definitions]: https://github.com/konflux-ci/build-definitions/
[release pipelines]: https://github.com/konflux-ci/release-service-catalog
[pipeline samples]: https://github.com/konflux-ci/pipeline-samples