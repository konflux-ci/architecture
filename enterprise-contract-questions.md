# Enterprise Contract Documentation — Open Questions

This file tracks items that could not be fully verified from the source
repositories during the documentation rewrite (issue #296). Remove this
file once all questions are resolved.

## Authentication and Authorization

- **RBAC for ECP CRD** — What RBAC roles or bindings are required for
  users or service accounts to read/write EnterpriseContractPolicy CRs?
  The conforma/crds repository defines the CRD but does not document
  the expected RBAC model in detail.

## Monitoring and Metrics

- **Structured logging or metrics** — Does the EC CLI emit any
  structured telemetry beyond the JSON task result output? Are there any
  plans for Prometheus metrics in the future?

## Network Traffic

- **Rekor usage** — The original document noted that Rekor was not in
  active use. Is Rekor transparency log verification now enabled by
  default for keyless signing flows, or is it still optional /
  not yet used in production?

## Source Repositories

- **conforma/golden-container and conforma/action-validate-image** —
  These repositories exist in the conforma org. Should they be mentioned
  as related projects in the architecture doc, or are they out of scope?

## Policy Bundles

- **OCI artifact location** — The policy bundles are currently
  referenced at `quay.io/enterprise-contract/ec-release-policy`. Has
  this location moved to a `conforma`-namespaced registry path, or does
  it remain under the `enterprise-contract` namespace?
