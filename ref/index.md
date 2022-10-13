# API Reference

## AppStudio

- [Application and Environment API](application-environment-api.md): Hybrid Application Service (HAS) provides an abstract way to define applications within the cloud. Also includes shared APIs for defining and managing environments.
- [Service Provider](service-provider.md): Responsible for providing a service-provider-neutral way of obtaining authentication tokens so that tools accessing the service provider do not have to deal with the intricacies of getting the access tokens from the different service providers.
- [GitOps Service](gitops.md): Responsible for synchronizing source K8s resources in a Git repository (as the single of truth), with target OpenShift/K8s cluster(s).
- [Pipeline Service](pipeline-service.md): Responsible for executing Tekton `PipelineRuns` and providing acccess to Tekton services.


## Control Plane

- [KCP](kcp.md)
