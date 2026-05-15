---
title: "67. Support for zstd:chunked image compression"
status: Proposed
applies_to:
  - build-service
topics:
  - compression
  - container-images
---

# 67. Support for zstd:chunked image compression

Date: 2026-05-13

## Status

Proposed

## Context

Konflux compresses all container image layers with gzip. zstd:chunked is a newer format built on the [Zstandard](https://facebook.github.io/zstd/) algorithm that offers smaller compressed sizes, faster decompression, and support for partial-layer downloads. There are [reports](https://fedoraproject.org/wiki/Changes/zstd:chunked) of up to 90% speed increase in large image pulls (e.g. CUDA) with zstd:chunked.

The problem is backward compatibility. Older Docker versions (pre-[23.0](https://docs.docker.com/engine/release-notes/23.0/)) try to read zstd layers as gzip and fail with `archive/tar: invalid tar header`. Other tools like [buildah](https://github.com/containers/buildah) (1.36+), [podman](https://github.com/containers/podman) (5.1+), [skopeo](https://github.com/containers/skopeo) (1.15+), and [CRI-O](https://github.com/cri-o/cri-o) already support zstd. Docker is the main blocker.

As described in [build-definitions#1264](https://github.com/konflux-ci/build-definitions/issues/1264), pushing both gzip and zstd:chunked variants into the same OCI image index works as long as gzip entries are listed first. Per the [OCI image index spec](https://github.com/opencontainers/image-spec/blob/main/image-index.md), clients select the first matching platform entry, so old Docker clients will pick gzip. Podman reads the `io.github.containers.compression.zstd` annotation and [prefers the zstd variant](https://github.com/containers/image/blob/main/internal/manifest/oci_index.go) automatically.

This was originally proposed in [build-definitions#1264](https://github.com/konflux-ci/build-definitions/issues/1264). It was also demanded in [build-definitions#3188](https://github.com/konflux-ci/build-definitions/issues/3188) for large CUDA images, and [release-service-catalog#634](https://github.com/konflux-ci/release-service-catalog/pull/634) already noted the need for zstd layer handling in Pyxis.

## Decision

Add a dual-compression setting to the build pipeline. Push both gzip and zstd:chunked formats from the `buildah` task and expose both digests as Tekton results. Dual-compression also risks breaking release pipeline tasks that assume one manifest per architecture, so those need deduplication fixes before the default can change.

### Implementation details

The `buildah` task will get 2 new params:
* `COMPRESSION_FORMAT` — `gzip` (default), `zstd-chunked`, or `dual`
* `FORCE_COMPRESSION` — when `true`, recompresses all layers, including the base image layers

In `dual` mode, the push step pushes the image twice, once with gzip, once with `--compression-format zstd:chunked`. Each push produces a different manifest digest. The `io.github.containers.compression.zstd` annotation is set on the manifest descriptor when it is added to the image index, which is how Podman and CRI-O identify and prefer the zstd variant. `IMAGE_DIGEST` always holds the primary digest (gzip in `dual` or `gzip` mode, zstd in `zstd-chunked` mode) so downstream tasks never see an empty result. In `dual` mode, the zstd digest is additionally exposed as `ZSTD_IMAGE_DIGEST`. Tekton Chains uses [type hinting](https://tekton.dev/docs/chains/slsa-provenance/#type-hinting) to match result name suffixes, so it will generate provenance for both variants without any changes in its code.

The `build-image-index` task will get a `ZSTD_IMAGES` array param. During index creation, gzip images are added first, then zstd images to enforce ordering. The `IMAGES` result continues to collect all digests via `buildah manifest inspect`. With dual-compression, it includes all 2N digests, which are already handled by Chains for provenance.

Four release tasks in [release-service-catalog](https://github.com/konflux-ci/release-service-catalog) call `get-image-architectures` and loop over all the manifests. With dual-compression they will see duplicate entries per architecture. Each task needs a `jq` dedup filter that groups by `(architecture, os)` and keeps the non-zstd entry. The zstd manifests remain in the released image index and are available for pull, the filter only prevents duplicate metadata in Pyxis, advisory content, and related systems

* `create-pyxis-image` — would create duplicate Pyxis entries and doesn't have zstd decompression logic
* `populate-release-notes` — would list the same architecture twice in advisory content
* `filter-already-released-advisory-images` — would treat zstd variants as "unreleased" since they have new digests
* `extract-oot-kmods` — would miscount architectures and fail extracting kmods from zstd layers

Signing tasks are not affected, they sign all manifests in the index, which is correct for both variants.

### Rollout

The default value of `COMPRESSION_FORMAT` stays as `gzip` until the release task fixes are merged and tested. Only then will the default change to `dual`. Once dual-compression adoption is stable and older Docker versions are no longer a concern, the default can move to `zstd-chunked` only, dropping the gzip variant entirely.

## Alternatives considered

### Add compression at index push time

Buildah's `--add-compression` flag automatically creates zstd variants at index push time. This is simpler, but the zstd manifests are created during `buildah manifest push` in the `build-image-index` task. They are not results of any TaskRun, so Chains cannot generate provenance for them. At release time, Conforma would find manifests without provenance and block the release.

### Separate intermediary task

A new task could accept the gzip manifest digest, pull the image, and re-push it with zstd compression. This works for provenance, but adds complexity, a new task definition, new pipeline wiring, and an extra cycle. Pushing twice from the existing buildah task is simpler and keeps everything in one place.

## Consequences

Pros:

* Faster pulls for modern clients. Users with Podman, CRI-O, or Docker 25+ will automatically benefit from zstd:chunked without changing their pipeline configuration.
* Full backward compatibility. Old Docker clients continue to work because gzip is listed first in the image index.
* Provenance and signing. Both variants get provenance from Tekton Chains (via result name matching) and are signed by Cosign. No changes needed to Chains or Conforma.

Cons:

* The image index contains 2N manifests instead of N (one per architecture per compression format). For typical arch counts (≤4), the 2N digests fit within Tekton's 4096-byte result limit.
* Registry storage per image roughly doubles. Each layer is stored in both gzip and zstd formats. Users who don't want this can keep `COMPRESSION_FORMAT=gzip`.
* Builds take longer in dual mode. The zstd push recompresses all layers, adding time proportional to image size.
* Release pipeline tasks must be updated to handle duplicate manifests before the default can safely change to `dual`.
