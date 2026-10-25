---
title: "73. Bring-Your-Own Build Logic with SLSA Build L3 / Source L4"
status: Proposed
applies_to:
  - build-service
  - enterprise-contract
  - integration-service
  - multi-platform-controller
  - pipeline-service
topics:
  - build
  - slsa
  - provenance
  - tekton
  - trusted-tasks
---

# 73. Bring-Your-Own Build Logic with SLSA Build L3 / Source L4

Date: 2026-10-19

## Status

Proposed

## Context

Design for letting Konflux users add a new build tool or artifact type
quickly -- by supplying a build image and a script, directly or via a
Pipeline edit -- without a platform catalog review or a new Conforma
policy, while every resulting artifact still carries a valid SLSA Build L3
claim. Source L4 evidence is required through the chain in
[ADR-0055](./0055-slsa-source-provenance-verification.md): a component whose
forge cannot mint a Source VSA cannot release on this policy.

Today, adding a new build tool or artifact type to Konflux means adding Tekton
Tasks and a Pipeline to the shared catalog, which goes through platform
review. That review protects the Build L3 trust boundary (provenance
integrity, isolation) but is slow relative to "I just want to build Python
wheels / a new binary format today."

A developer could already write a fully custom Tekton Pipeline without
going through that catalog review -- nothing technically stops it. But it
would not pass any existing Conforma release policy, so they would also
need to author a brand-new policy and get it approved before anything
built this way could ever release. That second burden is as heavy as the
first -- and it's not just a burden: a different bespoke Pipeline and
policy per component is exactly what SLSA's own "minimize the number of
trusted platforms" principle warns against. SLSA's example for that
principle is this scenario by name: "instead of each team within an
organization maintaining their own build platform, use a shared build
platform" (see "Evidence from the SLSA spec", under Decision).

Konflux already separates the platform trust boundary from the build logic
itself ([ADR-0053](./0053-trusted-task-model.md),
[ADR-0063](./0063-generalized-build-release-pipelines.md)) --
Build L3 is a property of the platform, and Source L4 of two-person source
review, neither of which requires platform review of build logic itself
(see "Why no catalog review is required" under Decision).

### Goals

- A developer can add a new build tool or artifact type using Konflux's
  default build image and script path convention, with no Konflux catalog
  PR and no platform review of the build logic itself.
- If the defaults don't fit -- a different image, a different script
  location, more than one build step -- the developer edits their own
  component's committed Pipeline directly to override params or add more
  steps, still with no catalog PR.
- Neither case requires the developer to author a Tekton Pipeline from
  scratch, or a new Conforma policy to get it released. One shared Pipeline
  shape and one shared Conforma policy -- both authored once by Konflux,
  not per component -- already cover this build type.
- Every artifact produced this way carries a Build L3 attestation.
  Source L4 evidence is the [ADR-0055](./0055-slsa-source-provenance-verification.md)
  chain, verifiable the same way as for a catalog-pipeline artifact. A
  component whose forge cannot mint a Source VSA cannot release on this
  policy.
- The existing two-party source review (already required for Source L4) is
  the only human review the build logic needs.

### Non-Goals

- **Hermetic execution.** This feature does not require or guarantee that the
  build only used bytes from the fetched revision. The build may fetch
  dependencies over the network, same as any other SLSA Build L3 build.
  `resolvedDependencies` completeness is best-effort, as the SLSA spec
  allows through Build L3. Hermetic builds are a separate, pre-existing
  Konflux initiative and orthogonal to this one. Isolation is in scope:
  see "Isolation" under Decision. Isolated is not hermetic.
- **Accepting a developer-authored Task.** See "Why not a developer-authored
  Task" under Decision. Only Pipeline edits (within fixed limits) are
  accepted from the developer -- never a Task.
- **Accepting arbitrary Tekton Pipelines or Tasks with inline steps.**
  Considered and rejected; see "Alternatives Considered."
- Redefining the must/may/must-not taxonomy of Konflux's user-facing
  platform contract. This feature should end up as one concrete instance of
  a "may" layer in that taxonomy, not a redefinition of it.

## Decision

Konflux will publish a single Konflux-owned Tekton Task (`run-build`, and a
`run-build-remote` variant for multi-platform VM builds) that runs a
developer-supplied build image and script, together with a default Pipeline
that wires `checkout` -> `run-build` -> `pack` and is scaffolded into new
components the same way existing build Pipelines are today. The file the
developer edits, `.tekton/push.yaml`, is a Pipelines-as-Code PipelineRun.
The developer edits only the fields named in "Developer-facing contract" --
never a Task, pod spec, or ServiceAccount.

Two different checks enforce that, because they see different objects:

- When the PipelineRun is created, the platform rejects a run that carries
  `taskSpec`, `taskRunSpecs`, or `podTemplate` (including
  `taskRunTemplate.podTemplate`), or a runtime override of `image`,
  `script-path`, `PLATFORM`, or a `*_ARTIFACT` param. Those fields change
  how a trusted Task executes, and they are not part of the Task digest.
  Pipelines as Code may still set the repository URL and revision; those
  must match the fetched revision.
- At the Conforma release gate, one shared policy reads the signed Tekton
  Chains predicate and applies a closed task allowlist. "On the trusted-task
  list" is not the check: that list also contains privileged catalog Tasks
  such as `buildah`.

### Trust model

**Owned by Konflux, never user-supplied, never admits user override:**

- Source checkout, from the revision Pipelines as Code (or equivalent)
  resolved -- the Source L4 revision.
- The generic Task that runs a build step (working name `run-build`, with a
  `run-build-remote` variant for multi-platform VM builds). Konflux fixes
  `volumes`, `sidecars`, and `stepTemplate`. The Task also fixes its runtime
  confinement: `automountServiceAccountToken: false`, a non-root
  `runAsUser`, capabilities dropped, and a `command`/`args` that exec the
  script with the image entrypoint cleared. `script-path` is resolved under
  the extracted source tree; an absolute path or a `..` component is
  rejected by the Task.
- Developer-editable params on that Task are `image` and `script-path`
  only. `run-build-remote` also takes `PLATFORM`, which is the
  multi-platform controller's contract parameter
  ([multi-platform controller](../architecture/add-ons/multi-platform-controller.md)),
  not a build-logic param. Platform-owned params are also present and are
  not editable build logic: each `*_ARTIFACT` param (for example
  `SOURCE_ARTIFACT`) is wired by the Pipeline to the previous task's
  matching result. See "Data between tasks."
- `run-build` declares no workspace a PipelineRun can bind a Secret to.
  The developer image is not the step that mounts a platform secret. On
  the remote path, the secret `multi-platform-ssh-$(context.taskRun.name)`
  is mounted by the Konflux-owned step that opens SSH, and the developer
  image runs only inside that step's `podman` invocation.
- The execution environment. In-cluster builds use an ephemeral pod and
  `run-build`. Other platforms use `run-build-remote` on a VM created for
  that TaskRun and destroyed when it finishes. See "Isolation."
- Output packaging: a Konflux task packs a declared output directory into the
  OCI Component Build Artifact, pushes it, and emits its reference and
  digest as Tekton Results (`IMAGE_URL`/`IMAGE_DIGEST`, the existing
  Konflux/Chains convention) -- Chains reads these to know what artifact to
  attach provenance to ([ADR-0063](./0063-generalized-build-release-pipelines.md)).
  **Only `pack` emits these results** -- `run-build`/`run-build-remote`
  don't produce the artifact, so they have nothing to report under those
  names, and emitting them there too would make Chains unable to tell
  which Task is the real subject when the escape hatch adds more than one
  `run-build` instance to a Pipeline. Everything else Chains needs from
  `run-build`/`run-build-remote` -- the `image`/`script-path` params, and
  the digest of the image actually used to run the step -- is captured
  automatically by Tekton/Chains without any Result declaration.
- `pack` documents `artifactType` (or `config.mediaType` where that is the
  right signal) for the Component Build Artifact, as
  [ADR-0063](./0063-generalized-build-release-pipelines.md) requires. For a
  format Konflux does not already document, `artifactType` is a literal in
  the reviewed PipelineRun. When the package ecosystem has an SBOM
  standard, `pack` emits that SBOM, so the SBOM does not add another task
  identity to the allowlist.
- Provenance generation and signing (Tekton Chains). The signing key and the
  ability to write PipelineRun/TaskRun status are never reachable from the
  environment that runs the developer's script.

**Supplied by the developer, reviewed only by the existing two-party source
review:**

- A build script at a path in the component repo (Konflux default:
  `./build.sh`; a developer-chosen path works too, by editing the Pipeline).
  The path is relative to the source tree.
- Optionally, by editing the committed PipelineRun directly: a different
  `image` (pinned by digest) and/or `script-path`, additional `run-build` /
  `run-build-remote` instances (any number) with `runAfter` ordering and
  `*_ARTIFACT` result wiring, and `artifactType` on `pack` when the format
  is new.

**Why no catalog review is required:** SLSA Build L3's accuracy guarantee is
about what the *control plane* can prove (isolation, unforgeable provenance),
not about pre-approval of build logic -- see "Evidence from the SLSA spec"
below. SLSA Source L4's guarantee is two-person review of the revision. The
source repo's own required reviewers are that review for the build logic and
for any Pipeline edit, since both live in the same revision.

That coverage holds only for values that are literal strings in the
PipelineRun committed at that revision. A runtime override -- a patched
PipelineRun, or a param PaC did not take from that file -- is a way for an
external party to influence the build. Build L3 requires `externalParameters`
to be complete, so an override that Chains does not record breaks the claim,
and an override that Chains does record is still outside the reviewed
revision. The platform rejects those overrides when the PipelineRun is
created. Pipelines as Code may still set the source-identity params (repository
URL and revision). Those are recorded in the predicate and must match the
fetched revision. There is no separate resolver call for `image` or
`script-path`: they are literals in the reviewed PipelineRun.

**Why not a developer-authored Task.** If the developer could author the
Task itself, they would control three fields no param-exposure discipline
can fix after the fact:

- `volumes` -- what storage backs a mount; a Task author can bind
  `hostPath`.
- `sidecars` -- a separate Task-level field, long-running containers with
  their own `securityContext`/`volumeMounts`.
- `stepTemplate` -- Task-level defaults merged into every step (`env`,
  `volumeMounts`, `securityContext`, `workingDir`).

So the Task is always the one Konflux publishes, with those three fields
fixed. The developer's editable surface is the PipelineRun in
`.tekton/push.yaml`, and a PipelineRun is larger than a PipelineTask.
A PipelineTask entry has `taskRef`, `params`, `workspaces`, `runAfter`,
`matrix`, and `when`. It can also carry `taskSpec` instead of `taskRef`,
and a `taskSpec` can set `volumes`, `sidecars`, and `stepTemplate` -- the
same three fields. The PipelineRun can also set `spec.taskRunSpecs[]`
(`podTemplate`, `serviceAccountName`, `stepOverrides`) and `spec.params`
that override the literals in the Pipeline. `podTemplate` can set
`hostNetwork`, `hostPID`, and extra volumes. None of that is part of the
Task digest, so a Task that stays on a trusted-task list still runs under
the override. `workspaces` is security-sensitive for the same reason: a
PipelineRun binding can mount a Secret into a Task that declares one.

`taskSpec` is not a threat under this decision because an inline Task has
no bundle digest on the closed allowlist, and the PipelineRun is rejected
at creation if it contains one. The release gate rejects it again when the
predicate shows it. `taskRunSpecs` and `podTemplate` are rejected at
creation because they are pod-level overrides outside the Task digest; the
release gate also rejects a predicate that contains them, so a Chains
formatter that records `externalParameters.runSpec` cannot be bypassed by
skipping admission.

**The envelope.** A run stays inside the envelope -- and its artifact
qualifies for release -- when all of the following hold:

- It runs from the Source L4 revision Konflux fetched, and Source L4
  evidence is present through the ADR-0055 chain.
- The attested PipelineRun has no `taskSpec`, `taskRunSpecs`, or
  `podTemplate`.
- Every task uses a digest-pinned `taskRef` from the closed set in
  "Conforma verification." No other Task identity appears.
- `script-path` is a relative path under the source tree.
- `image` is pinned by digest, and that digest equals the step `imageID`
  recorded for the step that ran the developer image.
- `*_ARTIFACT` params are wired to the previous task's `*_ARTIFACT` result.
  There is no general-purpose workspace and no shared PVC.
- No credential capable of patching the PipelineRun/TaskRun, writing
  attestation-relevant fields, or reading the Chains signing key is
  available to the developer image.
- A remote build uses `run-build-remote` on a VM created for that TaskRun
  and destroyed afterward. Local platforms use in-cluster `run-build`.

A run leaving the envelope is **not** blocked from starting when the only
problem is one the release gate can see in the signed predicate (a
non-pinned `image`, a Task outside the allowlist, a broken artifact chain).
It executes, produces an artifact, and gets signed provenance like any other
build -- and then fails the Conforma release gate, so it cannot be promoted
or released. A PipelineRun that carries `taskSpec`, `taskRunSpecs`,
`podTemplate`, or a runtime param override is rejected at creation, because
those are not reliably visible as an attested influence. See "Conforma
verification" below.

Network access *during* the build (fetching dependencies) is inside the
envelope -- see Non-Goals. What's outside the envelope is access to
Konflux's own control plane and cross-build state, not access to the
internet.

### Data between tasks

`checkout`, `run-build` / `run-build-remote`, and `pack` are separate
TaskRuns. [ADR-0036](./0036-trusted-artifacts.md) (Implemented) passes files
between TaskRuns as OCI trusted artifacts: a producing task records the
archive location and digest in a result whose name ends in `_ARTIFACT`, and
the next task receives that reference as a param with the same suffix.
[ADR-0063](./0063-generalized-build-release-pipelines.md) requires component
build pipelines to transmit large data between tasks this way. A
general-purpose workspace is not accepted. A shared PVC is the shared-cache
case the envelope forbids.

`checkout` emits `SOURCE_ARTIFACT`. Each `run-build` / `run-build-remote`
consumes `SOURCE_ARTIFACT` and emits `SOURCE_ARTIFACT` for the tree after
the script. `pack` consumes the last one. The Pipeline wires each param to
the previous task's result. Those params are platform-owned: the developer
does not put build logic in them. Conforma checks that each consumed digest
equals the producing task's result. That chain is the critical path
[ADR-0063](./0063-generalized-build-release-pipelines.md) requires the
policy to verify: `checkout`, every `run-build` / `run-build-remote`, and
`pack`.

### Evidence from the SLSA spec

The Build L3 claims above -- in Context, and in "Why no catalog review is
required" -- are what the spec says at the lines cited. The Source L4
bullet is a reading of the two-party-review scope, and it is labeled as a
reading.

Quoted from [slsa-framework/slsa](https://github.com/slsa-framework/slsa) at
commit [`048a3c4`](https://github.com/slsa-framework/slsa/commit/048a3c411b3a892fc41092b6688bbee345b7b386)
(2026-10-13) -- line numbers below are only guaranteed to match that commit;
the spec's `predicateType` URI tracks the latest minor version and can move.

- `externalParameters` MUST be complete at Build L3 (no other way for an
  external party to influence the build) -- but completeness is about the
  *build's inputs being enumerated*, not about every artifact-producing
  byte originating from the reviewed revision.
  ([`spec/build-provenance.md:192-199`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/build-provenance.md#L192-L199))
- `resolvedDependencies` -- the record of what a build step fetches --
  is explicitly best-effort through Build L3. The spec's own example is a
  build script that fetches and executes another script.
  ([`spec/build-provenance.md:217-227`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/build-provenance.md#L217-L227))
- Build L3 isolation MUSTs: the build has no access to platform secrets, no
  cross-build influence, an ephemeral environment per build, and no cache
  poisoning, and remote influence is recorded in `externalParameters`.
  ([`spec/build-requirements.md:302-317`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/build-requirements.md#L302-L317))
- The same section distinguishes "Isolated" from "Hermetic." Isolation does
  not prohibit a build from calling out to a remote system outside the
  platform's trust boundary.
  ([`spec/build-requirements.md:322-332`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/build-requirements.md#L322-L332))
- "No extraneous dependencies used" (hermetic) and "all dependencies
  listed" are named as *future-direction*, not current Build L3/L4,
  requirements.
  ([`spec/future-directions.md:12-30`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/future-directions.md#L12-L30))
- Source L4's two-party review applies to the final revision submitted on
  the protected branch, including changes made during review
  ([`spec/source-requirements.md:471-473`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/source-requirements.md#L471-L473)).
  Those lines do not discuss bytes a build fetches later. Reading that
  scope together with the `resolvedDependencies` rule above: two-party
  review covers the revision Konflux fetched, and a dependency fetched at
  build time is a resolved dependency, not a second source review.
- SLSA's "minimize the number of trusted platforms" principle names this
  exact scenario: "instead of each team within an organization maintaining
  their own build platform, use a shared build platform." Backs why one
  shared Konflux-owned Task/policy is preferred over a per-component
  custom Pipeline and policy, not just that it's less work.
  ([`spec/principles.md:73-83`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/principles.md#L73-L83))

### Isolation

Build L3's isolation requirement is a stronger obligation than "not
hermetic." The MUSTs cited above (no platform secrets, no cross-build
influence, an ephemeral environment per build, no cache poisoning, remote
influence recorded in `externalParameters`) are part of this decision. The
"Isolated is not hermetic" note is the separate citation at lines 322-332.

Today's multi-platform host model does not meet that bar on every
configured host, and this decision does not claim that it does:

- Static hosts and dynamic pools set `concurrency` greater than 1. The
  controller tracks slots because the host does not, so overlapping builds
  can share a machine.
- `local-platforms` sets the secret's `host` to `localhost` and runs the
  Task in the pod. That path uses in-cluster `run-build`, not
  `run-build-remote`.
- On the remote path the TaskRun pod still exists. It holds the OTP secret
  and opens SSH. There is a Kubernetes pod, and its spec is part of the
  threat model for that step.

`run-build-remote` is allowed only on a VM created for that TaskRun and
destroyed when the TaskRun finishes, with rootless `podman`, no
`--privileged`, and no host mounts. The developer image runs only inside
that `podman` invocation, never as the step that mounts
`multi-platform-ssh-$(context.taskRun.name)`. Host configs that share a
machine across builds are not valid hosts for this Task.

### Developer-facing contract

**Default: a script at the conventional path.** The developer commits
`./build.sh` to the component repo. Konflux's default, unedited Pipeline
runs it with a Konflux-provided default build image and no Pipeline edit
required. This is the fast path.

**Escape hatch: editing the PipelineRun.** When the default image or script
path doesn't fit, or more than one build step is needed, the developer
edits the component's `.tekton/push.yaml` directly. Any number of extra
`run-build` / `run-build-remote` tasks is allowed. The fields they may
change are:

- `image` and `script-path` on a `run-build` / `run-build-remote`
  PipelineTask. `script-path` is a relative path. `image` is digest-pinned.
- `PLATFORM` on `run-build-remote`, when the step is a remote build.
- `runAfter`, and the `*_ARTIFACT` wiring that passes the previous task's
  result into the next task's `SOURCE_ARTIFACT` param.
- `artifactType` on `pack`, when the format is not one the default Pipeline
  already documents.

They may not add a `taskSpec`, `taskRunSpecs`, `podTemplate`, workspace
secret binding, or any other task identity. `taskRef` stays a digest-pinned
bundle from the closed set.

### Example

```
[konflux: checkout @ Source L4 revision]
        |
        |  SOURCE_ARTIFACT (OCI trusted artifact)
        v
[konflux: run-build]        <-- escape hatch: more instances possible,
        |                        absent by default
        |  SOURCE_ARTIFACT
        v
[konflux: pack -> OCI Component Build Artifact]
        |
[tekton chains: generate + sign provenance]
```

**Default: unedited Pipeline, script at the conventional path.**

```
my-component/
  build.sh                  # developer-supplied
  .tekton/
    push.yaml               # konflux default, unedited
```

No Pipeline edit. Konflux's default `push.yaml` already has a `run-build`
PipelineTask with its default `image` and `script-path: build.sh`.

**Escape hatch: a different image, and a second build step.**

```yaml
# .tekton/push.yaml (excerpt -- developer-edited PipelineRun)
spec:
  pipelineSpec:
    tasks:
      - name: checkout        # konflux-owned, unedited
        taskRef:
          resolver: bundles
          params:
            - name: bundle
              value: quay.io/konflux-ci/catalog/checkout@sha256:<trusted-task-digest>
            - name: name
              value: checkout
            - name: kind
              value: task
      - name: codegen
        runAfter: ["checkout"]
        taskRef:
          resolver: bundles
          params:
            - name: bundle
              value: quay.io/konflux-ci/catalog/run-build@sha256:<trusted-task-digest>
            - name: name
              value: run-build
            - name: kind
              value: task
        params:
          # platform-owned; wired to checkout's result, not build logic
          - name: SOURCE_ARTIFACT
            value: $(tasks.checkout.results.SOURCE_ARTIFACT)
          - name: image
            value: quay.io/my-tenant/codegen@sha256:5e6f7a8b...
          - name: script-path
            value: scripts/generate-bindings.sh
      - name: build
        runAfter: ["codegen"]
        taskRef:
          resolver: bundles
          params:
            - name: bundle
              value: quay.io/konflux-ci/catalog/run-build@sha256:<trusted-task-digest>
            - name: name
              value: run-build
            - name: kind
              value: task
        params:
          - name: SOURCE_ARTIFACT
            value: $(tasks.codegen.results.SOURCE_ARTIFACT)
          - name: image
            value: quay.io/my-tenant/python-builder@sha256:1a2b3c4d...
          - name: script-path
            value: build.sh
      - name: pack             # konflux-owned, unedited except artifactType
        runAfter: ["build"]
        taskRef:
          resolver: bundles
          params:
            - name: bundle
              value: quay.io/konflux-ci/catalog/pack@sha256:<trusted-task-digest>
            - name: name
              value: pack
            - name: kind
              value: task
        params:
          - name: SOURCE_ARTIFACT
            value: $(tasks.build.results.SOURCE_ARTIFACT)
```

`codegen` runs after `checkout` because it reads
`scripts/generate-bindings.sh` from that checkout. Both `codegen` and
`build` reference the same Konflux `run-build` bundle digest; the developer
varies `image`, `script-path`, `runAfter`, and the `SOURCE_ARTIFACT` result
reference. The digest in each `taskRef` is the one on the closed allowlist.
No Task, pod spec, or ServiceAccount is written by the developer.

### Conforma verification

The release gate reads the signed Chains predicate. It does not see the
cluster. The fields this policy uses are:

- Task identities and bundle digests, from the predicate's resolved
  dependencies (and from `externalParameters.runSpec` when the configured
  Chains formatter records the PipelineRun spec).
- The parameter values that influenced the run, from `externalParameters`
  (SLSA v1.0) or `invocation.parameters` (SLSA v0.2), including `image`,
  `script-path`, `PLATFORM`, and `*_ARTIFACT`.
- The step `imageID` Chains copies from the TaskRun status for the step
  that executed the developer image.
- `pack`'s `IMAGE_URL` and `IMAGE_DIGEST` results, which name the subject.

Pod-level overrides the configured formatter does not copy into that
predicate are not a release-gate check. They are rejected when the
PipelineRun is created.

**New Conforma policy** (this feature's release gate), used instead of
today's trusted-task-name policies for components that opt in. The opt-in
hook is the component's EnterpriseContractPolicy, selected by its
ReleasePlan. A policy that means "any trusted task" is weaker than today's
task-name rules: a component that opts in and still runs `buildah` must
fail.

The rules are one closed allowlist:

- Provenance shows `checkout`, at least one `run-build` or
  `run-build-remote`, and `pack` each ran, at pinned trusted digests.
- No other Task identity appears. Catalog names such as `buildah` or
  `prefetch-dependencies` are outside this build shape and fail this
  policy.
- The predicate shows no `taskSpec`, `taskRunSpecs`, or `podTemplate`.
- For each `run-build` / `run-build-remote`, `image` in the external
  parameters is digest-pinned and equals the recorded step `imageID`.
  `script-path` is a relative path.
- Each `*_ARTIFACT` param equals the producing task's `*_ARTIFACT` result.
  The critical path is `checkout`, every `run-build` / `run-build-remote`,
  and `pack`.
- **Source L4 check:** the source revision meets Source L4 through the
  [ADR-0055](./0055-slsa-source-provenance-verification.md) chain. Repository
  owners mint a Source VSA, and an integration-test task republishes it.
  A component whose forge cannot produce a VSA cannot release on this
  policy.
- A VM build used `run-build-remote` at its pinned digest, not an arbitrary
  external endpoint. The Task's fixed script is what ran `podman`; the
  digest pin is what confirms that script.

The Task requirements in the trust model (`automountServiceAccountToken`,
non-root `runAsUser`, dropped capabilities, entrypoint cleared, developer
image kept off the OTP secret) are enforced by that digest pin. They are
what Konflux puts in the Task before it is added to the allowlist, not a
second per-field scan of Task YAML at release time.

This policy is opt-in: existing catalog-pipeline components keep using
existing policies unless their ReleasePlan selects this one.

## Consequences

- A developer can add a new build tool or artifact type with no catalog PR
  and no platform review of the build logic itself -- just the default
  script path, or a PipelineRun edit, under the existing two-party source
  review.
- No developer, and no component, needs its own Conforma policy. One
  shared policy covers every build using this path. The policy is a closed
  allowlist of pinned digests for `checkout`, `run-build` /
  `run-build-remote`, and `pack`, which is stricter than "any task on the
  trusted-task list." It does not scan Task fields, because those are fixed
  inside the pinned digest. PipelineRun fields outside that digest are
  rejected when the PipelineRun is created.
- Every artifact produced this way still carries a valid Build L3
  attestation. Source L4 evidence is required through the ADR-0055 chain,
  the same chain a catalog-pipeline artifact uses when that policy is on.
  A component whose forge cannot mint a Source VSA cannot release on this
  policy.
- `run-build` and `run-build-remote` become new entries in Konflux's
  trusted-task catalog and must go through the normal trusted-task
  release and signing process before they can be placed on the allowlist.
  The default Pipeline that wires them together (`checkout` -> `run-build`
  -> `pack`), including the trusted-artifact params, is new published
  surface too, scaffolded into components the same way as other default
  Pipelines today. Both are new platform surface Konflux must build and
  maintain, even though no catalog PR is needed per build type.
- Pipeline Service must reject, at PipelineRun creation, a run that
  carries `taskSpec`, `taskRunSpecs`, or `podTemplate`, or a runtime
  override of `image`, `script-path`, `PLATFORM`, or a `*_ARTIFACT` param.
  Source-identity params that Pipelines as Code sets for the repository
  URL and revision are the exception, and they must match the fetched
  revision.
- `run-build-remote` needs a host model this decision can actually claim:
  one VM per TaskRun, destroyed afterward. Static hosts and dynamic pools
  with `concurrency` greater than 1 are not that model. Local platforms
  stay on in-cluster `run-build`.
- Builds under this path are not required to be hermetic. This is a
  compromise, not an oversight: `resolvedDependencies` completeness
  remains best-effort, consistent with SLSA Build L3 (see "Evidence from
  the SLSA spec"). Hermetic builds stay a separate initiative. Isolation
  is not waived with hermeticity.
- A run that leaves the trust envelope in a way the predicate records (a
  non-pinned image, a Task outside the allowlist, an unsupported artifact
  chain) is not blocked at admission -- it still executes and produces
  signed provenance, then fails at the Conforma release gate. This matches
  how hermetic/prefetch enforcement already works, but means an
  out-of-envelope run consumes build resources before it's caught, rather
  than being rejected upfront. Creation-time rejection is reserved for
  influences the predicate cannot be relied on to show.
- Defects or compromises in the developer's build script are caught only
  by the standard two-party source review, the same review already
  required for Source L4 -- there is no additional platform reviewer in
  the loop for this build logic specifically.

## Alternatives Considered

### Tekton `StepAction`, resolved natively via `ref:`

Initially attractive: Tekton's admission webhook already rejects a `Step`
that combines `ref` with inline `image`/`command`/`script`/`env`/
`volumeMounts`, which looked like free protection. Rejected once two
problems surfaced:

- That protection is scoped to the `Step` object, not the `Task` object the
  Step lives in -- see "Why not a developer-authored Task" under Decision
  for the fields (`volumes`, `sidecars`, `stepTemplate`) it leaves open.
  The same reasoning is why a developer-authored Task whose Steps are all
  `ref`-only doesn't work either: it's still a developer-authored Task.
- On a multi-platform VM build the TaskRun pod still exists: it mounts the
  OTP secret and opens SSH. The developer's build runs via `podman` on the
  VM, not as a step in that pod. Tekton's native `ref:` resolution only
  resolves content for a step the reconciler is about to create, and it
  does not pin that `podman` invocation. Making it work would have meant a
  second, different pinning mechanism (reading a StepAction-shaped file out
  of the workspace and parsing it by hand) for the VM path, while the
  on-cluster path kept using the resolver. A plain param-based Task needs
  no resolver on either path, since Pipeline param values are literal
  strings in the already-reviewed PipelineRun.

### Custom YAML manifest (commands/sidecars/output-dir), not Tekton-native

An earlier draft of this design invented a bespoke manifest format compiled
by Konflux into Tekton Tasks. Rejected as unnecessary complexity once it
was clear that a Konflux-owned Task with a couple of Pipeline-level params
(`image`, `script-path`) gives the same capability without a new schema to
design, document, or version.

### Accept arbitrary Tekton Pipelines or Tasks with inline steps, filtered at admission

Rejected: the envelope becomes a denylist over Tekton's entire API surface
(workspaces, `stepTemplate`, `sidecars`, resolver params, podTemplate
overrides, inline `volumeMounts`, ...) -- every missed field is a
trust-boundary hole.

## Open Questions

- Exact name and ownership of `run-build` / `run-build-remote`, and the
  default Pipeline that wires them into `checkout` -> `run-build` -> `pack`
  -- all need a home in the build-definitions/build-templates catalog,
  presumably, alongside existing Tasks and Pipelines. `run-build`/
  `run-build-remote` additionally need to go through the normal
  trusted-task release and signing process so the Conforma check in
  "Conforma verification" has something to check against.
- What the Konflux default build image should be for the "no Pipeline edit"
  fast path -- likely a minimal generic image (e.g. UBI-minimal), given
  this feature's whole premise is supporting build tools Konflux doesn't
  already have a catalog image for.
- Relationship to Konflux's user-facing platform contract work: this
  feature's contract should be proposed as a concrete "may" entry in that
  contract's taxonomy, not decided independently of it.

## References

- [ADR-0036](./0036-trusted-artifacts.md) -- Trusted Artifacts
- [ADR-0053](./0053-trusted-task-model.md) -- Trusted Task model
- [ADR-0055](./0055-slsa-source-provenance-verification.md) -- SLSA Source Provenance Verification
- [ADR-0063](./0063-generalized-build-release-pipelines.md) -- Generalized Build and Release Pipelines
- [Enterprise Contract](../architecture/core/enterprise-contract.md) -- a specific result from a specific trusted task
- [Multi-platform controller](../architecture/add-ons/multi-platform-controller.md) -- `PLATFORM`, OTP secret, host concurrency
- [Tekton StepActions docs](https://tekton.dev/docs/pipelines/stepactions/) -- considered and rejected, see "Alternatives Considered"
- [slsa-framework/slsa](https://github.com/slsa-framework/slsa) -- SLSA spec, quoted at commit [`048a3c4`](https://github.com/slsa-framework/slsa/commit/048a3c411b3a892fc41092b6688bbee345b7b386)
