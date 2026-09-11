---
title: "72. Component Ownership and Routing Metadata"
status: Proposed
applies_to:
  - build-service
  - release-service
  - enterprise-contract
topics:
  - ownership
  - routing
  - container-images
  - provenance
  - enforcement
---

# 72. Component Ownership and Routing Metadata

Date: 2026-09-10

## Status

Proposed

[//]: # (One of: Proposed, Withdrawn, Deferred, Accepted, Implementable, Implemented, Replaced)

## References

* [ADR-0061](0061-vcs-info-specification.md) - Carries metadata as image labels and OCI manifest annotations, enforced by Conforma. This ADR reuses that pattern and its source-repository key.
* [ADR-0056](0056-revised-component-model.md) - Revised Component Model; target for any resource-level extension.
* [OCI Image Spec: Annotations](https://specs.opencontainers.org/image-spec/annotations/) - the `org.opencontainers.image.*` keys and the reverse-domain rule for custom keys.
* [rhtap-ec-policy `rule_data.yml`](https://github.com/release-engineering/rhtap-ec-policy/blob/main/data/rule_data.yml) - an example downstream Conforma label policy.

## Context

Konflux cannot reliably say who is accountable for a shipped artifact or where its
issues should be routed. Today the answer lives in people's heads, in
spreadsheets, or in ad hoc tooling. Operators feel it most, since their work is
tracked in issue-tracker projects.

Even though components, operators, and namespaces all need ownership, we can
solve all three by carrying OCI metadata on the artifact, making it available
for validation in the release pipeline.

## Decision

Carry ownership and routing metadata as standard OCI metadata. Specifically,
labels on non-OCI images and annotations on OCI manifests, per
[ADR-0061](0061-vcs-info-specification.md) and verified by Conforma per
`mediaType`. Reuse existing keys and policy rather than invent new ones:

* Ownership: `org.opencontainers.image.authors`, the OCI freeform contact
  string, instead of a new `owner` label. Deprecate the legacy `maintainer` in
  its favor through Conforma's `deprecated_labels` and `effective_on`, with a
  consistency check during the transition.
* Issue Routing: deployment-specific, since the OCI spec has no issue tracker
  key. This ADR mandates none; a deployment adds one with a namespaced label and
  a release task.

Tekton Chains already captures image labels into the signed build provenance, so
the metadata is attestation-backed with no pipeline change. Enforcement reuses
Conforma's `required_labels` and `effective_on`, and ratchets:

1. Build and staging: a build missing the metadata warns; nothing blocks.
2. Production release: a managed release task resolves each value against the
   deployment's backend — `authors` could read as a comma-delimited list
   against an identity provider (for example, each a group that exists and
   meets a minimum size), a tracker reference against the issue tracker — and
   blocks the release if any fails.

The backends, and how a value resolves, are deployment-specific and out of scope.
Upstream defines the gate; it does not name the backend. An RPM carries neither
labels nor annotations, so covering it needs a resource-level carrier
([ADR-0056](0056-revised-component-model.md)) and is out of scope.

### Deployment example

A Red Hat deployment relaxes its `com.redhat.component` (once a Bugzilla
component) to accept a tracker component, and adds `com.redhat.tracker` for the
project URL. Custom keys use reverse-domain notation, so they stay out of the
upstream set. On a non-OCI image the same keys become annotations on a manifest:

```dockerfile
LABEL org.opencontainers.image.authors="team@example.com"
LABEL org.opencontainers.image.source="https://github.com/example/component"
LABEL com.redhat.component="Example Component"
LABEL com.redhat.tracker="https://issues.example.com/projects/EXAMPLE"
```

## Consequences

* The metadata is a queryable, signed property of the artifact. Anyone holding
  it, like a security team with a CVE, reads the contact and routing from the
  labels or the verified provenance, tamper-evident, with no access to the
  producing cluster.
* Reusing OCI keys, [ADR-0061](0061-vcs-info-specification.md)'s carriers, and
  Conforma's policy machinery means no new upstream label and no build-pipeline
  change; the only new part is adding a validation task to the release pipeline.
* The owning team fixes a stale record directly. A correction applies going
  forward, not to artifacts already shipped, so provenance stays immutable.
* `effective_on` dates make enforcement a migration, not a cutover.
* Artifacts that carry neither labels nor annotations (RPMs) fall outside this
  mechanism and need a resource-level carrier in a follow-up.

## Open Questions

* `authors` is freeform, so the list format and normalization are the validating
  task's to define, not the spec's.
* An artifact may map to several tracker projects; single- versus multi-valued
  routing, and how a set is validated, is open.
* A private tracker will not resolve for outside consumers; whether external
  artifacts need a different routing signal is open.
