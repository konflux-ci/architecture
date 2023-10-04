# Hybrid Application Service (HAS)

Hybrid Application Service (HAS) provides an abstract way to define Applications and Components within the cloud. It also allows users to create new Applications and Components or import existing ones into AppStudio. HAS itself is a fully managed service with a set of predefined service types to provide out-of-the-box support.

## Goals
- Define an application model that defines the application and its containing components
- Create new multi-component applications that can be represented by the application model
- Governs the life-cycle of application model includes create, update and delete
- Create predefined component types to help to develop, build and deploy components of a particular language or framework
- Provide sample/starter component for the predefined component types
- Import existing applications and represent them by the application model
- Discovery mechanism matching the component type for each component to a predefined type support
- Set up the development environment (tools) easily for components that match the predefined component type



## Architecture Overview
To see how HAS fits into the AppStudio architecture, refer to the AppStudio [Application Context](./index.md#application-context).

The diagram below shows the interaction between HAC and HAS services for the creation of Application and Component.

### Flow Chart

![](../diagrams/hybrid-application-service/has-application-component-create.jpg)

### Sequence Diagram

![](../diagrams/hybrid-application-service/has-create-application-seqeuence.png)

## Documentation

Navigate the various Hybrid Application Service topics to read more about them.

- [Hybrid Application Service (HAS) Design](./HAS/hybrid-application-service-design.md)
- [Hybrid Application Service (HAS) Glossary](./HAS/hybrid-application-service-glossary.md)
- [Hybrid Application Service (HAS) Kubernetes API](./HAS/hybrid-application-service-api.md)
- [Hybrid Application Service (HAS) Kubernetes CRDs](./HAS/hybrid-application-service-crds.md)
- [Component Detection Query (CDQ) Controller Logic](./HAS/component-detection-query-controller-logic.md)
- [Hybrid Application Service (HAS) Component Types](./HAS/hybrid-application-service-component-types.md)
