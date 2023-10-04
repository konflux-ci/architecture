# Hybrid Application Service (HAS) Glossary

## Application
An application in AppStudio, represented by the HAS Application custom resource. May contain one or more “components”.

## Application Model
A devfile representation of the application, containing information about the HAS Application (e.g. its name, description, GitOps repo, etc), along with each component that is part of the application. The application model contains the pointers to where the components can be found.

## Application Model Repository
The git repository where the application model is stored (and available for later import). Specified when creating the HAS Application resource. Can be the same repository as the GitOps repository. The source of the child components may either be contained within a folder under the application model repository or it can be distributed in other repositories that contain the component source code.

## Component
A single containerized component, running as part of a HAS Application in AppStudio. Represented by the HAS Component custom resource. Each component will contain a devfile that contains information about how to build and deploy the application in App Studio.

## Devfile
A yaml file (and corresponding specification) defining a workflow of a component. It contains information on how to build, run, deploy and interact with the component if the devfile is on the component level. A devfile on the application describes the composition of the application.

# Devfile Registry
A service, such as the [public community registry](https://registry.devfile.io), that hosts devfile stacks and samples for consumption.

## GitOps Repository
The git repository where the Gitops resources for a given application is stored. This is “source of truth” for the operation of the GitOps services. Specified when creating the HAS Application resource. This can be the same repository as the application model repository. Whenever the HAS Application model changes, the GitOps repository will be updated to reflect the change in the application model.

