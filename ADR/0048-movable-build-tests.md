# 48. Attestable Build-Time Tests in Integration Service

Date: 2025-04-06

## Status

Proposed

## Context

Some of the security scans run during the build pipeline take a long time to
run. This forces users to wait longer to be notified of the results of their
builds.  In order to receive more immediate feedback, users have requested that
they be able to run security scans during their integration tests.

## Decision

We will add support for adding attestations to images from their integration
pipelines. Test pipelines can be run and re-run independently of build
pipelines but all pipelines will have attestations generated for them to enable
Conforma evaluations.

### Attestations

Each task will be responsible for generating an attestation in Cosign.
(https://github.com/in-toto/attestation/blob/main/spec/predicates/vulns_02.md)[vulnerability attestations]
will be used for security scans rather than `provenance` attestations. Tasks
will output `ARTIFACT_URI` and `ARTIFACT_DIGEST` which will point to the
location of the attestation in Quay.  These results will tell Chains to
generate and sign a SLSA provenance attestation for the task-generated
attestations.

#### Multiple Attestations

It may be the case that there are multiple attestations generated for a given 
test. Integration test scenarios can be re-run which will result in duplicate
attestations.  There is also a race condition where a user adds the build-time
test to their integration pipeline then removes the test from their build
pipeline. Between those two actions, another build might be triggered that uses
the old build pipeline and the new integration test scenario.  If there are
multiple attestations for a given test, Conforma will always use the newest
attestation when determining if a test has passed.

#### Splitting up required tasks

Not all build tasks can be run in the integration pipeline.  Tasks like build
and SBOM generation must be run at build-time.  To this end, Conforma will
split its list of required tasks into `required_in_build` and `required`.
`required` tasks can be run in the build or integration pipelines and all
required tasks will be part of this group unless there is a reason that they
cannot or should not be run in integration pipelines.

### Serialization

The integration service will also add support for serialization of tests so
that the Conforma pipeline can run after any tests that generate attestations.
Integration tests will run as a directed acyclic graph.

#### Integration Test Scenario DAG rules
- All parents must finish before a given child begins
- A failed or cancelled test will result in all child tests being cancelled
- If a test scenario is re-run and passes then child scenarios will also be
triggered

## Consequences

By leveraging IntegrationTestScenarios, Konflux users can separate their build
tasks from their testing tasks. This will enable faster turnaround time between
triggering a build and getting the result.  In some cases the build-test
process will take less time overall.

It is worth noting that right now, almost all of the scan tasks run in parallel
in the build pipeline. If we move some of those to be IntegrationTestScenarios
but not all of them, then the end to end may take even longer than it does
today. We will have taken one set of parallel things and turned it into two sets
of parallel things, run in sequence. However, some or all of this time increase
maybe offset by the fact that the security scans can be run in parallel with
other integration tests. Users with long-running integration tests will still
see a net decrease in end to end time.
