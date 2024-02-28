# 33. OpenTelemetry Tracing

Date started: 2024-02-27
Date accepted: 2024-MM-DD

## Status

Accepted

## Context

Instrumenting Konflux with OpenTelemetry tracing will provide SREs and developers invaluable insight for incident response, debugging and monitoring. Our goal is to get traces for the Tekton controller activity and generate spans for Tekton tasks in order to achieve an easier mental model to use for debugging.

OpenTelemetry is the industry standard to instrument, generate, collect, and export telemetry data (metrics, logs, and traces) to help you analyze software performance and behavior. Our goal is to collect [traces](https://opentelemetry.io/docs/concepts/signals/traces/) from the Konflux activity of building and deploying applications.

(what else can we add as context here?)

## Decision

We are going to enable as much native tracing in Konflux as we can so that we can quickly enable any pre-existing tracing capabilities in the system, and only once that is done shift focus towards more comprehensive instrumentation. (needs more details)

Tekton already natively supports [OpenTelemetry Distributed Tracing for Tasks and Pipelines](https://github.com/tektoncd/community/blob/main/teps/0124-distributed-tracing-for-tasks-and-pipelines.md), so no upstream changes are required.

[Pipeline Service](https://github.com/redhat-appstudio/architecture/blob/main/architecture/pipeline-service.md) also has to be instrumented with OTel as it provides Tekton APIs and services to RHTAP.

(figure out what other Konflux components also have native OTel tracing support that can be enabled)

## Consequences

A few environment variables will need to be set in the controller manifest of each Konflux instance in order to enable tracing:

```
OTEL_EXPORTER_JAEGER_ENDPOINT
OTEL_EXPORTER_JAEGER_USER
OTEL_EXPORTER_JAEGER_PASSWORD
```

At this time, instrumenting individual steps within each task is not natively supported by Tekton, so this is an option that can be explored as a potential upstream contribution.

(any other consequences that we can foresee?)

## Implementation

The Konflux Tekton pipeline definition and tasks will require changes.

(how much into detail do we want to get here?)
