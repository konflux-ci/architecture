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

We’ll enable tracing in Konflux and its services in the following order:

1. Enable native tracing capabilities
1. Enable tracing via [zero-code instrumentation](https://opentelemetry.io/docs/concepts/instrumentation/zero-code/) (automatic instrumentation)
1. Enable tracing via [code-based instrumentation](https://opentelemetry.io/docs/concepts/instrumentation/code-based/) (manual instrumentation)

### Native Tracing

We are going to enable as much native tracing in Konflux as we can so that we can quickly enable any pre-existing tracing capabilities in the system.

For instance, [Pipeline Service](https://github.com/redhat-appstudio/architecture/blob/main/architecture/pipeline-service.md) has to be instrumented with OTel as it provides Tekton APIs and services to RHTAP. Pipeline Services includes Tekton which already natively supports [OpenTelemetry Distributed Tracing for Tasks and Pipelines](https://github.com/tektoncd/community/blob/main/teps/0124-distributed-tracing-for-tasks-and-pipelines.md), so no upstream changes are required. We just need to work to enable this native tracing (e.g. set environment variables)

At this time, instrumenting individual steps within each task is not natively supported by Tekton, so this is an option that can be explored as a potential upstream contribution. This effort would likely be under Code-based Instrumentation.

### Zero-code Instrumentation

Next, we can quickly enable additional instrumentation for Konflux services with no functional code change through auto-instrumentation libraries.

See [https://opentelemetry.io/docs/concepts/instrumentation/zero-code/]

### Code-based Instrumentation

Later, we’ll create our own instrumentation code to fill gaps in the service’s instrumentation.

See [https://opentelemetry.io/docs/concepts/instrumentation/code-based/]

## Consequences

Enabling tracing will provide developers with insight into Konflux’s performance across its different components and workflows. This insight is valuable as it provides an easier mental model to use for debugging and optimizing Konflux’s performance (Expand on this) (For instance, answer the question: Why is this important?)

(any other consequences that we can foresee?)

## Implementation

The Konflux Tekton pipeline definition and tasks will require changes.

A few environment variables will need to be set in the controller manifest of each Konflux instance in order to enable tracing:

```
OTEL_EXPORTER_JAEGER_ENDPOINT
OTEL_EXPORTER_JAEGER_USER
OTEL_EXPORTER_JAEGER_PASSWORD
```

(how much into detail do we want to get here?)
