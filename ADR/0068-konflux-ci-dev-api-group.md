---
title: "68. Standardize on konflux-ci.dev as Official API Group"
status: Proposed
applies_to:
  - "*"
topics:
  - api
  - kubernetes
  - crds
  - branding
---

# 68. Standardize on konflux-ci.dev as Official API Group

Date: 2026-05-28

## Status

Proposed

## Context

Konflux currently uses different API Groups for its Custom Resource Definitions (CRDs).
The majority of the resources have `appstudio.redhat.com` as the API group.
This naming reflects the project's original identity as "App Studio," a Red Hat-branded
internal initiative. Since then, the project has evolved into Konflux, an open-source platform with
a broader community and upstream-first approach.

The `appstudio.redhat.com` API group presents several issues:

- **Brand misalignment**: The project is now publicly known as Konflux, not App Studio. API groups
  are highly visible to users (in every YAML manifest) and serve as a primary namespace for the
  project's API surface. The current API group does not reflect the project's identity.

- **Red Hat coupling**: The `.redhat.com` domain implies ownership and control by Red Hat, which is
  inconsistent with the project's positioning as an open-source, community-driven platform. While
  Red Hat remains a significant contributor, the API namespace should reflect the project's
  independence.

- **Migration precedent**: Similar projects have successfully migrated API groups as they matured
  (e.g., Tekton to `tekton.dev` replacing earlier experimental groups). Kubernetes itself has
  established patterns for API group migration and deprecation.

- **Ecosystem expectations**: Modern Kubernetes projects typically use API groups that reflect the
  project name and are not tied to a single vendor (e.g., `tekton.dev`, `knative.dev`,
  `argoproj.io`). The `konflux-ci.dev` domain is already registered and used for the project's web
  presence, making it the natural choice for API groups.

Continuing with `appstudio.redhat.com` as the long-term API group would perpetuate technical debt
and brand confusion. As Konflux approaches production maturity and broader adoption, establishing a
consistent, project-aligned API namespace is essential.

## Decision

- The official API group for all Konflux CRDs is `konflux-ci.dev`.

- All new CRDs introduced to Konflux MUST use the `konflux-ci.dev` API group.

- Existing CRDs currently using `appstudio.redhat.com` MUST be migrated to `konflux-ci.dev`
  following a controlled deprecation process:
  1. Introduce dual API group support in controllers (accept both `appstudio.redhat.com` and
     `konflux-ci.dev` versions of the same resource).
  2. Announce the deprecation of `appstudio.redhat.com` API group with a clear timeline.
  3. Migrate documentation, examples, and default templates to use `konflux-ci.dev`.
  4. Remove support for `appstudio.redhat.com` API group after the deprecation period.

- CRDs using `appstudio.redhat.com` MAY continue to be supported during the migration period, but
  new features and API versions MUST be introduced under `konflux-ci.dev`.
  New features MAY be backported to `appstudio.redhat.com` if required.

- The API group change does NOT require changes to resource names or kinds. For example,
  `Component` remains `Component`; only the `apiVersion` field changes from
  `appstudio.redhat.com/v1alpha1` to `konflux-ci.dev/v1alpha1` (or `v1` or another version).

## Consequences

- **Migration effort**: Controllers and other resources must be updated to support both API groups
  during the transition period. This requires changes to CRD definitions, controller code, and
  validation webhooks. However, Kubernetes conversion webhooks and multi-version CRD support provide
  established patterns for this migration.

- **User impact**: Existing users will need to update their YAML manifests in gitops repositories to
  use the new API group. This can be automated with tooling (e.g., `kustomize`, `yq`, or custom scripts),
  and the deprecation period allows time for communication and migration.

- **Documentation update**: All documentation, examples, tutorials, and operator guides must be
  updated to reference `konflux-ci.dev`. During the migration period, documentation should
  explicitly note the deprecation of `appstudio.redhat.com`.

- **Backward compatibility**: Controllers supporting both API groups will have increased complexity
  during the transition. Once migration is complete and `appstudio.redhat.com` support is removed,
  this complexity can be eliminated.

- **Brand consistency**: Using `konflux-ci.dev` aligns the API surface with the project's public
  identity, reducing confusion for new users and reinforcing the project's open-source positioning.

- **Upstream alignment**: Adopting a vendor-neutral API group positions Konflux more favorably for
  upstream adoption, integration with other CNCF projects, and contributions from a broader
  community.

- **Future flexibility**: If Konflux's organizational structure or branding changes in the future,
  `konflux-ci.dev` provides a stable, project-specific namespace that is not tied to any single
  vendor or corporate entity.

## Alternatives Considered

### Retain `appstudio.redhat.com` Indefinitely

This alternative would leave the current API group unchanged, avoiding migration costs.

This approach is rejected because:

- It perpetuates brand misalignment and vendor coupling, undermining the project's identity as an
  open-source platform.
- It creates long-term technical debt. Migrating later becomes progressively more expensive as
  adoption grows.
- It sends a signal to the community that the project is not committed to its open-source identity.

### Introduce `konflux-ci.dev` Only for New Services

This alternative would introduce `konflux-ci.dev` only for new services or major API versions,
leaving existing CRDs on `appstudio.redhat.com` permanently.

This approach is rejected because:

- It fragments the API namespace, creating inconsistency across the platform. Users would need to
  remember which resources use which API group.
- It does not address the brand misalignment issue for core resources like `Application`,
  `Component`, `Snapshot`, and `Release`, which remain on `appstudio.redhat.com`.
- It increases long-term maintenance burden by requiring indefinite support for two API groups.
- Majority of the core resources are already created.

### Use a Different Domain

Other domain options include `konflux.io`, `konflux.dev`, or `konflux.konflux-ci.dev`.

These are rejected because:

- `konflux-ci.dev` is already the established project domain and is used for the project's web
  presence and documentation.
- `konflux.dev` redirects to `konflux-ci.dev`, so is an option, but still the primary domain is
  `konflux-ci.dev`.
- Introducing a different domain for APIs would create unnecessary fragmentation.
- `konflux-ci.dev` clearly identifies the project and aligns with Kubernetes ecosystem naming
  conventions (e.g., `tekton.dev`, `knative.dev`).
