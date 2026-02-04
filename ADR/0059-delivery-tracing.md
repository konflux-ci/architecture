# 59. Delivery Tracing

Date started: 2026-02-04

## Status

Proposed

## Context

Tekton’s native OpenTelemetry tracing (TEP-0124) provides execution traces for individual PipelineRuns, but Konflux does not yet produce a single trace that spans the delivery lifecycle from SCM webhook receipt through build, snapshotting, integration, and release. That gap forces manual correlation across controllers and sometimes clusters, and it prevents consistent trace-based measurement of end-to-end delivery latency (MTTB).

This ADR defines delivery tracing only: propagation of a delivery-level trace context across Konflux resources and adoption of that context as a remote parent for Tekton execution traces. Enhancing execution traces with richer “workload” attributes and failure classification is out of scope here and will be addressed separately.

## Goals

Delivery tracing must preserve a single trace context across controllers and clusters for a delivery, remain inert unless enabled, never override existing Tekton execution parentage, and support reliable delivery timing analysis using resource timestamps (including “wait” versus “execute” breakdown).

## Decision

### Delivery trace context

A single Konflux-owned annotation carries a W3C `traceparent`:

`tekton.dev/deliveryTraceparent: <traceparent>`

Only `traceparent` is propagated in this design. `tracestate` and baggage are intentionally excluded.

### Propagation and continuity

PaC seeds delivery tracing while handling an SCM webhook. It starts a delivery span (child of an inbound trace if the webhook includes `traceparent`, otherwise a new root) and writes the resulting `deliveryTraceparent` value onto the build PipelineRun it creates.

After a successful build, the integration-service writes the same `deliveryTraceparent` onto the Snapshot it creates. That Snapshot is the durable handoff point for downstream stages and may be read and acted on much later (including weeks or months), potentially in a different reconciliation context or cluster. For any integration PipelineRuns derived from that Snapshot (per IntegrationTestScenario), integration-service propagates the Snapshot’s `deliveryTraceparent` onto each created PipelineRun. When release is initiated, integration-service copies the Snapshot’s `deliveryTraceparent` onto the Release CR; the release-service’s existing behavior then carries it onto release PipelineRuns.

A delivery may produce multiple integration PipelineRuns and multiple release PipelineRuns. The propagation rule remains consistent: any PipelineRun created as part of that delivery and derived from the Snapshot carries the Snapshot’s `deliveryTraceparent`.

### Heterogeneous snapshots and missing context

Some Snapshots may be heterogeneous (components built from different initiating events) or may lack a usable `deliveryTraceparent` (missing/invalid/never seeded). In these cases, integration-service starts a new delivery root span when it performs Snapshot-driven orchestration and writes the new root’s `deliveryTraceparent` onto the Snapshot for continuity going forward.

### Tekton parent resolution

Tekton Pipelines uses strict precedence when choosing the parent for the PipelineRun execution span. If `tekton.dev/pipelinerunSpanContext` exists, Tekton uses it (no behavior change). Otherwise, if `tekton.dev/deliveryTraceparent` exists, Tekton parses it and adopts it as a remote parent. If neither exists, Tekton starts a new root execution trace as it does today. This guarantees delivery tracing cannot override an already-established execution trace parent.

### Timing visibility

Delivery timing is represented by synthetic spans derived from resource timestamps and parented under the delivery trace context:

`wait_duration`: creationTimestamp → `status.startTime`  
`execute_duration`: `status.startTime` → `status.completionTime`

These timing spans are emitted for build, integration, and release PipelineRuns created as part of the delivery. This ensures both end-to-end delivery latency and stage-level breakdown are directly visible from trace data.

## Infrastructure Requirements

No new infrastructure is required beyond existing OTLP trace collection.

## Required Changes (by controller/component)

### PaC (pipelines-as-code)

PaC must emit a delivery span during webhook handling and inject/persist `tekton.dev/deliveryTraceparent` onto the build PipelineRun it creates.

### Tekton Pipelines

Tekton Pipelines must support adopting `tekton.dev/deliveryTraceparent` as a remote parent fallback for PipelineRun execution spans when `tekton.dev/pipelinerunSpanContext` is absent. This change must remain inert when the annotation is missing and must not alter current behavior otherwise.

### Integration-service

Integration-service must:

1. Persist delivery trace context by writing `deliveryTraceparent` onto the Snapshot it creates.  
2. Propagate Snapshot `deliveryTraceparent` onto all integration PipelineRuns and into release orchestration via the Release CR.  
3. Support long-lived/late reconciliation by treating the Snapshot as the durable carrier of delivery context, even when read much later or in a different cluster.  
4. When the Snapshot lacks valid context, create a new delivery root span and write its `deliveryTraceparent` onto the Snapshot for continuity.  
5. Emit `wait_duration` and `execute_duration` timing spans for build, integration, and release PipelineRuns using resource timestamps, parented under the active delivery trace context.

## Pros and Cons of Alternatives Considered

### Separate traces per stage
Good, because it may be simpler logic
Good, because it requires no Tekton changes.  
Bad, because it offers no end-to-end delivery view
Bad, because it offers weaker correlation across controllers/clusters
Bad, because MTTB is harder to compute from trace data across multiple traces.

### Link-only correlation (no remote parentage)
Good, because it avoids parenting concerns
Good, because it works with independent trace roots.  
Bad, because it offers worse navigation/querying than a single tree
Bad, because end-to-end timing analysis is less direct.

### Custom CRD fields for trace context
Good, because it provides typed storage and validation potential.  
Bad, because it requires schema changes and coordination cost
Bad, because it is more invasive than annotation-based propagation.

### Linking of non-triggering build PipelineRuns in Snapshot
Good, because it allows a stochastic sampling of correlated build PipelineRuns included in a multi-component Snapshot.
Bad, because limits on span links result in an _arbitrary_ sampling of component build times.
Bad, because a limited sampling cannot guarantee useful metrics or navigability.

## Consequences

Delivery tracing yields end-to-end trace continuity across controllers and clusters, enabling MTTB analysis and reducing manual correlation. It introduces controller responsibility to propagate `deliveryTraceparent` correctly, depends on an upstream Tekton enhancement to adopt it as a fallback parent, and provides a defined path for missing-context Snapshots by allowing integration-service to establish a new root.
