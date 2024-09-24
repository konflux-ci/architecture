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

Currently Tekton Results is a Konflux core component, however KubeArchive might integrate with Konflux as a Konflux
add-on. Integration with KubeArchive will mean that Knative-Eventing will be installed as a Konflux add-on.

## Decision

Knative-Eventing is a Konflux add-on. It might be installed in an instance of Konflux, but that is not guaranteed. Other
Konflux add-ons may use Knative-Eventing as a dependency. Konflux core components cannot use Knative-Eventing as a
dependency because Knative-Eventing is not guaranteed to be present in all Konflux installations.

## Consequences

If more Konflux add-ons take advantage of Knative-Eventing, duplicated Cloudevents infrastructure may appear. This
may require a centralization and standardization of the CloudEvent pipelines. As Konflux developers become more familiar
with CloudEvents, it may become apparent that there are parts of Konflux core that could benefit from the use of
CloudEvents, which would require this decision being revisited.
