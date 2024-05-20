# 33. Enable Native OpenTelemetry Tracing

Date started: 2024-02-27

Date accepted: 2024-04-02

## Status

Accepted

## Context

Konflux is a tool under active development and, therefore, unforeseen issues may arise. A recent (at the time of writing this ADR) example is the [long running](https://github.com/konflux-ci/build-definitions/pull/856/checks?check_run_id=22307468968) [e2e-test](https://github.com/konflux-ci/build-definitions/blob/main/.tekton/tasks/e2e-test.yaml) in Konflux’s build definitions. Fixing and debugging such issues is not a trivial thing for Konflux’s developers. Additional data, metrics, telemetry and tracing are essential in enabling Konflux developers and SREs to come up with fixes.

Tracing, in particular, enables a straightforward model for dealing with complex, distributed systems. It gives unique insight into a system’s execution, grouping functions together. These grouping functions can be critical for finding fields that correlate to some problem, and provide powerful insights to reduce the range of possible causes.

OpenTelemetry is the industry standard to instrument, generate, collect, and export telemetry data (metrics, logs, and traces) to help you analyze software performance and behavior. Our goal is to collect [traces](https://opentelemetry.io/docs/concepts/signals/traces/) from the Konflux activity of building applications.

Instrumenting Konflux with [OpenTelemetry (OTel)](https://opentelemetry.io/docs/) tracing will provide SREs and developers invaluable insight for incident response, debugging and monitoring. Our goal is to get traces for the Konflux activity in order to achieve an easier mental model to use for debugging.

## Decision

We are going to enable as much native tracing in Konflux as we can by quickly enabling any pre-existing tracing capabilities in the system. Any other type of tracing (e.g. zero code instrumentation or code based instrumentation) is out of scope for this ADR.

Native tracing will be enabled for the core Tekton controller as no upstream changes are required in order to do so, as Tekton  already natively supports [OpenTelemetry Distributed Tracing for Tasks and Pipelines](https://github.com/tektoncd/community/blob/main/teps/0124-distributed-tracing-for-tasks-and-pipelines.md). We just need to work to enable this native tracing (e.g. set environment variables).

There are a few ways to enable native tracing in Konflux. Openshift and Tekton natively have Jaeger tracing which can be collected by a compatible application, such as an actual Jaeger instance, an OpenTelemetry collector or even something like Grafana Tempo.

We recommend using an OpenTelemetry Collector as the way to collect Konflux native tracing as it has the least installation and setup overhead while also providing flexibility to forward traces to any tracing frontend.

Other Tekton pieces that Konflux leverages such as [pipeline as code](https://pipelinesascode.com/), [chains](https://tekton.dev/docs/chains/) and [results](https://tekton.dev/docs/results/) will have to be instrumented separately and will require upstream changes, so they are out of scope for this ADR.

Also, other Konflux services such as the [build service](https://github.com/redhat-appstudio/architecture/blob/main/architecture/build-service.md), [application service](https://github.com/redhat-appstudio/architecture/blob/main/architecture/hybrid-application-service.md) and [integration service](https://github.com/redhat-appstudio/architecture/blob/main/architecture/integration-service.md) will also require either automatic instrumentation or code based instrumentation and therefore are also out of scope for this ADR.

Any other type of instrumentation that isn't native will be addressed in a future ADR.

## Consequences

Additional applications will have to be installed in the same OpenShift cluster that the Konflux instance runs or OpenTelemetry collector(s) will have to be available in order to collect traces. Also, some configuration changes are required on the tekton-pipelines namespace in the OpenShift cluster that the Konflux instance runs.

Enabling Konflux native tracing is not without risks:
- There is a span or trace flooding risk from within the OpenShift cluster
- There is a secret leakage risk (although this is not an exclusive risk for traces, logs are also liable to this)

However, we assess that the benefits far outweigh the risks and therefore, by instrumenting Konflux with [OpenTelemetry (OTel)](https://opentelemetry.io/docs/) tracing, we will provide Konflux SREs and developers invaluable insight for incident response, debugging and monitoring, ultimately achieving an improved mental model for debugging and incident response.
