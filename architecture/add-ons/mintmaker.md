# MintMaker

## Overview

MintMaker is a Kubernetes controller that automates dependency updates for Konflux components using [Renovate](https://docs.renovatebot.com). It provides a declarative way to trigger dependency scanning and updates across multiple components in Konflux applications.

## Description

MintMaker introduces the `DependencyUpdateCheck` custom resource, which acts as a trigger for the dependency update process. When a `DependencyUpdateCheck` CR is created, MintMaker examines all components within Konflux for dependency updates and creates Tekton `PipelineRun` instances to execute Renovate scans.

Konflux components originate from repositories on two types of platforms, GitHub and GitLab. MintMaker adapts its functionality based on the platform:

* **GitHub**: If the repository has Konflux's Pipeline as Code GitHub Application installed, MintMaker utilizes the token generated from the application to run Renovate.
* **GitLab**: MintMaker scans the component's namespace for a secret containing the Renovate token. Upon finding the token, MintMaker employs it to execute Renovate for components within the same namespace.

## Dependencies

MintMaker depends on:
- Konflux [Application API](https://konflux-ci.dev/docs/reference/kube-apis/application-api/) for discovering Components
- Tekton Pipelines for executing Renovate scans
- GitHub or GitLab for repository access
- Package and container registries (e.g., crates.io, npm, PyPI, Quay.io) for discovering dependency updates

## Controllers

The MintMaker controller contains these controllers:

- **DependencyUpdateCheck Controller**: Monitors `DependencyUpdateCheck` CRs and creates Tekton `PipelineRun` instances for dependency scanning
- **PipelineRun Controller**: Monitors the execution of dependency update PipelineRuns
- **Event Controller**: Handles GitHub token generation and secret management for GitHub repositories

## Interface

### DependencyUpdateCheck CR

The `DependencyUpdateCheck` CR is the primary interface to trigger dependency updates in Konflux components.

#### To scan all components across the cluster:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: DependencyUpdateCheck
metadata:
  name: global-dependency-check
  namespace: mintmaker
spec: {}
```

#### To scan specific namespaces and applications:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: DependencyUpdateCheck
metadata:
  name: targeted-dependency-check
  namespace: mintmaker
spec:
  namespaces:
  - namespace: "my-namespace"
    applications:
    - application: "my-application"
      components:
      - "component1"
      - "component2"
    - application: "another-application"
  - namespace: "another-namespace"
```

### Component Annotations

Components can be excluded from MintMaker processing using annotations:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  name: my-component
  annotations:
    mintmaker.appstudio.redhat.com/disabled: "true"
```

### Generated Resources

When processing a `DependencyUpdateCheck`, MintMaker creates:

- **Tekton PipelineRun**: Executes Renovate to scan and update dependencies
- **Secrets**: Contains repository access tokens and container registry credentials
- **ConfigMaps**: Contains Renovate configuration
- **Labels**: Applied to PipelineRuns for tracking and identification

## Workflow

1. A `DependencyUpdateCheck` CR is created in the `mintmaker` namespace
2. The controller discovers Konflux Components based on the CR specification:
   - By default: all `Component` resources across the cluster
   - Or: a filtered subset when `spec.namespaces` is provided
3. For each unique repository+branch combination, the controller creates a Tekton `PipelineRun`
4. The PipelineRun executes Renovate to:
   - Scan the repository for outdated dependencies
   - Create pull requests with dependency updates
   - Generate reports on dependency status
5. Results are tracked through PipelineRun status and logs

## Security Considerations

- **Token Management**: GitHub tokens are generated dynamically and have a 1-hour lifespan to minimize exposure
- **Secret Isolation**: Repository access tokens are stored in secrets that are cleaned up after PipelineRun completion
- **RBAC**: MintMaker requires specific permissions to read Components and create PipelineRuns
- **Network Policies**: PipelineRuns run in the `mintmaker` namespace with appropriate network restrictions

## Configuration

MintMaker can be configured through:

- **Environment Variables**: 
  - `RENOVATE_IMAGE`: Custom Renovate container image
- **ConfigMaps**: 
  - `renovate-config`: Global Renovate configuration
  - `mintmaker-controller-configmap`: Controller settings
- **Secrets**:
  - `pipelines-as-code-secret`: GitHub application credentials
  - Component-specific secrets for GitLab access

## Monitoring and Metrics

MintMaker provides metrics for:
- Number of DependencyUpdateCheck resources processed
- PipelineRun creation and completion rates
- Component scanning statistics
- Error rates and failure modes

## Integration with Konflux

MintMaker integrates with Konflux by:
- Reading Component resources to discover repositories
- Using existing ServiceAccount credentials for container registry access
- Leveraging Tekton for pipeline execution
- Following Konflux naming conventions and resource patterns

The service operates as an add-on, providing dependency management capabilities without requiring changes to core Konflux services.
