# 47. Caching for container base images used during builds

Date: 2025-06-22

## Status

Implementable

## Context

Konflux builds container images using tools like Buildah. During the build process, base images are fetched from container registries like `quay.io`. This repeated fetching of the same images results in high network traffic, slower build times, and exposes builds to failures caused by network issues or registry rate-limiting. This negatively impacts both the user experience (in terms of build speed and reliability) and operational costs of running the platform.

## Decision

We will implement a caching layer for container base images used during the build process using Squid HTTP proxies to mitigate these issues.

### Rationale

Squid was chosen as the caching proxy for several reasons:

* **Maturity:** Squid is a long-standing, feature-rich, and stable caching proxy.
* **TLS Interception:** Its `ssl-bump` feature is well-documented and provides the necessary functionality to intercept TLS-encrypted traffic from container registries, which is a key requirement for caching container image layers.
* **Configurability:** Squid offers fine-grained control over caching policies, allowing us to specifically target immutable and content-addressable image layer blobs, which is crucial for minimizing security risks like cache poisoning.

### Implementation Details

* **Deployment:** The proxies will be deployed via a configurable Helm chart into a dedicated `proxy` namespace.
* **Access:** A well-known service endpoint, `http.proxy.svc.cluster.local`, will provide access to the proxy service within the cluster.
* **TLS Caching:** We will use Squid's `ssl-bump` feature to cache content from TLS-encrypted connections. This requires establishing an internal Certificate Authority (CA) using `cert-manager`. Following the common practice of using separate CAs for separate concerns, the CA will be dedicated to the proxy service. This may be revisited in the future if a service mesh with a shared CA infrastructure (e.g. SPIFFE/SPIRE) is adopted.
* **Private layer blob caching:** To allow for caching of private images, we will use a custom
Squid ACL policy to either compartmentalize the cache according to authorization headers or
otherwise find a cheap way to verify authorization with the upstream registry before returning
private layer blobs from the cache.
* **Trust:** The internal CA's trust bundle will be distributed to build pods using `trust-manager`.
* **Integration:** The `buildah` Tekton task will be updated to use the proxy by default via the standard `http_proxy` and `https_proxy` environment variables. To ensure visibility, pipeline templates will be updated to explicitly pass the proxy parameters. This "opt-in by default" approach ensures existing pipelines benefit from caching without modification, while new and updated pipelines make the use of the proxy explicit. Users can opt-out by either configuring the `HTTP_PROXY` parameter to an empty string or by deny-listing particular domains in the `no_proxy` environment variable via the `NO_PROXY` task parameter.
* **Configuration:** The full caching functionality is an optional add-on. When enabled, caching will be limited to a configurable allowlist of domains, initially targeting `quay.io`, `registry.access.redhat.com`, `registry.redhat.io` and the stage versions of those.
* **Storage:** The cache will initially be stored in the Pod's RAM or a host-local `tmpfs` volume. This is the simplest approach that does not require complex storage provisioning. As a cache, there is no minimum required size; rather, more storage generally leads to a better cache hit rate. The optimal storage size and medium (e.g., RAM vs. persistent volumes) will be determined and adjusted over time by monitoring the cache performance and hit rate in a production environment.

## Alternatives Considered

Several alternatives to using a Squid proxy were considered:

* **Mirroring images to a local registry:** This approach involves hosting a private registry within the cluster and preemptively mirroring all required base images to it. While it would provide fast and reliable access to those images, it was deemed too inflexible. It would require us to anticipate every image and tag that developers might use, which is not feasible in a dynamic development environment. It would also introduce significant storage overhead and management complexity.

* **Using a local registry in pull-through cache mode:** Many container registries can be configured to act as a pull-through cache for an upstream registry. In this setup, the first time an image is requested, the local registry pulls it from the upstream source and caches it for subsequent requests. While this avoids the need to pre-mirror images, it introduces its own challenges. It would require re-writing image references in user's Dockerfiles and pipeline definitions to point to the local registry. This would break portability and complicate the user experience, especially for users who need to pull images from various public and private registries. It can also complicate authentication, as credentials for all upstream registries would need to be managed by the caching registry.

The chosen Squid-based approach was preferred because it is more transparent. Clients continue to reference images by their canonical names (e.g., `quay.io/namespace/image:tag`), and the proxy transparently caches the underlying layer blobs without requiring any changes to image names or build definitions. This provides the benefits of caching with minimal impact on the user workflow.

## Consequences

* **Benefits:** This change is expected to reduce image pull times, lower network bandwidth consumption, and improve build reliability.
* **New Infrastructure:** We will now operate and maintain additional components: Squid proxy instances and an internal CA via `cert-manager`.
* **Monitoring & Health:** We will create a Prometheus exporter to monitor cache metrics (hit/miss rate, storage utilization, etc.) and an availability probe to continuously validate the proxy's functionality. This probe will also be part of the Helm chart's test suite.
* **Resilience:** Squid pods will be deployed with anti-affinity rules to spread them across different nodes. The choice of storage (RAM vs. persistent volumes) will impact cache persistence across pod restarts.
* **Documentation:** User-facing documentation will be required to explain how to use the proxy and how to opt-out.
* **Security:** The use of `ssl-bump` introduces a new security consideration around the management and protection of the internal CA. The primary defense against cache poisoning is the use of content-addressable storage for container image layers. Clients like `buildah` verify the digest (SHA checksum) of each layer after download. Any mismatch between the expected and actual digest due to a poisoned cache entry will cause the build to fail, preventing the use of a corrupted artifact. By limiting the scope of caching to only these content-addressable blobs, the risk is significantly minimized. Furthermore, the initial choice of ephemeral storage (Pod RAM or `tmpfs`) means that any potential cache poisoning event would be short-lived and cleared upon pod restart. This is a primary motivation for limiting the scope of this ADR and deferring caching of mutable content or intermediate layers, which would introduce greater risk.
* **Isolation for Private Repositories:** By default, Squid does not cache responses to requests that contain `Authorization` headers unless explicitly allowed by `Cache-Control` headers from the origin server. This prevents a user in one namespace from inadvertently accessing a cached image layer from a private repository that was fetched by a user in another namespace. While this default behavior provides strong isolation, we know Konflux users frequently use private images. Therefore, custom configuration to allow for caching of private images will be put in place as described above.
* **Scope:** This solution is focused on caching container base images used during the build process for in-cluster builds. Caching intermediate layers is out of scope for this ADR as it adds extra complexity. It does not address caching for other protocols, per-node caching, or builds running on external VMs. Caching other types of artifacts, like Tekton bundles or artifacts for trusted artifact verification, is also out of scope for this ADR. These may be addressed in future ADRs, and may be able to use the same caching infrastructure.
