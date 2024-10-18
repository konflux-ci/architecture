# 40. Konflux should send cloud events all system events.

Date: 2024-09-24

## Status

Proposed

## Context

Konflux had made the architectural decision to not use cloud events. However, that does not mean that
Konflux should not emit cloud events.

Emitting cloud events would allow Konflux users to easily track what is happening in the system. In addition,
they can use these cloud events to create their own product-specific infrastructure to support their build
and release process.

To support this, all Konflux components should be required to emit cloud events for signicant events. These
should be documented fully and made available for users.

Cloud event generation could be optional and that option could default to off. But users should be able to
turn it on so that Konflux will generate cloud events that they can then act on.

Note again that this ADR does not propose that Konflux generate cloud events for consumption by Konflux
itself. Rather it proposes Konflux generate cloud events to support addtional product-specific build and
release functionality outside of Konflux.

## Decision

All Konflux components shall generate cloud events for significant events.

## Consequences

Product teams can more easily build product-specific build and release infrastructure in Konflux.
