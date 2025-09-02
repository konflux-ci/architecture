# NN. Revised Component Model

## Status

Proposed
[//]: # (One of: Proposed, Withdrawn, Deferred, Accepted, Implementable, Implemented, Replaced)

## Context

The existing application and component model in Konflux presents several
limitations that hinder our ability to scale and support flexible workflows.
Specifically, the current model requires a new component to be registered for
each use case, even when the same underlying code is being used in multiple
release scenarios. This creates unnecessary overhead and complexity, while also
limiting the reusability of our components.

Furthermore, ownership of the current APIs is unclear. They were originally
owned by HAS (which is now deprecated) and exhibit excessive coupling across
multiple services.

## Decision

We have decided to adopt a revised component model that replaces the concept of
an "application" with a "component group." The key elements of this new model
are:

* **Component Branch**: A component can have one or more component branches,
  which are a combination of a component and a specific branch or tag. A single
  component branch can be referenced by multiple component groups.
  build-service owns the Component API going forwards and the spec changes
  for branches.
* **Component Group**: A component group can contain other component groups or
  component branches, forming a Directed Acyclic Graph (DAG) that represents
  the release structure. This allows for greater flexibility and reusability,
  as a component can be used in multiple groups without re-registration.
  integration-service owns the new Group API and the eventual decommissioning
  of the old Application API.

The implementation will be phased, starting with the core build team and
gradually migrating services and users over time, with the final goal of
decommissioning the old model once the migration is complete.

## Consequences

* Improved Reusability: Component branches can be easily reused across multiple
  component groups and release plans.
* Simplified Model: The new structure is more flexible and intuitive, reducing
  complexity for users.
* Clear Ownership: The Group and Component resources will be clearly associated
  by their controllers (integration-service and build-service respectively).
* Migration Effort: A significant effort is required to design, implement, and
  migrate all existing users and components to the new model.
* UI/UX Changes: The user interface and experience will need to be completely
  updated to reflect the new component group model.
* Documentation Updates: All existing documentation related to components and
  applications must be revised to reflect the new concepts and workflows.
* Partial decoupling: This should give us some progress towards decoupling, but
  the Snapshot resource will remain a common resource referenced by both
  integration service and release service.
