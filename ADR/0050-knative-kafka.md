# 50. Install a Backing Broker for Knative Eventing

Date: 2025-07-30

## Status

Draft

## Context

KubeArchive is an optional component of a Konflux deployment and depends on Knative Eventing. Knative provides a few
different [types](https://knative.dev/docs/eventing/brokers/broker-types/) of brokers. The default installation of
Knative Eventing only includes the Channel Based broker using In Memory Channels. The In Memory Channel does not provide
an guarantees of long term message persistance/durability and if the In Memory Channel component is restarted
(ex: when installing a new version of Knative Eventing), all messages currently stored in the broker are lost. Knative
in the documentation explicitly
[discourages the use of the Channel Based Broker](https://knative.dev/docs/eventing/brokers/broker-types/channel-based-broker/)
and encourages users to install and use one of the other broker implementations instead:
- [Apache Kafka](https://github.com/knative-extensions/eventing-kafka-broker)
- [RabbitMQ](https://github.com/knative-extensions/eventing-rabbitmq)

To provide more durable and reliable messaging, Konflux should pick a production ready broker implementation to use.

## Decision

Konflux will provide either a RabbitMQ or Kafka cluster to use with Knative, install the appropriate Knative Broker, and
install KubeArchive using the broker provided by the chosen Knative extension.

## Consequences

Deployments of Konflux that install KubeArchive will require either a RabbitMQ or Apache Kafka cluster before installing
KubeArchive. KubeArchive will be able to improve the realiability for message delivery and guarantee that all missed
Cloud Events can be captured and replayed to KubeArchive.Other components of Konflux that use Knative Eventing will be
able to use more performant and reliable Knative Brokers.
