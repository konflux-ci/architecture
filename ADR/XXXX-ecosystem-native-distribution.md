---
title: "XXXX. Ecosystem-Native Distribution for Non-OCI Artifacts"
status: Proposed
applies_to:
  - release-service
  - build-service
topics:
  - release
  - rpm
  - python
  - java
  - supply-chain
---

# XXXX. Ecosystem-Native Distribution for Non-OCI Artifacts

Date: 2026-03-18

## Status

Proposed

## Context

[ADR-0063](./0063-generalized-build-release-pipelines.md) established that Konflux uses OCI images
as its internal representation for all software artifacts, including non-container artifacts such as
RPMs, Python wheels, and Maven JARs. This is a valuable and necessary standardization: having a
single internal representation allows Konflux to consistently associate supply chain metadata
(signatures, attestations, SBOMs) with any artifact it builds, regardless of ecosystem. This ADR
builds on that foundation by addressing what must happen at the boundary where Konflux-internal
artifacts are distributed to language-native ecosystems.

The stakeholders who motivated ADR-0063 -- teams building and distributing language-native software
across any package ecosystem -- cannot meaningfully consume artifacts or their associated supply
chain metadata using native tooling when these are stored exclusively in OCI registries.

The tools those stakeholders use do not install software from OCI registries. Similarly, the supply
chain metadata standards those ecosystems have adopted are consumed by ecosystem-native tooling, not
by OCI registry clients. For example, a stakeholder using `pip` to install a Python package has no
means of discovering or verifying an SBOM or attestation stored as an OCI referrer; the same is
true for users of `dnf`, `mvn`, or the native tooling of any other package ecosystem.

ADR-0063 states that release pipelines "MUST extract content from the _Component Build Artifact_
and publish these to appropriate 'native' package registries... in the manner expected of the
respective package ecosystem." However, this requirement does not explicitly address supply chain
metadata or pre-release artifact availability during integration testing.

Konflux's role is to be a secure, universal software factory whose _internal_ representation is
OCI, while ensuring that all _external_ distribution conforms to the expectations of the target
ecosystem.

## Decision

- Release pipelines for non-OCI artifacts MUST publish software artifacts to ecosystem-native
  package registries, in the format and manner required by the target package ecosystem, to the
  extent possible as allowed by the standards of that ecosystem, which continue to evolve.

- Release pipelines for non-OCI artifacts MUST publish supply chain metadata -- including SBOMs,
  attestations, and signatures -- to the ecosystem-native location and in the ecosystem-native
  format, to the extent possible as allowed by the standards of that ecosystem, which continue to
  evolve. Examples include:
  - **RPM**: GPG-signed packages in a Yum/DNF repository with a signed `repomd.xml`.
  - **Python**: Attestations published to PyPI per [PEP 740](https://peps.python.org/pep-0740/).
  - **Maven**: Signatures published to Maven Central per its
    [publication requirements](https://central.sonatype.org/publish/requirements/).

  OCI referrers MAY be used to store supply chain metadata internally within Konflux, but this
  does not satisfy the requirement for ecosystem-native distribution. When an ecosystem does not
  yet support a particular metadata type natively, OCI referrers remain the sole store for that
  metadata within Konflux.

- Build and integration pipelines that make non-OCI artifacts available for pre-release or
  integration testing should be able to expose those artifacts via native package tooling.
  Consumers of pre-release builds should be able to install or resolve the artifact using
  standard ecosystem tools (e.g., `pip install`, `dnf install`) without requiring direct
  interaction with an OCI registry.

## Consequences

- Release pipeline authors for non-OCI ecosystems must have ecosystem expertise. A pipeline that
  performs only OCI operations does not satisfy this ADR.

- Supply chain metadata for non-OCI artifacts will exist in two locations: as OCI referrers
  (Konflux-internal) and in the ecosystem-native location (external). Release pipelines are
  responsible for this translation.

- Pre-release and integration test infrastructure for non-OCI artifacts should be able to include
  ecosystem-native package repositories or indices (e.g., a local Yum repository, a local PyPI
  index) so that tests can consume artifacts using standard tooling.

- Konflux's scope is bounded: it provides a consistent internal representation using OCI and
  ensures release pipelines translate that to whatever the target ecosystem requires. Konflux does
  not require downstream ecosystems to adopt OCI-based distribution.

- Ecosystem-native supply chain standards will evolve. Release pipelines are expected to track and
  adopt those standards over time.

## Alternatives Considered

### Publish Supply Chain Metadata Only as OCI Referrers

This alternative would have release pipelines publish SBOMs, attestations, and signatures
exclusively as OCI referrers attached to the _Component Build Artifact_, regardless of the target
package ecosystem.

This approach is rejected because:

- Ecosystem-native tooling does not query OCI registries for supply chain metadata. Consumers
  using standard tooling would have no visibility into SBOMs or attestations produced by Konflux.
- Package ecosystems have adopted or are actively adopting their own supply chain metadata
  standards. Publishing metadata only to OCI registries means Konflux-produced metadata is
  effectively invisible to the users it is meant to protect.
- Requiring ecosystem stakeholders to adopt OCI clients to access supply chain data creates
  friction and is unlikely to be adopted in practice, making the security guarantees Konflux
  provides meaningless in those ecosystems.
