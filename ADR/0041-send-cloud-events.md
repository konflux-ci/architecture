# 40. Konflux should send cloud events all system events.

Date: 2024-09-24

## Status

Proposed

## Context

Konflux had made the architectural decision to not use cloud events. However, that does not mean that
Konflux should not emit cloud events.

Emitting cloud events would allow Konflux users to easily track what is happening in the system. In addition,
they can use these cloud events to create their own application-specific infrastructure to support their build
and release process.

To support this, all Konflux components should be required to emit cloud events for signicant events. These
should be documented fully and made available for users.

Cloud event generation could be optional and that option could default to off. But users should be able to
turn it on so that Konflux will generate cloud events that they can then act on.

Note again that this ADR does not propose that Konflux generate cloud events for consumption by Konflux
itself. Rather it proposes Konflux generate cloud events to support addtional application-specific build and
release functionality outside of Konflux.

### Use Cases

* Teams want to kick off external QE/CI testing based on a some criteria using cloud events. These tests
  potentially run for days, making them unsuitable for embedding directly in the pipeline.
* Teams want to generate their own metrics for interal or external usage using cloud events.
* Teams want to integrate with other tools that use eventing.
* Teams want to move Jira states based on the generation of some artifacts.
* Teams want to publish to all Satellite capsules in the network when release contents become available.
* Teams want to be able to add infrastructure around their build and release processes without having to
  modify existing stable pipelines.
* Teams want to collect data for audit or send email alerts when certain artifacts are built or released.
* Teams want to be able to control their costs by moving non-build and non-release processes out of the cluster.

## Decision

All Konflux components shall generate cloud events for significant events.

## Consequences

Application teams can more easily create application-specific build and release infrastructure in Konflux.
