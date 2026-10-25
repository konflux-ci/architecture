---
title: "72. Sunset Squid container-image-layer proxy"
status: Accepted
applies_to:
  - build-service
  - pipeline-service
topics:
  - caching
  - squid-proxy
  - container-images
  - performance
---

# 72. Sunset Squid container-image-layer proxy

Date: 2026-10-25

## Status

Accepted

Supersedes [ADR 0047](0047-caching-for-container-build-layers.md) and
[ADR 0057](0057-pipeline-caching-feature-flag.md).

## Context

[ADR 0047](0047-caching-for-container-build-layers.md) chose Squid with SSL-bump as an
in-cluster forward proxy to cache container image layers from registry CDNs.
[ADR 0057](0057-pipeline-caching-feature-flag.md) added pipeline and cluster controls
(`enable-cache-proxy`, `allow-cache-proxy` in `cluster-config`).

Upstream delivers that stack primarily via:

- the `konflux-ci/caching` Helm chart and Squid image
- pipeline integration in container-build-catalog (`init`, `buildah*`) and related
  tooling

In practice:

- Use is opt-in (default off); deployments see little useful cache value.
- A/B testing showed higher CDN hit rates do not reduce build wall-clock. SSL-bump adds
  fixed overhead, and remote/multi-arch builds often ignore the in-cluster proxy.
- Maintaining Squid in upstream (chart, image, CA story, exporters, docs) is not
  justified, and does not provide value downstream.

## Decision

We will **deprecate and remove Squid-based OCI layer caching from upstream Konflux**.

Upstream scope:

- Retire Squid from `konflux-ci/caching` (chart defaults, Squid image/build, Squid-only
  tests and docs).
- Stop recommending `enable-cache-proxy`; clean up `init` / `buildah*` proxy wiring and
  related docs when convenient (safe no-ops once clusters disable the feature).
- Mark ADR 0047 / 0057 superseded; any future OCI layer cache needs a new ADR.

Downstream setups (for example `infra-deployments` / `container-image-proxy`) remain
responsible for disabling and removing their own Squid installs. Upstream removal does
not by itself uninstall those deployments; they should flip `allow-cache-proxy` off and
tear down Squid on their own timeline.

**Out of scope:** package-registry reverse proxy (NGINX), covered by
[ADR 0064](0064-hermeto-package-registry-proxy.md).

## Consequences

Positive:

- Less upstream surface to build, test, and document for OCI pull caching.
- Simpler and faster builds.

Negative:

- No Konflux-maintained in-cluster OCI layer cache for opt-in users.
- Downstream clusters that still run Squid must coordinate cutover themselves.
- Any future OCI layer-caching approach requires a new ADR.
