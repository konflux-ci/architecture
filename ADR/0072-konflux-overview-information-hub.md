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

Proposed for discussion. This draft proposes the initial experience and audience-separation requirements. It presents delivery alternatives for review; no delivery mechanism or authentication method has been selected. Research has covered source code and documentation. Deployment experiments have yet to be run.

## Context

Overview is the first page users encounter when entering Konflux. Users arriving to investigate a failed pipeline or a policy violation also need to understand whether a service disruption or an announced change affects their work.

Relevant information can be spread across announcements, service-status tools, documentation and dashboards. Users must know where to look and connect that information themselves. Overview could bring relevant summaries and links to authoritative sources into their normal workflow.

Different deployments serve different audiences, and users have different priorities. The page needs to present relevant information and let users remove optional content they do not find useful. Beginning with service communications gives the redesign a focused first release.

The redesign should preserve direct links to work and make relevant communications easy to scan during navigation. Urgent communication also needs to reach users who arrive directly at other pages. The global banner and other deployment communication channels remain important alongside Overview.

## Decision

We propose two initial widgets: announcements and service status. Each deployment configures the sources used to supply its content. Users can hide optional widgets and restore them later.

### What users will see

**Announcements** show recent notices and changes, with a short summary, publication date and a link to the full information. Corrections to a published announcement should reach Overview through the same delivery path.

**Service status** helps users recognize a wider disruption while investigating a problem. Ideally, one item follows an event through investigation and recovery, then links to an explanation or root cause analysis when available. For example, “Builds are delayed” could later show a recovery update and a link explaining what happened.

The first version can show a current summary and a detail link where the configured source provides limited information. Connected updates and explanations depend on the source supplying that relationship. Supporting a useful initial summary keeps the feature available to deployments with simpler sources.

We propose keeping the existing global banner independent of widget preferences. Hiding the optional service-status widget would leave urgent global messages visible elsewhere in Konflux. This behavior needs review alongside the proposed page experience.

### Customization

Users can hide individual optional widgets and restore the default selection. Their choices should be saved against their signed-in user account and available when they return from another browser or device.

Existing UI features, including dismissed cards and saved views, use browser storage. Account-based preferences extend that pattern and require a server-side way to save and retrieve each user's choices. The storage mechanism needs investigation and must follow Konflux's Kubernetes API model. No limitation requiring browser-only storage has been established.

A widget drawer, marketplace, layout editor, saved links and statistics remain future work. Choosing useful statistics requires user research.

### Content sources and audience separation

Overview reads announcements and incident information from sources configured for its deployment. Those sources remain authoritative for the content. This proposal covers how Konflux receives and presents updates; authoring and approval workflows can be provided separately by each deployment.

We propose that announcement authors identify intended audiences through labels. The delivery system uses those labels to select the content each deployment is permitted to receive. For example, a maintenance announcement affecting one environment can be delivered to that environment without appearing in unrelated deployments.

For a hosted source, we propose associating each receiving deployment or service with a credential and a set of permitted audience labels. For example, a deployment allowed to receive announcements labelled `environment-a` presents its credential when fetching updates. The source checks that permission and returns the matching announcements. Requesting a different label cannot expand what that credential is allowed to receive.

The source performs this selection before content reaches the browser. Overview receives the permitted announcements and displays them. The same separation can be achieved by publishing separate feeds with appropriate access restrictions, or by selecting content before publishing it into cluster configuration.

This proposal describes the required audience separation and a possible way to enforce it. It leaves credential issuance and management for integration design, including whether existing authentication can provide the needed permissions. A service could store permitted labels against a credential or use a validated credential carrying those permissions. Both implement the same proposed behavior. Credentials representing a whole deployment must remain in a trusted server-side component.

### Delivery alternatives

Content updates should reach users independently of Konflux software releases. Both alternatives below require initial implementation. Supporting both would add work and remains a review question.

#### Option A: read a hosted feed

A publishing system updates a hosted feed. Overview obtains the permitted content through the configured integration and checks for updates periodically. An already-open page picks up a new or corrected announcement on a subsequent refresh.

This approach separates communication updates from cluster configuration changes. It requires a reachable service, suitable access controls and a way to detect publication failures. Integration with restricted sources may require a server-side connection using an existing component or additional development; its feasibility needs investigation.

Push delivery is an additional possibility: a service sends updates to a receiving component. It requires a reachable receiver and permission checks for the sender and destination. Its value should be assessed against the simpler periodic-fetch workflow before adding that capability.

#### Option B: deliver content through cluster configuration

A publishing system updates supported configuration for an operator-managed deployment. The Konflux operator makes the content available inside the cluster, where the UI reads it. The existing banner provides a precedent for this path; richer announcements and service information would require further support.

This approach can use cluster access controls and configuration management. Publication must account for configuration updates, operator processing and refreshing the open page. Whether an update causes a workload restart or has a significant synchronization delay needs verification.

The publication path must use supported operator inputs so subsequent reconciliation preserves the content. A new announcement would be a content/configuration change and could be delivered without rebuilding Konflux.

#### Comparison

| Consideration | Hosted feed | Cluster configuration |
| --- | --- | --- |
| Publication destination | A reachable service | Supported configuration for the affected deployments |
| Main integration work | Reading updates and accessing the chosen source | Extending operator content support and publishing to its supported input |
| Access to restricted content | Enforced by the source and the configured connection | Enforced during publication and through cluster access controls |
| Possible update delays | Publication, service caches and refresh intervals | Configuration synchronization, operator processing and refresh intervals |
| Operational dependency | Feed availability and publication | Configuration publication and operator processing |

### Loading, freshness and failure

Each widget loads independently so slow or unavailable communications leave normal navigation usable. Widgets show when information was updated and clearly identify an inability to retrieve current information.

Service status needs particular care: missing information must not appear to mean the service is healthy. If an older message is retained during a failure, its age and the failed refresh remain visible.

Announcements and active incidents may require different refresh behavior. Review should establish suitable defaults and what deployments can configure.

## Consequences

Users gain a consistent place to find announcements and understand relevant disruptions. They can enter Konflux specifically to check for updates and follow links to authoritative details, reducing the need to search across other channels. Hide and restore controls give users a small, useful level of customization. The intended benefit is easier access to useful information; higher visit counts are not a success criterion by themselves.

The feature introduces dependencies on content sources and publication. The UI must handle updates and failures clearly. Deployments need a supported integration before their widgets can provide useful information; handling an unconfigured source needs to be defined during implementation design.

Audience selection adds integration requirements for restricted content. Hosted delivery requires a reliable connection to a service, while cluster delivery requires supported operator inputs and publication automation. Supporting both increases development and maintenance costs.

Saving preferences against user accounts makes customization available across browsers and devices. It also adds storage, access-control and availability requirements that the current browser-storage pattern does not address. We need to identify a suitable existing mechanism or agree on the additional work before implementation. Deferring links, statistics and broader customization keeps the initial release focused while leaving further opportunities to improve navigation.

## Decisions still needed before implementation

The proposed starting point is announcements, service status and widget choices saved for each user. The following decisions remain open because they affect the work needed to deliver that experience. Reviewers can assess the proposed directions and help resolve these specific choices.

| Topic | Proposed direction | What still needs deciding |
| --- | --- | --- |
| Delivering updates | Publish content independently of Konflux software releases. | Start with hosted feeds or operator-managed configuration, and establish whether supporting both is justified. |
| Access to restricted sources | Select announcements before they reach the browser; for authenticated feeds, associate credentials with permitted labels. | How existing authentication and server-side components can support that connection, and what additional integration is required. |
| Saving customization | Store widget choices against the signed-in user so they follow the user across browsers and devices. | Which server-side storage mechanism to use and how the UI saves and retrieves the choices. |
| Refreshing content | Refresh open pages and make old or unavailable information visible. | Suitable defaults for announcements and active incidents, and what deployments can configure. |
| Urgent messages | Keep global banners visible independently of optional widget preferences. | Confirm that this behavior meets the needs of the shared UI. |

## Validation needed

Source inspection establishes possible integration paths, with deployment behavior still to be tested. A local operator-based installation can help establish how supported configuration updates reach the UI, whether content survives reconciliation and whether updates cause restarts. Sample content can exercise refresh, independent loading, stale information and recovery on an already-open page.

Actual authentication, network access and publication timing require validation against the source chosen by each deployment. These checks can follow the architectural discussion; a demonstration that a browser can fetch sample data would leave those integration questions open.

Account-based preferences require investigation of available server-side storage and user access controls. Validation should establish that one user's choices remain private to that user and are available when the user signs in from another browser.

## References

- [Existing UI banner reader](https://github.com/konflux-ci/konflux-ui/blob/main/src/components/KonfluxBanner/useBanner.ts).
- [Operator info controller](https://github.com/konflux-ci/konflux-ci/blob/main/operator/internal/controller/info/konfluxinfo_controller.go).
- [Architecture contribution guidelines](https://github.com/konflux-ci/architecture/blob/main/CONTRIBUTING.md).
- [Community ADR process](https://github.com/konflux-ci/community/blob/main/ADRs.md).
