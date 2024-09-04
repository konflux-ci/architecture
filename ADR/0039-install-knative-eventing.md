# 39. Install Knative Eventing

Created: 2024-07-15

## Status

Proposed

## Context

Konflux currently uses [Tekton Results](https://tekton.dev/docs/results) to store Tekton PipelineRuns off the Kubernetes
Cluster that they were run on. There have been many performance issues that Konflux has encountered while using Tekton
Results. To side step the issues with Tekton Results, Konflux may decide to integrate with
[KubeArchive](https://github.com/kubearchive/kubearchive) to store PipelineRuns and potentially other kinds of resources
on the cluster in a database for long term storage.

Unlike Tekton Results, KubeArchive does not provide its own component to watch resources in the cluster. Instead it uses
[`ApiServerSource` from Knative Eventing](https://knative.dev/docs/eventing/sources/apiserversource) to listen to
resource specified on the cluster and create [Cloudevents](https://cloudevents.io) that contain the definition of the
object on the cluster that has changed.

Integration with KubeArchive will mean that Knative-Eventing will be installed as well. This may lead to a desire from
Konflux developers to take advantage of the features of Knative-Eventing.

## Decision

Konflux developers can use functionality provided by Knative-Eventing to provide new functionality for components of
Konflux or improve performance/maintainability of existing functionality of Konflux components.

## Consequences

As Konflux learn about and take advantage of Knative-Eventing, duplicated Cloudevents infrastructure may appear. This
may require a centralization and standardization of the CloudEvents pipeline. As Konflux starts to generate more
Cloudevents, it may become difficult to find which CloudEvents relate to what action in Konflux. Naming conventions may
become necessary for Cloudevents as well as Cloudevent extensions (headers provided in a cloudevent that are not part of
the Cloudevents standard) used by Konflux to make data and event discovery easier. Guidelines may also be necessary for
when and how Cloudevents should be used.
