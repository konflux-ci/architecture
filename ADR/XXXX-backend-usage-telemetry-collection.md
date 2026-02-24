# XXXX. Backend Usage Telemetry Collection from Konflux Clusters

Date: 2026-01-26

## Status

Proposed

## Context

We are adding a functional telemetry mechanism to collect anonymized usage data. This data is critical for understanding feature adoption, identifying friction points in the user journey, and guiding future product investment.

The telemetry system needs to collect usage events from Konflux clusters and backend services. Data will be gathered by either querying the cluster itself or Tekton Results. The collected data will be sent to Segment (a usage/analytics data routing SaaS) for analysis in Amplitude.

We will gather various usage events such as system installation started/complete (with success status), pipeline started/finished, and component created. These will allow us to calculate metrics such as installation success rates, pipeline success rates and run durations.

## Decision

We will implement the collection job and logic in the system setup operator to deploy and enable it.

An hourly job will run inside the cluster in its own "segment-bridge" namespace. The job will run API queries to collect data from the cluster and Tekton Results. We will query data from 4 hours back, thereby causing each event to be sent up to 4 times, increasing resilience to connectivity issues. This does imply that we need to generate the events in a consistent manner that will allow Segment's event de-duplication to take place.

The collection job will need to be able to read PipelineRun and Component resources from all namespaces in the cluster, and to access Tekton Results to read PipelineRun resources that were already removed from the cluster.

We will avoid collecting or sending any PII. All user names and namespace names will be anonymized at collection time by sending a hash of the name joined with the cluster ID instead of the name itself. The cluster ID exists natively in OpenShift as part of the singleton ClusterVersion resource. In vanilla K8s clusters we will fall back to using the UUID of the system namespace.

Enabling/disabling the collection would be done via a flag on the Operator's "Konflux" resource. If the flag is unspecified, the default behavior will depend on the kind of cluster the system is running on. On vanilla k8s clusters collection will be disabled by default. Since OpenShift clusters already contain similar telemetry collection mechanisms for the OpenShift console, on OpenShift clusters the default would match the enabled/disabled collection state for the OpenShift console.

In addition to the enable/disable flag, the operator will also support configuring:

1. The key used to write events into Segment
2. The URL of the Segment API

This will allow the users to route the telemetry data their own Segment projects or to other systems which implement the Segment API.

To encourage users to share Telemetry with the Konflux dev team, the user-installable builds of Konflux will include a Segment key that routes data to a Segment/Amplitude project that is accessible by the dev team. This means that if telemetry is enabled but the Segment API URL and Key are left unconfigured, data will be sent by default to the public Segment service, to an account owned by the dev team.

The konflux operator will install the key and URL in appropriate locations to make them available for the "segment-bridge" job and the Konflux UI. While specifying if and what kinds of telemetry collection will be done by the UI goes beyond the intended scope of this ADR, we seek to specify a basic "contract" that enables the UI to send telemetry to the same destination as the backend.

If connectivity to Segment is unavailable for more than 4 hours, we will accept that certain events will not be sent.

### Rejected Alternatives

**Collection via the notification-service**: This would rely on real-time capture and sending of events from the cluster. There is a risk of "missing" important events, or failing to send due to network issues.

**Collection from the UI using the Segment client libraries**: The client simply does not have visibility into all the events we want to send. For example, the client is unaware of pipeline starting and ending events unless the user happens to be looking at a screen showing that particular pipeline.

## Consequences

* **Reliability**: The 4-hour lookback window provides built-in retry logic, ensuring events are not lost due to transient connectivity issues
* **Low Resource Consumption**: Hourly batch collection is more efficient than real-time event streaming
* **Implementation Simplicity**: Using a dedicated job with API queries is straightforward to implement and maintain
* **Data Delay**: There is possibly a large delay between an event occurring and having it be sent, with events potentially being delayed up to 4 hours
* **Event Loss**: If Segment is unavailable for more than 4 hours, certain events will not be sent
* **Privacy**: No PII is collected, with user and namespace names being hashed with the cluster ID for anonymization
