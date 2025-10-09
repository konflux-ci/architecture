# 49. Verification Summary Attestations for Release Policies

Date: 2025-07-02

## Status

Accepted

## Context

We are facing several challenges with our current approach to Conforma verification and software
development lifecycle (SDL) checks:

1. **Release-time Conforma verification performance**: Running Conforma at release time requires
   checking a large number of attestations, with each attestation invoking several potentially
   complex Rego policy checks. We have multiple examples of Konflux applications with over 100
   components - to check these at scale requires significant amounts of memory and compute.
2. **Pipeline arrangement limitations**: Currently we have to run all SDL checks in the build
   pipeline, which limits our options on how to arrange pipelines and prevents us from potentially
   moving some checks into integration tests. See [ADR 48](https://github.com/konflux-ci/architecture/pull/229).
3. **Redundant verification of unchanged artifacts**: Pre-merge Conforma checks for large snapshots
   often include one freshly built image plus a number of images that haven't changed, yet we redo
   the Conforma check on all images.
5. **Release externally-built artifacts**: Our current policies for release pipelines assume
   artifacts were built using a sanctioned Konflux Tekton pipeline. This inhibits ingestion and
   release of artifacts from external (but trusted) systems that do not execute builds with Tekton.
   Ex: and artifact produced from a trusted Jenkins instance, or Java artifacts built using
   [Project Newcastle](https://github.com/project-ncl).

A "[summary attestation](https://docs.google.com/presentation/d/1feaRK72-_uE8EUNJ6GGIM0iUuvMsJqY69rj3Uhbb4-M/edit?usp=sharing&resourcekey=0-qd3NpNHhCR7Y7fXFWQcLzw)"
can address these issues in the following manner:

- Document the policy that was used to verify an attestation at a point in time.
- Document the policy checks that were executed and passed.
- Allow Conforma to verify attestations by checking for the presence/absence of a policy check in
  the summary attestation. This should perform faster than a deeper inspection of the attestation
  and related artifacts.
- Allow Conforma to verify attestations in a general manner from a non-Konflux (or Tekton) system.

## Decision

We will adopt SLSA Verification Summary Attestations ([VSAs](https://slsa.dev/spec/v1.1/verification_summary))
for recording SDL policy check results. These VSAs will be used as the input to release pipeline
Conforma checks.

VSAs must be distributed as a signed OCI artifact. Separate in-toto attestations for this OCI
artifact are recommended, but not required. Konflux should be agnostic to the manner in which the
VSA is produced.

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
  - The output format must be in the prescribed SLSA VSA v1.1 format.
- EC check pipelines on merge to the component's branch produce a VSA attestation that is
  uploaded to one of the following locations:
  - **Rekor**: Store VSAs in Rekor with indexes on artifact digest, attestor identity fingerprint,
    and expiration date for quick retrieval across repositories.
  - **Quay well-known location**: Store VSAs in a dedicated repository using deterministic tagging
    based on subject artifacts.
- Release pipeline Conforma policies must be able to:
  - Detect if a VSA has been produced for a given artifact(s) (on Rekor or a well-known OCI repository).
  - Determine if the VSA was produced by a trusted verifier.
  - Determine if one of the verification levels is subject to an expiration. For example, checking
    if a task within the build pipeline was up to date.
  - Use the VSA's verification levels to determine if an artifact satistfies the release policy.
- Artfifacts built by external systems and released by Konflux must:
  - Be packaged in an OCI artifact.
  - Provide an attestation using the VSA format, and "attach" it to the related OCI artifact using
    the OCI Referrers API.
  - Provide other evidence used to verify the specific Conforma policy. Ex: cosign signatures,
    other related OCI artifacts.

### Alternatives Considered

We are working with the in-toto community to adopt this concept more broadly ("simple verification
attestation"). The conversation is active with a [proposed specification](https://github.com/in-toto/attestation/pull/470).
The proposal has the notion of a "verified property", which generalizes the SLSA `verifiedLevels`
idea. These may be easier to generate from Conforma rules and policies.

If the proposal is accepted, this ADR should be reconsidered to use the more general simple/summary
attestation format.
