---
title: Use our own pipelines
number: 17
---
# Use our own pipelines

* Date 2023-02-10

## Status

Accepted

* Relates to [ADR 7. Change Management](0007-change-management.md)
* Relates to [ADR 27. Container Image Management Practice](0027-container-images.md)

## Context

The maintainers of Konflux components need to demonstrate evidence of practices that support
a secure software development lifecycle (for example scanning, manifesting, vulnerability detection,
etc.)

There are lots of options out there for us to use, notably github actions. However, we're building
a ci/cd platform that is meant to support a secure software development lifecycle from the start.

## Decision

Use our own pipelines to build and scan Konflux components. Almost all of our components already
do this today. Look for evidence in the `.tekton/` directory of their git repo.

However, we have stopped short of configuring an [Application] and [Components] for Konflux.
We're using the pipelines directly, but not via the Konflux UI. This is something we intend to
start doing, but haven't made time to do so yet.

## Consequences

* When asked for evidence that teams are practicing secure development, they can point to Konflux
  pipelines in some cases.
* If our pipelines produce incorrect or erroneous errors, we will be in a position to notice this
  sooner and act to fix them.
* If there are gaps in the user experience, we'll also be in a position to notice this and work to
  improve UX (i.e. [STONE-459](https://issues.redhat.com/browse/STONE-459)).
* We won't get to exercise or benefit from the [integration-service] or the Konflux UI so long as
  we are only using the Konflux build pipelines and not yet onboarding to use of the [Application]
  and [Component] APIs.
* This ADR supports [STONE-434](https://issues.redhat.com/browse/STONE-434).

[integration-service]: ../ref/integration-service.html
[Application]: ../ref/application-environment-api.html#application
[Components]: ../ref/application-environment-api.html#component
