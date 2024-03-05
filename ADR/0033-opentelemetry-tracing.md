# 33. OpenTelemetry Tracing

Date started: 2024-02-27
Date accepted: 2024-MM-DD

## Status

Accepted

## Context

Instrumenting Konflux with [OpenTelemetry (OTel)](https://opentelemetry.io/docs/) tracing will provide SREs and developers invaluable insight for incident response, debugging and monitoring. Our goal is to get traces for the Konflux activity in order to achieve an easier mental model to use for debugging.

OpenTelemetry is the industry standard to instrument, generate, collect, and export telemetry data (metrics, logs, and traces) to help you analyze software performance and behavior. Our goal is to collect [traces](https://opentelemetry.io/docs/concepts/signals/traces/) from the Konflux activity of building and deploying applications.

## Decision

We’ll enable tracing in Konflux and its services in the following order:

1. Enable native tracing capabilities
1. Enable tracing via [zero-code instrumentation](https://opentelemetry.io/docs/concepts/instrumentation/zero-code/) (a.k.a. automatic instrumentation)
1. Enable tracing via [code-based instrumentation](https://opentelemetry.io/docs/concepts/instrumentation/code-based/) (a.k.a. manual instrumentation)

### Native Tracing

We are going to enable as much native tracing in Konflux as we can so that we can quickly enable any pre-existing tracing capabilities in the system.

For instance, [Pipeline Service](https://github.com/redhat-appstudio/architecture/blob/main/architecture/pipeline-service.md) has to be instrumented with OTel as it provides Tekton APIs and services to Konflux. Pipeline Services includes Tekton which already natively supports [OpenTelemetry Distributed Tracing for Tasks and Pipelines](https://github.com/tektoncd/community/blob/main/teps/0124-distributed-tracing-for-tasks-and-pipelines.md), so no upstream changes are required. We just need to work to enable this native tracing (e.g. set environment variables).

#### Prerequisites & Implementation

Jaeger should be installed and accessible from the Kubernetes cluster that Konflux pipelines run:

```
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm upgrade -i jaeger jaegertracing/jaeger -n jaeger --create-namespace
```

Then use port-forwarding to open the jaeger query UI or adjust the service type to Loadbalancer for accessing the service directly:

```
kubectl port-forward svc/jaeger-query -n jaeger 8080:80
```

Finally, in order to enable native Tekton Jaeger tracing, we need to set a few environment variables:

```
OTEL_EXPORTER_JAEGER_ENDPOINT
OTEL_EXPORTER_JAEGER_USER # optional
OTEL_EXPORTER_JAEGER_PASSWORD # optional
```

The only mandatory variable is `OTEL_EXPORTER_JAEGER_ENDPOINT`, setting it as the actual Jaeger instance hostname enables native Tekton tracing.

### Zero-code Instrumentation

Next, we can quickly enable additional instrumentation for Konflux services (e.g. Pipeline Service, Build Service, etc.) with no functional code change through auto-instrumentation libraries. In Pipeline Service’s case, we see the potential to benefit from not only the native Tekton tracing but also from zero-code instrumentation as well.

See [Zero-code Instrumentation](https://opentelemetry.io/docs/concepts/instrumentation/zero-code/).

Also, for golang there is [OpenTelemetry Go Automatic Instrumentation](https://github.com/open-telemetry/opentelemetry-go-instrumentation).

### Code-based Instrumentation

Later, we’ll create our own instrumentation code to fill the perceived gaps in the services’ instrumentation.

For instance, at the time of writing, instrumenting individual steps within each task is not natively supported by Tekton. So, we can propose and submit changes upstream to Tekton in order to enable tracing of each individual step within a task. That will allow us to create spans not only for the tasks but also for the steps themselves.

Also, at the time of writing, Tekton doesn’t support the OTLP export format. So, we can also propose and submit changes upstream to Tekton in order to enable OTLP exports so that those traces can be exported to a regular [OpenTelemetry collector](https://opentelemetry.io/docs/collector/) instance instead of a Jaeger instance.

See [Code-based Instrumentation](https://opentelemetry.io/docs/concepts/instrumentation/code-based/).

## Consequences

Enabling tracing will provide developers with insight into Konflux’s performance across its different components and workflows. This insight is valuable as it provides an easier mental model to use for debugging and optimizing Konflux’s performance and also empowers SREs and developers during incident response.

However, the Konflux Tekton pipeline definition, tasks and a few Konflux services will require changes. A few environment variables will need to be set in the controller manifest of each Konflux instance in order to enable tracing.

It is possible that some new dependencies such as the [OpenTelemetry Go Automatic Instrumentation](https://github.com/open-telemetry/opentelemetry-go-instrumentation) are introduced into Konflux’s code.

On top of that, a local Jaeger instance and a local [OpenTelemetry collector](https://opentelemetry.io/docs/collector/) instance will have to be created in order to collect and display the traces generated by each Openshift instance where Konflux pipelines are running.
