# XXXX. Pipeline Caching Feature Flag Configuration

Date: 2025-10-23

## Status

Proposed

## Context

Following the implementation of container build layer caching via Squid HTTP proxies as described in [ADR 0047](0047-caching-for-container-build-layers.md), we need to provide users with flexible control over when and how the proxy caching is enabled for their pipelines. Users need the ability to:

* Enable or disable HTTP proxy use for individual pipelines without knowing technical details about the proxy configuration
* Control proxy usage at the namespace level for all pipelines running in that namespace
* Control proxy usage at the cluster level for all pipelines in the cluster
* Apply GitOps processes for this configuration, similar to other Konflux configuration elements

The current design requires users to manually configure `HTTP_PROXY` and `NO_PROXY` parameters to the buildah task, which exposes implementation details and creates a poor user experience. We need a more user-friendly configuration mechanism that abstracts away the technical details while providing appropriate levels of control.

## Decision

We will implement a hierarchical feature flag system for controlling pipeline caching proxy usage with the following configuration levels and precedence:

### Configuration Levels

1. **Pipeline Level**: An `ENABLE_CACHE_PROXY` parameter that can be set in individual pipeline definitions
2. **Namespace Level**: An `enable-cache-proxy` value in the `konflux-config` config map in the pipeline's namespace
3. **Cluster Level**: An `enable-cache-proxy` value in the `cluster-config` config map in the `konflux-info` namespace

### Precedence Order

Configuration takes effect based on the following precedence (highest to lowest):

1. Cluster-level configuration (`cluster-config` in `konflux-info` namespace)
2. Namespace-level configuration (`konflux-config` in pipeline's namespace)
3. Pipeline-level configuration (`ENABLE_CACHE_PROXY` parameter)

### Implementation Details

* **Pipeline Integration**: The `ENABLE_CACHE_PROXY` parameter will be passed to the pipeline init task
* **Configuration Resolution**: The init task will read configuration values from the appropriate config maps and resolve the final proxy settings
* **Environment Variables**: The init task will emit `HTTP_PROXY` and `NO_PROXY` configuration values to be used by the buildah task
* **Default Values**: If no configuration is found, the system will fall back to default values:
  * `HTTP_PROXY`: `squid.caching.svc.cluster.local:3128`
  * `NO_PROXY`: *<TBD>*
* **Configuration Values**: Each level supports `true`, `false`, `""` (empty), `"defer"`, or unset values
* **Proxy Activation**: The proxy will be enabled if any of the configuration levels is set to `true`, following the precedence order above

### Configuration Logic

The proxy will be enabled if any of these conditions are met (in order of precedence):

* Cluster flag is `true`
* Cluster flag is unset/empty/deferred AND namespace flag is `true`
* Cluster flag is unset/empty/deferred AND namespace flag is unset/empty/deferred AND pipeline parameter is `true`

## Consequences

* **Improved User Experience**: Users can control proxy usage through simple boolean flags without needing to understand proxy technical details like ports or addresses
* **Flexible Control**: Three levels of configuration provide appropriate control for different user roles (pipeline authors, namespace administrators, cluster administrators)
* **GitOps Integration**: Configuration can be managed through GitOps processes using config maps, consistent with other Konflux configuration elements
* **Implementation Complexity**: The init task becomes more complex as it needs to resolve configuration from multiple sources and apply precedence rules
* **Configuration Management**: Cluster and namespace administrators need to understand the precedence rules to effectively manage proxy usage
* **Documentation Requirements**: Clear documentation will be needed to explain the configuration options and precedence rules for different user roles
* **Migration Path**: The implementation can be done incrementally, starting with basic pipeline-level support and adding cluster/namespace configuration later to avoid breaking changes
