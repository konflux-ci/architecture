---
title: Enterprise Contract
eleventyNavigation:
  key: Enterprise Contract
  parent: Core Services
  order: 6
toc: true
overview:
  scope: "Policy enforcement, attestation validation, release gating"
  key_crds:
    - EnterpriseContractPolicy
  related_services:
    - release-service
    - integration-service
    - pipeline-service
  related_adrs:
    - "0036"
    - "0044"
    - "0049"
  key_concepts:
    - Rego policies
    - Conftest
    - signature verification
    - attestation checks
    - ec-cli
    - policy sources
---

# Enterprise Contract

## Overview

The Enterprise Contract (EC) ensures that container images produced by
Konflux meet clearly defined requirements before they are considered
releasable. When an image does not meet the requirements, the Enterprise
Contract produces a list of the reasons why so they can be addressed.

Enterprise Contract requirements fall into two categories:

- **Built-in requirements** — the container image is signed with a known
  and trusted key, and the image has an attestation also signed with a
  known and trusted key.
- **Rule-based requirements** — defined using
  [Rego](https://www.openpolicyagent.org/docs/latest/policy-language/),
  the [Open Policy Agent](https://www.openpolicyagent.org/) query
  language. These are evaluated against the content of the pipeline run
  attestation. Examples include verifying that tasks used in the pipeline
  run were defined in known and trusted task bundles, and that a defined
  set of tests were run with passing results.

The technique of checking for a specific task result from a specific
known and trusted task definition is a useful way to create robust
policy rules. The Rego language is flexible and expressive, so arbitrary
policy rules can be created based on anything exposed in the pipeline
run attestation.

## Goals

- Gate releases by enforcing supply chain security policies before
  content is shipped.
- Validate container image signatures and attestations against known
  and trusted keys.
- Evaluate configurable Rego-based policy rules over build pipeline
  attestations to enforce organizational requirements.
- Provide clear, actionable feedback when images fail policy checks so
  that issues can be resolved quickly.
- Allow organizations to define and maintain their own policy rule sets
  alongside the reference set provided by the project.

## Architecture and Workflow

### Validation Workflow

The EC validation is triggered during the release pipeline. The
[Release Service](./release-service.md) includes an instance of the EC
Tekton task which gates the release — if the EC task fails, the release
is blocked.

The [Integration Service](./integration-service.md) can also invoke EC
validation via an IntegrationTestScenario configured with the
`enterprise-contract` kind annotation, allowing policy checks to run
after builds complete and before a release is created.

The validation proceeds as follows for each image included in the
release (the list of images is defined in a Snapshot CR):

1. Confirm the image is signed and verify the signature.
2. Confirm the image has a signed and verifiable attestation.
3. For each policy source group defined in the EnterpriseContractPolicy
   CR configuration:
   - Download all defined policy (Rego) sources.
   - Download all defined data sources.
   - Run [Conftest](https://www.conftest.dev/) against the image's
     attestation using those policies and data.
4. Output results in JSON format showing details about failures,
   warnings, or violations.

### Data Flow

```
Build Pipeline
      │
      ▼
Tekton Chains ──► signs image + creates attestation
      │
      ▼
Integration / Release Pipeline
      │
      ▼
EC Tekton Task
      │
      ▼
ec-cli validate
  ├── verify image signature (cosign / sigstore)
  ├── verify attestation signature
  ├── download Rego policies + data from configured sources
  ├── run Conftest evaluation against attestation
  └── output JSON results (pass / fail / warn)
```

## API

The Enterprise Contract defines one Custom Resource:

- **EnterpriseContractPolicy (ECP)** — a Kubernetes CR that holds the
  configuration needed for running a specific instance of the Enterprise
  Contract. This includes the public key required to verify signatures,
  the list of policy and data sources, and any other required
  configuration.

Example:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: EnterpriseContractPolicy
metadata:
  name: my-policy
spec:
  description: "My Enterprise Contract Policy"
  sources:
    - name: "default-policies"
      policy:
        - "git::https://github.com/conforma/policy//policy/lib"
        - "git::https://github.com/conforma/policy//policy/release"
      data:
        - "git::https://github.com/conforma/policy//data"
  configuration:
    exclude:
      - "step_image_registries"
    include:
      - "attestation_type.slsa_provenance_02"
```

For detailed CRD documentation, see the
[ECP CRD source](https://github.com/conforma/crds) and the
[API Reference](https://redhat-appstudio.github.io/architecture/ref/enterprise-contract.html).

## Sub-components

### EC CLI (`ec`)

The `ec` command line tool is written in Go. Its primary purpose is to
perform EC policy validation. It supports several sub-commands:

- **`validate image`** — validates container image signatures,
  attestations, and evaluates policy rules against attestation content.
- **`validate policy`** — validates policy configurations.
- **`validate input`** — validates arbitrary input against policies.
- **`fetch policy`** — downloads policy sources for inspection.
- **`track bundle`** — tracks Tekton bundle references.
- **`opa`** — embedded OPA/Conftest for running and testing Rego
  policies directly.
- **`inspect`** — inspects attestations and signatures on images.
- **`sigstore`** — sigstore-related operations.
- **`version`** — prints version information.

For more information on the CLI, refer to the
[documentation](https://conforma.github.io/conforma.github.io/) and
the [source code](https://github.com/conforma/cli).

### EC Tekton Task

The EC Tekton task (`verify-enterprise-contract`) defines how the
`ec` CLI should be run within a Tekton pipeline. It handles task
inputs (the image list from a Snapshot, the policy configuration
reference, and the public key) and calls the CLI to perform EC
validation.

The task definition is maintained in the
[conforma/cli repository](https://github.com/conforma/cli/blob/main/tasks/verify-enterprise-contract/0.1/verify-enterprise-contract.yaml).
Tekton bundles containing the task are also published by the
[conforma/tekton-catalog](https://github.com/conforma/tekton-catalog)
repository.

### EC Policy CRD

The EnterpriseContractPolicy CRD is defined and maintained in the
[conforma/crds](https://github.com/conforma/crds) repository. It
provides the CRD definitions, validation schemas, and generated code
for working with EnterpriseContractPolicy resources in Kubernetes.

### EC Policies (Reference Rule Set)

The reference set of Rego policy rules for Konflux is maintained in
[conforma/policy](https://github.com/conforma/policy). It includes
rules for a range of supply chain security policies. The policies are
documented using [Antora](https://antora.org/) and published at
[conforma.github.io](https://conforma.github.io/conforma.github.io/).

Conftest bundles containing the latest version of these policies are
available as OCI artifacts in
[quay.io](https://quay.io/repository/enterprise-contract/ec-release-policy?tab=tags).

## Source Repositories

| Repository | Description |
|---|---|
| [conforma/cli](https://github.com/conforma/cli) | EC CLI tool and Tekton task definitions |
| [conforma/policy](https://github.com/conforma/policy) | Reference Rego policy rules |
| [conforma/crds](https://github.com/conforma/crds) | EnterpriseContractPolicy CRD definitions |
| [conforma/tekton-catalog](https://github.com/conforma/tekton-catalog) | Tekton bundle publishing for EC tasks |

## Dependencies

The Enterprise Contract depends on the following services and
components:

- **[Tekton Chains](./pipeline-service.md)** — EC works by examining
  attestations created by Tekton Chains during Konflux build pipeline
  runs. Chains signs both the container images and the attestations
  that EC subsequently validates. Without Chains, there are no
  attestations or signatures for EC to verify.
- **[Release Service](./release-service.md)** — the release pipeline
  contains an instance of the EC Tekton task that gates releases. If
  EC validation fails, the release is blocked.
- **[Integration Service](./integration-service.md)** — can invoke EC
  validation via IntegrationTestScenarios of kind
  `enterprise-contract`, running policy checks after builds complete.
- **[Sigstore / Cosign](https://www.sigstore.dev/)** — used for
  cryptographic signature verification of images and attestations.
- **[Open Policy Agent / Conftest](https://www.conftest.dev/)** — the
  Rego policy evaluation engine embedded in the EC CLI.

## Authentication and Authorization

- **Signature verification keys** — the public key(s) used to verify
  image and attestation signatures are specified in the
  EnterpriseContractPolicy CR. These are typically cosign-format
  public keys.
- **Policy source access** — policy and data sources can be fetched
  from git repositories or OCI registries. Access to private
  repositories requires appropriate credentials to be configured in
  the namespace where the EC task runs.
- **Image registry access** — the EC CLI needs pull access to the
  container registries where images and their attestations are stored.
  This is handled through standard Kubernetes image pull secrets in
  the task's service account.

## Network Traffic

The EC CLI, running as a Tekton task within the cluster, makes outbound
network requests to:

- **OCI registries** (e.g., `quay.io`) — to pull container image
  signatures, attestations, and Conftest policy bundles.
- **Git hosting services** (e.g., `github.com`) — to fetch policy and
  data sources when configured as git references.
- **Sigstore infrastructure** (e.g., Rekor transparency log, Fulcio
  CA) — when keyless signing verification is configured. This is
  optional and depends on the signing configuration.

All network traffic is outbound from the cluster. The EC components do
not expose any inbound services or endpoints — there is no running
controller or long-lived service. The EC CLI executes as a short-lived
process within a Tekton TaskRun pod.

## Performance and Availability

- **No long-running controller** — unlike most Konflux services, the
  Enterprise Contract does not have a continuously running controller
  or operator. It executes as a Tekton task on demand, so there are no
  availability concerns for an EC service itself.
- **Execution time** — EC validation time depends on the number of
  images in the Snapshot, the number of policy rules to evaluate, and
  network latency for fetching policy sources and image attestations.
- **Policy bundle caching** — Conftest policy bundles are published as
  OCI artifacts, which benefit from registry-level caching.
- **Scalability** — scales with the Tekton pipeline infrastructure.
  Each release or integration test runs its own EC TaskRun pod.

## Monitoring and Metrics

The EC CLI produces structured JSON output that includes detailed
results for each policy rule evaluated, including pass, fail, and
warning outcomes. This output is captured as a Tekton task result and
can be consumed by downstream systems for reporting and auditing.

There are no dedicated EC-specific Prometheus metrics or monitoring
dashboards, as the EC CLI runs as a short-lived Tekton task rather
than a persistent service. Monitoring of EC validation is handled
through:

- **Tekton PipelineRun / TaskRun status** — standard Kubernetes and
  Tekton monitoring of task success or failure.
- **EC task result output** — the JSON results from EC validation can
  be archived and analyzed via Tekton Results or other pipeline
  result storage mechanisms.
