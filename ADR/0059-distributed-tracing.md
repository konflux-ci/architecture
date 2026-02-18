# 59. Distributed Tracing

Date started: 2026-02-04

## Status

Proposed

## Context

Tekton's OpenTelemetry instrumentation (TEP-0124) emits spans for PipelineRun and TaskRun reconciliation, and propagates SpanContext from parent PipelineRuns to child TaskRuns via the `tekton.dev/pipelinerunSpanContext` annotation. However, **PipelineRun spans are always created as root spans** — the reconciler does not extract a remote parent SpanContext from any incoming context. This is non-compliant with W3C Trace Context ([Section 3.3.3](https://www.w3.org/TR/trace-context/#processing-model)): a component receiving a `traceparent` SHOULD create child spans under that parent.

Because PipelineRuns are created via Kubernetes resource manifests rather than HTTP requests, there is no HTTP header channel to carry `traceparent`. Resource annotations serve as the equivalent TextMapCarrier. By honoring a `tekton.dev/traceparent` annotation as a remote parent, Tekton can participate in any distributed trace that spans the delivery lifecycle — from SCM webhook receipt through build, snapshotting, integration, and release — enabling consistent trace-based measurement of end-to-end delivery latency (MTTB) across controllers and clusters.

## Goals

1. Propagate a W3C Trace Context remote SpanContext across Konflux controllers and clusters so that all PipelineRuns in a delivery form a single distributed trace.
2. Remain inert when trace context annotations are absent — no behavioral change to existing PipelineRuns.
3. Preserve TEP-0124 local parent linkage: `tekton.dev/pipelinerunSpanContext` retains precedence when present.
4. Support reliable timing analysis using resource timestamps (wait vs. execute breakdown).

## Decision

### Trace context annotations

Three annotations on Tekton resources form a complete TextMapCarrier for W3C context propagation:

| Annotation | W3C Spec | Required |
|---|---|---|
| `tekton.dev/traceparent` | [Trace Context `traceparent`](https://www.w3.org/TR/trace-context/#traceparent-header) | Yes |
| `tekton.dev/tracestate` | [Trace Context `tracestate`](https://www.w3.org/TR/trace-context/#tracestate-header) | No |
| `tekton.dev/baggage` | [Baggage](https://www.w3.org/TR/baggage/) | No |

Each annotation encodes the same value format as its corresponding HTTP header. A TextMapPropagator configured for these annotations can inject and extract a full remote SpanContext, including vendor-specific tracestate and cross-cutting baggage, using standard OpenTelemetry APIs.

### Propagation and continuity

PaC extracts a remote SpanContext from inbound webhook headers using a W3C TraceContext TextMapPropagator (creating a new root when no incoming context is present), then injects the resulting SpanContext as `tekton.dev/traceparent` (plus `tracestate` and `baggage` when present) onto the build PipelineRun it creates.

After a successful build, integration-service persists the trace context annotations onto the Snapshot — the durable carrier for propagated context across temporal and cluster boundaries. For any integration PipelineRuns derived from that Snapshot, integration-service injects the Snapshot's trace context onto each created PipelineRun. When release is initiated, integration-service copies the Snapshot's trace context onto the Release CR; the release-service carries it onto release PipelineRuns.

A delivery may produce multiple integration and release PipelineRuns. The propagation rule is consistent: any PipelineRun derived from the Snapshot carries the Snapshot's trace context.

### Heterogeneous snapshots and missing context

Some Snapshots may be heterogeneous (components built from different initiating events) or may lack a usable `traceparent` (missing, invalid, or never seeded). In these cases, integration-service creates a new root span and injects its SpanContext onto the Snapshot for continuity.

### Tekton remote parent extraction

Tekton's TEP-0124 currently creates PipelineRun execution spans as root spans, ignoring any incoming remote parent. This is a W3C Trace Context compliance gap ([Section 3.3.3](https://www.w3.org/TR/trace-context/#processing-model)).

The fix: when the PipelineRun reconciler creates the execution span, it extracts a remote SpanContext from the PipelineRun's `tekton.dev/traceparent` (and `tracestate`) annotations using a TextMapPropagator. If a valid remote SpanContext is present, the execution span is created as a child of that remote parent — standard W3C behavior. If `tekton.dev/pipelinerunSpanContext` is also present (indicating an already-established local parent from Tekton-internal linkage), it takes precedence. If neither annotation is present, a new root span is created as today.

Once the execution span is parented correctly, the resulting SpanContext propagates to child TaskRuns via TEP-0124's existing `taskrunSpanContext` mechanism. No downstream changes are needed.

### Timing visibility

Synthetic spans derived from resource timestamps are parented under the propagated SpanContext:

`wait_duration`: creationTimestamp → `status.startTime`
`execute_duration`: `status.startTime` → `status.completionTime`

These timing spans are emitted for build, integration, and release PipelineRuns, making end-to-end delivery latency and per-stage breakdown directly visible from trace data.

## Infrastructure Requirements

No new infrastructure is required beyond existing OTLP trace collection.

## Required Changes (by controller/component)

### PaC (pipelines-as-code)

PaC must extract trace context from inbound webhook headers via a W3C TraceContext TextMapPropagator and inject the resulting SpanContext as `tekton.dev/traceparent` (plus `tracestate` and `baggage` when present) onto the build PipelineRun.

### Tekton Pipelines

Tekton Pipelines must extract `tekton.dev/traceparent` (and `tracestate`) as a remote parent SpanContext when creating PipelineRun execution spans, per W3C Trace Context. `tekton.dev/pipelinerunSpanContext` retains precedence when present. This is a compliance fix to TEP-0124, not a new feature — the change is inert when the annotation is absent.

### Integration-service

Integration-service must:

1. Propagate trace context (`traceparent`, `tracestate`, `baggage`) across the Snapshot → PipelineRun → Release CR chain, treating the Snapshot as the durable carrier across temporal and cluster boundaries.
2. Create a new root span and inject its SpanContext onto the Snapshot when valid context is missing.
3. Emit `wait_duration` and `execute_duration` timing spans for build, integration, and release PipelineRuns, parented under the propagated SpanContext.

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

### Linking of non-triggering build PipelineRuns in Snapshot
Good, because it allows a stochastic sampling of correlated build PipelineRuns included in a multi-component Snapshot.
Bad, because limits on span links result in an _arbitrary_ sampling of component build times.
Bad, because a limited sampling cannot guarantee useful metrics or navigability.

## Consequences

W3C Trace Context propagation via resource annotations yields end-to-end trace continuity across controllers and clusters, enabling MTTB analysis and reducing manual correlation. It introduces controller responsibility to inject and extract trace context annotations correctly, depends on an upstream fix to Tekton Pipelines (TEP-0124) for W3C compliance, and provides a defined path for missing-context Snapshots by allowing integration-service to establish a new root. This approach aligns Tekton with the W3C Trace Context specification, allowing any system that creates PipelineRuns to participate in distributed tracing by injecting standard trace context annotations.
