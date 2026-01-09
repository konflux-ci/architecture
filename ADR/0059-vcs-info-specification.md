# 59. VCS Info Specification for Container Images

Date: 2026-01-09

## Status

Implementable

## Context

VCS (Version Control System) information for container images is currently handled inconsistently
across Konflux, making it difficult to reliably trace images back to their source code.

### Current State

Images currently use various labels to store VCS information:

* Source repository, e.g. git repository: `org.opencontainers.image.source`,
  `io.openshift.build.source-location`, `url`
* Source revision, e.g. git commit ID: `org.opencontainers.image.revision`, `vcs-ref`

However, several problems exist with the current approach:

1. The `buildah` Task adds labels and annotations only when explicitly provided with the
   `COMMIT_SHA` and `SOURCE_URL` Task parameters. These parameters are not required, and there are
   no Conforma policies to enforce them being set.

2. OCI artifacts don't have labels - they use annotations instead. Also, while the
   `org.opencontainers.*` keys are officially defined as annotation keys in the [OCI Image
   Spec](https://github.com/opencontainers/image-spec/blob/main/annotations.md#pre-defined-annotation-keys),
   using them as labels (as is common practice) is technically not correct, though acceptable.

3. Some images produced by Konflux cannot use the OCI format and instead use the old Docker Version
   2 Schema 2 (v2s2) format, which does not support annotations at all.

4. While the `buildah` Task has some support for recording VCS info, other builder Tasks have
   different or no VCS information handling.

5. VCS information is not included in the Software Bill of Materials (SBOM), making it difficult,
   if not impossible, to trace artifacts through the SBOM alone.

## Decision

We will standardize VCS information by requiring it to be present in three places:

### OCI Manifest Annotations

All OCI manifests (for both OCI artifacts and runnable images) produced by a Konflux builder Task
must contain VCS information in the form of annotations using the official OCI pre-defined
annotation keys:

* `org.opencontainers.image.source` - The URL to the source repository
* `org.opencontainers.image.revision` - The git commit SHA

Conforma will verify these annotations are set in any OCI Image Manifest, identified by the
`mediaType` value `application/vnd.oci.image.manifest.v1+json`.

### Image Labels

All images (excluding OCI artifacts) produced by a Konflux builder Task must also set the same VCS
information as image labels:

* `org.opencontainers.image.source` - The URL to the source repository
* `org.opencontainers.image.revision` - The git commit SHA

Although this is only needed for non-OCI images (Docker v2s2), it provides some level of
consistency for consumers.

Conforma will verify these labels are correctly set for any image that is not an OCI artifact. This
includes Docker v2s2 images as well as OCI Image Manifests without the `artifactType` attribute
set:

* `mediaType` `==` `application/vnd.oci.image.manifest.v1+json` AND `artifactType` is empty or not
  defined; or
* `mediaType` `==` `application/vnd.docker.distribution.manifest.v2+json`

### SBOM

VCS information must be included in the SBOM generated for each image. Builder Tasks will be
updated to include:

* Source repository URL
* Git commit SHA

Conforma will verify this information is available in the SBOM.

TODO: Provide info on how to represent this info in CycloneDX and SPDX.

**Note**: This ADR opts for the simpler approach of teaching builder Tasks to directly include VCS
information in the SBOM. A more sophisticated approach (having the `git-clone` Task generate a
partial SBOM that gets merged by builder Tasks) is deferred to future work.

## Consequences

### Positive

* VCS information will be reliably available across all image formats regardless of the builder
  Task used
* Conforma can enforce that VCS information is present and correct
* Including VCS info in SBOMs improves its quality

### Negative

* All builder Tasks must be updated to:
  * Set both annotations (for OCI manifests) and, in some cases, labels
  * Include VCS information in generated SBOMs
* New Conforma policies must be implemented to verify:
  * OCI manifest annotations are present
  * Image labels are present
  * SBOM contains VCS information
* Users may need to update their build PipelineRuns
