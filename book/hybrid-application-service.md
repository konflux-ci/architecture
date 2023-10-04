# Hybrid Application Service

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
The diagram below shows the interaction between HAC and HAS services for the creation of Application and Component.

### HAS Flow Chart

![](../diagrams/hybrid-application-service/has-application-component-create.jpg)

### HAS Sequence Diagram

![](../diagrams/hybrid-application-service/has-create-application-seqeuence.png)

## Documentation

- [Hybrid Application Service Design](./HAS/hybrid-application-service-design.md)
