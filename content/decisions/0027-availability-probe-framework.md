---
title: Availability Probe Framework
number: 27
---
# Availability Probe Framework

* Date 2023-07-06

## Status

Accepted

## Context

As an Konflux developer building functionality for the platform, I want to be able to
easily visualize and comprehend the stability and availability of deployed systems in
order to inform and influence future work towards improving the overall system
reliability.

Such indication should tell us the overall uptime of Konflux with respect to services
under the control of Konflux developers.

Konflux is defined to be available at a given moment if all of its components are
reporting to be available at that given moment, and unavailable otherwise.

A component is defined to be available at a given moment if all of its availability
probes are reporting to be available at that given moment, and unavailable otherwise.

A convention is required for providing the availability of a probe.

Once this is in place, those indicators can be aggregated in order to report the overall
availability of Konflux.

## Decision

Probes' availability will be provided as a Prometheus metric. The metric will contain
metric labels to allow differentiating between the different probes. When exported out
of the cluster of origin, additional labels will be attached to the metric to mark the
cluster in which the metric was generated.

### Details

The availability Prometheus metric will be computed for each component based on the exit
status of the latest execution of the CronJobs evaluating the component's availability.
Component owners will provide the implementation for each component's CronJobs. By
adhering to a specific standard
([see naming convention below](#probes-naming-convention)),
results will be aggregated into a standardized Prometheus metric to report on
availability (i.e. component owners will not be required to provide the translation
mechanism).

It is up for each team to define what it means for its component(s) to be available.
Fundamentally, a component should be reported as available as long as it's capable of
providing the service it aims to provide, and unavailable otherwise.

Each team will define CronJobs that will test the availability of their components.
The Job started by each CronJob will terminate successfully if the test completes
successfully, and will terminate with an error in case the test fails.

Kube-state-metrics is a Prometheus exporter generating metrics based on the Kubernetes
API server. It generates
[Jobs](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/job-metrics.md)
and
[CronJob](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/cronjob-metrics.md)
metrics that will be processed using Prometheus recording rules in order to
generate Konflux's availability Prometheus metric.

A single set of rules will be defined globally which will apply for all CronJobs.

The resulting Prometheus metric will identify each probe based on its CronJob name and
the namespace in which the CronJob was defined.

#### Probes Requirements

A Job running for a probe is required to:

* Evaluate the availability of the component being probed.
* Exit with status `Failed` if the component was evaluated to be unavailable or with
  status `Complete` if it was evaluated to be available (referring to the status field
  of the Kubernetes Job resource).
* Be able to exhaust its `backoffLimit` by the time it's due to run again (e.g. if the
  cronjob is defined to run every 10 minutes and can take up to 2 minutes to execute
  it cannot have a `backoffLimit` larger than 4).
* Clean up all resources generated during its run.

#### Probes Naming Convention

To allow generating the Prometheus metric only for relevant CronJobs, probe CronJob
names should have a standardized format:

* `appstudio-probe-<probe_name>`

`appstudio-probe-` being a literal to be used in order to capture only the relevant
CronJobs, and `<probe_name>` is a variable to be translated to a label in the resulting
Prometheus metric that will correlate the value to the individual probe or check.

To allow aggregating the Prometheus availability metric per component, the namespaces
in which the CronJobs will be created should have a standardized format:

* `appstudio-probe-<component_name>`

`<component_name>` is the name of the component under which probes will be aggregated.

The nature and size of each service and component will dictate the number of probes it
should have. E.g. some services may have multiple components, while some others may have
just one. Some components may require multiple probes while others may require just one.

> **_NOTE:_** The probe-name part of the CronJob name should be unique in the context of
the CronJob's **namespace**.

#### Probes Design Considerations

Considerations for defining probes' CronJobs:

* Where should it run in order to provide reliable evaluation?
    * Which namespace?
    * Which clusters?
* What sort of permissions does it require to have?
    * Would that be a good-enough representation of what it aims to evaluate?
* What sort of APIs does it need to access?
* How often should it run?
* Does it affect performance in a reasonable manner?
* How resources are to be cleaned up?
    * Upon startup? completion? failure?
    * Using another CronJob? Finalizers?

## Consequences

* The different teams for all Konflux services will define the CronJobs required for
  testing their components' availability, and will name them according to the naming
  convention.
* A single set of Prometheus recording rules will be defined for transforming the
  CronJob results into availability Prometheus metric time series.
* Existing Prometheus alerting rules should be examined and adjusted so that they do not
  generate unnecessary alerts caused by CronJobs failures.
