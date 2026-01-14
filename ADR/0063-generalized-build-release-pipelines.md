---
title: "63. Generalized Build and Release Pipelines"
status: Implementable
applies_to:
  - pipeline-service
  - build-service
  - integration-service
  - release-service
topics:
  - build
  - rpm
  - python
  - java
  - release
---

# 63. Generalized Build and Release Pipelines

Date: 2026-03-17

## Status

Implementable

## Context

Konflux was originally designed to produce container images. As a result, all of Konflux's core
software modeling APIs (`Application`, `Component`, `Snapshot`) assume a container image is used
to _store_ and _distribute_ software artifacts. Dependencies between components were assumed
to be represented as container image references in source code. Container image standards (OCI) are
also used to associate secure software supply chain metadata (signatures, attestations, and SBOMs)
with executable code.

Over the past year, the Konflux community has added build and release pipelines for non-container
software, such as [RPMs](https://github.com/konflux-ci/rpmbuild-pipeline) and [Python wheels](https://github.com/calungaproject/plumbing).
It is clear that Konflux aspires to be a _universal_ secure software factory, and therefore should
support additional software ecosystems such as npm (NodeJS) and Maven (Java).

This ADR codifies and generalizes the patterns for building and releasing non-container software.

### Definitions

For the remainder of this ADR, the term _"OCI image"_ will refer to any artifact that meets the OCI
[image specification](https://specs.opencontainers.org/image-spec/). This can refer to runnable
images, [index images](https://specs.opencontainers.org/image-spec/image-index/?v=v1.1.1), or
non-runnable [OCI artifacts](https://specs.opencontainers.org/image-spec/manifest/?v=v1.1.1#guidelines-for-artifact-usage).

The terms "artifact" and "package" will use the [SLSA v1.2 definition of these terms](https://specs.opencontainers.org/image-spec/manifest/?v=v1.1.1#guidelines-for-artifact-usage),
namely:
- An "artifact" is any immutable blob of data, whether that be a single file, a git commit, or a
  container image.
- A "package artifact" is an artifact that is _distributed_ as an output of a build process.
- A "package name" is the primary identifier for a _mutable_ collection of artifacts used to obtain
  software. More than one package artifact can be referenced or implied by a package name.
- A "package registry" is an entity that maps package names and identities to package artifacts.

This ADR will also introduce the term "package identity", with the following definition:

```
A "package identity" is a reference to a specific package artifact within or belonging to a package
name. This is often known as a "package version" within package ecosystems, however:

- The format and requirements of such identity can vary across package ecosystems. SemVer v2 format
  is often encouraged, but not always required.
- A package artifact may have one or more package identities at a given point in time, subject to
  the requirements of the artifact's package ecosystem.
- Package identities are not required to be immutable, depending on the requirements of its related
  package ecosystem.
```

"Software" may be used as a preceding adjective for the above terms to distinguish artifacts
containing executable code from supplementary metadata artifacts, such as Software Bill of
Materials (SBOMs), signatures, and security scan reports.

## Decision

- The definition of a `Component` (its current form, or successor as defined in [ADR-56](./0056-revised-component-model.md))
  is updated as follows:

  ```
  A "Component" is a set of one or more software package artifacts that are meant to be assembled
  and distributed through a single action. This set of package artifacts is stored as an OCI image,
  and is referred to as the _Component Build Artifact_.
  ```

- The definition of a `Release` is updated as follows:

  ```
  A "Release" is the process of verifying and distributing the software package artifacts within an
  `Application` or `ComponentGroup`, which in turn are comprised of one or more Components and
  their related Component Build Artifacts. A successful "Release" publishes all identified software
  package artifacts for an `Application` or `ComponentGroup` to a destination package registry.
  ```

- All Konflux build pipelines MUST produce an OCI image that _stores_ all content that is intended
  to be _distributed_ through a single action (the "Component Build Artifact"). The particulars of
  the OCI image can vary as needed, for example:
  - A containerized multi-arch application build produces an OCI image _index_ which contains
    references to architecture-specific OCI container images.
  - An no-arch RPM build produces an OCI artifact with a single layer containing the compressed
    (tar+gzip) contents of the RPM package.

- The _Component Build Artifact_ MUST be stored on a container registry that
  enables the [OCI Distribution Referrers API](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#listing-referrers).

- The _Component Build Artifact_ MUST provide sufficient metadata that allows its contents to be
  analyzed and extracted, namely:
  - Provide a `mediaType` of either `application/vnd.oci.image.index.v1+json` (Image Index) or
    `application/vnd.oci.image.manifest.v1+json` (Image Manifest)
  - If the _Component Build Artifact_ is an Image Manifest, provide one of the following:
    - A value for `artifactType`, OR
    - A value for `config.mediaType` that is not set to the [empty value](https://github.com/opencontainers/image-spec/blob/main/manifest.md#guidance-for-an-empty-descriptor)
  - If the `artifactType` value is set, it SHOULD use a recognized OCI MIME type for the artifact's
    package ecosystem (ex: runnable container images, Helm charts). If no MIME type for OCI exists
    within the package ecosystem, the build pipeline can set an arbitrary media type value that
    uses the `vnd.konflux` namespace prefix.

- The build pipeline MUST document the expected `mediaType`, `artifactType`, and/or
  `config.mediaType` for the _Component Build Artifact_.

- In `Snapshot` objects, the `spec.components[*].containerImage` field stores a reference to a
  build's _Component Build Artifact_. Downstream pipelines (`IntegrationTestScenario`, `Release`)
  MUST use the image references in the `Snapshot` as input.

- Supplementary artifacts used to verify the Component's software artifacts MUST be stored as an
  OCI image, using the reference to the _Component Build Artifact_ as its `subject`. These include:
  - Provenance attestations (generated by Tekton Chains).
  - Image signatures (generated by Tekton Chains).
  - Software Bill of Materials (SBOM). These MUST be generated as an output of the build
    pipeline.
  - Source code used to create the component build artifact. Such an image can be sourced from a
    [trusted artifact](./0036-trusted-artifacts.md) used as a build input, updated to add the
    _Component Build Artifact_ as its OCI image `subject`. These images SHOULD use the `-src`
    suffix as part of its published name, and provide necessary metadata identifying the contents
    as source code.
  - Security scan results. These MAY be produced as part of the build pipeline, or as the result of
    an `IntegrationTestScenario` - see [ADR-0048](./0048-movable-build-tests.md).

- Component build pipelines MUST use trusted artifacts to transmit large data (volumes) between
  tasks - see [ADR-0036](./0036-trusted-artifacts.md).

- Component build pipelines MUST document the critical path of tasks that must be executed, which
  shall be verified by an associated Conforma policy.

- The `Release` object is responsible for documenting all artifacts published by its corresponding
  release pipeline. For each component referenced in the provided `Snapshot`, the release pipeline
  must verify that it is able to publish the contents of OCI image's artifact type.

## Consequences

- Build pipelines will need to document the `mediaType`, `artifactType`, and/or `config.mediaType`
  for the component build artifact in their catalog `README.md` files.

- `IntegrationTestScenario` pipelines MUST only accept `Snapshot` data as their primary input.
  Additional inputs such as SBOMs, signatures, etc. MUST be obtained through OCI image referrers of
  components referenced in the `Snapshot` data.

- Component "nudging" (see [ADR-0029](./0029-component-dependencies.md) and [ADR-0056](./0056-revised-component-model.md))
  is limited to components that are able to reference dependant Component Build Artifacts directly.
  Developers MAY choose to modify their source code such that their build process is able to
  consume the contents within a Component Build Artifact.

- Components MAY release artifacts to a pre-release package registry and configure automatic
  releases. This workflow can provide similar capabilities as Konflux's "nudging" mechanism.
  - Pre-release artifacts MUST have at least one immutable package identifier. These
    identifiers SHOULD be generated as part of the build process.
  - The format of these identifiers and mechanisms to enforce immutability MAY be provided by the
    package registry and/or package ecosystem tooling.

- Current known build pipelines for container images, RPMs, and Python wheels meet the metadata
  requirements for _Component Build Artifacts_. Future build pipelines for non-container artifacts
  must adhere to these requirements.

- Release pipelines for a given component MUST verify that they are capable of releasing the
  provided _Component Build Artifacts_ based on their metadata. Most known release pipelines do not
  do this explicitly, and SHOULD be updated to prevent failures extracting release content.

- Release pipelines for non-container artifacts MUST extract content from the provided _Component Build_
  _Artifact_ and publish these to appropriate "native" package registries. The release pipeline
  MUST publish this content in the manner expected of the respective package ecosystem. The set of
  artifacts published during the release process MUST be documented on the associated Konflux
  `Release` object.

- Current release pipelines update the `Release` object's `status.artifacts` field in-place to
  document the set of released artifacts. This practice can remain for the time being.

## Alternatives Considered

### Publish Build Artifacts to Native Package Registries

This sub-feature would have required build pipelines to publish artifacts to a native "development"
package registry for the component's package ecosystem. Release pipelines would then be responsible
for promoting components from "development" repositories to "release" repositories. In this
alternative, the _Component Build Artifact_ is a thin artifact (ex: a single layer with a JSON file)
containing references to the artifacts published to the development package registry.

Konflux is currently built on two core principles that are at times in conflict with non-container
package development workflows:

- Any released artifact must ensure that its contents were not tampered with from build to
  release. OCI images - the "unit deliverable" for every Konflux `Component` - provide such
  guarantees by design through content-addressable identifiers. Many package ecosystems do not
  provide content-addressable version identifiers, however they typically provide other means of
  ensuring artifacts were not tampered with (ex: required checksums).
- The decision to release a particular artifact is determine by policy after the build completes.
  Builds do not know _a priori_ if they are capable of being released -- every build is a release
  candidate. Many non-container build and release tools assume that the release process happens as
  part of the build (ex: Maven [Deploy Plugin](https://maven.apache.org/plugins/maven-deploy-plugin/)).

#### Requirements and Benefits

Publishing build artifacts to native "development" package repositories would require the following:

- Builds would need to generate a unique package version identifier that is sortable and can be
  predictably incremented. Package ecosystems may or may not have built in means of doing this,
  and may potentially require developers to modify source code.
- The native package registry would need to enforce immutability for a published "development"
  version using the unique identifier. Commercial package registries _may_ enforce this in
  practice, however it is harder to state if this is generally true for all package registries.
- The native "development" package registry would need to provide mechanisms for artifacts to be
  garbage collected. As above, commercial package registries _may_ provide this as a feature in
  practice.
- The build pipeline would need to generate a list of artifacts published to the development
  registry in a machine-readable format.

There are multiple benefits to this approach:

- "Development" artifacts are easier to consume natively in dependent `Components`.
- Component "nudging" through Renovate can be implemented with native tooling, rather than obscure
  OCI artifacts or a scheduled Renovate run that obtains the latest "released" artifact.
- Release pipelines may be easier to maintain by taking advantage of native tooling, instead of
  unpacking content in bespoke layouts.
- Package artifact content is stored and promoted through native registries. We do not risk
  duplicating storage in a separate, non-native container registry.

#### Drawbacks and Blockers

Potential downsides and blockers for this approach include:

1. Release pipelines will need to modify build version identifiers during the publication process.
   Example: A package with build version id `1.3.2.dev20260311-1345` is published as `1.3.2`. This
   may require modifications to built package artifacts depending on the package ecosystem.
2. The destination package registry must enforce version immutability. It is not clear if this is
   universally true, or depends on the particular package registry provider. Konflux aspires to be
   a "neutral" upstream when possible, and moving forward we should design solutions based on agreed
   standards.
3. Package ecosystem tooling must be able to document all artifacts that are published to
   respective package registries, preferably in machine-readable formats. This data would be stored
   in the Component Build Artifact referenced above. Not all tooling produces this data today (ex:
   Maven [Deploy Plugin](https://maven.apache.org/plugins/maven-deploy-plugin/deploy-mojo.html)).
4. We have existing precedent in Konflux for using non-container OCI artifacts to publish content
   through a release pipeline. See [ADR-0049](./0049-vsa-support.md).
5. Component nudging and primary artifact distribution are separate concerns. The blockers above
   apply specifically to using native registries as the primary storage/distribution mechanism
   during the build phase. Alternative nudging approaches (tenant release pipelines, MintMaker)
   are potentially viable for addressing developer workflow needs.

Items 1, 2, and 3 above are considered "high risk"/"blockers" for adopting the "native package
registry" approach.

#### Workarounds

Developers have the following alternatives at their disposal:

- Change their "nudged" component source code such that they can consume a _Component Build Artifact_,
  OR
- Establish the following workflow:
  - Create a "development" package registry, using appropriate configuration/conventions for the
    component's package ecosystem.
  - Set up a [Tenant release pipeline](https://konflux-ci.dev/docs/releasing/tenant-release-pipelines/)
    that publishes content to the pre-release package registry. The corresponding `ReleasePlan` can
    have [auto-release enabled](https://konflux-ci.dev/docs/releasing/create-release-plan/#auto-release-logic)
    to minimize developer toil.
  - Configure [MintMaker](https://konflux-ci.dev/docs/mintmaker/user/) to update the appropriate
    dependencies at any desired cadence.

In some respects "nudging" is an implied automatic Konflux `Release` to a development (container)
package registry.

#### Reasons to Reconsider

Using native package repositories (in general or on a per-ecosystem basis) may be reconsidered
based on the following criteria:

- Release pipelines demonstrate that extraction from OCI artifacts creates unacceptable
  complexity, maintenance burden, or performance issues compared to native registry promotion.
- Changing version identifiers in release pipelines does not require modifications to built
  artifacts.
- Destination package repositories enforce version immutability through a specific ecosystem
  standard, or in practice by a significant majority of repository providers.
- Package ecosystem tooling documents all artifacts during the "publication" process, or the set
  of published artifacts can be inferred through process outputs (ex: "verbose" logs printed to
  `stdout`).
- Workarounds above provide unacceptable developer experiences. Ex:
  - "Nudging" experience that extracts _Component Build Artifact_ contents.
  - Overhead of creating and maintaining tenant release pipelines.
  - Time delays from scheduled MintMaker/Renovate runs.


### Document Published Artifacts in Release Object

This sub-feature would have deprecated the current unstructured `status.artifacts` field and
replaced it with the following fields:

- `status.packageArtifacts`: This is a list of software package artifacts published by the
  release pipeline, with structured data allowing the contents to be resolved.
- `status.additionalData`: This is unstructured JSON/YAML containing any additional data that
  release consumers may need.

Example YAML:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: Release
spec:
  ...
status:
  additionalData: # Begin unstructured YAML
    sboms:
      component:
    ...
  packageArtifacts:
    - checksum: "sha256:<checksum-hash>" # format <algorithm>:<checksum>
      ecosystem: oci # Can be other types, such as `maven`, `npm`, `rpm`, etc.
      identities:
        - "@sha256:<digest>"
        - "10.0.2-20260113-15845"
        - "10.0.2"
        - "10.0"
        - "10"
        - "latest"
      name: ubi10/ubi
      platform: # optional - used to describe os/arch specific package artifacts
        os: linux # GOOS values. If not set or empty, the package is OS-agnostic.
        arch: amd64 # GOARCH values. If not set or empty, the package is CPU-agnostic.
      registry: registry.redhat.io
```

The current `status.artifacts` field is capable of storing this data, albeit without any OpenAPI
schema validations provided by Kubernetes Custom Resource Definitions. This feature is not a hard
requirement to generalize builds and releases on Konflux, however it may be reconsidered through a
follow-up feature or ADR.

### Publish Conforma Policies Alongside Build Pipelines

This sub-feature would have required build pipeline repositories to include Conforma policies that
verified the build pipeline execution. This idea had far reaching consequences for how Conforma
policies are defined today:

- Konflux policies currently reside in the Conforma GitHub organization. This creates a tight
  coupling between the two projects, inhibiting wider adoption of Conforma as a tool. There is
  active discussion to minimize this coupling - see [Conforma Discussion #75](https://github.com/conforma/community/discussions/75).
- Inputs to Conforma policies need to be well documented so build pipeline authors have the
  ability to maintain the corresponding verification policy.
- Conforma policies need to be composable and able to be imported from multiple sources.

This idea was considered too large to be included in this ADR. The community is seeking a follow-up
ADR from Conforma experts who could refine this idea further.
