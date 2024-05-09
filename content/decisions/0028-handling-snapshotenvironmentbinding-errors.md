---
title: Handling SnapshotEnvironmentBinding Errors
number: 28
---
# Handling SnapshotEnvironmentBinding Errors
date: 2023-08-31T00:00:00Z

## Status
Superceded by [ADR 32. Decoupling Deployment](0032-decoupling-deployment.html)

## Context
It is currently not possible to determine whether a SnapshotEnvironmentBinding (SEB) is stuck in an unrecoverable state.  This is a major problem when deciding if an ephemeral SEB needs to be cleaned up by the integration service's SnapshotEnvironmentBinding controller.  An inability to clean up errored SEBs can overload the cluster.

## Decision
The integration service has a reconciler function that cleans up errored SnapshotEnvironmentBindings with an ErrorOccured condition.  This condition is set to 'true' by default and is set to 'false' when the environment becomes available.  The integration service will consider that all SEBs with a 'true' ErrorOccured condition and a LastUpdateTime of more than five minutes ago are unrecoverable and can be cleaned up.

## Consequence
- SnapshotEnvironmentBindings will be cleaned up after five minutes if they are not ready.  Environments that take a long time to provision may be cleaned up erroneously.  To accomodate this, the timeout threshold can be adjusted via a pull request to the integration service.

## Footnotes
- This change has been implemented as a stopgap measure to avoid permanently stuck integration tests while a generic solution for detecting provisioning errors is designed.  That work will be tracked in [RHTAP-1530](https://issues.redhat.com/browse/RHTAP-1530).
