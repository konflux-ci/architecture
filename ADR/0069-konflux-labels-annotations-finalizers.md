---
title: "69. Replace Appstudio Labels, Annotations, and Finalizers with Konflux equivalents"
status: Accepted
applies_to:
  - "*"
topics:
  - api
  - kubernetes
  - labels
  - annotations
  - finalizers
  - branding
  - migration
---

# 69. Replace Appstudio Labels, Annotations, and Finalizers with Konflux equivalents

Date: 2026-06-11

## Status

Accepted

Builds upon [ADR 68. Standardize on konflux-ci.dev as Official API Group](0068-konflux-ci-dev-api-group.md).

## Context

Following the decision in ADR 68 to standardize on `konflux-ci.dev` as the official API group for all Konflux CRDs, a similar branding misalignment exists in Kubernetes labels, annotations, and finalizers currently used throughout the platform.

Konflux currently uses various prefixes for labels, annotations, and finalizers that reflect the project's original identity as "App Studio" and its Red Hat-branded origins:

- `appstudio.openshift.io/*` — Most common prefix for labels and annotations
- `appstudio.redhat.com/*` — Alternative prefix in some services
- `build.appstudio.openshift.io/*` — Build-service specific labels/annotations
- `appstudio.application/*`, `appstudio.component/*` — Legacy label patterns
- `pac.test.appstudio.openshift.io/*` — Pipelines as Code integration labels
- Various finalizers with `appstudio` in their names

### Issues with Current Naming

The current label, annotation, and finalizer naming presents the same fundamental issues as the API group naming:

- **Brand misalignment**: The project is publicly known as Konflux, not App Studio. Labels and annotations appear in every resource manifest and are highly visible to users, operators, and tooling.

- **Vendor coupling**: The `.redhat.com` and `.openshift.io` domains imply Red Hat and OpenShift ownership, inconsistent with Konflux's positioning as an open-source, vendor-neutral, community-driven platform.

- **Ecosystem expectations**: Modern Kubernetes projects use labels and annotations that reflect the project name and avoid vendor-specific domains (e.g., `tekton.dev/*`, `knative.dev/*`, `argoproj.io/*`).

- **Technical debt**: Continuing with `appstudio` prefixes perpetuates brand confusion and creates long-term maintenance burden as the codebase grows.

- **Discovery and debugging**: Labels and annotations are critical for resource discovery, filtering, monitoring, and debugging. Having them clearly associated with "Konflux" improves user experience and reduces confusion.

### Scope

This ADR covers all Kubernetes metadata fields that are user-visible or persisted in etcd:

1. **Labels** — Used for resource selection, filtering, and organization
2. **Annotations** — Used for non-identifying metadata, configuration hints, and cross-service communication
3. **Finalizers** — Used to control resource deletion and cleanup logic

This ADR does NOT cover:

- Internal variable names, function names, or code identifiers (these are implementation details)
- Log messages or debug output (unless they expose appstudio names to users)
- Non-Kubernetes metadata (e.g., git commit messages, build artifact metadata)

### Current Usage Inventory

A comprehensive audit of the codebase reveals the following high-level categories of labels, annotations, and finalizers that need migration:

**Common Label Patterns:**
- `appstudio.openshift.io/application` — Application association
- `appstudio.openshift.io/component` — Component association
- `appstudio.openshift.io/environment` — Environment association
- `build.appstudio.openshift.io/pipeline` — Pipeline identification
- `pac.test.appstudio.openshift.io/*` — Pipelines as Code integration
- `appstudio.application`, `appstudio.component` — Legacy short-form labels

**Common Annotation Patterns:**
- `build.appstudio.openshift.io/*` — Build configuration and metadata
- `integration.appstudio.openshift.io/*` — Integration test configuration
- `release.appstudio.openshift.io/*` — Release configuration
- `appstudio.redhat.com/*` — Cross-cutting annotations
- `metrics.appstudio.redhat.com/*` — Metrics and telemetry annotations
- `image.redhat.com/*` — Image metadata (less common, but present)

**Common Finalizer Patterns:**
- `appstudio.redhat.com/*` — Various service finalizers
- `appstudio.openshift.io/*` — Alternative finalizer prefix
- Service-specific finalizers with `appstudio` embedded

The exact inventory of labels, annotations, and finalizers will be maintained in a tracking document separate from this ADR, as the list is large and changes frequently during active development.

## Decision

- The official domain for all Konflux labels and annotations is `konflux-ci.dev`.
- The official domain for all Konflux finalizers is `konflux-ci.dev`.
- All new labels, annotations, and finalizers introduced to Konflux MUST use the `konflux-ci.dev` domain.
- Existing labels, annotations, and finalizers currently using `appstudio.openshift.io`, `appstudio.redhat.com`, `build.appstudio.openshift.io`, or other `appstudio` occurances MUST be migrated to `konflux-ci.dev` following a controlled deprecation process.
- The migration will follow a dual-support approach during the transition period:
  1. Controllers and operators are updated to recognize and write BOTH old (`appstudio`) and new (`konflux-ci.dev`) metadata.
  2. New resources created during the transition period receive BOTH old and new metadata to ensure backward compatibility.
  3. Controllers are updated to prefer reading from new metadata but fall back to old metadata if new is absent.
  4. After a deprecation period, support for old metadata is removed and only `konflux-ci.dev` metadata is written and read.
- The naming structure should follow established Kubernetes conventions:
  - Use lowercase with hyphens for multi-word components: `konflux-ci.dev/component-name`, not `konflux-ci.dev/componentName`
  - Use hierarchical naming for service-specific metadata: `build.konflux-ci.dev`, `integration.konflux-ci.dev`, `release.konflux-ci.dev`
  - Preserve semantic meaning from old names where possible to ease migration
- Labels and annotations do NOT require changes to their semantic meaning or usage pattern. For example, `appstudio.openshift.io/component: my-component` becomes `konflux-ci.dev/component: my-component` — only the prefix changes.
- Finalizers follow the same naming pattern: `appstudio.redhat.com/integration-finalizer` becomes `konflux-ci.dev/integration-finalizer`; `appstudio.openshift.io/image-repository` becomes `konflux-ci.dev/image-repository`.
- In case a new name could give more clarity, it should be used instead during the migration.

## Migration Plan

For the cross team or cross component functionality, the migration will be executed in **four phases**
to minimize user disruption and ensure backward compatibility.

If the items to migrate are scoped to internal resources of only one service (e.g. a finalizer rename) OR
the migration could be fully automated on cross services internal resources, then the migration plan could be simplified.

### Phase 1: Dual Write (Controllers Updated)

**Actions:**
1. Update all controllers, operators, and webhooks to write BOTH old and new metadata when creating or updating resources.
2. Update all controllers to read from new metadata first, falling back to old metadata if new is absent.
3. Update tests.
4. Update internal documentation and developer guides.

**Validation:**
- All new resources created during this phase have both `appstudio` and `konflux-ci.dev` metadata.
- Controllers can successfully read resources with either old-only, new-only, or dual metadata.
- No functional regressions in resource reconciliation or selection.

**User Impact:**
- None. This phase is fully backward compatible.
- Users may notice both old and new metadata appearing on new resources, but existing resources are unchanged.

### Phase 2: Backfill Existing Resources

**Actions:**
1. Develop and test a migration script/controller that backfills new metadata onto existing resources.
2. Run the migration script in non-production environments first (dev, staging).
3. Announce the migration plan to users with a clear timeline and instructions.
4. Execute the migration script in production environments (gitops and clusters) or via a dedicated controller.
5. Validate that all resources in all namespaces have both old and new metadata.

**Validation:**
- 100% of resources have dual metadata (both `appstudio` and `konflux-ci.dev`).
- No resources were missed by the migration script.
- No functional disruptions during or after backfill.

**User Impact:**
- Minimal. Users may see additional metadata appear on their existing resources.
- GitOps users must update their manifests to include new metadata to avoid sync drift.

### Phase 3: Deprecation Period (Documentation and Warnings)

**Actions:**
1. Update all official documentation, examples, tutorials, and guides to use only `konflux-ci.dev` metadata.
2. Add deprecation notices to the old metadata in documentation.
4. Provide migration tooling to update GitOps repositories.
5. Communicate the deprecation timeline through announcements, community calls, and documentation.

**Validation:**
- Official documentation references only `konflux-ci.dev` metadata.
- Migration tooling is available and can be executed.

**User Impact:**
- Users are notified of the deprecation and given time to migrate.
- Users who rely on custom tooling (scripts, GitOps pipelines, monitoring queries) that references old metadata must update their tooling.
- All functionality continues to work during this period.

### Phase 4: Removal of Old Metadata Support

**Actions:**
1. Update all controllers to stop writing old metadata.
2. Update all controllers to stop reading from old metadata (remove fallback logic).
3. Run a cleanup to remove old metadata from existing resources.
4. Remove old metadata from all documentation and examples.
5. Announce the completion of the migration.

**Validation:**
- No controllers reference old metadata in code.
- New resources created after this phase have only `konflux-ci.dev` metadata.
- No functional regressions.

**User Impact:**
- Users who did not migrate their custom tooling during the deprecation period may experience issues if their tooling relies exclusively on old metadata.
- Official Konflux tooling and documentation will no longer support old metadata.

## Migration Plan and the New Component Model

The resources in [New Component model](0056-revised-component-model.md) can support only new `konflux-ci.dev` naming from start.
In such case the migration should be done during migration from the old to the new model.

## Consequences

### Positive

- **Brand alignment**: Labels, annotations, and finalizers clearly reflect the Konflux project identity, reducing user confusion and improving discoverability.

- **Vendor neutrality**: Removing `.redhat.com` and `.openshift.io` domains positions Konflux as a vendor-neutral, open-source platform.

- **Consistency with API group decision**: Aligns metadata naming with the `konflux-ci.dev` API group standardization from ADR 68, creating a cohesive branding strategy.

- **Improved user experience**: Users can easily identify Konflux-related metadata in their resources, improving debugging and operational clarity.

- **Long-term maintainability**: Eliminates technical debt from legacy `appstudio` naming, reducing confusion for new contributors and maintainers.

- **Ecosystem alignment**: Matches naming conventions of other CNCF and Kubernetes ecosystem projects.

### Negative

- **Migration complexity**: Updating labels, annotations, and finalizers across all controllers, resources, and user manifests is a significant engineering effort.

- **Risk of breaking changes**: Label selector and annotation-reading logic is fragile. Any mistakes in migration could break resource reconciliation, testing, or deployment.

- **User disruption**: Users managing resources via GitOps or custom tooling must update their repositories and scripts. The deprecation period mitigates this, but does not eliminate it.

- **Increased controller complexity during transition**: Controllers must support dual metadata during the migration period, adding conditional logic and increasing test surface area.

- **Documentation burden**: All documentation, examples, tutorials, and guides must be updated to reflect new metadata. During the transition period, documentation must explain both old and new metadata, which adds complexity.

- **Backward compatibility concerns**: External tools and integrations that are not actively maintained may break if they rely exclusively on old metadata and are not updated before Phase 4.

## Alternatives Considered

### Retain `appstudio` Naming Indefinitely

This alternative would leave the current label, annotation, and finalizer naming unchanged, avoiding all migration costs.

This approach is rejected because:

- It perpetuates the same brand misalignment and vendor coupling issues identified in ADR 68.
- It creates inconsistency between the API group (`konflux-ci.dev`) and the metadata prefixes (`appstudio`), which is confusing for users.
- It signals to the community that the project is not committed to its rebranding and open-source identity.

### Introduce `konflux-ci.dev` Only for New Services

This alternative would introduce `konflux-ci.dev` metadata only for new services or features, leaving existing services on `appstudio` permanently.

This approach is rejected because:

- It fragments the metadata namespace, creating inconsistency across the platform. Users would need to remember which services use which prefix.
- It does not address the brand misalignment issue for core services and resources.
- It increases long-term maintenance burden by requiring indefinite support for two metadata namespaces.

### Use a Shorter Prefix (e.g., `konflux.dev` or `konflux`)

Alternative domain options include `konflux.dev` or even omitting the domain entirely (e.g., `konflux`).

These are rejected because:

- `konflux-ci.dev` is the established project domain and is used for the project's API group (ADR 68), web presence, and documentation. Using a different domain for metadata would create unnecessary fragmentation.
- Omitting the domain entirely (`konflux`) violates Kubernetes best practices, which recommend using fully-qualified domain prefixes for labels and annotations to avoid collisions.
- `konflux.dev` redirects to `konflux-ci.dev`, so `konflux-ci.dev` is the canonical domain.

### Immediate Hard Cutover (No Dual-Support Period)

This alternative would skip the dual-support phases and immediately replace all old metadata with new metadata in a single release.

This approach is rejected because:

- It creates a high-risk, high-disruption event for users, especially those managing resources via GitOps.
- It breaks external tools and integrations with no grace period for migration.
- It increases the likelihood of bugs and missed resources during migration.
- The dual-support approach adds complexity but significantly reduces user disruption and risk.

## References

- [ADR 68. Standardize on konflux-ci.dev as Official API Group](0068-konflux-ci-dev-api-group.md) — Establishes `konflux-ci.dev` as the official domain for Konflux APIs.
- [ADR 56. Revised Component Model](0056-revised-component-model.md) — defines new Application and Component model.
- [Kubernetes Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/) — Best practices for Kubernetes labels.
- [Kubernetes Annotations](https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/) — Best practices for Kubernetes annotations.
- [Kubernetes Finalizers](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/) — Understanding finalizer behavior and usage.
