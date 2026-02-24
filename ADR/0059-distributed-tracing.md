# 59. Distributed Tracing

Date started: 2026-02-04

## Status

Proposed

## Context

Tekton's OpenTelemetry instrumentation (TEP-0124) emits spans for PipelineRun and TaskRun reconciliation, and propagates SpanContext from parent PipelineRuns to child TaskRuns via the `tekton.dev/pipelinerunSpanContext` annotation. This annotation accepts a JSON-encoded OTel TextMapCarrier (`{"traceparent":"00-...","tracestate":"..."}`) and parents the PipelineRun's `ReconcileKind` span under the provided SpanContext. Although designed for Tekton-internal parent-child PipelineRun linkage, the annotation accepts a SpanContext from any source — enabling external systems to provide a remote parent by injecting the same JSON carrier format.

By injecting a `pipelinerunSpanContext` annotation onto PipelineRuns it creates, a Konflux controller can cause Tekton's execution spans to appear as children in an external distributed trace. This enables end-to-end trace continuity across the delivery lifecycle — from SCM webhook receipt through build, snapshotting, integration, and release — supporting consistent trace-based measurement of delivery latency (MTTB) across controllers and clusters, with no upstream Tekton changes required.

## Goals

1. Propagate a remote SpanContext across Konflux controllers and clusters so that all PipelineRuns in a delivery form a single distributed trace.
2. Remain inert when trace context annotations are absent — no behavioral change to existing PipelineRuns.
3. Support reliable timing analysis using resource timestamps (wait vs. execute breakdown).

## Decision

### Trace context carrier

A single annotation on PipelineRuns, Snapshots, and Release CRs carries the propagated trace context:

| Annotation | Format | Description |
|---|---|---|
| `tekton.dev/pipelinerunSpanContext` | JSON-encoded OTel TextMapCarrier | Contains `traceparent` and optionally `tracestate` per [W3C Trace Context](https://www.w3.org/TR/trace-context/) |

Example value: `{"traceparent":"00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01","tracestate":"vendorname=opaqueValue"}`

This reuses TEP-0124's existing annotation and carrier format. Tekton's PipelineRun reconciler already extracts a SpanContext from this annotation and parents the `ReconcileKind` span under it. Once the execution span is parented correctly, the resulting SpanContext propagates to child TaskRuns via TEP-0124's existing `taskrunSpanContext` mechanism. No Tekton changes are needed.

### Propagation and continuity

PaC extracts a remote SpanContext from inbound webhook headers using a W3C TraceContext TextMapPropagator (creating a new root when no incoming context is present), then injects the resulting SpanContext as a JSON-encoded carrier in `tekton.dev/pipelinerunSpanContext` onto the build PipelineRun it creates.

After a successful build, integration-service persists the trace context onto the Snapshot — the durable carrier for propagated context across temporal and cluster boundaries. For any integration PipelineRuns derived from that Snapshot, integration-service injects the Snapshot's trace context onto each created PipelineRun. When release is initiated, integration-service copies the Snapshot's trace context onto the Release CR; release-service carries it onto release PipelineRuns.

A delivery may produce multiple integration and release PipelineRuns. The propagation rule is consistent: any PipelineRun derived from the Snapshot carries the Snapshot's trace context.

### Heterogeneous snapshots and missing context

Some Snapshots may be heterogeneous (components built from different initiating events) or may lack a usable trace context (missing, invalid, or never seeded). In these cases, integration-service creates a new root span and injects its SpanContext onto the Snapshot for continuity.

### Timing visibility

Synthetic spans derived from resource timestamps are parented under the propagated SpanContext:

`wait_duration`: creationTimestamp → `status.startTime`
`execute_duration`: `status.startTime` → `status.completionTime`

These timing spans are emitted for build, integration, and release PipelineRuns, making end-to-end delivery latency and per-stage breakdown directly visible from trace data.

## Infrastructure Requirements

No new infrastructure is required beyond existing OTLP trace collection.

## Required Changes (by controller/component)

### PaC (pipelines-as-code)

PaC must extract trace context from inbound webhook headers via a W3C TraceContext TextMapPropagator and inject the resulting SpanContext as a JSON-encoded OTel TextMapCarrier in the `tekton.dev/pipelinerunSpanContext` annotation onto the build PipelineRun. If no existing trace context is present, a new root span is created.

### Integration-service

Integration-service must:

1. Propagate the `pipelinerunSpanContext` annotation across the Snapshot → PipelineRun → Release CR chain, treating the Snapshot as the durable carrier across temporal and cluster boundaries.
2. Create a new root span and inject its SpanContext onto the Snapshot when valid context is missing.
3. Emit `wait_duration` and `execute_duration` timing spans for build and integration PipelineRuns, parented under the propagated SpanContext.

### Release-service

Release-service must emit `wait_duration` and `execute_duration` timing spans for release PipelineRuns, parented under the propagated SpanContext. This completes the end-to-end timing visibility from webhook receipt through release completion.

## Pros and Cons of Alternatives Considered

### Separate traces per stage
Good, because it may be simpler logic.
Good, because it requires no Tekton changes.
Bad, because it offers no end-to-end delivery view.
Bad, because it offers weaker correlation across controllers/clusters.
Bad, because MTTB is harder to compute from trace data across multiple traces.

### Link-only correlation (no remote parentage)
Good, because it avoids parenting concerns.
Good, because it works with independent trace roots.
Bad, because span links do not establish parent-child relationships, so tools cannot render a single trace tree.
Bad, because end-to-end timing analysis is less direct.

### Custom CRD fields for trace context
Good, because it provides typed storage and validation potential.
Bad, because it requires schema changes and coordination cost.
Bad, because it is more invasive than annotation-based propagation.

### Dedicated `traceparent`/`tracestate` annotations on PipelineRuns
Good, because it uses standard W3C header formats directly as annotation values.
Good, because external systems can inject a flat string without constructing JSON.
Bad, because it duplicates the existing `pipelinerunSpanContext` mechanism with a different carrier format.
Bad, because it requires an upstream Tekton change to recognize the new annotations.
Bad, because it introduces a second code path that produces identical behavior to the existing one.

### Linking of non-triggering build PipelineRuns in Snapshot
Good, because it allows a stochastic sampling of correlated build PipelineRuns included in a multi-component Snapshot.
Bad, because limits on span links result in an _arbitrary_ sampling of component build times.
Bad, because a limited sampling cannot guarantee useful metrics or navigability.

## Consequences

Reusing TEP-0124's existing `pipelinerunSpanContext` annotation for external trace propagation yields end-to-end trace continuity across controllers and clusters with no upstream Tekton changes required. It introduces controller responsibility to inject and extract the JSON-encoded carrier correctly, and provides a defined path for missing-context Snapshots by allowing integration-service to establish a new root. Because the carrier format uses standard W3C Trace Context values inside a JSON-encoded OTel TextMapCarrier, any system that creates PipelineRuns can participate in distributed tracing by injecting the same annotation.
