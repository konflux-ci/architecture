# Hybrid Application Service (HAS) Glossary

## Application
An Application in Konflux, represented by the HAS Application custom resource. May contain one or more “components”.

## Application Model
A Devfile representation of the Application, containing information about the HAS Application (e.g. its name, description, GitOps repo, etc), along with each Component that is part of the Application. The Application model contains the pointers to where the Components can be found.

## Application Model Repository
The git repository where the Application model is stored (and available for later import). Specified when creating the HAS Application resource. Can be the same repository as the GitOps repository. The source of the child Components may either be contained within a folder under the Application model repository or it can be distributed in other repositories that contain the Component source code.

## Component
A single containerized Component, running as part of a HAS Application in Konflux. Represented by the HAS Component custom resource. Each Component will contain a Devfile that contains information about how to build and deploy the Application in App Studio.

## Devfile
A yaml file (and corresponding specification) defining a workflow of a Component. It contains information on how to build, run, deploy and interact with the Component if the Devfile is on the Component level. A Devfile on the Application describes the composition of the Application.

# Devfile Registry
A service, such as the [public community registry](https://registry.devfile.io), that hosts Devfile stacks and samples for consumption.

## GitOps Repository
The git repository where the Gitops resources for a given Application is stored. This is “source of truth” for the operation of the GitOps services. Specified when creating the HAS Application resource. This can be the same repository as the Application model repository. Whenever the HAS Application model changes, the GitOps repository will be updated to reflect the change in the Application model.

