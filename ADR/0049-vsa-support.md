# ADR-0049: Verification Summary Attestations for Release Policies

Date: 2025-07-02

## Status

Proposed

## Context

We are facing several challenges with our current approach to Enterprise Contract (EC) verification
and SDL checks:

1. **Release-time EC verification performance**: Running EC at release time requires checking a
   large number of attestations, which takes too long. Scaling to handle large applications like
   OpenShift is proving challenging.
2. **Pipeline arrangement limitations**: Currently we have to run all SDL checks in the build
   pipeline, which limits our options on how to arrange pipelines and prevents us from potentially
   moving some checks into integration tests.
3. **Redundant verification of unchanged artifacts**: Pre-merge EC checks for large snapshots often
   include one freshly built image plus a number of images that haven't changed, yet we redo the EC
   check on all images.
4. **Scalability concerns**: As our applications grow in complexity (like OpenShift snapshots), the
   current approach becomes increasingly inefficient.
5. **Release externally-built artifacts**: Our current policies for release pipelines assume
   artifacts were built on Konflux. This inhibits ingestion and release of artifacts from other
   external (but trusted) systems.

## Decision

We will adopt Verification Summary Attestations ([VSAs](https://slsa.dev/spec/v1.1/verification_summary))
for recording SDL policy check results. These VSAs will be used as the input to release pipeline
Conforma checks.

## Consequences

### Impacts

- Conforma policy [packages](https://conforma.dev/docs/policy/authoring.html#_package_annotations)
  provide metadata that associates a set of rules with a VSA [verification level](https://slsa.dev/spec/v1.1/verification_summary#fields).
  - Rules that validate SLSA build levels MUST indicate the appropriate [SlsaResult](https://slsa.dev/spec/v1.1/verification_summary#emslsaresult-stringem)
    value.
  - Rules that are not related to SLSA (or have not been incorporated into SLSA yet) MUST use a
    value that does not have the `SLSA_*` prefix. For example, rulesets that verify an artifact
    provides source in accordance with GPL v3 could use `GNU_GPL_3` as its "verification level."
- Conforma's CLI produces output in VSA format:
  - The CLI provides options/flags for specifying the `verifier` in the predicate.
  - Policy package metadata is used to produce appropriate verification level values.
    `SLSA_<track>_*` values MUST produce only one value per track.
- EC check pipelines on merge to the component's branch produce a VSA attestation that is
  uploaded to one of the following locations:
  - **Rekor**: Store VSAs in Rekor with indexes on artifact digest, attestor identity fingerprint,
    and expiration date for quick retrieval across repositories
  - **Quay well-known location**: Store VSAs in a dedicated repository using deterministic tagging
    based on subject artifacts
- Release pipeline Conforma policies must be able to:
  - Detect if a VSA has been produced for a given artifact(s) (on Rekor or a well-known OCI repository).
  - Determine if the VSA was produced by a trusted verifier.
  - Use the VSA's verification levels to determine if an artifact satistfies the release policy.

### Alternatives Considered

We are working with the in-toto community to adopt this concept more broadly ("simple verification
attestation"). The conversation is active with a [proposed specification](https://github.com/in-toto/attestation/pull/470).
The proposal has the notion of a "verified property", which generalizes the SLSA `verifiedLevels`
idea. These may be easier to generate from Conforma rules and policies.

If the proposal is accepted, this ADR should be reconsidered to use the more general simple/summary
attestation format.
