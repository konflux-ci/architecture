# 36. Trusted Artifacts

Date: 2024-06-11

## Status

Implemented

## Context

One of the properties of Konflux is that users should be allowed to include their own Tekton Tasks
in a build Pipeline, e.g. to execute unit tests, without jeopardizing the integrity of the build
process. This is distinct from other build systems where a rigid process prevents users from
applying such customizations. To support this, Konflux build Pipelines use Trusted Artifacts to
securely share files between Tasks. Enterprise Contract is then responsible for verifying that
Trusted Artifacts were properly used in the parts of the build Pipeline that affect the build
outcome, typically the `git-clone`, `prefetch-dependencies`, and `buildah` Tasks.

Trusted Artifacts is inspired by the upcoming work being done by the Tekton Community,
[TEP-0139](https://github.com/tektoncd/community/blob/main/teps/0139-trusted-artifacts.md). The
Konflux version is meant to be a stop-gap until that feature is implemented and ready to be used.
When the time comes, the Konflux implementation should align with what is provided by the Tekton
Community, requiring a revision of this ADR and likely a new ADR.

In brief, the processes of *creating* a Trusted Artifact wraps files into an archive. Then, the
location of the archive and its checksum digests are recorded as a Task result. The process of
*consuming* a Trusted Artifact extracts such an archive, while verifying its checksum digest, into a
volume only accessible to the Task, e.g. `emptyDir`. The name and the checksum digest of the archive
is provided via Task parameters. This ensures the artifacts produced by one Task are not tampered
with when they are consumed by other Tasks.

Furthermore, Konflux takes the approach of sharing such artifacts between Tasks via an OCI registry,
e.g. quay.io, instead of using Tekton Workspaces backed by Persistent Volume Claims. This has
several advantages that were previously discussed
[here](https://github.com/konflux-ci/build-definitions/pull/913#issue-2215784386).

## Decision

Sharing files between Tasks is done via Trusted Artifacts backed by OCI storage.

## Consequences

* To facilitate the transition, a set of new Tasks have been added to support Trusted Artifacts.
  These are variants of existing Tasks. They follow the naming convention of using the suffix
  `-oci-ta`, e.g. `git-clone-oci-ta`.
* New Tasks that implement new functionality, e.g. new code scanner, and share files with other
  Tasks do not not need to follow the naming convention.
* Any Task that *uses* Trusted Artifacts must do so via parameters named with the suffix
  `_ARTIFACT`, e.g. `SOURCE_ARTIFACT`.
* Any Task that *creates* Trusted Artifacts must do so via results named with the suffix
  `_ARTIFACT`, e.g. `SOURCE_ARTIFACT`.
* Any Task that uses or creates Trusted Artifacts must NOT accept a general-purpose workspace. Files
  must always be shared as a Trusted Artifact. Workspaces can, of course, still be used for other
  purposes, such as mounting Secrets.
