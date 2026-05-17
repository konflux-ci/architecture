---
title: "67. Nudging Relationship Storage via Singleton CRD"
status: Proposed
applies_to:
  - integration-service
  - build-service
topics:
  - nudging
  - component-dependencies
  - orchestrated-builds
  - singleton-crd
---

# 67. Nudging Relationship Storage via Singleton CRD

Date: 2026-05-11

## Status

Proposed

Partially supersedes [ADR 29. Component Dependencies](0029-component-dependencies.html)
with respect to nudging relationship storage and execution. This ADR
moves both the nudge configuration (from the Component CR's
`build-nudges-ref` field to a new `NudgeConfig` CRD) and the nudge
execution (from build-service to integration-service). The nudging
*concept* — directed component-to-component dependency edges that
trigger downstream rebuilds via Renovate — remains as defined in ADR 29.
Build-service retains ownership of the build pipeline and Renovate
tooling; integration-service becomes the orchestrator that decides
*when* and *whether* a nudge fires.

Builds upon [ADR 60. ComponentGroups](0060-component-groups.html) and
[ADR 56. Revised Component Model](0056-revised-component-model.html).

## Context

### Current State

Today, component nudging relationships are defined in the `Component` CR
via the `build-nudges-ref` field in the spec
([ADR 29](0029-component-dependencies.html)). When a component build
succeeds, the build-service triggers Renovate to create pull requests
that update image references in downstream ("nudged") components.

### Problems with the Current Approach

The [revised component model](0056-revised-component-model.html) and the
introduction of [ComponentGroups](0060-component-groups.html) create
several problems for the current nudging storage:

1. **Ownership boundary violation.** Under the revised model, the
   build-service owns the `Component` CR while the integration-service
   owns orchestration and testing. Keeping nudging relationships on the
   Component spec forces the build-service to understand dependency
   semantics it should not own.

2. **Redundant builds.** The current immediate-nudge-on-build model
   triggers downstream builds before upstream tests have passed. When
   upstream tests fail, the downstream builds are wasted. With
   multi-component groups this problem compounds: an operator bundle
   component may be nudged N times for N upstream builds that could have
   been batched into a single nudge after validation.

3. **Component Group ambiguity.** A component can belong to multiple
   ComponentGroups. Storing nudge relationships on the component makes it
   impossible to express group-scoped nudging rules without ambiguity.

4. **No structured API for UI consumption.** The current field is a
   simple list embedded in the Component spec. The UI team cannot easily
   discover or visualize the full dependency graph across a namespace.

5. **Application-scoped limitations.** Under ADR 29, nudge
   relationships are Application-scoped — cross-Application nudges are
   invalid. With the deprecation of the Application CR (ADR 56/60) and
   the introduction of ComponentGroups where a component can belong to
   multiple groups, Application-scoping is no longer a meaningful
   boundary. This ADR intentionally broadens nudge scope to the
   namespace level, which aligns with Konflux's existing tenant
   isolation boundary. All components within a namespace may participate
   in nudge relationships regardless of their ComponentGroup membership.

### Alternatives Considered

| Alternative | Why rejected |
|---|---|
| **Annotation on Component CR** | Unstructured data, poor UI discoverability, no schema validation. Breaks backward compatibility when adding future fields (e.g., nudge timing mode). |
| **Annotation on build PipelineRun** | Requires git-stored configuration, removes the ability to manage dependencies through the UI. |
| **ConfigMap per namespace** | Same etcd footprint as a CR but without schema validation, RBAC granularity, or structured API. Expensive to watch and cache. |
| **Dedicated CRD per component pair** | Object explosion risk: namespaces with many components could create thousands of CRs, exacerbating etcd pressure. |
| **Field on ComponentGroup CR** | A component can belong to multiple ComponentGroups, making it ambiguous where the relationship is defined. Also mixes group topology concerns with dependency concerns. |

### Constraints

- **etcd pressure.** The Konflux infrastructure team has identified etcd
  storage as the primary scaling bottleneck. Any new CR must minimize
  object count. The singleton-per-namespace design ensures at most one
  NudgeConfig CR exists per tenant namespace, and only in namespaces
  that use nudging. This is negligible compared to the per-build
  PipelineRun objects that dominate etcd storage.

- **1 MB resource size limit.** Kubernetes enforces a 1 MB limit per
  resource. The singleton design must account for namespaces with many
  component relationships.

- **Stale data.** When components are deleted, the nudging configuration
  must not retain references to non-existent components, otherwise
  downstream nudge attempts will fail or produce confusing errors.

## Decision

Introduce a new **`NudgeConfig`** Custom Resource Definition, implemented
as an **optional singleton per namespace**, to store all component nudging
relationships for that namespace. Namespaces that do not use nudging
do not need to create a `NudgeConfig`. Ownership of nudging relationship
storage moves from the build-service (`Component` CR) to the
integration-service.

### CRD Design

```yaml
apiVersion: konflux-ci.dev/v1alpha1
kind: NudgeConfig
metadata:
  name: nudge-config          # singleton — one per namespace
  namespace: my-tenant
spec:
  nudges:
    - from: component-a       # source component (the one being built)
      to: component-b         # target component (the one to be nudged)
      mode: validated          # "immediate" | "validated"
      gatingGroup: frontend-group  # required when mode=validated
    - from: component-a
      to: component-c          # mode defaults to "immediate"
    - from: component-d
      to: component-e
      mode: validated
      gatingGroup: backend-group
status:
  conditions:
    - type: Valid
      status: "True"
      reason: AllComponentsExist
      message: "All referenced components exist in namespace"
    - type: Valid
      status: "False"
      reason: StaleReferences
      message: "Components [component-x] referenced in nudges no longer exist"
  lastValidationTime: "2026-05-11T10:00:00Z"
```

### Fields

| Field | Type | Description |
|---|---|---|
| `spec.nudges` | `[]NudgeRelationship` | List of directed component-to-component nudge edges. |
| `spec.nudges[].from` | `string` | Name of the source component whose build triggers the nudge. |
| `spec.nudges[].to` | `string` | Name of the target component to be nudged. |
| `spec.nudges[].mode` | `enum` | Optional. `immediate`: nudge fires after the source build PLR succeeds. `validated`: nudge fires after the Snapshot for the gating ComponentGroup passes integration tests. Defaults to `immediate` if omitted. |
| `spec.nudges[].gatingGroup` | `string` | Name of the ComponentGroup whose Snapshot must pass integration tests before the nudge fires. Required when `mode: validated`; ignored for `immediate`. Phase 1 reserves this field; implementation deferred to Phase 2. |
| `status.conditions` | `[]metav1.Condition` | Reports validation state — specifically whether all referenced components still exist. |
| `status.lastValidationTime` | `metav1.Time` | Timestamp of the last stale-reference validation run. |

### Singleton Enforcement

The singleton constraint is enforced via a CEL validation rule in the
CRD schema (`x-kubernetes-validations`) that restricts
`metadata.name` to `nudge-config`. This runs in-process in the API
server with no webhook overhead. Attempts to create an instance with
any other name are rejected.

### Validation Rules

The following constraints are enforced on `NudgeConfig`, inheriting
the DAG enforcement responsibility from Application-service (which is
being deprecated per ADR 56/60). Stateless rules use CEL validation
in the CRD schema; stateful rules that require cluster queries use a
[ValidatingAdmissionPolicy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)
or a lightweight webhook.

**Stateless (CRD-level CEL):**

1. **Self-nudge rejection.** An entry where `from` equals `to` is
   rejected. A component cannot nudge itself.

2. **Duplicate pair rejection.** Only one entry per `(from, to)` pair is
   allowed. If a user needs to change the mode for an existing pair,
   they must update the existing entry rather than add a second one.

3. **Cycle detection.** The set of nudge entries forms a directed graph.
   Any update that would introduce a cycle is rejected, including
   transitive cycles (e.g., A→B→C→A). This prevents infinite nudge
   loops. Validation is performed on the full graph within the
   `NudgeConfig` on every create/update.

**Stateful (ValidatingAdmissionPolicy or webhook):**

4. **Component existence validation.** Both `from` and `to` must
   reference components that exist in the namespace at the time of
   creation. Post-creation staleness (component deleted after the entry
   was added) is handled by the stale reference controller described
   below, not by the admission check.

### Nudging Flow

In Phase 1, nudging is triggered by push (post-merge) build
PipelineRuns only, consistent with the current ADR 29 behavior. The
design does not preclude extending nudging to pull request builds in
the future.

#### Immediate Mode (`mode: immediate`)

```
Build PLR succeeds for component-a
  → integration-service reads NudgeConfig
  → finds edge: component-a → component-b (immediate)
  → triggers Renovate nudge PipelineRun for component-b
    in the tenant namespace
  → component-b build starts immediately
```

#### Validated Mode (`mode: validated`)

```
Build PLR succeeds for component-a
  → integration-service updates GCL in the gating ComponentGroup
  → Snapshot is created with latest GCL images
  → Integration tests run against the Snapshot
  → All tests pass (Snapshot is marked as successful)
  → integration-service reads NudgeConfig
  → finds edge: component-a → component-b (validated, gatingGroup: frontend-group)
  → triggers Renovate nudge PipelineRun for component-b
    in the tenant namespace, using the validated image digest
    from the passing Snapshot
```

The validated mode leverages the Global Candidate List (GCL) and
Snapshot infrastructure to eliminate redundant downstream builds. Instead
of nudging N times for N upstream builds, the integration-service waits
for the Snapshot to pass and fires a single nudge with the validated
image.

Since a component can belong to multiple ComponentGroups
([ADR 60](0060-component-groups.html)), the `gatingGroup` field
explicitly resolves which group's Snapshot must pass before the nudge
fires. This avoids ambiguity when the source component participates in
multiple groups with different test configurations.

### Migration from `build-nudges-ref`

The integration-service will perform a one-time migration:

1. Read existing `build-nudges-ref` values from all `Component` CRs in
   each namespace.
2. Generate the corresponding `NudgeConfig` singleton with `mode:
   immediate` (preserving current behavior).
3. After migration is confirmed, the `build-nudges-ref` field is
   deprecated and eventually removed from the Component spec.

Users who want validated nudging can then update their `NudgeConfig` to
change specific edges to `mode: validated`.

For users managing resources via GitOps, the automated migration
creates the `NudgeConfig` on the cluster, but git-stored Component
manifests must also be updated manually. Users should remove the
`build-nudges-ref` field from their Component definitions and add the
generated `NudgeConfig` manifest to their repository to prevent
GitOps sync conflicts during the deprecation period. For managed
production clusters, a migration script must be provided to
automate these GitOps repository changes at scale.

Existing nudge PR customization mechanisms are handled as follows:

- **`build-nudge-files`** (annotation on the push build PipelineRun,
  not the Component CR) specifies file-pattern regexes for Renovate to
  match when updating image references. As part of this migration,
  integration-service deprecates this PipelineRun annotation in favor
  of ConfigMap-based file-pattern configuration, consistent with
  rcerven's recommendation and the overall move away from
  annotation-driven config.

- **`build-nudge-simple-branch`** (annotation on the Component CR)
  controls Renovate branch naming. Since integration-service takes
  over nudge orchestration, it reads this annotation from the
  Component and propagates it to the Renovate PipelineRun it creates.

Renovate behavior customization is configured via a two-tier
ConfigMap mechanism, which integration-service inherits ownership of:

- **Namespace-wide default:** A ConfigMap named
  `namespace-wide-nudging-renovate-config` (mandatory name) applies to
  all nudged components in the namespace. Supported keys include
  `automerge`, `commitMessagePrefix`, `commitMessageSuffix`,
  `fileMatch`, `automergeType`, `platformAutomerge`, `ignoreTests`,
  `gitLabIgnoreApprovals`, `automergeSchedule`, and `labels`.

- **Per-component override:** If the nudged (target) component has
  annotation `build.appstudio.openshift.io/nudge_renovate_config_map`,
  the named ConfigMap is used instead of the namespace-wide default.

Note: user-created ConfigMaps are not mounted directly into the
Renovate PipelineRun. The orchestrating controller reads the
appropriate ConfigMap, merges the options into the generated Renovate
configuration, and saves the final config as a temporary ConfigMap
that is mounted into the PipelineRun and garbage-collected with it.
Integration-service preserves this behavior.

#### Behavioral Changes from ADR 29

Under ADR 29, integration-service skips all testing for nudging
components — builds are promoted to the GCL but never tested,
deployed, or released directly. This ADR preserves that behavior for
`immediate` mode: the nudging component's build is not independently
tested before firing the nudge.

In `validated` mode, this behavior changes: the nudging component's
build is included in a Snapshot that must pass integration tests before
the nudge fires. Users switching an entry from `immediate` to
`validated` should be aware that this enables testing for the nudging
component, which may require configuring appropriate
IntegrationTestScenarios.

### Stale Reference Handling

A controller in the integration-service reconciles the `NudgeConfig`
whenever:

- A `Component` CR is deleted from the namespace.
- The `NudgeConfig` itself is modified.

On reconciliation:

1. List all `Component` CRs in the namespace.
2. Validate that every `from` and `to` reference in `spec.nudges` maps
   to an existing component.
3. Update `status.conditions` to report any stale references.
4. Stale entries are **not** automatically deleted — the controller
   reports them via status conditions so the user or UI can remediate.
   This avoids silent data loss if a component is temporarily removed
   and re-created.

### 1 MB Size Limit Considerations

Each nudge entry is approximately 100–150 bytes of JSON. A 1 MB resource
can hold roughly 7,000–10,000 nudge relationships. Even in namespaces
with thousands of components, the number of nudge edges is bounded by
actual dependency relationships, which are typically sparse relative to
the total component count. The CRD schema enforces a `maxItems: 5000`
constraint on the `spec.nudges` array to stay well within the 1 MB
limit with margin for metadata overhead.

## Consequences

### Positive

- **Clean ownership boundary.** Nudging configuration is owned by the
  integration-service, consistent with the revised component model where
  integration-service owns orchestration.

- **Minimal etcd impact.** One lightweight CR per namespace (only in
  namespaces that use nudging) adds negligible load. Each NudgeConfig is
  on the order of 1–10 KB depending on the number of entries, compared
  to per-build PipelineRun objects that dominate etcd storage.

- **Structured API for UI.** The CRD provides a typed, validated schema
  that the UI team can consume directly to visualize the dependency
  graph, without parsing annotations or searching for ConfigMaps.

- **Reduced redundant builds.** The `validated` mode eliminates wasted
  downstream builds by waiting for upstream tests to pass before nudging.

- **Future extensibility.** The schema can be extended in Phase 2 to
  support component-to-group and group-to-group relationships by adding
  new fields to `NudgeRelationship` without breaking existing entries.

### Negative

- **New CRD to maintain.** Adds one more CRD to the integration-service
  API surface. Requires a controller for stale-reference validation.

- **Migration effort.** Existing users must be migrated from
  `build-nudges-ref` to `NudgeConfig`. An automated migration path is
  defined above, but some manual validation may be needed.

- **Singleton pattern is unusual.** The one-per-namespace constraint
  requires webhook enforcement and may surprise users who expect to
  create per-component configurations.

### Phase 2 (Out of Scope)

The following are explicitly deferred to a future ADR:

- Component-to-ComponentGroup nudge relationships.
- ComponentGroup-to-ComponentGroup nudge relationships.
- Nudge timing configuration beyond immediate/validated (e.g., nudge
  before vs. after a specific test).
- Batched nudging for operator bundles — wait for multiple upstream
  components to produce new builds before firing a single nudge to the
  downstream component. This addresses the current pain point where an
  operator bundle is rebuilt N times for N upstream operand builds.
- UI for editing NudgeConfig (the API is designed to support it).

## References

- [ADR 29. Component Dependencies](0029-component-dependencies.html) —
  defines the current `build-nudges-ref` mechanism.
- [ADR 56. Revised Component Model](0056-revised-component-model.html) —
  introduces component versions and service ownership boundaries.
- [ADR 60. ComponentGroups](0060-component-groups.html) — defines the
  ComponentGroup CR with GCL and test graph.
- [STONEINTG-1588](https://issues.redhat.com/browse/STONEINTG-1588) —
  spike investigating nudging relationship storage.
- [STONEINTG-1495](https://issues.redhat.com/browse/STONEINTG-1495) —
  epic for implementing component nudging logic in integration-service.
- [Component nudges documentation](https://konflux.pages.redhat.com/docs/users/building/component-nudges.html)
  — current user-facing documentation.
