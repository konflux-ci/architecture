# 37. Integration service promotes components to GCL immediately after builds complete

* Date: 2024-06-21

## Status

Accepted

Supersedes:

- [ADR 15. The Two-phase Architecture of the Integration Service](0015-integration-service-two-phase-architecture.html)
- [ADR 16. Integration Service Promotion Logic](0016-integration-service-promotion-logic.html)

## Context

In the initial implementation of the Integration Service, when a single component image is built, the
Integration Service tests the application by creating a Snapshot.
All Components with their images from the Global Candidate List are included within the Snapshot and then the Component
that was newly built is updated/overwritten to complete the Snapshot creation.
The Global Candidate List for the newly built component would only be updated once all required integration tests
for the created Snapshot have passed successfully.
See more about this in [ADR 16. Integration Service Promotion Logic](0016-integration-service-promotion-logic.html) and
[ADR 15. The Two-phase Architecture of the Integration Service](0015-integration-service-two-phase-architecture.html).

This logic created issues for the end users, especially in cases where older components would start failing
Enterprise Contract checks as new rules/policies get introduced. This led to Global Candidate List deadlocks where
it was impossible for a user to promote a new build of their component if more than one of their other components were
failing integration tests.

## Decision

Instead of holding off on promoting individual component builds to the Global Candidate List until they pass
all required integration tests, the Integration service will promote the Snapshots that were created
for those builds to the GCL immediately after they are created.

Note: Integration service still does not promote the Snapshots originating from PRs, only those originating from
push (merge-to-main) events gets promoted to the Global Candidate List.

Note: Integration-service will still create the Releases for each ReleasePlan that has an auto-release label only for
Snapshots that have passed all the required integration tests.

## Consequences

* The users can have an assumption that their Global Candidate List is (in most cases) in sync
  with the head of the branch for each of their components
* The users can unblock most(if not all) deadlock-type issues by simply submitting new builds of
  components that are causing issues
* Related builds from monorepos or PR groups would not be blocked from being promoted after merging
* Since the race-condition from the two-phase architecture has been eliminated on account of the Global Candidate List
  being updated immediately, Integration service will stop creating composite Snapshots

## Footnotes

The new promotion logic will be implemented as part of the STONEINTG-83 epic.
This document is created for posterity and visibility.

[Global Candidate List]: ../architecture/integration-service.html
