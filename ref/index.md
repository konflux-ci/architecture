# API Reference

## AppStudio

- [Application and Environment API](application-environment-api.md): Hybrid Application Service (HAS) provides an abstract way to define applications within the cloud. Also includes shared APIs for defining and managing environments.
- [Service Provider](service-provider.md): Responsible for providing a service-provider-neutral way of obtaining authentication tokens so that tools accessing the service provider do not have to deal with the intricacies of getting the access tokens from the different service providers.
- [GitOps Service](gitops.md): Responsible for synchronizing source K8s resources in a Git repository (as the single of truth), with target OpenShift/K8s cluster(s).

## HACBS

- [JVM Build Service API](jvm-build-service.md): Responsible for rebuilding Java components of an application from source.
- [Integration Service API](integration-service.md): Responsible for initiating functional integration tests for an [Application] when one of its [Components] gets a new build.
- [Release Service API](release-service.md): Responsible for carrying out [Releases] initiated either by the user or automatically by [integration-service](integration-service.md).
- [Enterprise Contract API](enterprise-contract.md): Used by administrators to express policy. Interpreted by [Release Service](release-service.md) as a policy enforcement point.

## Control Plane

- [KCP](kcp.md)

[Application]: application-environment-api.md#application
[Components]: application-environment-api.md#component
[Releases]: release-service.md#release
