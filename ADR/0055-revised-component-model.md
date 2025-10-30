# NN. Revised Component Model

## Status

Proposed
[//]: # (One of: Proposed, Withdrawn, Deferred, Accepted, Implementable, Implemented, Replaced)

## References

* [Konflux Community Call, 2025-03-11](https://www.youtube.com/watch?v=IwNFRNjRC_Q)
* [Konflux Community Call, 2025-03-25](https://www.youtube.com/watch?v=VwzDbUH_vjU)

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
* Nudging: The "nudging" feature will need design changes. There is some idea
  to nudge the same component branch (by name) across components with ability
  to configure/override the behavior - but at this time not yet clearly
  defined.

## Roadmap

At the time of this writing, we have a low level of detail about the particular spec of the
new Component API and the Group API. The following is an ordered roadmap of
activities to move that forwards.

* The build team designs and implements a new component object with component branches.
* The build team updates the build service so it supports components with the branches.
* The build team updates the documentation to mention components with component branches.
* The UI team adds support for the new components with components into branches into the UI.
  * The old model stays the primary model for the UI. Users can switch to the UI for the new model by toggling options in the UI.
* The MintMaker team updates MintMaker so it provides dependency management for the new components.
* The feature owner announces the new model as a tech preview to the users.
* The integration team designs and implements a new group object.
* The integration team updates the Snapshot creation to also support creating snapshots from groups.
* The integration team updates the integration service so it supports integration testing for groups and group snapshots.
* The integration team updates documentation to mention groups.
* The UI team adds support for the groups into the UI.
  * Features *Status Reporting* and *Run Visualization* do not block changes to releases.
* The feature owner announces Groups to the users.
* The release team updates the release service so it supports releases of groups and group snapshots.
* The feature owner announces the ability to release group-based snapshots to the users.
* Konflux implores the users to start migrating to the new model.
* The UI team makes the new model the primary one for the Konflux UI.
* The old component/application model is decommissioned.
  * The build and integration teams automatically migrate existing users that are using the old model to the new one.
    * The build team is responsible for migration of the components.
    * The integration team is responsible for migration of the groups-applications.
  * The feature owner deletes the documentation connected to the old mode.
  * The UI team removes the support for the old model from the UI.
  * The build and integration teams  remove CDR connected to the old model from clusters.
  * Konflux teams responsible for the Konflux services and functionality remove support for the old mode.
