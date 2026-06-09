---
title: "68. Support for zstd:chunked image compression"
status: Proposed
applies_to:
  - build-service
topics:
  - compression
  - container-images
---

# 68. Support for zstd:chunked image compression

Date: 2026-05-13

## Status

Proposed

## Context

Konflux compresses all container image layers with gzip. zstd:chunked is a newer format built on the [Zstandard](https://facebook.github.io/zstd/) algorithm that offers smaller compressed sizes, faster decompression, and support for partial-layer downloads. There are [reports](https://fedoraproject.org/wiki/Changes/zstd:chunked) of up to 90% speed increase in large image pulls (e.g. CUDA) with zstd:chunked.

The problem is backward compatibility. Older Docker versions (pre-[23.0](https://docs.docker.com/engine/release-notes/23.0/)) try to read zstd layers as gzip and fail with `archive/tar: invalid tar header`. Other tools like [buildah](https://github.com/containers/buildah) (1.36+), [podman](https://github.com/containers/podman) (5.1+), [skopeo](https://github.com/containers/skopeo) (1.15+), and [CRI-O](https://github.com/cri-o/cri-o) already support zstd. Docker is the main blocker.

As described in [build-definitions#1264](https://github.com/konflux-ci/build-definitions/issues/1264), pushing both gzip and zstd:chunked variants into the same OCI image index works as long as gzip entries are listed first. While the [OCI image index spec](https://github.com/opencontainers/image-spec/blob/main/image-index.md) leaves platform selection implementation-defined, older Docker clients predictably select the first matching platform entry, so they will pick gzip. Podman reads the `io.github.containers.compression.zstd` annotation and [prefers the zstd variant](https://github.com/containers/image/blob/main/internal/manifest/oci_index.go) automatically.

This was originally proposed in [build-definitions#1264](https://github.com/konflux-ci/build-definitions/issues/1264). It was also demanded in [build-definitions#3188](https://github.com/konflux-ci/build-definitions/issues/3188) for large CUDA images, and [release-service-catalog#634](https://github.com/konflux-ci/release-service-catalog/pull/634) already noted the need for zstd layer handling in Pyxis.

## Decision

Add a dual-compression setting to all build pipelines. In `dual` mode, the build task pushes both gzip and zstd:chunked variants and bundles them into a per-arch OCI image index. The task exposes the index digest as `IMAGE_DIGEST`, and explicitly lists the individual gzip and zstd child manifest digests in the `IMAGES` result. 

This is an experimental approach with a known constraint on Tekton result sizes (the 4KB limit). TEP-0164 ([tektoncd/community#1248](https://github.com/tektoncd/community/pull/1248)) proposes external storage for Tekton results which will resolve this limitation. Until then, dual-compression is opt-in. It also risks breaking release pipeline tasks that assume one manifest per architecture, so those need deduplication fixes before the default can change.

While the implementation details below focus on the `buildah` task, this convention applies to all image-producing tasks and pipelines in the Konflux ecosystem (e.g. `oci-copy`, `modelcar`, and any future build tasks). Authors of those tasks should follow the same dual-compression pattern when adding zstd support.

### Implementation details

The `buildah` task will get 2 new params:
* `COMPRESSION_FORMAT` — `gzip` (default), `zstd-chunked`, or `dual`
* `FORCE_COMPRESSION` — when `true`, recompresses all layers, including the base image layers

In `dual` mode, the push step creates a **per-arch index** containing both compression variants:

1. Build the image locally
2. Push the gzip variant to the registry
3. Push the zstd:chunked variant to the registry
4. Create a per-arch index with `buildah manifest create` + `buildah manifest add`, adding the gzip manifest first
5. Push the per-arch index to the unique tag and the real image tag

The individual manifests do not need their own temporary tags; they are pushed by digest and referenced from the per-arch index directly.

Both variant pushes must use `--format=oci`. Mixing OCI and Docker manifest formats within a single index causes "manifest invalid" error on Quay. If `COMPRESSION_FORMAT=dual` and the image format is not OCI, the task must detect this incompatible combination and error out early with a clear message.

`IMAGE_DIGEST` points to the per-arch index, which contains both variants. Because Tekton Chains does not currently support recursive signing of child manifests within an index ([tektoncd/chains#1070](https://github.com/tektoncd/chains/issues/1070)), the build task explicitly exports the digests for both the gzip and zstd child manifests in its `IMAGES` result. This allows Chains to generate provenance for each manifest directly from the trusted build task, closing potential trust gaps. Downstream tasks, SBOM generation, and signing consume `IMAGE_DIGEST` as the primary artifact. The `io.github.containers.compression.zstd` annotation is set on the zstd manifest descriptor within the index, which is how Podman and CRI-O [identify and prefer](https://github.com/containers/image/blob/main/internal/manifest/oci_index.go) the zstd variant.

In `gzip` or `zstd-chunked` mode, the build task pushes a single manifest as it does today. `IMAGE_DIGEST` holds the primary digest (gzip in `gzip` mode, zstd in `zstd-chunked` mode).

The `build-image-index` task requires no new parameters. Each entry in the existing `IMAGES` array is now a per-arch index (in `dual` mode) instead of a single manifest. The task's existing `--all` flag on `buildah manifest add` extracts child manifests from per-arch indexes and flattens them into the final multi-arch index. Buildah appends manifests in the order they appear in the source index, which preserves the gzip-first invariant in the flat index.

SBOM generation requires an update; the SBOM must attach to the gzip manifest digest (identified by the absence of the zstd annotation) directly, not the per-arch index. The per-arch index is an intermediate build artifact that gets flattened by `build-image-index`, so it is not a valid long-term attachment point. Individual compression variants do not receive separate SBOMs; they share identical content, only differing in layer compression.

Five release tasks in [release-service-catalog](https://github.com/konflux-ci/release-service-catalog) call `get-image-architectures` and loop over all the manifests. With dual-compression they will see duplicate entries per architecture. Each task needs a `jq` dedup filter that groups by `(architecture, os)` and keeps the non-zstd entry. The zstd manifests remain in the released image index and are available for pull; the filter only prevents duplicate metadata in Pyxis, advisory content, and related systems.

* `create-pyxis-image` — would create duplicate Pyxis entries and doesn't have zstd decompression logic
* `populate-release-notes` — would list the same architecture twice in advisory content
* `filter-already-released-advisory-images` — would treat zstd variants as "unreleased" since they have new digests
* `extract-oot-kmods` — would miscount architectures and fail extracting kmods from zstd layers
* `push-rpm-data-to-pyxis` — uses `cosign download` to fetch SBOMs from child manifest digests, so the SBOM must be attached to the gzip manifest for resolution to succeed

Signing tasks are not affected; they sign all manifests in the index, which is correct for both variants.

### Rollout

The default value of `COMPRESSION_FORMAT` stays as `gzip` until the release task fixes are merged and tested. Only then will the default change to `dual`. Once dual-compression adoption is stable and older Docker versions are no longer a concern, the default can move to `zstd-chunked` only, dropping the gzip variant entirely. There may be additional considerations to take into account when deciding to switch the default to `dual` or `zstd-chunked`. For example, if major installations are still requiring the Docker format instead of OCI for images, then changing this default might need to wait until those installations are ready to move.

## Alternatives Considered

### Add compression at index push time

Buildah's `--add-compression` flag automatically creates zstd variants at index push time. This is simpler, but the zstd manifests are created during `buildah manifest push` in the `build-image-index` task. They are not results of any TaskRun, so Chains cannot generate provenance for them. At release time, Conforma would find manifests without provenance and block the release.

### Push two individual manifests with separate results

Instead of creating a per-arch index, the buildah task could push two individual manifests and expose both digests as separate results (`IMAGE_DIGEST` for gzip, `ZSTD_IMAGE_DIGEST` for zstd). This requires a new `ZSTD_IMAGES` parameter on `build-image-index` and raises several concerns: orphaned manifests subject to garbage collection if not referenced by a tag or index, and breakage in `gzip`-only mode when the zstd result is empty. The per-arch index avoids all of these by bundling both variants under a single digest.

### Separate intermediary task

A new task could accept the gzip manifest digest, pull the image, and re-push it with zstd compression. This works for provenance, but adds complexity, a new task definition, new pipeline wiring, and an extra cycle. Pushing twice from the existing buildah task is simpler and keeps everything in one place.

## Consequences

Pros:

* Faster pulls for modern clients. Users with Podman and CRI-O will automatically benefit from zstd:chunked without changing their pipeline configuration. Docker 23.0+ clients gain tolerance for the zstd layer, but will continue to receive the gzip variant via first-match selection.
* Full backward compatibility. Old Docker clients continue to work because gzip is listed first in the image index.
* Provenance and signing. Because the build task explicitly exports the child manifests in `IMAGES`, Tekton Chains can generate provenance for each manifest directly from the trusted build task, avoiding trust gaps where manifests are only discovered by downstream tasks.

Cons:

* The final image index contains 2N manifests instead of N (one per architecture per compression format). Exposing all of these in the `IMAGES` result increases the Tekton result size, pushing closer to the 4KB limit for large matrix builds (e.g., builds exceeding 4-5 architectures may hit this limit).
* Registry storage per image roughly doubles. Each layer is stored in both gzip and zstd formats. Users who don't want this can keep `COMPRESSION_FORMAT=gzip`.
* Builds take longer in dual mode. The zstd push recompresses all layers, adding time proportional to image size.
* Release pipeline tasks must be updated to handle duplicate manifests before the default can safely change to `dual`.

