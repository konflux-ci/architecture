# 38. Integration service removes composite snapshots and logic around them

* Date started: 2024-07-10

## Status

Accepted

## Context

Composite snapshots main goal was to prevent race condition when teams merged multiple PRs to multiple components
of the same application at nearly the same time. This concept was confusing for users and we managed to simplify it
by immediate promotion to GCL using override snapshots. Users also ran into the issue with GCL deadlock. In short, 
components already in the GCL can cause the tests for a new component to fail if they are bundled into a snapshot. 
If two or more components in an application run into this issue it can create a deadlock that prevents the release 
of new versions of the application.


## Decision

Introduction of override snapshots should prevent this race condition and GCL deadlock with much simpler concept to understand,
replacing the composite snapshots which served the same purpose.
This decision led to removing of all logic regarding composite snapshots within integration-service codebase, since override snapshot
solves same problems.
Override snapshot is created manually by users, its special kind of Snapshot which, if it passes the integration tests,
updates the GCL for all the components contained within it.

## Consequences

* Removal of code connected to composite snapshots

## Footnotes

The new promotion logic will be implemented as part of the STONEINTG-83 epic.
This document is created for posterity and visibility.

