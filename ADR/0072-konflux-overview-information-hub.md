---
title: "72. Konflux Overview Page as an Information Hub"
status: Proposed
applies_to:
  - "*"
topics:
  - user-interface
  - communications
  - configuration
---

# 72. Konflux Overview Page as an Information Hub

Date: 2026-11-06

## Status

Proposed for peer discussion. The two approaches for delivering information to Overview remain open for review. Research so far consists of reviewing source code and documentation; deployment tests have yet to be run.

## Context

Overview is the first page users encounter when entering Konflux, but it currently provides little to no value. Users investigating a failed pipeline or a policy violation need to find their next step. They may also need to know whether a service disruption or a recently announced change affects what they are seeing. That information is spread across communication channels, documentation, dashboards and a separate portal. Users must know where to look, leave Konflux and connect the information themselves.

The landing page is an opportunity to make relevant information and its authoritative sources easier to find while users are working. Different users and deployments need different information. A useful Overview must help users recognize what matters to them without becoming another page of unrelated content. This proposal addresses how Overview can become that relevant entry point, beginning with service communications.

## Decision

We propose starting with two widgets on Overview: announcements and service status. They will show information relevant to the user's Konflux environment and link to further details. Users will be able to hide optional widgets and restore them when needed.

The sections below describe the proposed experience and two ways to deliver its information. We are seeking agreement on the initial scope, the delivery approach and the teams responsible for keeping the information available and current.

### What users will see

- **Announcements** will show recent changes and notices relevant to the user's environment. Each announcement will have a short summary, its date and a link to the full information. This gives users a place to find communications they may have missed in email or chat.
- **Service status** will help users understand whether a problem they are experiencing is connected to a wider disruption. Ideally, one item will follow an event from the initial outage through investigation and recovery, with a link to the explanation or root cause analysis (RCA) when it becomes available. For example, a build-service disruption could first appear as "Builds are delayed," later show a recovery update, and eventually link to the report explaining what happened. We need to establish whether the incident sources can provide these connected updates. If they can, users can follow the event in one place. If they cannot, the first version can show a current summary and a link to the available details. The amount of information in the first release will depend on what those sources can reliably provide. Active disruptions should be easy to find.

The relationship between this widget and the existing global status banner needs review with the incident and UX teams. Our proposal is that the banner remains visible when a user hides the service-status widget, so urgent messages continue to reach users elsewhere in Konflux.

### What users can customize

Users can hide optional widgets and restore the default selection. This lets them keep Overview relevant to their work while giving us a small first step toward broader customization.

For the first version, we propose remembering those choices in the user's current browser. This keeps the work small, with the limitation that users would need to repeat their choices on another browser or device. We would like feedback on whether that is sufficient for the initial release.

### Where the information comes from

The Service Enhancement team's proposed GitOps announcement system is the intended source of announcement content. That work is still at the ADR stage. We need to agree together on where it can publish announcements for Overview to read and how subsequent corrections will reach the page. Its editorial and distribution workflow is covered by that separate effort.

The incident communication team will need to identify a suitable source for service-status information. We need to know where to obtain the latest approved statement, how resolution is communicated, and whether a later explanation can be linked to the same event. The incident communication initiative is relevant to this work; its current capabilities need confirmation with its owners.

Announcement authors and incident responders remain responsible for the accuracy of their information. The UI team is responsible for presenting it clearly. The chosen delivery approach will also need a team responsible for availability and publishing failures. Agreeing on that responsibility is part of this review.

### Showing information to the right audience

Community and internal deployments need different content, and individual clusters or rings may have their own announcements. For example, an internal ring-2 maintenance notice should reach the internal clusters affected by that work.

We propose marking content with its intended audience and affected environments. The publishing system can use those labels to create separate feeds, or a service can select the permitted content when Konflux requests it. In either case, the content returned to a community deployment must contain only information approved for that audience. Internal feeds also need appropriate access restrictions. Labels help route information, while access controls determine who can retrieve it. The selected delivery approach must provide both.

Content whose intended audience is unclear should be held back until that is resolved.

### How information could reach Overview

Both options below are intended to support content updates independently of Konflux releases. Each requires initial development and deployment work. Their differences are mainly in where content is published, how access is managed and who operates the delivery path.

#### Option A: publish a feed that Overview reads

The announcement system publishes to a reachable hosting service, and Overview periodically checks that service for updates. A similar arrangement could deliver incident information from its own source.

For example, after an announcement is approved, the publishing process updates the hosted feed. An already-open Overview page picks up the new announcement on its next refresh.

This approach lets the communications teams publish through a shared destination without changing each cluster's configuration for every message. It introduces a hosting dependency: we must choose a service, control access to internal content and agree who maintains it. We also need to verify that Konflux can read it under the authentication and network rules of each deployment. A user's Konflux login may require additional integration to grant access to the chosen host.

This option is feasible in principle. Choosing a host and validating access are the main research tasks needed to make it concrete.

#### Option B: deliver content through cluster configuration

The publishing process updates the relevant cluster configuration. The Konflux operator then makes the content available inside the cluster, where the UI reads it. Production and staging clusters already use the operator. The existing banner follows a similar path, so there is an established pattern to build on. Supporting announcements and richer service information would require extending that pattern.

This approach uses existing cluster operations and access controls. It also means publication must account for cluster and ring configuration, review and synchronization steps. These steps may affect how quickly a message appears and how much work publication requires.

A configuration update can carry a new announcement without a Konflux release. We still need to check the actual update process and whether it causes any workload restart. The publisher would have to update configuration that the operator accepts; directly editing content generated by the operator could be overwritten.

#### Trade-offs to discuss

| Question | Hosted feed | Cluster configuration |
| :- | :- | :- |
| **Where is new content published?** | To the chosen hosting service | To the relevant cluster configuration |
| **What existing capability can we use?** | A suitable hosting service, once identified | The operator's existing banner-delivery pattern |
| **What additional work is needed?** | Hosting, access integration and UI refresh behavior | Support for richer content, publishing automation and UI refresh behavior |
| **What needs an operating owner?** | The feed and its hosting/access setup | The publishing process and cluster configuration integration |
| **What could delay an update?** | Publication, hosting caches and the page's refresh interval | Configuration review/synchronization, operator processing and the page's refresh interval |

### What happens when information is old or unavailable

Users should be able to use the rest of Overview while either widget is loading or unavailable. Each widget should show when its information was last updated and explain when it cannot obtain current information.

This matters especially for service status. A failed request must result in a clear availability warning; otherwise users could mistake missing information for a healthy service. If we retain an older message during a failure, its age should remain visible.

We need to agree how quickly each type of update should appear. Announcements and active incidents may need different refresh intervals. The delivery team must also own the response when publishing stops working. The UI can show that information is old, while restoring publication requires attention from that team.

## Scope of the first release

The first release covers announcements, service-status information supported by the available sources, and hiding/restoring optional widgets. The service-status widget can begin with a small amount of useful information and grow as the sources support more.

The following remain future work:

- Useful links and personal shortcuts.
- Statistics, after research establishes which measures users need.
- A widget drawer or marketplace and broader layout customization.
- Consolidating the remaining portal content and retiring the portal once users can find its useful information through Konflux.

The announcement initiative continues to own its GitOps workflow. Incident owners continue to own incident response and communication.

## Consequences

Konflux becomes the main place to find out about news, new features, incidents, or other Konflux related docs. Users gain a consistent place to find announcements and understand relevant service disruptions. Hide/restore controls let them adjust that page to their needs. Starting with these two widgets keeps the first release focused and gives us a basis for learning what else users find useful.

Each delivery option adds maintenance work. Hosted delivery requires a supported service and access setup; cluster delivery requires integration with configuration and operator workflows. Both require the page to handle updates and failures clearly. Choosing between them should include the cost of running the solution after it ships.

Browser-based preferences offer a small initial implementation, with a limited experience across devices. Deferring links, statistics and the marketplace leaves further work toward making Overview a complete replacement for the portal.

## Research and validation still needed

The following work can inform the design as it moves through review:

- **Incident sources:** confirm where approved updates can be read and whether an outage, its changing status and its explanation can be connected. This determines how much the initial service-status widget can show.
- **Hosted delivery:** identify a candidate host and verify public/internal access from the intended Konflux environments. This determines whether Option A is practical under current hosting and authentication arrangements.
- **Cluster delivery:** use a local operator-based Konflux deployment to observe how a content change reaches the UI, whether it survives operator updates and whether any workload restarts. This helps establish the practical workflow for Option B.
- **Page behavior:** use sample content to check updates on an already-open page, old or unavailable information, and recovery after a failure. These checks become useful once the behavior being evaluated is agreed.

The future announcement publishing process can be tested end to end once it exists. Local tests can provide early evidence about UI and operator behavior; actual hosting access and publication delays require checks against the chosen services.

These investigations can continue alongside peer review. This proposal can be discussed now with the remaining uncertainties made explicit. The delivery approach, operating responsibilities and expected update times need agreement before implementation is planned in detail.

## Questions for peer review

| Question | Who can help answer it? |
| :- | :- |
| **Do announcements and service status provide the right starting point for Overview?** | Users, product and UX |
| **Which incident source can provide current updates and connect them to a later explanation? What can we show initially?** | Incident communication owners |
| **Which delivery option fits our infrastructure and publication needs, and which team would operate it?** | Service Enhancement, platform/operator and UI teams |
| **How should public/internal audiences and cluster or ring targets be managed?** | Service Enhancement, platform and access-control owners |
| **How quickly should announcements and incident updates appear, and who responds when publication fails?** | Communications, incident, product and delivery owners |
| **Is remembering widget choices in the current browser sufficient for the first release?** | Users, product and UX |
| **How should the service-status widget and global banner work together, including when a widget is hidden?** | Incident owners and UX |

## References

- [Overview redesign: KONFLUX-16423](https://redhat.atlassian.net/browse/KONFLUX-16423)
- [GitOps announcement proposal: KONFLUX-16419](https://redhat.atlassian.net/browse/KONFLUX-16419)
- [Incident communication initiative: KONFLUX-12397](https://redhat.atlassian.net/browse/KONFLUX-12397)
- [Existing UI banner reader](https://github.com/konflux-ci/konflux-ui/blob/main/src/components/KonfluxBanner/useBanner.ts)
- [Operator info controller](https://github.com/konflux-ci/konflux-ci/blob/main/operator/internal/controller/info/konfluxinfo_controller.go)
- [Architecture contribution guidelines](https://github.com/konflux-ci/architecture/blob/main/CONTRIBUTING.md)
- [Community ADR process](https://github.com/konflux-ci/community/blob/main/ADRs.md)
