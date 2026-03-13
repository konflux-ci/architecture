# NN. Registry Proxy Feature Flag Configuration for Hermeto

Date: YYYY-MM-DD

## Status

Proposed

## Context

Hermeto is the content prefetching tool used in Konflux build pipelines to fetch application dependencies before the container image build step. It supports multiple package managers including npm, yarn, gomod, pip, cargo, and bundler. Currently, Hermeto fetches dependencies directly from upstream package registries such as registry.npmjs.org, proxy.golang.org, PyPI, crates.io, and rubygems.org.

This direct fetching from upstream sources exposes the build process to supply chain attacks. Malicious packages published to public registries can be consumed by builds without any policy evaluation or control. Recent high-profile incidents have demonstrated that attackers actively target package registries to distribute malware.

To address this security gap, organizations can deploy a registry proxy with a policy enforcement layer that:

1. **Evaluates all consumed artifacts** against organizational governance policies during ingestion, automatically quarantining components that violate policy before they are available for use in builds.
2. **Stores all consumed artifacts** in a controlled repository, providing an audit trail and enabling reproducible builds.

By routing Hermeto's dependency fetching through such a registry proxy, malicious or non-compliant components can be blocked before they ever reach the build environment.

### Architecture Overview

The deployment architecture involves two components between Hermeto and upstream package registries:

1. **Registry proxy** (e.g., Sonatype Nexus Repository Server): An external service that proxies upstream package registries, enforces governance policies on ingested artifacts, and stores them in controlled repositories.
2. **On-cluster reverse proxy**: A reverse proxy deployed on the Konflux cluster that sits in front of the registry proxy and handles authentication transparently. Hermeto sends requests to this reverse proxy, which forwards them to the registry proxy with the appropriate credentials.

The design and deployment of the on-cluster reverse proxy is outside the scope of this ADR.

**Users** need the ability to:

* Use the registry proxy automatically when available, without manual configuration
* Opt out of registry proxy use for individual pipelines when needed

**Platform administrators** need the ability to:

* Enable/disable registry proxy usage at the cluster level for all pipelines
* Configure registry proxy URLs for different package managers (npm, pip, cargo, etc.) since they may be served from different registry proxy repositories
* Apply GitOps processes for this configuration, similar to other Konflux configuration elements

## Decision

We will extend the `cluster-config` ConfigMap described in [ADR 0057](0057-pipeline-caching-feature-flag.md) with an `allow-registry-proxy` flag and per-package-manager registry proxy URL keys. We will also introduce an `enable-registry-proxy` pipeline parameter that gives users control over whether their pipeline uses the proxy.

The registry proxy is used only when both the administrator and user permit it: `allow-registry-proxy` must be `true` in the ConfigMap and `enable-registry-proxy` must be `true` in the pipeline. The administrator flag defaults to `false`, so the proxy is disabled until explicitly enabled at the cluster level. The pipeline parameter defaults to `true`, so once an administrator enables the proxy, all pipelines use it automatically. Users who need to bypass the proxy for debugging or compatibility reasons can set their pipeline parameter to `false`.

This is the opposite of the cache proxy model in [ADR 0057](0057-pipeline-caching-feature-flag.md), where each user must enable the proxy for their own pipeline. The difference reflects the nature of the feature: caching is a performance optimization individual users choose to adopt, while registry proxying is a security control that should apply globally unless a user explicitly opts out.

### Implementation Details

Each supported package manager gets its own proxy URL key in the ConfigMap, named `registry-proxy-<pkg>-url`. The initially supported package managers are npm, yarn, gomod (with a separate `registry-proxy-gomod-sum-url` for the checksum database), pip, cargo, and bundler. Multiple package managers may share the same URL if they use the same upstream registry. The configured URLs point to the on-cluster reverse proxy, which handles authentication to the registry proxy transparently.

The init task resolves `allow-registry-proxy` and `enable-registry-proxy` into a single `use-registry-proxy` result that is passed to the prefetch-dependencies task, so that the effective setting is visible in Chains attestation data. When `use-registry-proxy` is true, the prefetch-dependencies task reads the per-package-manager proxy URLs directly from the ConfigMap and sets the corresponding Hermeto environment variables. This avoids threading a growing number of URL parameters through the pipeline definition as Hermeto adds support for more package ecosystems.

Unlike ADR 0057, we do not define hard-coded fallback URLs. Hermeto does not use a registry proxy by default, so the presence of a proxy URL in the ConfigMap is what triggers the prefetch-dependencies task to configure Hermeto to proxy that package manager's requests. If a package manager's proxy URL is not present in the ConfigMap, Hermeto fetches directly from upstream for that package manager.

### Alternatives considered

**Proxy URLs as pipeline parameters**: An approach where the init task reads all proxy URLs from the ConfigMap and emits them as individual Tekton results, with the prefetch-dependencies task consuming them as parameters. This was rejected because it requires ~7 result/parameter pairs threaded through the pipeline definition, and the number grows as Hermeto adds support for more package ecosystems. Additionally, Tekton imposes a 4096-byte limit on a task's combined results; a large number of URL results emitted from the init task would consume a significant portion of that budget.

**Single base URL**: One URL (e.g., `https://registry-proxy.example.com`) would be configured and per-package-manager paths constructed at runtime. While simpler to configure, this would hardcode path assumptions in the prefetch-dependencies task and prevent administrators from selectively enabling the proxy for some package managers while leaving others disabled, or from routing different package managers to different proxy servers.

**Per-namespace ConfigMap**: Proxy URLs would be placed in a namespace-scoped ConfigMap directly available to tasks. However, [ADR 0057](0057-pipeline-caching-feature-flag.md) already rejected per-namespace configuration for the cache proxy.

## Consequences

* **Attestation**: The `use-registry-proxy` setting flows through Tekton task parameters, making it visible in Chains attestation data. Conforma policies can use this to quickly determine whether the registry proxy was enabled for a build before doing package-level analysis.
* **Simple User Experience**: Users control registry proxy usage through simple boolean flags without needing to understand registry proxy URLs, authentication, or repository configurations.
* **Cluster-level Control**: The cluster-level `allow-registry-proxy` flag enables quick cluster-wide enable/disable, and per-package-manager URLs allow phased rollout across package ecosystems. Since builds depend on the registry proxy being available, this flag provides a fast way to unblock all builds if the proxy experiences an outage.
* **User Retains Ultimate Control**: As with all Konflux pipeline configuration, advanced users can modify their pipeline YAML to bypass these settings. Users who do not want the proxy can set `enable-registry-proxy` to `false`. Note that the proxy URLs themselves are not user-configurable and are set by the administrator at the cluster level.
* **Minimal Pipeline Wiring**: Only a single boolean parameter is threaded through the pipeline. The proxy URLs are read directly from the ConfigMap by the prefetch-dependencies task, so adding support for new package managers does not require pipeline definition changes.
* **No Silent Fallback**: Hermeto will fail a request if a configured proxy URL is unreachable or invalid, rather than falling back to upstream registries.
* **Documentation Requirements**: Clear documentation will be needed to explain the two-level configuration model and per-package-manager URL setup for both administrators and users.
