# API Reference

## Konflux

- [Application and Environment API](application-environment-api.md): Hybrid Application Service (HAS) provides an abstract way to define applications within the cloud. Also includes shared APIs for defining and managing environments.
- [Pipeline Service](pipeline-service.md): Responsible for executing Tekton `PipelineRuns` and providing access to Tekton services.
- [Integration Service API](integration-service.md): Responsible for initiating functional integration tests for an [Application] when one of its [Components] gets a new build.
- [Release Service API](release-service.md): Responsible for carrying out [Releases] initiated either by the user or automatically by [integration-service](integration-service.md).
- [Enterprise Contract API](enterprise-contract.md): Used by administrators to express policy. Interpreted by [Release Service](release-service.md) as a policy enforcement point.

## Control Plane

[Application]: application-environment-api.md#application
[Components]: application-environment-api.md#component
[Releases]: release-service.md#release
