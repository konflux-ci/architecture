---
title: Let Pipelines Proceed
number: 14
---
# Let Pipelines Proceed

* Date Decided: 2022-05-??
* Date Documented: 2023-01-31

## Status

Accepted

Relates to:
* [ADR 13. Konflux Test Stream - API contracts]({{< relref "0013-integration-service-api-contracts.md" >}})
* [ADR 30. Tekton Results Naming Convention]({{< relref "0030-tekton-results-naming-convention.md" >}})
* [ADR 32. Decoupling Deployment]({{< relref "0032-decoupling-deployment.md" >}})

## Context

The user's build pipeline includes scanning and linting tasks that operate on the source code and
the built image (SAST, antivirus, clair, etc..). The purpose of these tasks is to find problems in
the user's source code or dependencies and alert the user so they can take action ([STONE-459]).

One frustration we've heard from users in previous systems is that they don't want to be blocked in
their development or testing by complications in the build system, by compliance concerns. We want
to fix that by offering a system that permits as much progress in the lifecycle of the user's
application (build, test, and pre-production deployment) but which also protects production from
non-compliant builds via mechanisms in the [enterprise contract].

A problem we face: in Tekton, a failing TaskRun causes the whole PipelineRun to fail. If the purpose
of our linting and scanning tasks is to find problems - which usually looks like failure with
a non-zero exit code - how do they do their job without constantly breaking the user's build,
stopping them from running integration tests, and stopping them from deploying candidate builds to
their lower [Environments]?

## Decision

All scanning and linting TaskRuns should *succeed* even if they find problems in the content they
are evaluating.

Use the `TEST_OUTPUT` result convention from [ADR-0030] to expose those results and render them
for users ([STONE-459]).

## Consequences

* Users should find that even if their scanners find problems, they can still build, test, and
  deploy to lower [Environments].
* Without special treatment in [STONE-459], users may be misled or confused if their tasks appear to
  succeed but really are reporting errors under the hood.

## Footnotes

* We originally made this decision verbally in May of 2022, and have been operating with it as an
  unwritten principle. Documenting it here for posterity, visibility.

[STONE-459]: https://issues.redhat.com/browse/STONE-459
[Environments]: {{ relref "../ relref "../ref/application-environment-api.md#environment" }}" }}
[ADR-0030]: {{< relref "0030-tekton-results-naming-convention.md" >}}
[enterprise contract]: {{< relref "../architecture/enterprise-contract.md" >}}
