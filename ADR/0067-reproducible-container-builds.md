---
title: "0067. Reproducible Container Builds in Konflux"
status: Proposed
applies_to:
  - "*"
topics:
  - reproducible-builds
  - buildah
  - sbom
---

# 0067. Reproducible Container Builds in Konflux

Date: 2026-05-20

## Status

Proposed

## Context

Konflux container builds currently produce different image digests from identical source commits. That blocks third parties from independently verifying that a deployed artifact matches the signed-off source, the property reproducible builds are supposed to give us.

The `buildah-oci-ta` task gained the upstream reproducibility primitives in [PR konflux-ci/build-definitions#2947](https://github.com/konflux-ci/build-definitions/pull/2947): `--source-date-epoch`, `--rewrite-timestamp`, and `--omit-history` are all accepted as task params. The build pipelines on top of the task do not yet pass those params through. A previous attempt to wire `commit-timestamp` into `SOURCE_DATE_EPOCH` ([PR #3263](https://github.com/konflux-ci/build-definitions/pull/3263)) closed without merging, blocked on secondary-artifact race-condition review feedback ([Ralph Bean's review](https://github.com/konflux-ci/build-definitions/pull/3263#issuecomment-2810378493)). Three earlier attempts at a verify-reproducibility task
([PRs #3383, #3385, #3386](https://github.com/konflux-ci/build-definitions/pulls?q=3383+3385+3386))
also closed without merging, on the feedback that a "build twice and compare" step does not fit a pipeline that builds once.

This ADR proposes decisions to move reproducible builds in Konflux from "available primitive" to "supported user feature." It aligns with the long-term roadmap in [architecture issue #299](https://github.com/konflux-ci/architecture/issues/299), which describes a future in which the buildah task is a thin wrapper around `buildah build` and rebuild verification is a separate prefetch-then-build-hermetically operation. The decisions here are compatible with that direction without depending on it.

### Sources of non-determinism

We catalog the sources in four families. Each entry includes a severity ("blocks reproducibility" / "user-side") and the mitigation strategy this ADR commits to.

**Timestamp-based.** The image config `created` field, file mtimes inside layer tarballs, build history timestamps, and gzip header timestamps all default to wall-clock time.

*Severity:* blocks reproducibility.

*Mitigation:* `--source-date-epoch` sets the config `created` field and clamps mtimes; `--rewrite-timestamp` clamps them further across the entire image; `--omit-history` removes build history timestamps. Buildah 1.43 makes `--timestamp` and `--source-date-epoch` mutually exclusive ("timestamp and source-date-epoch would be ambiguous if allowed together"), and the buildah-oci-ta task enforces this at the script level ([task/buildah-oci-ta/0.9/buildah-oci-ta.yaml line 700](https://github.com/konflux-ci/build-definitions/blob/main/task/buildah-oci-ta/0.9/buildah-oci-ta.yaml#L700)).

**Ordering-based.** Filesystem iteration order inside tar archives depends on the underlying filesystem and creation time. RPM installation order is not deterministic by default. Multi-architecture manifest ordering is subject to Go map iteration randomization (the underlying issue is [buildah#6383](https://github.com/containers/buildah/issues/6383), where `platformsForBaseImages` returns platforms in unpredictable order).

*Severity:* blocks reproducibility for multi-arch.

*Mitigation:* this ADR proposes an upstream-only fix path for the buildah issue.

**Content-based.** The Konflux pipeline injects `labels.json` and `content-sets.json` into builds through appended COPY instructions in the buildah-oci-ta task. One of the labels written into `labels.json` is `io.buildah.version=$(buildah version)` ([line 844 in the task](https://github.com/konflux-ci/build-definitions/blob/main/task/buildah-oci-ta/0.9/buildah-oci-ta.yaml#L844)), which means identical source against a different task image version produces a different image. The Fedora/RHEL rpm database defaults to SQLite WAL mode, which is non-deterministic; Project Hummingbird (Red Hat, March 2026) demonstrated that switching to DELETE journal mode makes the rpmdb byte-stable. Preliminary experiment also found `/var/log/dnf5.log` contains non-deterministic transaction text (24 bytes of divergence between two otherwise identical builds, mtimes already clamped). `--rewrite-timestamp` cannot fix this because the divergence is content, not timestamp.

*Severity:* blocks reproducibility for any image whose pipeline injects labels that include task-image-version data; user-side for the `dnf5.log` case.

*Mitigation (label injection):* see Decision for the `SKIP_INJECTIONS` and label policy.

*Mitigation (`dnf5.log`):* a Containerfile-side fix. Deleting it in the same `RUN` as the install (`RUN dnf install ... && dnf clean all && rm -rf /var/log/dnf*`) removes the divergent bytes from the final layer. We are not proposing a task-level strip because making `buildah-oci-ta` silently delete files post-build would add exactly the kind of out-of-band Containerfile mutation that architecture issue #299 wants to eliminate. Logs are event records and are unlikely to ever be byte-deterministic upstream, hence the workaround.

**External.** Unpinned package versions (`dnf install curl` resolves to different versions over time), floating base image tags (`FROM fedora:latest`), and network-fetched build inputs.

*Severity:* user-side.

*Mitigation:* documentation. The hermetic build mode (`HERMETIC=true` with `PREFETCH_INPUT`) addresses the network-fetching part; the rest are Containerfile-authoring practice.

### Findings from experiments

An initial four-cell flag experiment was run across three Containerfile scenarios (Alpine COPY-only, Fedora `dnf install`, Go multi-stage), using plain `buildah build` from podman. Three findings carry into this ADR.

First, `--timestamp` and `--source-date-epoch` are mutually exclusive in buildah 1.43+. The pipeline should wire only `SOURCE_DATE_EPOCH`, not both. The task already enforces this, so no pipeline-level guard is needed.

Second, for the Alpine COPY-only case, `--source-date-epoch` plus `--rewrite-timestamp` produces byte-identical images at both the uncompressed (`diff_ids`) and compressed (blob digest) level. The
trivial scenario is solvable today.

Third, for the Fedora RPM case, the strongest flag combination still produces divergent images because `/var/log/dnf5.log` contains non-deterministic transaction text. Mtimes are clamped; the remaining
source is content, not time. This is a known limitation we surface in Consequences.

A second wave of experiments ran the actual `buildah-oci-ta` task against a local Konflux kind cluster, validating the same claims at the task-wrapper level (where label injection, SBOM generation, and hermetic mutation are exercised). Two PipelineRuns of a patched `docker-build-oci-ta` pipeline (wiring `commit-timestamp → SOURCE_DATE_EPOCH` and exposing the opt-in flags described in Decision) against an Alpine COPY-only Containerfile produced identical `sha256:2296efeca6...` digests. The Go multi-stage scenario likewise reproduced byte-for-byte. The Fedora `dnf install curl` scenario did NOT reproduce, confirming the `dnf5.log` finding at the task wrapper level: the wrapper does not mask the content non-determinism the binary already showed.

## Decision

We'll wire the existing buildah reproducibility primitives through Konflux build pipelines as opt-in parameters, expose `SKIP_INJECTIONS` as a prerequisite for byte-wise reproducibility, treat reproducibility verification as a separate pipeline, and defer the multi-arch and SBOM content questions to follow-up work described below.

### Pipeline-level wiring of reproducibility parameters

We'll wire `clone-repository.results.commit-timestamp` into the `buildah-oci-ta` task's `SOURCE_DATE_EPOCH` parameter in every `docker-build*` pipeline variant. We'll expose `REWRITE_TIMESTAMP` and `OMIT_HISTORY` as pipeline-level parameters whose default is `false`. We won't be introducing a new pipeline-level `SOURCE_DATE_EPOCH` parameter that competes with the auto-sourced one; reproducible builds should track the source commit, not an arbitrary epoch.

Changes set in `konflux-ci/build-definitions`: `docker-build`, `docker-build-oci-ta`, `docker-build-multi-platform-oci-ta`, and `docker-build-oci-ta-min`. After modifying pipeline definitions, run `./hack/generate-everything.sh` so Trusted Artifact variants stay in sync.

### Default policy: opt-in, not default-on

`REWRITE_TIMESTAMP` and `OMIT_HISTORY` ship default-false. The `SOURCE_DATE_EPOCH` auto-wiring ships enabled: matching the image's `created` field to the source commit is a strictly better default and does not change layer content. We propose revisiting the `REWRITE_TIMESTAMP` default-on question after a deprecation window once downstream consumers (registry tooling, cache invalidation logic that reads the `created` field) have had time to adapt.

### Containerfile-side prerequisites for byte-wise reproducibility

`SKIP_INJECTIONS=true` is a prerequisite for byte-wise reproducibility. With injection enabled, the task appends `COPY labels.json` and `COPY content-sets.json` instructions, and `labels.json` includes `io.buildah.version`. When the task image is upgraded, that label changes and identical source produces a different image. Users who want byte-wise reproducibility across task image rebuilds must bake their labels into the Containerfile and set `SKIP_INJECTIONS=true`. Within a single task image, both settings are equally reproducible: PipelineRuns of the patched pipeline against an Alpine COPY-only Containerfile produced identical digests at `SKIP_INJECTIONS=false` (`sha256:2296efeca6...`) and at `SKIP_INJECTIONS=true` (`sha256:fc04d038...`). The two settings differ because injection adds one layer (the appended COPY instructions). So `SKIP_INJECTIONS` is a content choice the user picks once and stays with.

We'll document this as a user-side requirement and update the buildah-oci-ta README accordingly. We will not remove the injection path or change its default. Third-party security scanners that read labels from the current injection locations ([raised by MartinBasti on PR #3263](https://github.com/konflux-ci/build-definitions/pull/3263)) must keep working; making `SKIP_INJECTIONS` opt-in keeps their
integration stable.

### Verification as a separate pipeline, not a build step

We will not add a build-twice-and-compare step inside the default `docker-build*` pipeline (a verification step that builds twice does not belong there, as the review of PRs #3383, #3385, and #3386 established).

Instead, we'll deliver a standalone `verify-reproducibility` pipeline that accepts an image reference and a source artifact, runs the build twice from the same source with identical reproducibility parameters, compares the resulting digests, and emits `REPRODUCIBLE=true|false` plus a structured `DIFF_SUMMARY` result. On mismatch, it invokes [diffoci](https://github.com/reproducible-containers/diffoci) for a layer-by-layer diff. Users or CI trigger this pipeline on demand; it is independent of the production build flow. This also extends naturally toward the two-stage prefetch-then-hermetic model in architecture issue #299.

### Secondary artifacts and tag-collision awareness

When primary image digests become reproducible, secondary artifacts (SBOM, SLSA provenance, SARIF results, source image) face a tag collision: the same digest causes secondary-artifact tags to overwrite each other in the registry. Ralph Bean's review on PR #3263 describes the failure mode in detail: secondary artifacts from the first run lose their registry tag to the second run, Quay's garbage collector then deletes them, and provenance attestations from the first run point at now-missing artifacts.

[`conforma/policy` PR #1590](https://github.com/conforma/policy/pull/1590) (merged 2025-12-04) addresses the verification side by returning the latest pipelineRun attestation.

A preliminary inventory on local cluster reproduces the collision empirically. Two PipelineRuns that produced the same primary digest left these tags in the registry: `sha256-<digest>.att` (SLSA provenance), `sha256-<digest>.sbom` (SBOM blob), `sha256-<digest>.sig` (cosign signature), and `sha256-<digest>.dockerfile`. All four are digest-derived, so Run B's push overwrote Run A's on each. The Trusted Artifact tags (source `.git`, build-output) avoid collision because they are derived from
per-run identifiers. The provenance-fetch path is covered by `conforma/policy#1590`. The remaining concern is the SBOM blob path: if syft is non-deterministic, attestations from the first run point at a SBOM digest that no longer matches the overwritten tag. We propose either making the SBOM blob tag derive from the TaskRun UID or ensuring syft determinism so the blob digest itself is stable across runs.

### Upstream dependencies

Multi-architecture manifest ordering is governed by Go map iteration randomization inside buildah's `platformsForBaseImages` ([buildah#6383](https://github.com/containers/buildah/issues/6383)). A fix there is upstream, not task-level. So, we'll be monitoring the issue and adding a sort step to the buildah-oci-ta task only if the upstream fix stalls.

### Open Questions

1. Is the Hermeto/cachi2 RUN-line Containerfile mutation byte-stable across runs given identical `PREFETCH_INPUT`? The first attempt failed because the test Containerfile lacked an `rpms-lock.yaml`, so cachi2 produced no prefetch artifact and the downstream `use-trusted-artifact` step had nothing to extract. To be re-run with a properly declared hermetic scenario.
2. Is the syft-generated SBOM byte-identical when run twice against a byte-identical input image? Direct comparison was inconclusive in local experiments because the SBOM blob is stored under a tag derived from the primary image digest (`sha256-<digest>.sbom`), so identical primary digests caused the second run's SBOM tag to overwrite the first's before we could pull both. Resolving this needs either capturing the SBOM blob inside each TaskRun before push, or moving the tag derivation off the primary digest.

## Consequences

* Users gain an opt-in path to reproducible container image digests without changes to existing CI consumers. The default for new pipelines tracks the commit timestamp; layer content is unchanged unless the user opts in to `REWRITE_TIMESTAMP`.

* The non-determinism catalog in Context becomes the reference for evaluating future changes to the buildah-oci-ta task. New code added to the task gets compared against the four families to confirm it does not introduce a new non-determinism source.

* The verification scope is separated from production build. Pipelines that run today continue to run as a single build. Users who want verification opt into a separate pipeline whose only job is to re-run the build and diff.

* The pipeline parameter grows by three fields (`SOURCE_DATE_EPOCH` auto-wired plus two opt-in flags). This sits within the precedent set by PR #2947 at the task level, which added the same three params there. Cleanup of the param surface, if any, will be in a future ADR.

* `SKIP_INJECTIONS=true` for byte-wise reproducibility places a documentation burden on the user: their Containerfile must bake in any labels the pipeline would have injected. Third-party security scanners that depend on the current injection locations continue to work because the default does not change.

* `dnf5.log` content non-determinism is a documented Containerfile authoring gotcha for the RPM scenario. The workaround is to delete `/var/log/dnf*` in the same `RUN` as the install; the user guide will call this out.

* Multi-architecture manifest ordering remains non-deterministic until the upstream buildah fix. The ADR does not commit to a task-level workaround because the right place to fix it is upstream.

* Secondary-artifact tag collisions are partially addressed by the merged conforma/policy fix. The build-side inventory this ADR commits to may expose additional guardrails. If it does, this ADR will be amended; if it does not, the verification-side fix is sufficient.

* The decisions in this ADR are forward-compatible with the two-stage prefetch-then-hermetic verification model described in the architecture roadmap in issue #299: our verification pipeline can later be extended to a fully hermetic rebuild without re-litigating any of the choices made here.
