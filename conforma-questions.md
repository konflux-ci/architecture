# Conforma Documentation — Open Questions

This file tracks items that could not be fully verified from the source
repositories during the documentation rewrite (issue #296). Remove this
file once all questions are resolved.

## Authentication and Authorization

- **RBAC for ECP CRD** — What RBAC roles or bindings are required for
  users or service accounts to read/write EnterpriseContractPolicy CRs?
  The conforma/crds repository defines the CRD but does not document
  the expected RBAC model in detail.

## Monitoring and Metrics

- **Structured logging or metrics** — Does the Conforma CLI emit any
  structured telemetry beyond the JSON task result output? Are there any
  plans for Prometheus metrics in the future?

## Network Traffic

- **Rekor usage** — The original document noted that Rekor was not in
  active use. Is Rekor transparency log verification now enabled by
  default for keyless signing flows, or is it still optional /
  not yet used in production?

## Source Repositories (Resolved)

- ~~**conforma/golden-container and conforma/action-validate-image**~~
  **Resolved:** `conforma/golden-container` is used for CI tests and
  is not worth mentioning in the architecture doc.
  `conforma/action-validate-image` is a publicly available GitHub
  Action equivalent of the Tekton task for Konflux — a community
  interface for the Conforma CLI. Not in scope for the architecture
  doc but may be worth a note in the future.

## Policy Bundles (Resolved)

- ~~**OCI artifact location**~~ **Resolved:** The policy bundles have
  moved to `quay.io/conforma/release-policy`. Other artifacts in the
  new org:
  - `quay.io/conforma/tekton-task`
  - `quay.io/conforma/cli`
  The main architecture doc has been updated with the new locations.
