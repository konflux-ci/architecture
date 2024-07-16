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
object on the cluster that has changed. KubeArchive subscribes to these Cloudevents from `ApiServerSource` which allows
it to be notified of state changes for resources on the cluster.

In addition to `ApiServerSource`, Knative Eventing also provides
[`Brokers`](https://knative.dev/docs/eventing/brokers) and [`Channels`](https://knative.dev/docs/eventing/channels) to
allow for persistence storage of Cloudevents.
[Both `Brokers` and `Channels` provide ways handle Cloudevent delivery failure](https://knative.dev/docs/eventing/event-delivery).
Additionally, `Brokers` use [`Triggers`](https://knative.dev/docs/eventing/triggers) provide a way to subscribe to and
filter events, so that a Cloudevent consumer can specify the types of Cloudevents that it wants to receive.

## Decision

To enable a smooth integration with KubeArchive in the future, Konflux will install Knative Eventing in Konflux Clusters.
Knative Eventing can be installed on a cluster by running the following command

```bash
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.14.3/eventing-core.yaml`
```

## Consequences

Konflux will install Knative Eventing. This will enable smooth integration with KubeArchive if and when Konflux decides
to. This will require the Konflux installation process to be modified to include the installation of Knative Eventing.
This will give Konflux Services access to the features that are provided by Knative Eventing. Such services may decide
to use ApiServerSource to watch resources they are interested in, instead of writing their own watcher logic, for
example. Konflux Services may also decide to publish their own Cloudevents, that other services may decide to subscribe
to, when particular events occur. This may lead to further ADR(s) to decide how Knative Eventing should be used.
