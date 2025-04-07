# 47. Attestable Build-Time Tests in Integration Service

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
pipelines.

### Attestations

It is already possible to generate attestations from an integration pipeline. Users can add `IMAGE_URL` and `IMAGE_DIGEST` result fields to the pipeline definition. When the pipeline runs and completes, Tekton Chains will sign an attestation and push it to the matching image/digest in Quay.  We will need to document this process.

### Serialization

The integration service will also add support for serialization of tests so
that the Conforma pipeline can run after any tests that generate attestations.
The exact mechanism for this has yet to be determined.

## Consequences

Users can have a faster turnaround time between triggering a build and getting
the results. In some cases the build->test process will take less time overall.
