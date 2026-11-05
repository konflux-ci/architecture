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
---

# 73. Bring-Your-Own Build Logic with SLSA Build L3 / Source L4

Date: 2026-10-19

Updated: 2026-11-06

## Status

Proposed

A proof of concept is available in
[byob-pipeline at `ef146c8`][implementation]. This ADR describes its build
contract and distinguishes implemented controls from the platform integration
still required for SLSA Build L3 and Source L4. The catalog alone does not
establish either level.

## Context

Adding a new build tool or artifact type to Konflux normally means adding
Tekton Tasks and a Pipeline to the shared catalog, followed by platform
review. A fully custom Pipeline also needs an approved Conforma policy
before its output can release. Repeating that work for each tool makes it
slow to introduce Python wheels, binaries, or other non-container payloads.

Konflux already separates platform controls from build logic
([ADR-0053](./0053-trusted-task-model.md),
[ADR-0063](./0063-generalized-build-release-pipelines.md)).
Build L3 depends on isolation and unforgeable provenance; Source L4 depends
on SCM controls and source review. Neither requires platform review of
each build script. SLSA's "minimize the number of trusted platforms"
principle supports a shared execution boundary and policy rather than a
different build platform per component.

### Goals

- Let developers supply a build command and image through a committed
  PipelineRun, without authoring a Task or requesting catalog review of
  the build logic.
- Provide a conventional `./build.sh` fast path, plus local, remote,
  multi-platform, and chained builds using the same build contract.
- Publish arbitrary build-output files inside one documented OCI format,
  so adding a payload format does not require a new packaging Task.
- Reuse one platform-maintained Conforma policy for this build shape.
  The prototype policy currently permits only the default builder image
  and OCI artifact type; broader image support remains integration work.
- Support Build L3 when the deployment supplies the isolation, admission,
  and signed-provenance controls below. Require Source L4 evidence through
  [ADR-0055](./0055-slsa-source-provenance-verification.md) before release.
  Build completion alone proves neither requirement.

### Non-Goals

- **Hermetic execution.** Builds may fetch dependencies. Completeness of
  `resolvedDependencies` is best-effort through Build L3; hermetic builds
  remain a separate initiative. Isolation is still required.
- **Developer-authored build Tasks.** The editable surface is the Pipeline
  and the permitted parameters of platform-owned Tasks, not arbitrary
  inline steps, pod specifications, sidecars, or volume definitions.
- **Provisioning the platform.** The catalog does not install Konflux,
  configure production admission, provision or destroy VMs, generate a
  Source VSA, or operate a release destination.
- Redefining Konflux's user-facing platform contract. This is a concrete
  candidate for its "may" layer.

## Decision

Use platform-owned `run-build` and `pack` Tasks, with a generated
`run-build-remote` variant. The default sequence is `checkout` ->
`run-build` -> `pack`. Developers commit an executable `build.sh` and
write deliverables to `$BUILD_OUTPUT`. They can edit their component's
`.tekton/push.yaml` PipelineRun to select another executable or image,
add build Tasks, or use a platform matrix.

The proof of concept provides four [Pipelines][pipelines]:

- `byob`: checkout, in-cluster build, and pack.
- `byob-remote`: checkout, controller-selected build, and pack.
- `byob-matrix`: one controller-selected build per `PLATFORM`, then one pack.
- `byob-chained`: code generation followed by a build, with explicit
  output-artifact inputs.

Development Pipelines reference namespace-installed build and pack Tasks;
checkout already uses an upstream bundle pinned by digest. The
[Pipelines-as-Code example][pac] embeds the matrix Pipeline and has
placeholders for published build and pack bundle digests. Publishing those
bundles, approving their identities, and scaffolding this into Konflux
components are separate integration steps.

### Trust model

**Owned by the platform:**

- **Checkout.** The pinned upstream `git-clone-oci-ta` Task checks out the
  requested exact commit and reports `SOURCE_ARTIFACT`,
  `CHAINS-GIT_URL`, and `CHAINS-GIT_COMMIT`. SCM review and a Source VSA
  for that commit remain external requirements.
- **Build Task definitions.** The platform fixes steps, volumes, mounts,
  and security contexts. Trusted steps restore inputs, prepare the
  workspace, validate outputs, and export Trusted Artifacts. The
  developer image runs only the requested executable and arguments.
- **Credential separation.** Registry credentials are mounted only in
  trusted restore/export/publish steps. Controller SSH credentials are
  mounted only in trusted controller/remote steps. The developer step
  mounts the source, work directory, and its output volume.
- **Execution confinement.** Developer code runs as UID 1000, with
  privilege escalation disabled and all capabilities dropped. A fixed
  preparation step runs as root with `CHOWN` to initialize empty volumes;
  this exception does not run developer code. The example `byob-build`
  ServiceAccount disables token automount. Selection of that account and
  restrictions on run-level overrides must be enforced by the platform.
- **Output publication.** Only `pack` emits `IMAGE_URL` and
  `IMAGE_DIGEST`. These name the final OCI manifest for Chains and the
  Snapshot, following
  [ADR-0063](./0063-generalized-build-release-pipelines.md).
  Build Tasks emit `BUILD_ARTIFACT` for intermediate outputs.
- **Provenance and signing.** Chains runs outside the developer workload.
  The deployment must keep signing keys and permission to change
  TaskRun/PipelineRun status out of build workloads.

The trusted operations use a shared Go CLI. `run-build-remote` is generated
from the local Task and adds controller routing, remote execution, image
recording, and platform metadata. The checked-in CLI image reference is
`localhost/byob-cli:devel`; a production deployment must publish and pin
that image and its Task bundles before trusting them.

**Supplied by the developer in the reviewed component revision:**

- `image`: a builder image containing the executable and its runtime.
  Production acceptance requires an approved immutable digest.
- `build-cmd`: an argv array, defaulting to `["./build.sh"]`.
- `build-args`: an argv array appended to `build-cmd`, defaulting to `[]`.
- Additional `run-build` / `run-build-remote` PipelineTasks, their
  dependencies, and output-artifact wiring.
- `PLATFORM` or a platform matrix when using `run-build-remote`.

These parameters are supported by the Tasks. Acceptance by admission and
Conforma is a separate condition; the prototype policy does not yet accept
arbitrary builder images or every command form.

**Why no catalog review of build logic is required.** The platform reviews
the fixed execution boundary once. Component reviewers review the command,
script, and PipelineRun as source. Production admission must ensure the
execution plan matches those reviewed literals, apart from approved
source-identity values supplied by Pipelines as Code. A runtime change
that Chains records is still outside that reviewed revision.

**Why not a developer-authored build Task.** A Task author controls
`volumes`, `sidecars`, and `stepTemplate`, including mounts and security
contexts. A trusted task name does not constrain an inline `taskSpec` or
run-level pod/step overrides. Production admission must reject inline build
Tasks, replacement steps, extra pod templates, unauthorized accounts, and
credential bindings outside the approved checkout path. Resource requests
and limits in `taskRunSpecs` are permitted; the presence of
`taskRunSpecs` alone is not a violation.

### Data between tasks

The catalog uses [Trusted Artifacts](./0036-trusted-artifacts.md) for
cross-TaskRun file transfer, with digest-bearing OCI references in results
and parameters. It does not share a source PVC between build Tasks.

`checkout` emits the original `SOURCE_ARTIFACT`. Every build in the
published Pipelines restores that same checkout at `/var/source`.
A build does not export a modified source tree. Its optional
`BUILD_ARTIFACTS` array restores preceding outputs separately:

- `codegen=$(tasks.codegen.results.BUILD_ARTIFACT)` restores under
  `$BUILD_INPUTS/codegen/out/`.
- Bare references restore under numeric directories starting at
  `$BUILD_INPUTS/0/out/`.
- An array must use either named entries throughout or bare entries
  throughout; duplicate names are rejected.

The command runs from `/var/source`, with writable `HOME` and
`BUILD_INPUTS` under `/var/workdir`. `BUILD_OUTPUT` is an initially empty
directory at `/var/byob/output`, on a volume separate from the checkout.
The developer must put at least one regular file there. A repository
directory named `out/` is not implicitly published.

After the command succeeds, a trusted step validates `BUILD_OUTPUT` and
copies it into a separate export volume that the developer step does not
mount. The resulting `BUILD_ARTIFACT` contains `out/` and, for the
controller-enabled Task, trusted `.konflux-platform` metadata. Validation
rejects special files, an output root that is a symlink, and links that
escape the output tree. Source files and caches are not exported unless
the build explicitly copies them into its output.

A chained build receives earlier outputs through `BUILD_INPUTS` and must
copy any files it wants to retain into its own `BUILD_OUTPUT`.
The final `pack` Task consumes an array of `BUILD_ARTIFACTS`. It selects
the archive layout from the references:

- One bare reference: files at the archive root.
- Several bare references: directories derived from trusted platform
  markers, such as `linux-amd64/` and `linux-arm64/`. Result ordering is
  not used to identify a platform.
- Named references: one directory per supplied task label.

`pack` publishes one OCI artifact per PipelineRun, with
`artifactType: application/vnd.konflux.build-output.v1` and exactly one
layer named `payload.tar.gz`, with media type
`application/vnd.oci.image.layer.v1.tar+gzip`. The Snapshot identifies its
manifest digest. A new payload format, such as wheels or binaries, can use
this same envelope. Although the Task exposes `artifactType`, changing it
is rejected by the current sample policy. `pack` does not generate an SBOM;
a build may include an SBOM among its output files.

### Private source checkout

All four Pipelines declare an optional `git-auth` workspace and map it
only to checkout's `basic-auth` workspace, following the Konflux build
Pipeline pattern. A PipelineRun binds a namespace
`kubernetes.io/basic-auth` Secret by name; it does not contain credentials.
Build Tasks declare no workspace that can receive this binding.

Trusted preparation scrubs Git authentication configuration from the
restored source before developer code runs. Git credentials must not be
forwarded to build Tasks, remote VMs, or output-artifact handoffs.
Production Conforma admission must approve both the Git URL and the Secret
reference. The repository supplies an example binding, not that admission
integration.

### Evidence from the SLSA spec

These citations explain the intended Build L3 and Source L4 boundary;
they do not establish that the prototype or a deployment meets it. The
Source L4 bullet is a reading of the two-party-review scope and is labeled
as a reading.

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

### Isolation and remote execution

The generated `run-build-remote` Task consumes the controller's
`multi-platform-ssh-$(context.taskRun.name)` Secret. If its host is
`localhost`, a conditional `build-local` step runs the developer image
in the Task pod. Otherwise, a trusted `build-remote` step opens SSH and
runs the developer image inside rootless Podman on the VM. The developer
image never runs as the step mounting the SSH Secret.

The remote implementation verifies controller-supplied host keys, supports
a controller key or a TLS-protected OTP exchange, and copies source and
build inputs into the container rather than mounting host directories.
It disables Podman's automatic host-secret mounts with
`--default-mounts-file=/dev/null`, drops capabilities, disables privilege
escalation, and uses UID 1000. It returns only `BUILD_OUTPUT` to the Task
pod for validation and export. Developer images must be pullable without
forwarded registry credentials.

The Task also emits `BUILD_IMAGE_ARTIFACT_INPUTS`, an object containing
the builder URI and digest. For a VM it records the digest Podman
observed; for the local route it records the requested immutable image.
A production Chains configuration and policy must capture and verify
this evidence. A Task pod's own step image does not identify a developer
image executed inside remote Podman.

These mechanisms do not allocate or destroy VMs. Build L3 requires the
controller to provide a fresh, dedicated VM per TaskRun and remove it on
success, failure, or cancellation. Shared static hosts and overlapping
builds on pooled hosts do not meet this boundary. The CLI attempts to
clean up its container and temporary workspace; that is not a substitute
for controller-owned VM cleanup.

For local builds, the cluster must validate equivalent isolation between
developer and trusted steps, deny access to control-plane credentials and
other builds, and prevent status/provenance forgery. A matrix may mix local
and remote members only when both paths meet those requirements. The
catalog's non-root settings alone do not prove Build L3 isolation.

### Developer-facing contract

**Default.** Commit an executable `./build.sh` and write deliverables to
`$BUILD_OUTPUT`. The default image is the digest-pinned Konflux task-runner
image. The selected image must supply the executable and its dependencies;
it needs no BYOB CLI or shell unless the command itself requires one.

**Command execution.** `build-cmd` selects an executable and any fixed
leading arguments; `build-args` appends arguments. Each array element is
one argv entry, without shell parsing, on both local and remote paths.
The Task does not require the executable to be a script from the checkout;
it can be provided by the image. The sample policy is narrower: it
restricts `build-cmd` entries to source-relative `./...` paths without
`..` and requires a matching recorded step entrypoint.

**Pipeline edits.** Developers can select the Task's supported image,
command, arguments, dependencies, extra build inputs, and platform matrix
through their committed PipelineRun. The production policy must define
which values are approved. The Task definitions, accounts, credential
mounts, artifact-storage destinations, and runtime confinement remain
platform-owned. An approved `git-auth` binding is the only source
credential workspace in these Pipelines.

For example, the chained Pipeline uses the following build/pack excerpt.
The checkout task, Pipeline parameters, and results are omitted here;
the complete manifests are in the [implementation][pipelines].

```yaml
tasks:
- name: codegen
  taskRef:
    name: run-build
  params:
  - name: build-cmd
    value: ["./scripts/generate.sh"]
  - name: SOURCE_ARTIFACT
    value: $(tasks.checkout.results.SOURCE_ARTIFACT)
  - name: ociStorage
    value: $(params.oci-storage)
- name: build
  taskRef:
    name: run-build
  params:
  - name: build-cmd
    value: ["./build.sh"]
  - name: build-args
    value: ["--target", "release"]
  - name: SOURCE_ARTIFACT
    value: $(tasks.checkout.results.SOURCE_ARTIFACT)
  - name: BUILD_ARTIFACTS
    value:
    - codegen=$(tasks.codegen.results.BUILD_ARTIFACT)
  - name: ociStorage
    value: $(params.oci-storage)
- name: pack
  taskRef:
    name: pack
  params:
  - name: BUILD_ARTIFACTS
    value:
    - $(tasks.build.results.BUILD_ARTIFACT)
  - name: IMAGE
    value: $(params.output-image)
  - name: artifactType
    value: application/vnd.konflux.build-output.v1
```

Result references establish task dependencies. `build` reads generated
files at `$BUILD_INPUTS/codegen/out/` while running against the original
checkout. To publish a generated file, it copies it to `$BUILD_OUTPUT`.
The namespace Task references above match the development catalog;
production references must use approved immutable bundles.

### Release consumption

The `unpack-build-output` StepAction consumes
`registry/repository@sha256:<manifest-digest>` and an empty destination.
It checks the artifact type, the single payload layer's name and media
type, and the downloaded layer digest, then safely extracts the archive
while preserving its layout. The consuming release Task supplies the
destination volume and any registry-authentication or CA mounts.

This StepAction restores files; signature and policy verification must
happen before it is allowed to run. The [release demo][release-demo]
verifies the same manifest digest with Conforma, then unpacks and consumes
its files. It is an example Tekton release Pipeline, not a production
ReleasePlan integration.

Using a StepAction here does not open the build trust boundary to
developer-authored Tasks. The release Pipeline owns the consuming Task;
the alternative rejected below concerns the execution of arbitrary build
logic.

### Conforma verification

The proof of concept includes [Rego rules][policy] and a Konflux
[IntegrationTestScenario Pipeline][integration]. The integration service
supplies a Snapshot. For each image, `ec validate image` verifies the
Chains signature using the public key in `chains-public-key/cosign.pub`
and binds the attestation subject to that image digest before evaluating
the rules. The example ignores Rekor because its test cluster does not
publish transparency entries; it does not skip signature verification.

The current rules consume Chains SLSA v0.2 PipelineRun statements and
check:

- A catalog Pipeline name: `byob`, `byob-chained`, `byob-remote`, or
  `byob-matrix`.
- Checkout, at least one build Task, and pack are present; other task
  names/references are outside the closed build shape.
- Checkout uses the pinned upstream bundle, its URL and revision match
  Pipeline parameters and Git material, and its Git results agree.
- `pack` records the attested manifest digest and uses the Pipeline's
  output destination and the documented OCI artifact type.
- Build Tasks request the pinned default task-runner image. The command
  check looks for that image digest and an entrypoint matching the
  source-relative `build-cmd` in recorded step data.
- Each `SOURCE_ARTIFACT` is checkout's source or a build output in the
  same attestation. Each additional build input and pack input is a
  `BUILD_ARTIFACT` from a build Task in that attestation; named input
  labels are accepted. The published Pipelines use the original checkout
  as `SOURCE_ARTIFACT` throughout.
- Checkout and build handoffs use the Pipeline's `oci-storage`
  repository or its accepted tag/path forms.

The Pipeline emits the standard `TEST_OUTPUT` summary with successes,
failures, warnings, and a `SUCCESS`, `WARNING`, or `FAILURE` result,
prints the rule report, and fails unless the result is `SUCCESS` or
`WARNING`. System tests cover a passing resource override, a rejected
artifact-type change, and a rejected source artifact from another run.

**Production enforcement still required.** This sample is not the complete
release policy described by the goals:

- The local catalog rules recognize namespace references for build and
  pack; only checkout has a bundle-digest identity check. They do not yet
  enforce immutable build/pack bundles or generalize the builder-image
  allowlist. The PaC bundle example therefore needs corresponding policy
  integration.
- Admission must reject inline build Tasks and execution overrides before
  Task Pods start, while permitting resource requests/limits. It must
  approve source identity, image, command/arguments, platform and output
  settings, storage, accounts, and private-checkout URL/Secret bindings.
  The sample Rego rules evaluate provenance after the build; they do not
  implement this admission integration.
- Chains must record the final manifest, exact source identity, approved
  Task and image identities, and input/output-artifact chain. Remote image
  evidence from `BUILD_IMAGE_ARTIFACT_INPUTS` and matrix child TaskRuns
  must be captured and verified; the current recorded-step check does not
  verify the VM-reported image digest.
- Source L4 must be verified through the
  [ADR-0055](./0055-slsa-source-provenance-verification.md) Source VSA
  chain for the exact checked-out commit. SCM must preserve verifiable
  history, protect reviewed refs, require two distinct reviewers, and
  prevent self-approval. The build catalog and sample policy do not
  produce or validate that evidence.
- A production ReleasePlan must select a policy enforcing these
  requirements, including the existing trusted-task requirements of
  [ADR-0053](./0053-trusted-task-model.md), before release.

Checks needing the live execution plan belong at admission. Checks against
signed provenance and source evidence belong in integration/release
verification. A successful build, signed provenance alone, or a passing
prototype integration test must not be presented as a Build L3 / Source L4
claim without the remaining controls.

## Consequences

- New build logic fits inside reusable platform-owned Tasks. Changing the
  payload does not require a new Task or OCI envelope.
- Output-only handoffs keep checkout and caches out of intermediate build
  exports by default. Chained builds explicitly consume and retain earlier
  outputs; mutations to the checkout do not carry into the next build.
- Matrix builds produce one final OCI artifact with platform directories.
  Release Tasks consume that artifact by manifest digest using the unpack
  StepAction.
- The platform maintains the Tasks, CLI image, remote generator, Pipeline
  examples, bundle publication, and shared policy. The proof of concept
  does not yet supply automatic component scaffolding or complete
  production enforcement.
- Resource overrides are supported. Pod, step, account, or credential
  overrides need restrictions beyond a trusted Task identity.
- Private checkout needs an approved namespace Secret bound only to
  checkout, with no Git credential propagation into builds.
- Build L3 remains conditional on deployment isolation, admission, and
  Chains configuration. Source L4 remains conditional on SCM controls and
  a matching Source VSA. The ADR remains Proposed despite the prototype.
- Non-hermetic builds are permitted. Defects in build logic still depend
  on component review and testing; this design protects the platform and
  provenance boundary, not the correctness of arbitrary commands.

## Alternatives Considered

### Tekton StepActions as the developer build interface

Rejected for the build boundary. Tekton rejects a Step that combines
`ref` with inline execution fields, but the enclosing Task still controls
`volumes`, `sidecars`, and `stepTemplate`. That does not safely admit a
developer-authored Task. Native StepAction resolution also does not
describe the separate Podman invocation on a VM.

The implementation uses a StepAction for the narrower release operation
of restoring a verified build-output artifact into a platform-owned
consuming Task.

### Custom YAML manifest for commands, sidecars, and output directories

Rejected as an unnecessary schema and compiler. Task parameters already
express the executable, argv, image, and output-artifact inputs, while
fixed `BUILD_OUTPUT` defines what is exported.

### Arbitrary developer-authored build Pipelines or Tasks with inline steps

Rejected because safe execution would depend on a denylist over the
entire Tekton API: mounts, sidecars, templates, resolver parameters, and
runtime overrides. This design instead fixes the build Task definitions
and exposes a bounded parameter contract.

## Open Questions

- Which Konflux catalogs will own and publish the Tasks, CLI image,
  Pipelines, and release StepAction, and how will components receive the
  default PaC PipelineRun?
- How will production admission bind permitted literals and private-source
  Secret references to the reviewed PipelineRun, while allowing resource
  overrides?
- How will the shared policy support approved builder images and argv
  forms beyond the prototype's fixed task-runner image and source-relative
  command checks?
- Which Chains configuration and policy will verify immutable build/pack
  bundles, VM-recorded image identities, matrix child TaskRuns, and the
  complete artifact chain?
- How will controller deployments guarantee fresh VM allocation and cleanup
  on every completion path, and what evidence establishes equivalent
  isolation for the local route?
- How will the Source VSA chain and production ReleasePlan policy be wired
  for components opting into this build shape?
- How should this contract fit Konflux's user-facing platform contract
  taxonomy?

## References

- [Proof-of-concept implementation][implementation] -- snapshot used for this update
- [Pipeline manifests][pipelines] and [PaC bundle example][pac]
- [Conforma rules][policy] and [integration Pipeline][integration]
- [Release verification and unpack example][release-demo]
- [ADR-0036](./0036-trusted-artifacts.md) -- Trusted Artifacts
- [ADR-0053](./0053-trusted-task-model.md) -- Trusted Task model
- [ADR-0055](./0055-slsa-source-provenance-verification.md) -- SLSA Source Provenance Verification
- [ADR-0063](./0063-generalized-build-release-pipelines.md) -- Generalized Build and Release Pipelines
- [Enterprise Contract](../architecture/core/enterprise-contract.md)
- [Multi-platform controller](../architecture/add-ons/multi-platform-controller.md)
- [Tekton StepActions docs](https://tekton.dev/docs/pipelines/stepactions/)
- [slsa-framework/slsa](https://github.com/slsa-framework/slsa) -- spec quoted at commit [`048a3c4`](https://github.com/slsa-framework/slsa/commit/048a3c411b3a892fc41092b6688bbee345b7b386)

[implementation]: https://github.com/gbenhaim/byob-pipeline/tree/ef146c8ae3b907d9bfb2b842dc98f7e8023a4f7d
[pipelines]: https://github.com/gbenhaim/byob-pipeline/tree/ef146c8ae3b907d9bfb2b842dc98f7e8023a4f7d/pipelines
[pac]: https://github.com/gbenhaim/byob-pipeline/blob/ef146c8ae3b907d9bfb2b842dc98f7e8023a4f7d/examples/pac/push.yaml
[policy]: https://github.com/gbenhaim/byob-pipeline/blob/ef146c8ae3b907d9bfb2b842dc98f7e8023a4f7d/policy/rules/pipeline.rego
[integration]: https://github.com/gbenhaim/byob-pipeline/blob/ef146c8ae3b907d9bfb2b842dc98f7e8023a4f7d/examples/integration/byob-pipeline-policy.yaml
[release-demo]: https://github.com/gbenhaim/byob-pipeline/blob/ef146c8ae3b907d9bfb2b842dc98f7e8023a4f7d/examples/demo/release.yaml
