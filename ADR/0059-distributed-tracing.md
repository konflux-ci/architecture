# 59. Distributed Tracing

Date started: 2026-02-04

## Status

Proposed

## Context

Tekton's OpenTelemetry instrumentation (TEP-0124) supports propagating a parent span context onto PipelineRuns via the `tekton.dev/pipelinerunSpanContext` annotation. When present, Tekton parents its execution spans under the provided context and propagates it to child TaskRuns. Although designed for Tekton-internal parent-child PipelineRun linkage, the annotation accepts a span context from any source.

By injecting this annotation onto PipelineRuns it creates, a Konflux controller can cause Tekton's execution spans to appear as children in an external distributed trace. This enables end-to-end trace continuity across the delivery lifecycle — from SCM webhook receipt through build, snapshotting, integration, and release — supporting consistent trace-based measurement of delivery latency (MTTB) across controllers and clusters, with no upstream Tekton changes required.

## Goals

1. Propagate a remote span context across Konflux controllers and clusters so that all PipelineRuns in a delivery form a single distributed trace.
2. Remain inert when trace context annotations are absent — no behavioral change to existing PipelineRuns.
3. Support reliable timing analysis using resource timestamps (wait vs. execute breakdown).

## Decision

### Trace context carrier

The `tekton.dev/pipelinerunSpanContext` annotation on PipelineRuns, Snapshots, and Release CRs carries the propagated trace context, reusing TEP-0124's existing annotation ([W3C Trace Context](https://www.w3.org/TR/trace-context/) values inside a JSON-encoded OTel TextMapCarrier). No Tekton changes are needed.

### Propagation and continuity

PaC propagates trace context from inbound webhook headers onto the build PipelineRun it creates, establishing a new root when no incoming context is present.

After a successful build, integration-service persists the trace context onto the Snapshot — the durable carrier for propagated context across temporal and cluster boundaries. For any integration PipelineRuns derived from that Snapshot, integration-service injects the Snapshot's trace context onto each created PipelineRun. When release is initiated, integration-service copies the Snapshot's trace context onto the Release CR; release-service carries it onto release PipelineRuns.

A delivery may produce multiple integration and release PipelineRuns. The propagation rule is consistent: any PipelineRun derived from the Snapshot carries the Snapshot's trace context.

### Heterogeneous snapshots and missing context

Some Snapshots may be heterogeneous (components built from different initiating events) or may lack a usable trace context (missing, invalid, or never seeded). In these cases, integration-service creates a new root span and injects its context onto the Snapshot for continuity.

### Timing visibility

Timing spans derived from resource timestamps are parented under the propagated span context:

`wait_duration`: creationTimestamp → `status.startTime`
`execute_duration`: `status.startTime` → `status.completionTime`

These timing spans are emitted for build, integration, and release PipelineRuns, making end-to-end delivery latency and per-stage breakdown directly visible from trace data.

`wait_duration` captures all pre-execution delays, including queue admission and provisioning time when Kueue manages PipelineRun scheduling. Finer-grained breakdown is available through Kueue's native metrics. Tekton's own reconciliation-driven spans accumulate with each pod status change under Kueue, but the timing spans defined here are emitted once per PipelineRun completion and are not affected.

### Span attributes

Timing spans are emitted once per PipelineRun, when the controller observes completion. Each span carries attributes read directly from the PipelineRun's own metadata, labels, and status — no attributes are propagated across services or carried on the Snapshot. The Snapshot carries only the trace context annotation (trace ID and parent span ID); all span attributes are local to the emitting controller.

| Attribute | Required |
|---|---|
| `konflux.namespace` | Yes |
| `konflux.pipelinerun.name` | Yes |
| `konflux.pipelinerun.uid` | Yes |
| `konflux.stage` (`build`, `test`, or `release`) | Yes |
| `konflux.application` | Yes |
| `konflux.component` | When available |
| `konflux.success` | Yes (execute only) |
| `konflux.reason` | Yes (execute only) |

No cross-service attribute propagation (e.g., OTel Baggage) is required for the current attribute set.

As the Application/Component model evolves toward ComponentGroup, attributes such as `konflux.application` and `konflux.component` will be updated to reflect the new model.

## Infrastructure Requirements

No new infrastructure is required beyond existing OTLP trace collection.

## Required Changes (by controller/component)

### PaC (pipelines-as-code)

PaC propagates trace context from inbound webhooks onto build PipelineRuns, creating a new root when no incoming context is present.

### Integration-service

Integration-service propagates the trace context across the Snapshot → PipelineRun → Release CR chain, creates a new root when valid context is missing, and emits timing spans with required attributes for build and integration PipelineRuns.

### Release-service

Release-service propagates trace context from the Release CR onto release PipelineRuns and emits timing spans with required attributes. When a Release CR lacks trace context (e.g., a manually created release), release-service creates a new root span for the release trace. This completes the end-to-end timing visibility from webhook receipt through release completion.

## Pros and Cons of Alternatives Considered

### Separate traces per stage

- Good, because it may be simpler logic.
- Good, because it requires no Tekton changes.
- Bad, because it offers no end-to-end delivery view.
- Bad, because it offers weaker correlation across controllers/clusters.
- Bad, because MTTB is harder to compute from trace data across multiple traces.

Not adopted because the primary goal is end-to-end delivery latency measurement, which requires a single trace spanning all stages.

### Link-only correlation (no remote parentage)

- Good, because it avoids parenting concerns.
- Good, because it works with independent trace roots.
- Bad, because span links do not establish parent-child relationships, so tools cannot render a single trace tree.
- Bad, because end-to-end timing analysis is less direct.

Not adopted because span links do not produce a navigable trace tree, making delivery latency analysis indirect and tool-dependent.

### Custom CRD fields for trace context

- Good, because it provides typed storage and validation potential.
- Bad, because it requires schema changes and coordination cost.
- Bad, because it is more invasive than annotation-based propagation.

Not adopted because annotation-based propagation achieves the same result with no schema changes and reuses an existing Tekton mechanism.

### Dedicated `traceparent`/`tracestate` annotations on PipelineRuns

- Good, because it uses standard W3C header formats directly as annotation values.
- Good, because external systems can inject a flat string without constructing JSON.
- Bad, because it duplicates the existing `pipelinerunSpanContext` mechanism.
- Bad, because it requires an upstream Tekton change.
- Bad, because it introduces a second code path that produces identical behavior.

Not adopted because `pipelinerunSpanContext` already exists and works; adding a parallel annotation mechanism provides no functional benefit.

### OTel Baggage for attribute propagation

- Good, because it propagates contextual attributes through the trace without requiring labels on each resource.
- Bad, because all MTTB-required attributes are already locally available at each emission point.

Not adopted for current requirements. Can be reconsidered if future attributes that are not locally available need cross-service propagation.

### Linking of non-triggering build PipelineRuns in Snapshot

- Good, because it allows a stochastic sampling of correlated build PipelineRuns included in a multi-component Snapshot.
- Bad, because limits on span links result in an _arbitrary_ sampling of component build times.
- Bad, because a limited sampling cannot guarantee useful metrics or navigability.

Not adopted because span link limits make the sampling arbitrary and unreliable for metrics or navigation.

## Consequences

Reusing TEP-0124's existing annotation for external trace propagation yields end-to-end trace continuity across controllers and clusters with no upstream Tekton changes required. It introduces controller responsibility to propagate trace context correctly, and provides a defined path for missing-context Snapshots by allowing integration-service to establish a new root. Any system that creates PipelineRuns can participate in distributed tracing by injecting the same annotation.

All attributes required for per-namespace MTTB analysis are locally available at each timing span emission point. No OTel Baggage or cross-service attribute propagation is needed for the current attribute set.

Any future controller that creates PipelineRuns should follow the same propagation pattern: inject the trace context annotation onto created PipelineRuns, emit timing spans with the required attributes, and create a new root span when valid trace context is unavailable.
