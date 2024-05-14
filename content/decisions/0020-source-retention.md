---
date: 2023-04-04T00:00:00Z
title: Source Retention
number: 20
---
# Source Retention

## Status

Accepted

Relates to [ADR 7. Change Management]({{< relref "0007-change-management.md" >}})

## Context

Red Hat's SSML requirements "SSML.PS.1.1.1 Securely Store All Forms of Code" requires that "The
revision and its change history are preserved indefinitely and cannot be deleted, except when
subject to an established and transparent policy for obliteration, such as a legal or policy
requirement."

We intend for the Konflux pipeline to support this requirement in
[RHTAP-107](https://issues.redhat.com/browse/RHTAP-107). Since we [Use our own pipelines (ADR
.17)]({{< relref "0017-use-our-pipelines.md" >}}), this would satisfy the control for us, if it were implemented.

So long as it is not yet implemented, we need a policy (an "administrative control" rather than
a "technical control") that precribes how our own source repositories must be managed.

## Decision

The source history of branches used to build Konflux components (usually the `main` branch), must
not be overwritten or deleted.

This practice can be supported by enabling branch protection rules on a repo by repo basis that
prohibit force pushing and branch deletion for protected branches.

## Consequences

* So long as [RHTAP-107](https://issues.redhat.com/browse/RHTAP-107) is not implemented, we will
  need to abide by this administrative control, increasing the number of rules that team members
  need to remember.
* Github branch protection rules can help reduce that cognitive load, but could be accidentally
  disabled if this ADR is not frequently discussed or referenced.
