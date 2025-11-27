# XXXX. Pipeline Caching Feature Flag Configuration

Date: 2025-10-23

## Status

Proposed

## Context

Following the implementation of container build layer caching via Squid HTTP proxies as described in [ADR 0047](0047-caching-for-container-build-layers.md), we need to provide users with flexible control over when and how the proxy caching is enabled for their pipelines. Users need the ability to:

* Enable or disable HTTP proxy use for individual pipelines without knowing technical details about the proxy configuration
* Control proxy usage at the cluster level for all pipelines in the cluster
* Apply GitOps processes for this configuration, similar to other Konflux configuration elements

The current design requires users to manually configure `HTTP_PROXY` and `NO_PROXY` parameters to the buildah task, which exposes implementation details and creates a poor user experience. We need a more user-friendly configuration mechanism that abstracts away the technical details while providing appropriate levels of control.

## Decision

We will implement a two-level feature flag system for controlling pipeline caching proxy usage with the following configuration levels and precedence:

### Configuration Levels

1. **Pipeline Level**: An `enable-cache-proxy` parameter that can be set in individual pipeline definitions
3. **Cluster Level**: An `enable-cache-proxy` value in the `cluster-config` config map in the `konflux-info` namespace

### Precedence Order

Configuration takes effect based on the following precedence (highest to lowest):

1. Cluster-level configuration (`cluster-config` in `konflux-info` namespace)
3. Pipeline-level configuration (`enable-cache-proxy` parameter)

The motivation for this seemingly unintuitive precedence order is to allow for
overriding the per-pipeline configuration from the namespace or cluster level.
This serves as a quick "emergency escape hatch" in case of proxy-based failure
scenarios. See the "Configuration Logic" section below for details.

### Implementation Details

* **Pipeline Integration**: The `enable-cache-proxy` parameter will be passed to the pipeline init task
* **Configuration Resolution**: The init task will read configuration values from the appropriate config maps and resolve the final proxy settings
* **Environment Variables**: The init task will emit `HTTP_PROXY` and `NO_PROXY` configuration values to be used by the buildah task
* **Default Values**: If no configuration is found, the system will fall back emitting empty values, effectively switching the proxy off.
* **Configuration Values**: Each level supports `true`, `false`, `""` (empty), `"defer"`, or unset values
* **Proxy Activation**: The proxy will be enabled if any of the configuration levels is set to `true`, following the precedence order above. The emitted values for `HTTP_PROXY` and `NO_PROXY` will be read from the `cluster-config` config map, from the `http-proxy` and `no-proxy` keys respectively. If the keys are missing from the config map, the following default values would be had-coded in the init task:
  * `HTTP_PROXY`: `squid.caching.svc.cluster.local:3128`
  * `NO_PROXY`: "" (Empty string)
* **Logging**: The pipeline init task will log the proxy configuration applied to the pipeline run and the reasoning for it being in effect.

### Configuration Logic

The proxy will be enabled if any of these conditions are met (in order of precedence):

* Cluster flag is `true`
* Cluster flag is unset/empty/deferred AND pipeline parameter is `true`

What this means in practice is that setting the flag to `false` switches the
proxy off regardless of the configuration in the lower precedence levels, while
leaving an unset or empty value (Or explicitly deferring) lets the lower levels
decide.

The default behavior is a consequence of having the value be unset in all
levels. That results in the proxy being "off".

### Rejected ideas

Originally this ADR proposed a per-namespace configuration level to override the pipeline configuration and be overridden by the cluster-level configuration. Following community discussion, this idea was rejected due to concerns of introducing unnecessary complexity.

## Consequences

* **Improved User Experience**: Users can control proxy usage through simple boolean flags without needing to understand proxy technical details like ports or addresses
* **Flexible Control**: Three levels of configuration provide appropriate control for different user roles (pipeline authors, namespace administrators, cluster administrators)
* **User retains ultimate control**: To be effective, the setting here rely on the pipeline being configured in a certain way, namely, on the output values of the "init" task being fed back to the "buildah" task parameters. If they want to, the users may sever this relationship and use a completely different configuration.
* **GitOps Integration**: Configuration can be managed through GitOps processes using config maps, consistent with other Konflux configuration elements
* **Implementation Complexity**: The init task becomes more complex as it needs to resolve configuration from multiple sources and apply precedence rules
* **Configuration Management**: Cluster and namespace administrators need to understand the precedence rules to effectively manage proxy usage
* **Documentation Requirements**: Clear documentation will be needed to explain the configuration options and precedence rules for different user roles
* **Migration Path**: The implementation can be done incrementally, starting with basic pipeline-level support and adding cluster/namespace configuration later to avoid breaking changes
