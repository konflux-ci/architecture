---
title: "72. FBC OCP Version Label and Binaryless FBC Support"
status: Implementable
supersedes: ["0026"]
applies_to:
  - build-service
  - integration-service
  - release-service
topics:
  - fbc
  - operators
  - versioning
  - container-labels
---

# 72. FBC OCP Version Label and Binaryless FBC Support

Date: 2026-11-03

## Status

Implementable

Supersedes [ADR 26. Specifying OCP targets for File-based
Catalogs](0026-specifying-ocp-targets-for-fbc.md).

## Context

[ADR 26](0026-specifying-ocp-targets-for-fbc.md) established that the target OCP version for
[File-based Catalog (FBC)][FBC] components is derived from the base image tag of
`registry.redhat.io/openshift4/ose-operator-registry:vX.YY`, read via the
`org.opencontainers.image.base.name` annotation. That decision assumed:

1. Every FBC image uses a version-tagged `ose-operator-registry` base image.
2. The base image contains `/bin/opm` and `/bin/grpc_health_probe`.
3. Each FBC targets exactly one OCP version.

These assumptions no longer hold for all FBC components. They introduce limitations for existing
workflows and do not account for newer build types:

### Early pre-GA testing

The `ose-operator-registry` image for a new OCP version is not automatically published at branch cut.
ART must perform a manual "silent release" each cycle to make it available for FBC builds before GA.
This manual dependency adds operational overhead and can delay pre-release workflows if the silent
release is not performed promptly.

### One build per version increases toil

Under ADR 26, product teams must produce one FBC fragment per OCP version they intend to target,
each with the corresponding `ose-operator-registry` base image. This increases build and maintenance
toil, particularly for operators whose upgrade graph is consistent across OCP versions.

### Binaryless FBCs

Beginning with OCP 4.15, the base image is no longer required to serve the content of the FBC image
on OpenShift clusters. OLM was updated to use a cluster-wide configured `opm` image to serve the
catalog, rather than expecting one embedded in each FBC image. This enables **binaryless FBCs** —
catalog images that contain only the declarative catalog data (e.g., JSON or YAML) without shipping
`/bin/opm` or `/bin/grpc_health_probe`. Removing the binary also reduces the image size.

Binaryless FBCs may use a minimal or scratch base image instead of the version-tagged
`ose-operator-registry` image. When they do, the base image tag no longer carries OCP version
information, making ADR 26's detection mechanism insufficient.

## Decision

### 1. Require the `com.redhat.fbc.openshift.version` container image label

FBC components MUST declare their target OCP versions using the `com.redhat.fbc.openshift.version`
container image label in their Dockerfile/Containerfile.

#### Format

The label value MUST be a **non-empty JSON array of unique strings** in `v<major>.<minor>` format,
where each string represents a target OCP version.

```dockerfile
# Single target version
LABEL com.redhat.fbc.openshift.version='["v4.18"]'

# Multiple target versions
LABEL com.redhat.fbc.openshift.version='["v4.18", "v4.19", "v4.20", "v5.0"]'
```

### 2. Fallback and version detection precedence

When the `com.redhat.fbc.openshift.version` label is absent — for example, on pre-existing FBC
components that have not yet adopted the label — the target OCP version is determined by inspecting
the base image, preserving backward compatibility with components that follow [ADR
26](0026-specifying-ocp-targets-for-fbc.md). This fallback yields a single target version and cannot
express multi-version targeting.

Konflux services MUST follow this precedence when determining target OCP version(s):

1. **`com.redhat.fbc.openshift.version` label** — if present and valid, this is authoritative. Each
   version in the array is a separate target.
2. **Base image tag** — extracted from the `FROM` instruction in the Dockerfile/Containerfile.
   Yields a single target version.

If none of these sources produce a version, the pipeline MUST fail with a clear error rather than
proceeding without a target version.

### 3. Binaryless FBC components are a supported build type

Konflux explicitly supports building FBC images that do not include `/bin/opm` or
`/bin/grpc_health_probe` in the shipped artifact.

For binaryless FBCs:

* The `com.redhat.fbc.openshift.version` label is required, since there is no version-tagged base
  image to fall back to.
* Pipeline validation tasks that require `opm` (e.g., opm validate) MUST source the binary from a
  trusted `ose-operator-registry` image at task execution time, not from the component's image.
* The base image allowlist for trusted opm sources includes images from the
  `registry.redhat.io/openshift4/` and `registry.redhat.io/openshift5/` namespaces.

## Consequences
* Backward compatible: Existing FBC components that use the `ose-operator-registry` base image and
  do not yet set the label continue to work via the fallback mechanism. No immediate migration is
  required, though adoption of the label is expected for all FBC components going forward.
* Multi-version support: A single FBC component can target multiple OCP versions in one build,
  eliminating the need to rebuild per OCP version when the operator upgrade graph is consistent.
* Pre-GA publishing unblocked: FBC components can target a future OCP version (e.g., 5.0) before its
  `ose-operator-registry` image is published, using the label to declare the correct target.
* Binaryless FBC enablement: Operators that do not need to ship `opm` in their catalog image can use
  lightweight base images while still declaring their OCP targets, reducing image size.
* Konflux services SHOULD avoid directly executing the `opm` binary from FBC component images,
  consistent with [ADR 26](0026-specifying-ocp-targets-for-fbc.md)'s principle of not running
  untrusted binaries in the trusted control plane.

[FBC]: https://olm.operatorframework.io/docs/reference/file-based-catalogs/
