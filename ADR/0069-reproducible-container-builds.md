---
title: "69. Reproducible Container Builds in Konflux"
status: Proposed
applies_to:
  - build-service
  - pipeline-service
topics:
  - reproducible-builds
  - buildah
  - sbom
---

# 69. Reproducible Container Builds in Konflux

Date: 2026-05-28

## Status

Proposed

## Context

Konflux container builds currently produce different image digests from identical source commits. Build the same git SHA twice through the same pipeline and you get two distinct sha256. That blocks a third party from independently verifying that a deployed artifact matches the source recorded in its SLSA provenance, which is the property reproducible builds give us.

The mechanism to produce identical digests already exist at the task level. The `buildah-oci-ta` task accepts `--source-date-epoch`, `--rewrite-timestamp`, and `--omit-history` as task params (the wiring was done when [the buildah task picked up the buildah 1.41+ reproducibility flags](https://github.com/konflux-ci/build-definitions/pull/2947)). What's missing is the pipeline passing those params through, and a story about what users opt into, what verification looks like, and what happens to the secondary artifacts (SBOMs, attestations, signatures) that are tagged by the primary image digest. A [previous PR that tried to wire `commit-timestamp` into `SOURCE_DATE_EPOCH`](https://github.com/konflux-ci/build-definitions/pull/3263) closed unmerged after review pointed out a tag-collision concern: when two runs produce the same digest, secondary artifacts tagged by that digest can overwrite each other in the registry. Three [earlier attempts at a `verify-reproducibility` task](https://github.com/konflux-ci/build-definitions/pulls?q=3383+3385+3386) also closed unmerged, on the observation that a "build twice and compare" step does not fit a pipeline whose contract is to build once.

This ADR proposes decisions that'll turn the existing primitives into a supported user feature: pipeline wiring, an opt-in default policy with a roadmap to default-on, a separation between production builds and verification, and a path forward on the secondary-artifact problem. It also aligns with the long-term direction in [the architecture-level reproducibility roadmap](https://github.com/konflux-ci/architecture/issues/299), which moves the buildah task toward being a thin wrapper around `buildah build` and frames rebuild verification as a separate [prefetch-then-build-hermetically operation](https://github.com/konflux-ci/architecture/issues/299#issuecomment-3656614799). None of the decisions here depend on that long-term work, but are all in alignment with it.

### Sources of non-determinism

Non-determinism enters a container build from four sources: timestamps, ordering, content the pipeline (or buildah) adds on top of the user's Containerfile, and external inputs that aren't pinned. Some of these we can mitigate today through pipeline params or already-shipped behavior in buildah. Others are open work that lives either upstream of Konflux or in the user's Containerfile. The two tables below split them along that line.

The Evidence column comes from two experiments. The first was a scenario sweep with plain `buildah build` invoked directly from the host (Alpine COPY-only, Fedora `dnf install`, Go multi-stage) under different flag combinations. The second experiment ran the same scenarios through the actual `buildah-oci-ta` task on a local Konflux kind cluster, using a forked `docker-build-oci-ta` pipeline that wires the `commit-timestamp` result from `git-clone-oci-ta` into the task's `SOURCE_DATE_EPOCH` param. Methodology details live alongside the implementation. The relevant findings are below:

#### What we can mitigate today

| Source | Mitigation | Evidence | Owner |
|---|---|---|---|
| Image config `created` field, build history timestamps, gzip header timestamps | `--source-date-epoch` sets the image's `created` field to the `SOURCE_DATE_EPOCH` value. `--omit-history` strips the build history block | Alpine COPY-only run twice through `buildah-oci-ta` produces the same image digest (`sha256:2296efeca6...`) | Konflux pipeline wiring |
| File mtimes inside layer tarballs | Pass both `--source-date-epoch=<value>` and `--rewrite-timestamp` to buildah. `--rewrite-timestamp` performs the clamp against the `SOURCE_DATE_EPOCH` value. Passing `--source-date-epoch` alone updates the image config's `created` field but leaves file mtimes inside the layer alone. (Separately: buildah 1.43+ rejects `--timestamp` and `--source-date-epoch` together as mutually exclusive, so the task refuses `BUILD_TIMESTAMP` and `SOURCE_DATE_EPOCH` set together for the same reason.) | Same Alpine round-trip as above. mtimes inside the layer matched byte-for-byte | Konflux pipeline wiring |
| `io.buildah.version` label inside the image | Native buildah behavior: the `--identity-label` flag (which controls this label) is documented to default to `true` *unless* `--timestamp` or `--source-date-epoch` is used. Setting `SOURCE_DATE_EPOCH` therefore suppresses the label automatically. Version 0.9 of the buildah-oci-ta task injects the label manually outside of buildah's control, defeating that suppression. [An upcoming task version moves the build step into a Go binary](https://github.com/konflux-ci/build-definitions/pull/3533) (the new `konflux-build-cli`), which lets buildah handle the label correctly | konflux-build-cli already has [a reproducibility integration test](https://github.com/konflux-ci/konflux-build-cli/blob/ea157f10ecc086b55fe0268cc8834833ba6d33ca/integration_tests/build_test.go) that covers the same-version case | Konflux task definition (moving to the new task version) |
| `content-sets.json` injection (separate from labels) | Within a single task image version, the injection is byte-deterministic. Across versions it changes whenever the injection logic does. `SKIP_INJECTIONS=true` opts out entirely for users who prefer to bake equivalent content into their Containerfile | Two Alpine runs at `SKIP_INJECTIONS=false` matched (`sha256:2296efeca6...`); two runs at `SKIP_INJECTIONS=true` matched (`sha256:fc04d038...`). The two settings produced different digests, both internally reproducible | User choice; task supports both |
| `/var/log/dnf5.log` in RPM-based images | The log is non-deterministic transaction text and `--rewrite-timestamp` doesn't help (the divergence is content, not time). The fix lies in the Containerfile: delete it in the same `RUN` as the install, for example `RUN dnf install ... && dnf clean all && rm -rf /var/log/dnf*` | Fedora `dnf install curl` scenario did not reproduce; the diff between two layer tarballs was 24 bytes inside `/var/log/dnf5.log`, with all mtimes already clamped | Containerfile author |
| Network-fetched build inputs (apt, dnf, pip, npm resolving at build time) | Konflux's hermetic build mode (`HERMETIC=true` with `PREFETCH_INPUT`) prefetches dependencies via Hermeto and disables network access during the `buildah build` step | Not directly measured in this round (the hermetic experiment needed an `rpms-lock.yaml`). The mechanism is documented and carried out by Konflux's existing hermetic-build tests | User opts in; Konflux provides the mode |
| Unpinned package versions, floating base image tags | Containerfile authoring practice: pin base images by digest, use lockfiles where the package manager supports them | Not a measurement, but a best practice to be included in the user guide | Containerfile author |

#### What is still open work

| Source | Why it isn't fixed yet | Where the fix lives |
|---|---|---|
| RPM installation order | `rpm` doesn't order package installs deterministically by default. Even when you hand `dnf install` a pre-sorted package list, dependency resolution decides the actual install order. So, the fix has to be at the `rpm`/`dnf` level. | Upstream `rpm` / `dnf`; no Konflux-side fix proposed here |
| `rpmdb` SQLite WAL files (`/var/lib/rpm/rpmdb.sqlite-wal`) on RHEL and Fedora images | Whether `SOURCE_DATE_EPOCH` is honored natively by `rpm` for these files is unverified. A demonstrated fix exists in the form of forcing DELETE journal mode (the approach taken by Project Hummingbird), but that's a Fedora-side configuration change rather than something a Konflux task can apply per build | Upstream Fedora `rpm` config, or an enforced setting in Konflux base images if the upstream change stalls |
| Multi-architecture manifest ordering | The platform list for multi-arch builds is iterated through a Go map inside [buildah's `platformsForBaseImages`](https://github.com/containers/buildah/issues/6383). Go randomizes map iteration, so the manifest order is unstable. The upstream issue has had no activity since September 2025, which is long enough to treat as stalled. A sort step inside `build-image-index` (which is our task) could enforce order at the manifest-list assembly stage. See Decision for the proposal | Upstream buildah (preferred), or `build-image-index` as a fallback |

The two tables above describe the **what** (where non-determinism comes from and whether a mitigation exists). The Decision section below describes the **how** (which mitigations we wire into the pipeline, what defaults we ship, and how we plan to close the open-work entries over time).

## Decision

We will wire the existing buildah reproducibility primitives through Konflux build pipelines as opt-in parameters, treat the cross-task-version label question as something Konflux solves at the task level rather than asking users to set `SKIP_INJECTIONS=true`, deliver reproducibility verification as a separate pipeline rather than a step inside the default build, and lay out next steps for the secondary-artifact and multi-arch questions. Each of those is addressed below:

### Pipeline-level wiring of reproducibility parameters

We will expose three new opt-in pipeline parameters on every `docker-build*` variant:

- `source-date-epoch`: when set, the pipeline passes it to the task's `SOURCE_DATE_EPOCH` param. When not set, the pipeline auto-sources it from `clone-repository.results.commit-timestamp` *only if* `rewrite-timestamp` is also enabled. The reason for the coupling is that `--rewrite-timestamp` needs a `SOURCE_DATE_EPOCH` value to clamp file mtimes against; without one, the flag does nothing. `omit-history` does not have this dependency (it just strips the build history block regardless of any timestamp value), so setting `omit-history` alone does not trigger the auto-source.
- `rewrite-timestamp`: passed straight through to the task's `REWRITE_TIMESTAMP`. Default `false`.
- `omit-history`: passed straight through to the task's `OMIT_HISTORY`. Default `false`.

We will not add a competing pipeline-level `SOURCE_DATE_EPOCH` semantics on top of the auto-sourced one. When a reproducible build is what the user wants, the source commit's timestamp is the right reference point. An arbitrary epoch would defeat that property.


### Default policy: opt-in (not default-on)

`source-date-epoch`, `rewrite-timestamp`, and `omit-history` all ship default-off. None of them are auto-applied to existing pipelines.

The case for keeping `source-date-epoch` opt-in (rather than auto-wiring it for every build) is that the image's `created` field has an existing semantic users rely on: it answers the question "when was this artifact assembled?" If we silently set it to the source commit's timestamp on every build, we mislead users whose Containerfiles don't pin their dependencies. Those builds aren't actually reproducible, and the `created` field would reflect a property the build doesn't have. Better to make the user signal intent explicitly.

Users opt out of the new behavior simply by not setting the new parameters. Existing pipelines continue to behave exactly as they do today.

#### Roadmap to default-on

Opt-in is the starting point. The idea is that reproducible builds become the default for new pipelines once a few conditions are met:

1. The upcoming buildah-oci-ta task version (the one that delegates to `konflux-build-cli`) ships and reaches the same trust level as v0.9, removing the manual `io.buildah.version` injection that defeats buildah's own suppression logic.
2. The secondary-artifact tag-collision concern (covered below) has a build-side resolution in addition to the verification-side fix that already landed in [Conforma's "return the latest pipelineRun attestation" change](https://github.com/conforma/policy/pull/1590).
3. Downstream consumers that read the image `created` field for cache invalidation or build-time monitoring have had a deprecation window to adapt or document an alternate signal.
4. The `verify-reproducibility` pipeline (covered below) has been tested against enough real Konflux components that we have confidence the default-on change won't surprise users.

When those conditions are met, a follow-up ADR can flip the default and document the migration path.

### Containerfile-side prerequisites for byte-wise reproducibility

There are two pieces of metadata the task adds on top of the user's Containerfile that interact with reproducibility: the `io.buildah.version` label, and the appended `COPY content-sets.json` instruction.

**The `io.buildah.version` label.** Buildah's `--identity-label` flag, which controls whether the image carries this label, is documented to default to `true` *unless* `--source-date-epoch` (or `--timestamp`) is set. So when the user opts into reproducibility, buildah itself stops emitting the label, and cross-task-version reproducibility is preserved at the buildah level. The problem is task-internal: version 0.9 of buildah-oci-ta computes the label outside of buildah's control (in the task's bash) and injects it via the appended `labels.json` file, defeating buildah's own suppression. An [upcoming task version replaces the bash build step with a call to `konflux-build-cli`](https://github.com/konflux-ci/build-definitions/pull/3533). That new version leaves label handling to buildah and so respects `--identity-label`'s default. Once that task version is the recommended one, cross-task-version reproducibility doesn't require `SKIP_INJECTIONS=true` at all.

**The `content-sets.json` injection.** The task appends a `COPY content-sets.json` instruction to the user's Containerfile to carry repository metadata that third-party security scanners look for. Within a single task version, the injection is byte-deterministic (two PipelineRuns against the Alpine COPY-only scenario at `SKIP_INJECTIONS=false` produced identical digests, `sha256:2296efeca6...`). Across task versions, the injection content can shift as the metadata schema evolves. Users who want byte-stability across task upgrades, *and* who don't need the scanner-compatible injection, can set `SKIP_INJECTIONS=true` and bake equivalent metadata into their Containerfile directly. That path also gives the same internal reproducibility within its own setting: two runs at `SKIP_INJECTIONS=true` produced identical digests of `sha256:fc04d038...`. The two settings produce different digests from each other (the inject path adds one layer) but each is internally reproducible.

We are not removing the injection path or changing its default. The injection exists because third-party security scanners read labels and content-sets metadata from the locations the task currently writes them, and breaking that contract silently would harm users who depend on it. `SKIP_INJECTIONS` stays opt-in, with the user guide documenting (a) that the upcoming task version handles the `io.buildah.version` case without any user-side action, and (b) that `SKIP_INJECTIONS=true` is the right choice for users who want cross-version content-sets stability and are willing to take on the labels-in-Containerfile responsibility themselves.

### Verification as a separate pipeline

Reproducibility is a property you verify. A pipeline whose contract is to build an artifact once shouldn't also build it a second time to check its own work. The two activities have different inputs and different consumers. Mixing them inside `docker-build*` would double every build's cost for every user even though only some users care about the verification result at any given moment, and it would mix "build failed" with "build succeeded but the verification step found a diff." Three earlier task-level attempts at this approach ([PRs #3383](https://github.com/konflux-ci/build-definitions/pull/3383), [#3385](https://github.com/konflux-ci/build-definitions/pull/3385), and [#3386](https://github.com/konflux-ci/build-definitions/pull/3386)) ran into versions of the same issue and were closed without merging.

Instead, we will deliver a standalone `verify-reproducibility` pipeline. It accepts an image reference (the artifact to verify) and a source artifact (the recipe the image claims to have been built from), rebuilds the image once from that source using identical reproducibility parameters, and compares the resulting digest against the supplied image reference's digest. It emits a `REPRODUCIBLE=true|false` result plus a structured `DIFF_SUMMARY`. On digest mismatch, it invokes [diffoci](https://github.com/reproducible-containers/diffoci) to produce a layer-by-layer diff. Users and CI trigger it on demand. It is independent of the production build flow, keeping the production flow unchanged for everyone.

The property the verification pipeline asserts (i.e. given the same source, the same task version, and the same prefetched inputs, the same digest) aligns with how SLSA frames reproducibility today, as a property attested separately and tracked in the Verification Summary Attestation rather than as a property of the build itself (see [`slsa.buildReproduced`](https://slsa.dev/spec/v1.2/verified-properties#slsabuildreproduced)). There's also a limitation though: reproducing on the same build platform doesn't defend against attacks on the build platform itself. The stronger property, where an independent identity on an independent platform reproduces the same artifact from the provenance recipe, is something the verification pipeline's shape can extend toward (but isn't what this ADR plans to do out of the box).

### Secondary artifacts and tag-collision awareness

Konflux pipelines produce more than just the primary container image. A typical `docker-build*` run also emits a SLSA provenance attestation, an SBOM, SAST results, a copy of the Dockerfile, and (for some pipelines) a source image. Most of those are pushed to the registry under tags derived from the primary image's digest (e.g. `sha256-<digest>.sbom`, `sha256-<digest>.att`, `sha256-<digest>.sig`). That convention works well when each primary image has a unique digest, because the secondary-artifact tag is then unique too. The convention breaks the moment two builds produce the same primary digest.

Build a commit, the pipeline pushes `image:abcd` plus `sha256-abcd.sbom`, `sha256-abcd.att`, and friends. Trigger `/retest` on the PR. The second pipelineRun produces the same primary digest (because the build is reproducible), so it pushes secondary artifacts under the same tags. The second pipelineRun's `.sbom` push overwrites the first's at the registry. The first pipelineRun's attestation, which is still attached to the image digest, references a SBOM blob digest that no longer matches whatever the `.sbom` tag now points to. Registry garbage collection will delete the orphaned SBOM blob shortly after. Anything trying to verify the first attestation against its referenced SBOM gets a stale-or-missing artifact.

This was reproduced on a local cluster: two `docker-build-oci-ta` PipelineRuns producing the same primary digest collided on four tags (`sha256-<digest>.sbom`, `.att`, `.sig`, `.dockerfile`). The Trusted Artifact tags for source and build-output didn't collide because they're derived from per-pipelineRun identifiers rather than from the primary digest.

The verification-side of this problem is already addressed: [Conforma's change to always return the latest pipelineRun attestation](https://github.com/conforma/policy/pull/1590) ensures that verifiers reading the attestation get one whose referenced blob digests are consistent with what's currently in the registry. That handles the case where a verifier is looking up an attestation for a digest and accepts the most recent one as authoritative.

This ADR proposes two options for the build-side:

1. **Move the cosign-style tag derivation off the primary digest for the blobs that aren't expected to be byte-stable.** SBOMs, for example, may or may not be byte-identical across two runs that produce the same image digest depending on whether the SBOM tool (syft, in our case) is deterministic. If we tag the SBOM blob with the pipelineRun UID (e.g. `sha256-<digest>-<prun-uid>.sbom`) the collision disappears at the cost of making lookups slightly more involved, because verifiers now need to know which pipelineRun's SBOM to fetch.
2. **Move secondary-artifact storage to the OCI [Referrers API](https://github.com/opencontainers/distribution-spec/blob/d40ddd746adcc9f56bcaccf45396deb26280385d/spec.md#listing-referrers)** instead of the tag-based fallback. The Referrers API stores multiple referrers per subject without tag-derived naming, so two SBOMs for the same image digest can coexist. This is a more significant pipeline-side change but addresses the whole class of collisions, not just the SBOM one. cosign and other tools have varying support for the Referrers API today. This option needs an audit before we commit to it.

We are not picking one in this ADR. The preference is to gather data during the RFC window (which tools in the pipeline already speak the Referrers API, which still need updates, how Conforma fetches SBOMs) and write a follow-up that commits to one path.

### Multi-architecture manifest ordering

Multi-arch manifest ordering is unstable because the platform list is iterated through a Go map inside [buildah's `platformsForBaseImages`](https://github.com/containers/buildah/issues/6383), and Go map iteration is randomized. The cleanest fix is upstream in buildah (sort the list once before producing the manifest), and that upstream issue is where we'd prefer the fix to land. It has had no activity since September 2025, so we are treating it as stalled for planning purposes.

The logical fallback lives in Konflux: `build-image-index` is our own task, and the manifest-list assembly step inside it can sort the entries by platform before pushing. That sort would make manifest ordering deterministic at the Konflux layer regardless of what buildah does upstream. A suggestion is adding the sort in `build-image-index` and treating the upstream fix as a future cleanup that lets us remove our sort. We'd still have to decide on the sort key (platform name as a string sort, or `(os, arch, variant)` tuple sort) during implementation.

### Open Questions

1. Is the syft-generated SBOM byte-identical when run twice against a byte-identical input image? Direct comparison was inconclusive in the local experiments because the SBOM blob is stored under the digest-derived `sha256-<digest>.sbom` tag, and the second run's push overwrote the first's before both could be pulled. Resolving this needs either capturing the SBOM blob inside each TaskRun before push, or one of the two tag-derivation changes proposed in the secondary-artifact section.

## Consequences

* Existing pipelines are unaffected. Reproducibility is reached by setting new opt-in pipeline parameters. Users who don't set any of them get exactly the behavior they have today.

* When a user does opt in, they get byte-wise reproducible primary image digests for any Containerfile pattern whose non-determinism sources are listed in the "What we can mitigate today" table. The "What is still open work" table sets expectations for the patterns we don't yet cover (RPM install order, multi-arch manifest ordering, `rpmdb` WAL files).

* The non-determinism catalog (the two tables in Context) is a review reference. When a future PR proposes adding logic to the buildah-oci-ta task, reviewers can check whether the change introduces or moves an entry between the two tables.

* Verification is a separate user-triggered pipeline. Users who don't care about verification pay no cost. Users who do, run it on demand.

* The `io.buildah.version` label is handled at the task level, not by asking users to set `SKIP_INJECTIONS=true`. Once the upcoming buildah-oci-ta task version is the recommended one, no Containerfile change is required for cross-task-version reproducibility.

* `SKIP_INJECTIONS=true` remains useful but for a narrower purpose: users who want byte-stability across task upgrades of the `content-sets.json` injection, and who are willing to add equivalent metadata into their Containerfile, opt into it. Third-party security scanners that rely on the current injection locations are unaffected because the default doesn't change.

* The image `created` field's existing semantic ("when was this artifact assembled?") is preserved for users who don't opt in. Users who opt in change that to "the source commit's timestamp" deliberately, and the user guide will say so.

* Secondary artifacts (SBOM, attestations, signatures) collide on tags derived from the primary digest when reproducible builds make digests identical across runs. The Conforma verification-side fix is necessary but not sufficient. This ADR commits to a follow-up ADR that picks between off-digest tag derivation and the OCI Referrers API. Until that follow-up lands, pipelines that produce identical digests across runs will have overwritten secondary-artifact tags.

* Multi-arch manifest ordering becomes deterministic once `build-image-index` sorts the manifest list before push (this ADR proposes the sort). An upstream buildah fix would make our sort redundant, but isn't blocking.

* The default-on roadmap (four conditions listed in "Default policy") becomes the migration target. Each condition is independently trackable, so progress can be reviewed against them rather than against an open-ended "is reproducibility the default yet?" question.

* One open question remains: whether syft produces a byte-identical SBOM when run twice against a byte-identical input image.
