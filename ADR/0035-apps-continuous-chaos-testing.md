# 35. Continuous Chaos Testing of Apps in AppStudio

Date: 2024-06-04

## Status

Accepted

## Context

The chaos engineering strategy enables users to discover potential causes of service degradation. It helps users understand their app behavior under unpredictable conditions, identify areas to harden, and utilize performance data points to size and tune their application to handle failures, thereby minimizing downtime.

There are two approaches to chaos testing in the CI/CD pipeline.

### Resilience based Chaos scenario

These Chaos scenarios are expected to cause application failure. Example scenarios include simulating memory pressure, storage errors, killing random or dependent resources. The objective of these chaos test cases in the CI/CD pipeline is to assess whether the application is capable of mitigating and maintaining reliability.

![Architecture diagram of Resilience based Chaos test scenario](../diagrams/ADR-0035/chaos-resilience.png "Architecture diagram of Resilience based Chaos test scenario")

### SLA based Chaos scenario

Test the resiliency of a application under turbulent conditions by running tests that are designed to disrupt while monitoring the application adaptability and performance:
Establish and define your steady state and metrics - understand the behavior and performance under stable conditions and define the metrics that will be used to evaluate the application’s behavior. Then decide on acceptable outcomes before injecting chaos.
Analyze the statuses and metrics of all components during the chaos test runs.
Improve the areas that are not resilient and performant by comparing the key metrics and Service Level Objectives (SLOs) to the stable conditions before the chaos. For example: evaluating the API server latency or application uptime to see if the key performance indicators and service level indicators are still within acceptable limits.

![Architecture diagram of SLA based Chaos test scenario](../diagrams/ADR-0035/chaos-sla.png "Architecture diagram of SLA based Chaos test scenario")


### Glossary

- krkn: Chaos testing framework: <https://github.com/krkn-chaos/krkn>

## Decision

* Users can leverage Krkn, a chaos testing framework, to execute chaos tests within the IntegrationTestScenarios.

* Ephemeral clusters ([provisioning-ephemeral-openshift-clusters](https://github.com/konflux-ci/architecture/pull/172)) will be used for executing the tests, to provide a more isolated and production-like testing environment compared to ephemeral namespaces.

* Users can gather Prometheus metrics for analysis during chaos testing.

* Optionally, users can gather metrics exposed by the application, if [monitoring for user-defined projects](https://docs.openshift.com/container-platform/4.15/observability/monitoring/enabling-monitoring-for-user-defined-projects.html#accessing-metrics-from-outside-cluster_enabling-monitoring-for-user-defined-projects) feature is enabled in the cluster.

## Consequences

* The user/service account will require elevated privileges (cluster-admin) within the ephemeral environment to execute CRUD operations (configure RBAC,  Prometheus instances) 

* The Tekton Tasks within the chaos pipeline will need to ascertain the different permission levels  (cluster-admin vs. namespace admin vs. monitoring access) and set up the environment depending on the Chaos Test scenario, before starting the Tekton Tasks related to the Chaos testcase.