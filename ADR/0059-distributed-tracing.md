# 59. Distributed Tracing

Date started: 2026-02-04

## Status

Proposed

## Context

Tekton's OpenTelemetry instrumentation supports propagating a parent span context onto PipelineRuns. When present, Tekton parents its execution spans under the provided context and propagates it to child TaskRuns. Although designed for Tekton-internal parent-child PipelineRun linkage, the mechanism accepts a span context from any source.

By propagating trace context onto PipelineRuns they create, Konflux controllers cause Tekton's execution spans to appear as children in an external distributed trace. This enables end-to-end trace continuity across the delivery lifecycle — from SCM event receipt through build, snapshotting, integration, and release — supporting consistent trace-based measurement of delivery latency (MTTB) across controllers and clusters.

## Goals

1. Propagate a remote span context across Konflux controllers and clusters so that all PipelineRuns in a delivery form a single distributed trace.
2. Remain inert when trace context is absent — no behavioral change to existing PipelineRuns.
3. Support reliable timing analysis using resource timestamps (wait vs. execute breakdown).

## Decision

### Alignment principles

Trace context propagation follows two complementary standards:

- **W3C Trace Context**: All propagated trace context uses W3C Trace Context semantics. Controllers extract and inject trace context using standard W3C propagation, whether the carrier is an HTTP header, resource metadata, or any other medium.

- **Kubernetes resource ownership**: Controllers propagate trace context using Kubernetes-idiomatic resource metadata, respecting controller ownership boundaries. Controllers that create resources own the trace context they inject; controllers that reconcile resources read trace context observationally without competing for ownership of fields managed by other controllers.

Following extraction from inbound HTTP headers, the same trace context carrier is used uniformly across PipelineRuns, Snapshots, and Release CRs, ensuring a single propagation mechanism throughout the resource-level delivery lifecycle.

### Trace context propagation

PaC extracts trace context from inbound SCM webhook headers and propagates it onto the build PipelineRun it creates, establishing a new root when no incoming context is present. The initiating event's trace context takes precedence — controllers propagate the event-origin context, not any pre-existing context that may be present in a PipelineRun template.

After a successful build, integration-service persists the trace context onto the Snapshot — the durable carrier for propagated context across temporal and cluster boundaries. For any integration PipelineRuns derived from that Snapshot, integration-service injects the Snapshot's trace context onto each created PipelineRun. When release is initiated, integration-service copies the Snapshot's trace context onto the Release CR; release-service carries it onto release PipelineRuns.

A delivery may produce multiple integration and release PipelineRuns. The propagation rule is consistent: any PipelineRun derived from the Snapshot carries the Snapshot's trace context.

### Heterogeneous snapshots and missing context

Some Snapshots may be heterogeneous (components built from different initiating events) or may lack a usable trace context (missing, invalid, or never seeded). In these cases, integration-service creates a new root span and injects its context onto the Snapshot for continuity.

### Timing visibility

Timing spans derived from resource lifecycle timestamps are parented under the propagated span context, decomposed into two phases:

- **Pre-execution**: captures all delays from resource creation to execution start, including queue admission and provisioning time.
- **Execution**: captures active execution from start to completion.

These timing spans are emitted for build, integration, and release PipelineRuns, making end-to-end delivery latency and per-stage breakdown directly visible from trace data.

Pre-execution timing captures all delays as a single measurement. Finer-grained breakdown (e.g., queue vs. provisioning) is available through native scheduling metrics where applicable. Timing spans are emitted once per PipelineRun at completion and are not affected by reconciliation-driven span accumulation.

### Span attributes

Timing spans carry attributes sufficient for per-namespace delivery latency analysis, read directly from the PipelineRun's own metadata and status at the point of emission. No attributes are propagated across services. The Snapshot carries only trace context; all span attributes are local to the emitting controller. The attribute set covers:

- **Resource identity**: namespace, PipelineRun name and UID
- **Workload identity**: application and, when available, component
- **Stage classification**: build, test, or release
- **Outcome** (execution spans only): success/failure status and condition reason

No cross-service attribute propagation (e.g., OTel Baggage) is required for the current attribute set.

As the workload identity model evolves, attribute semantics will be updated to reflect the current model.

## Infrastructure Requirements

No new infrastructure is required beyond existing OTLP trace collection.

## Required Changes (by controller/component)

### PaC (pipelines-as-code)

PaC propagates trace context from inbound SCM events onto build PipelineRuns, creating a new root when no incoming context is present. PaC also emits timing spans with required attributes for build PipelineRuns, since its watcher already observes PipelineRun completion.

### Integration-service

Integration-service propagates the trace context across the Snapshot, PipelineRun, and Release CR chain, creates a new root when valid context is missing, and emits timing spans with required attributes for integration PipelineRuns.

### Release-service

Release-service propagates trace context from the Release CR onto release PipelineRuns and emits timing spans with required attributes. When a Release CR lacks trace context, release-service creates a new root span. This completes the end-to-end timing visibility from event receipt through release completion.

## Pros and Cons of Alternatives Considered

### Separate traces per stage

- Good, because it may be simpler logic.
- Bad, because it offers no end-to-end delivery view.
- Bad, because it offers weaker correlation across controllers/clusters.
- Bad, because delivery latency is harder to compute from trace data across multiple traces.

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
- Bad, because it is more invasive than metadata-based propagation.

Not adopted because metadata-based propagation achieves the same result with no schema changes and reuses existing runtime mechanisms.

### Parallel trace context carriers on the same resource

- Good, because it allows different consumers to read from their preferred carrier format.
- Bad, because multiple carriers for the same semantic value create ambiguity about which is authoritative.
- Bad, because it introduces parallel code paths that produce identical behavior.

Not adopted because a single trace context carrier per resource avoids ambiguity and redundant mechanisms.

### OTel Baggage for attribute propagation

- Good, because it propagates contextual attributes through the trace without requiring labels on each resource.
- Bad, because all required attributes are already locally available at each emission point.

Not adopted for current requirements. Can be reconsidered if future attributes that are not locally available need cross-service propagation.

### Linking of non-triggering build PipelineRuns in Snapshot

- Good, because it allows a stochastic sampling of correlated build PipelineRuns included in a multi-component Snapshot.
- Bad, because limits on span links result in an arbitrary sampling of component build times.
- Bad, because a limited sampling cannot guarantee useful metrics or navigability.

Not adopted because span link limits make the sampling arbitrary and unreliable for metrics or navigation.

## Consequences

Reusing the runtime's existing trace parent adoption mechanism for external trace propagation yields end-to-end trace continuity across controllers and clusters with minimal integration cost. It introduces controller responsibility to propagate trace context correctly, and provides a defined path for missing-context Snapshots by allowing integration-service to establish a new root. Any system that creates PipelineRuns can participate in distributed tracing by propagating trace context onto created PipelineRuns using the same pattern.

All attributes required for per-namespace delivery latency analysis are locally available at each timing span emission point. No cross-service attribute propagation is needed for the current attribute set.

Any future controller that creates PipelineRuns should follow the same propagation pattern: inject trace context onto created PipelineRuns, emit timing spans with the required attribute categories, and create a new root span when valid trace context is unavailable.
