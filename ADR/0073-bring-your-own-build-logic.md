---
title: "73. Bring-Your-Own Build Logic with SLSA Build L3 / Source L4"
status: Proposed
applies_to:
  - build-service
  - enterprise-contract
  - multi-platform-controller
topics:
  - build
  - slsa
  - provenance
  - tekton
  - trusted-tasks
---

# 73. Bring-Your-Own Build Logic with SLSA Build L3 / Source L4

Design for letting Konflux users add a new build tool or artifact type
quickly -- by supplying a build image and a script, directly or via a
Pipeline edit -- without a platform catalog review or a new Conforma
policy, while every resulting artifact still carries a valid SLSA Build L3
and Source L4 claim.

Date: 2026-10-19

## Status

Proposed

## Context

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
- Every artifact produced this way carries a Build L3 and Source L4
  attestation, verifiable the same way as a catalog-pipeline artifact.
- The existing two-party source review (already required for Source L4) is
  the only human review the build logic needs.

### Non-Goals

- **Hermetic execution.** This feature does not require or guarantee that the
  build only used bytes from the fetched revision. The build may fetch
  dependencies over the network, same as any other SLSA Build L3 build.
  `resolvedDependencies` completeness is best-effort, as the SLSA spec
  allows through Build L3. Hermetic builds are a separate, pre-existing
  Konflux initiative and orthogonal to this one.
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
components the same way existing build Pipelines are today. The developer
edits only Pipeline-level params and ordering -- never a Task, pod spec, or
ServiceAccount. Compliance with the trust envelope is verified entirely at
the Conforma release gate, reusing Konflux's existing trusted-task
mechanism, rather than through a new admission-time check or a new policy
per component.

### Trust model

**Owned by Konflux, never user-supplied, never admits user override:**

- Source checkout, from the revision Pipelines as Code (or equivalent)
  resolved -- the Source L4 revision.
- The generic Task that runs a build step (working name `run-build`, with a
  `run-build-remote` variant for multi-platform VM builds): its `volumes`,
  `sidecars`, and `stepTemplate` are fixed by Konflux, and the only params it
  exposes are `image` and `script-path` (and, for the remote variant,
  `platform`). See "Why not a developer-authored Task" below for why this
  matters.
- The execution environment: an ephemeral pod, or (for other platforms) a VM
  provisioned by the multi-platform controller, with `run-build`/
  `run-build-remote` doing the execution.
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
- Provenance generation and signing (Tekton Chains). The signing key and the
  ability to write PipelineRun/TaskRun status are never reachable from the
  environment that runs the developer's script.

**Supplied by the developer, reviewed only by the existing two-party source
review:**

- A build script at a path in the component repo (Konflux default:
  `./build.sh`; a developer-chosen path works too, by editing the Pipeline).
- Optionally, by editing the committed Pipeline directly: a different
  `image` (pinned by digest) and/or `script-path` param value, or additional
  `run-build` instances for a multi-step build.

**Why no catalog review is required:** SLSA Build L3's accuracy guarantee is
about what the *control plane* can prove (isolation, unforgeable provenance),
not about pre-approval of build logic -- see "Evidence from the SLSA spec"
below. SLSA Source L4's guarantee is two-person review of the revision. The
source repo's own required reviewers are that review for the build logic and
for any Pipeline edit, since both live in the same revision -- and since the
`image`/`script-path` values are literal strings in that same reviewed
Pipeline, that review already covers exactly what will run. No separate
resolver call or declarative file to cross-reference.

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
fixed and only `image`/`script-path`/`platform` exposed as params. The
developer's only editable surface is the Pipeline, which carries none of
those fields itself -- a `PipelineTask` entry has `taskRef`, `params`,
`workspaces`, `runAfter`, `matrix`, `when`, nothing security-sensitive.

**The envelope.** A run stays inside the envelope -- and its artifact
qualifies for release -- when it only ever touches things Konflux owns:

- Runs from the Source L4 revision Konflux fetched.
- The `image` param value is pinned by digest, not a mutable tag.
- Every Pipeline `taskRef` resolves to a Konflux-pinned Task (`run-build`,
  `run-build-remote`, or another fixed Konflux Task) -- never a Task the
  developer defines.
- No `privileged`, `hostPath`, `hostPID`, or shared-cache volume anywhere
  in the resolved Pipeline/Task graph.
- No credential capable of patching the PipelineRun/TaskRun, writing
  attestation-relevant fields, or reading the Chains signing key.
- Any VM used for the build is provisioned by the Konflux multi-platform
  controller, and the thing that executes the script on it is the
  Konflux-owned `run-build-remote` Task -- not an arbitrary remote machine.

A run leaving the envelope is **not** blocked from starting. It executes,
produces an artifact, and gets signed provenance like any other build --
and then fails the Conforma release gate, so it cannot be promoted or
released. See "Conforma verification" below.

Network access *during* the build (fetching dependencies) is inside the
envelope -- see Non-Goals. What's outside the envelope is access to
Konflux's own control plane and cross-build state, not access to the
internet.

### Evidence from the SLSA spec

The claims above -- in Context, and in "Why no catalog review is
required" -- that Build L3 and Source L4 don't require platform review of
build logic aren't an interpretation; they're what the spec says directly.
Here's where they come from.

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
- Build L3's isolation requirement explicitly does *not* prohibit a build
  from calling out to a remote system outside the platform's trust
  boundary, and explicitly distinguishes "Isolated" from "Hermetic."
  ([`spec/build-requirements.md:317-331`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/build-requirements.md#L317-L331))
- "No extraneous dependencies used" (hermetic) and "all dependencies
  listed" are named as *future-direction*, not current Build L3/L4,
  requirements.
  ([`spec/future-directions.md:12-30`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/future-directions.md#L12-L30))
- Source L4's two-party review requirement is scoped to the final revision
  submitted on the protected branch -- it does not extend to artifacts a
  build process fetches at build time.
  ([`spec/source-requirements.md:471-472`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/source-requirements.md#L471-L472))
- SLSA's "minimize the number of trusted platforms" principle names this
  exact scenario: "instead of each team within an organization maintaining
  their own build platform, use a shared build platform." Backs why one
  shared Konflux-owned Task/policy is preferred over a per-component
  custom Pipeline and policy, not just that it's less work.
  ([`spec/principles.md:73-83`](https://github.com/slsa-framework/slsa/blob/048a3c411b3a892fc41092b6688bbee345b7b386/spec/principles.md#L73-L83))

### Developer-facing contract

**Default: a script at the conventional path.** The developer commits
`./build.sh` to the component repo. Konflux's default, unedited Pipeline
runs it with a Konflux-provided default build image and no Pipeline edit
required. This is the fast path.

**Escape hatch: editing the Pipeline.** When the default image or script
path doesn't fit, or more than one build step is needed, the developer
edits the component's `.tekton/` Pipeline directly:

- Override the `image` and/or `script-path` params on the existing
  `run-build` `PipelineTask` entry.
- Add more `PipelineTask` entries, each a `taskRef` to the same Konflux
  `run-build` Task, varying only `image`/`script-path` and `runAfter`
  ordering, for a multi-step build.

Neither path lets the developer write a Tekton Task, a pod spec, or a
ServiceAccount -- editing is limited to params and ordering on
Konflux-pinned `taskRef`s.

### Example

```
[konflux: checkout @ Source L4 revision]
        |
[konflux: run-build]        <-- escape hatch: more instances possible,
        |                        absent by default
        |
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
`PipelineTask` with its default `image` and `script-path: build.sh`.

**Escape hatch: a different image, and a second build step.**

```yaml
# .tekton/push.yaml (excerpt -- developer-edited Pipeline)
spec:
  tasks:
    - name: checkout        # konflux-owned, unedited
      taskRef: {resolver: ..., params: [...]}
    - name: codegen
      taskRef: {resolver: ..., params: [{name: name, value: run-build}]}
      params:
        - name: image
          value: quay.io/my-tenant/codegen@sha256:5e6f7a8b...
        - name: script-path
          value: scripts/generate-bindings.sh
    - name: build
      runAfter: ["codegen"]
      taskRef: {resolver: ..., params: [{name: name, value: run-build}]}
      params:
        - name: image
          value: quay.io/my-tenant/python-builder@sha256:1a2b3c4d...
        - name: script-path
          value: build.sh
    - name: pack             # konflux-owned, unedited
      runAfter: ["build"]
      taskRef: {resolver: ..., params: [...]}
```

Both `codegen` and `build` reference the same Konflux `run-build` Task; the
developer only varies `image`, `script-path`, and `runAfter` ordering. No
Task, pod spec, or ServiceAccount is written by the developer.

### Conforma verification

Every check for staying inside the envelope runs at
the Conforma release gate, against the signed provenance Chains already
produced.

**New Conforma policy** (this feature's release gate), used instead of
today's trusted-task-name policies for these artifacts:

- **Trusted-task check (reused, not new).** Every Task identity/digest that
  ran -- `run-build`/`run-build-remote`, checkout, pack -- must be on
  Konflux's existing trusted-task list ([ADR-0053](./0053-trusted-task-model.md)).
  This is the same mechanism that already stops a substituted Task; no new
  logic, just the existing rule applied to these Task names. Since the
  fixed Konflux Tasks never set `privileged`/`hostPath`/`hostPID`/a
  shared-cache volume, and the developer can only vary Pipeline-level
  params (never Task content), this one check is what rules out the
  breakout surface, rather than a separate per-field scan.
- **`image` param is digest-pinned,** for every `run-build`/
  `run-build-remote` instance recorded in provenance's `externalParameters`
  -- not a mutable tag.
- **Source L4 check:** the source revision referenced meets Source L4,
  verified against the SCS's Source VSA or equivalent evidence.
- **Platform check:** a VM build, if any, used the Konflux
  `run-build-remote` Task, not an arbitrary external endpoint.
- Does **not** check for specific catalog task names (`buildah`,
  `prefetch-dependencies`, etc.) -- those are irrelevant to this build
  shape and would fail it today under existing policies.

This policy is additive: existing catalog-pipeline components keep using
existing policies unless they opt into this path.

For the VM path specifically: there is no Kubernetes object the way a
PodSpec is at all. The isolation guarantee there rests on review of
`run-build-remote`'s fixed, Konflux-authored script (hardcoded `podman run`
flags, SSH key never exposed to the container that runs the developer's
image) -- the trusted-task check above confirms that script, and no other,
is what ran.

## Consequences

- A developer can add a new build tool or artifact type with no catalog PR
  and no platform review of the build logic itself -- just the default
  script path, or a Pipeline edit, under the existing two-party source
  review.
- No developer, and no component, needs its own Conforma policy. One
  shared policy -- reusing the existing trusted-task mechanism
  ([ADR-0053](./0053-trusted-task-model.md))
  rather than inventing new per-field checks -- covers every build using
  this path.
- Every artifact produced this way still carries a valid Build L3 and
  Source L4 attestation, verifiable the same way as a catalog-pipeline
  artifact.
- `run-build` and `run-build-remote` become new entries in Konflux's
  trusted-task catalog and must go through the normal trusted-task
  release and signing process. The default Pipeline that wires them
  together (`checkout` -> `run-build` -> `pack`) is new published surface
  too, scaffolded into components the same way as other default Pipelines
  today. Both are new platform surface Konflux must build and maintain,
  even though no catalog PR is needed per build type.
- Builds under this path are not required to be hermetic. This is a
  compromise, not an oversight: `resolvedDependencies` completeness
  remains best-effort, consistent with SLSA Build L3 (see "Evidence from
  the SLSA spec"). Hermetic builds stay a separate initiative.
- A run that leaves the trust envelope (a non-pinned image, a Task not on
  the trusted list, an unsupported Pipeline shape) is not blocked at
  admission -- it still executes and produces signed provenance, then
  fails at the Conforma release gate. This matches how hermetic/prefetch
  enforcement already works, but means an out-of-envelope run consumes
  build resources before it's caught, rather than being rejected upfront.
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
- Multi-platform VM builds don't schedule a Kubernetes pod at all (the
  build runs via SSH + `podman` on a remote machine), so Tekton's native
  `ref:` resolution -- which only resolves content for a pod the Tekton
  reconciler is about to create -- has nothing to attach to there. Making
  it work would have meant a second, different pinning mechanism (reading
  a StepAction-shaped file out of the workspace and parsing it by hand) for
  the VM path, while the on-cluster path kept using the resolver. A plain
  param-based Task needs no resolver on either path, since Pipeline param
  values are literal strings in the already-reviewed Pipeline YAML.

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
- How a Source VSA (or equivalent) is obtained/verified for SCSs that don't
  yet issue one, to feed the new Conforma policy's Source L4 check.
- Whether Pipeline edits for multi-step builds are fully free-form (any
  number/order of `run-build` instances) or the default Pipeline ships with
  a bounded number of optional slots.
- Relationship to Konflux's user-facing platform contract work: this
  feature's contract should be proposed as a concrete "may" entry in that
  contract's taxonomy, not decided independently of it.

## Related

- [ADR-0036](./0036-trusted-artifacts.md) -- Trusted Artifacts
- [ADR-0053](./0053-trusted-task-model.md) -- Trusted Task model
- [ADR-0063](./0063-generalized-build-release-pipelines.md) -- Generalized Build and Release Pipelines
- [Tekton StepActions docs](https://tekton.dev/docs/pipelines/stepactions/) -- considered and rejected, see "Alternatives Considered"
- [slsa-framework/slsa](https://github.com/slsa-framework/slsa) -- SLSA spec, quoted at commit [`048a3c4`](https://github.com/slsa-framework/slsa/commit/048a3c411b3a892fc41092b6688bbee345b7b386)
