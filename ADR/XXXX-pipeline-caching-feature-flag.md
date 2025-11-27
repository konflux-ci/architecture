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

A `enable-cache-proxy` pipeline parameter will determine wither a particular pipeline uses the caching proxy or not.

A `cluster-config` config map in the `konflux-info` namespace will be defined. That config map will contain the `http-proxy` and `no-proxy` keys that will provide the configuration values needed by the pipeline to actually use the proxy. The config map will be defined to be globally readable from all namespaces in the cluster, but writable only by the infra team and the ArgoCD instance managing the cluster (if any). This is similar to other config maps that already reside in the `konflux-info` namespace.

The default behavior if the proxy is not explicitly enabled is to have it be disabled. If it is explicitly enabled but the necessary configuration values are missing from the cluster level config map, the system will fallback to hard-coded default values that assume the proxy is up and running.

To facilitate disabling use of the proxy throughout the cluster, a `allow-cache-proxy` flag will be defined in the `cluster-config` config map. Setting it to `false` will disable use of the proxy throughout the cluster.

### Implementation Details

* **Pipeline Integration**: The `enable-cache-proxy` parameter will be passed to the pipeline init task
* **Configuration Resolution**: The init task will read configuration values from the `cluster-config` config map in the `konflux-info` namespace and resolve the final proxy settings
* **Environment Variables**: The init task will emit `HTTP_PROXY` and `NO_PROXY` configuration values to be used by the buildah task
* **Default Values**: If no configuration is found, the system will fall back emitting empty values, effectively switching the proxy off.
* **Proxy Activation**: The proxy will be enabled if `enable-cache-proxy` is set to `true` and `allow-cache-proxy` is either set to `true` or unset.
* **Emitted Values**: The init task will emit `HTTP_PROXY` and `NO_PROXY` configuration values be used by the buildah task, The emitted values for `HTTP_PROXY` and `NO_PROXY` will be read from the `cluster-config` config map, from the `http-proxy` and `no-proxy` keys respectively. If the keys are missing from the config map, the following default values would be had-coded in the init task:
  * `HTTP_PROXY`: `squid.caching.svc.cluster.local:3128`
  * `NO_PROXY`: "" (Empty string)
* **Environment Variables**: The values emitted from the init task need to explicitly be passed to the right parameters of the buildah task (And other relevant tasks). It is the responsibility of code within the task to convert the parameters into the appropriate environment variables to effectively facilitate the use of the proxy. At the point of writing this ADR, this capability had already been implemented for the buildah task.
* **Logging**: The pipeline init task will log the proxy configuration applied to the pipeline run and the reasoning for it being in effect.

### Rejected ideas

Originally this ADR proposed a per-namespace configuration level to override the pipeline configuration and be overridden by the cluster-level configuration. Following community discussion, this idea was rejected due to concerns of introducing unnecessary complexity.

## Consequences

* **Improved User Experience**: Users can control proxy usage through simple boolean flags without needing to understand proxy technical details like ports or addresses
* **Cluster level Control**: The cluster level `allow-cache-proxy` enables the cluster admins to quickly switch off proxy use for most users.
* **User retains ultimate control**: To be effective, the setting here rely on the pipeline being configured in a certain way, namely, on the output values of the "init" task being fed back to the "buildah" task parameters. If they want to, advanced users may sever this relationship and use a completely different configuration.
* **GitOps Integration**: Configuration can be managed through GitOps processes using config maps, consistent with other Konflux configuration elements
* **Implementation Complexity**: The init task becomes more complex as it needs to resolve configuration from multiple sources and apply precedence rules
* **Documentation Requirements**: Clear documentation will be needed to explain the configuration options and precedence rules for different user roles
* **Migration Path**: The implementation can be done incrementally, starting with basic pipeline-level support and adding cluster configuration later to avoid breaking changes
* **Attestation**: Since configuration values are passed around as pipeline task input and output values, the values and how they are passed around will be visible in the Tekton Chains attestation date. If desired, the Conforma policy can be set to enforce use of certain values and in a certain way.
