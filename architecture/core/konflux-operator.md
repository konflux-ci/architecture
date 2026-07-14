---
title: Konflux Operator
eleventyNavigation:
  key: Konflux Operator
  parent: Core Services
  order: 1
toc: true
overview:
  scope: "Platform installation and lifecycle management via Konflux CR"
  key_crds:
    - Konflux
  related_services:
    - build-service
    - integration-service
    - release-service
    - pipeline-service
    - enterprise-contract
    - konflux-ui
  related_adrs: []
  key_concepts:
    - Single Konflux CR reconciles all platform components
    - Declarative lifecycle management (install, upgrade, configure, remove)
    - Optional component toggling (image controller, internal registry, telemetry)
---

# Konflux Operator

The Konflux Operator is a Kubernetes operator that installs, configures, and manages the entire Konflux platform from a single declarative `Konflux` Custom Resource. It deploys all core services and selected optional components, propagates configuration changes, and removes disabled components automatically.

The operator reconciles the top-level `Konflux` CR into a set of child CRs, one per platform component, each managed by its own sub-reconciler. This fan-out pattern keeps component logic isolated while providing a single control point for platform administrators.

## Key CRDs

| CRD | API Group | Description |
|-----|-----------|-------------|
| `Konflux` | `konflux.konflux-ci.dev/v1alpha1` | Defines the desired state of the entire Konflux platform installation |

## Further Reading

- **Documentation** (installation, configuration, API reference): <https://konflux-ci.dev/konflux-ci/docs/>
- **Source code**: <https://github.com/konflux-ci/konflux-ci> (see `operator/` directory)
