# Project Controller

## Overview

The Project Controller is a Kubernetes controller that enables users to manage projects and development streams in Konflux. It provides a templating system for creating multiple similar development streams with consistent resource structures, streamlining the process of setting up complex multi-component applications.

## Description

The Project Controller introduces three main custom resources that work together to provide project and development stream management:

- **Project**: Represents a major piece of software that can be worked on by multiple teams over an extended period of time
- **ProjectDevelopmentStream**: Indicates an independent stream of development that can contain one or more Applications, each containing one or more Components
- **ProjectDevelopmentStreamTemplate**: Defines reusable resource templates that can be instantiated with variable values to create consistent development streams

The controller uses [Go text/template](https://pkg.go.dev/text/template) syntax to enable variable substitution and customization of generated resources.

## Dependencies

The Project Controller depends on:
- Konflux [Application API](https://konflux-ci.dev/docs/reference/kube-apis/application-api/) for creating and managing Applications and Components
- Kubernetes controller-runtime for reconciliation logic
- Go text/template engine for resource templating

## Controllers

The Project Controller contains:

- **ProjectDevelopmentStream Controller**: Monitors `ProjectDevelopmentStream` resources and applies templates to generate Konflux resources
- **Template Engine**: Processes Go text/template syntax with custom functions like `hyphenize` for Kubernetes-compliant naming

## Interface

### Project CR

The `Project` resource provides metadata and organization for related development streams.

```yaml
apiVersion: projctl.konflux.dev/v1beta1
kind: Project
metadata:
  name: my-project
spec:
  displayName: "My Cool Project"
  description: |
    Description of my project that can span multiple lines.
```

### ProjectDevelopmentStreamTemplate CR

The `ProjectDevelopmentStreamTemplate` defines reusable resource templates with variable substitution.

```yaml
apiVersion: projctl.konflux.dev/v1beta1
kind: ProjectDevelopmentStreamTemplate
metadata:
  name: my-project-template
spec:
  project: my-project
  variables:
  - name: version
    description: A version number for a new development stream
  - name: versionName
    description: A K8s-compliant name for the version
    defaultValue: "{{hyphenize .version}}"
  
  resources:
  - apiVersion: appstudio.redhat.com/v1alpha1
    kind: Application
    metadata:
      name: "cool-app-{{.versionName}}"
    spec:
      displayName: "Cool App {{.version}}"
  
  - apiVersion: appstudio.redhat.com/v1alpha1
    kind: Component
    metadata:
      name: "cool-comp1-{{.versionName}}"
    spec:
      application: "cool-app-{{.versionName}}"
      componentName: "cool-comp1-{{.versionName}}"
      source:
        git:
          context: "."
          dockerfileUrl: "Dockerfile"
          revision: "{{.version}}"
          uri: git@github.com:example/comp1.git
```

### ProjectDevelopmentStream CR

The `ProjectDevelopmentStream` instantiates templates with specific variable values.

```yaml
apiVersion: projctl.konflux.dev/v1beta1
kind: ProjectDevelopmentStream
metadata:
  name: my-project-1-0-0
spec:
  project: my-project
  template:
    name: my-project-template
    values:
    - name: version
      value: "1.0.0"
```

## Supported Resource Types

The Project Controller supports templating for the following Konflux resource types:

- **Application**: Creates Konflux applications with templated names and display names
- **Component**: Creates components with templated source URLs, revisions, and application references
- **ImageRepository**: Creates image repositories with templated names and component associations
- **IntegrationTestScenario**: Creates integration test scenarios with templated parameters
- **ReleasePlan**: Creates release plans with templated application references

## Template Features

### Variable System

- **Variable Definition**: Variables are defined in the template with optional default values
- **Variable Substitution**: Values can be provided when creating development streams
- **Default Values**: Variables can have default values that can reference other variables
- **Validation**: Template variables are validated before resource creation

### Custom Template Functions

- **hyphenize**: Converts strings to Kubernetes-compliant names by replacing invalid characters with hyphens
- **Go text/template**: Full support for Go's text/template syntax including conditionals, loops, and functions

### Resource Management

- **Ownership**: Generated resources are automatically owned by the ProjectDevelopmentStream
- **Ordering**: Resources are created in a specific order to establish proper ownership relationships
- **Validation**: Resource names are validated against Kubernetes naming conventions
- **Conflict Resolution**: Uses server-side apply for conflict resolution during updates

## Workflow

1. A `Project` resource is created to define the project scope
2. A `ProjectDevelopmentStreamTemplate` is created with resource definitions and variables
3. One or more `ProjectDevelopmentStream` resources are created referencing the template
4. The controller processes each development stream:
   - Resolves template variables using provided values or defaults
   - Generates Konflux resources using the template
   - Creates resources with proper ownership relationships
   - Sets up cross-references between generated resources

## Known Limitations

- **Template Drift**: Resources modified after creation are not automatically aligned with templates unless the controller restarts or parent resources are modified
- **Template Changes**: Changing templates or switching between templates may not clean up resources not defined in the new template
- **Resource Ordering**: Resource creation order is fixed and may not accommodate all dependency scenarios

## Integration with Konflux

The Project Controller integrates with Konflux by:

- Creating and managing Konflux Application and Component resources
- Establishing proper ownership relationships between resources
- Supporting all major Konflux resource types through templating
- Following Konflux naming conventions and resource patterns
- Providing a declarative approach to multi-component application management

The service operates as an add-on, providing project management capabilities that complement the core Konflux development workflow.
