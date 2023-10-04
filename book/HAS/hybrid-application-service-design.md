# Hybrid Application Service (HAS) Design

## Application CR Create

HAC collects the information required for creating applications. An application is a collection of one or more components. Required information to be collected can be found in the API [doc](). When all the application information is available, HAC will create the Application CR to trigger the application creation. The HAS Application CR Operator will:
1. Validate all the required fields in the Application CR
2. If the app model repository and the GitOps repository repos are specified:
   1. It will validate if the specified repo exists.
3. If any of those are not specified:
   1. it will generate a repo under the org https://github.com/redhat-appstudio-appdata
   2. Update the application CR with the generated repo information
   3. Triggers the creation of the GitOps repository for the generated repo
   4. Create the application level devfile under the Application CR status

## Component CR Create

### Importing a Devfile Sample
HAC will prompt the user to select a sample (retrieved via the Devfile Registry REST API) to choose from. The Git repository corresponding to this sample (such as https://github.com/devfile-samples/devfile-sample-code-with-quarkus) will be specified when creating the Component CR.

### Importing from Git
HAC will prompt the user to provide a Git repository.
A ComponentDetectionQuery CR will be created, it will:
1. If a devfile is present, then:
   1. If the devfile is valid and has the outerloop Kubernetes component and the deploy command, the information in the Devfile will be returned
   2. If the Devfile is not valid, the ComponentDetectionQuery will check for a matching devfile from the devfile registry
2. If the repo doesn’t have a devfile but has a dockerfile, a devfile will be generated to refer to the Dockerfile and store that as part of the component CR.
3. If a devfile and Dockerfile is not available, the ComponentDetectionQuery will check for a matching devfile from the devfile registry. The ComponentDetectionQuery status.data will be updated to reflect the mapping and a Component stub will be generated. This can be used to create a Component CR to create a component.

If the Git repository contains more than one component, the ComponentDetectionQuery will return a list of components and their associated mapping. If a component is not mapped, then HAC will prompt the user for further information ie, should the directory be ignored, or to manually provide a mapping

### Importing from an Image
HAC will prompt the user to enter an image to import a Component from. The Component CR controller will create a basic devfile with the image specified and store in the status field

### Component Creation Flow
After all of the individual components have been selected by the user, and the Application CR has been created, HAC will create Component CRs for each individual component. The HAS Component controller will:
1. Validate the required fields in the Component CR
   1. Does the Application CR exist
   2. Does it point to a valid Sample/Github repo/devfile?
2. Retrieve the devfile from the specified source, and validate it
3. Add the devfile to the Component CR’s status
4. Update the Application CR with an entry to the newly created Component

## Application CR Update

Application model update can be done by updating an existing Application CR directly. Application CR update is handled by the Application Controller. Only the mutable fields listed in the required fields in the Application CR can be updated.

When an Application CR is being updated, the Application Controller will:
1. Check to make sure all changed fields are mutable. Any changes on the immutable fields will result in an error in the Application CR Update.
2. Update the application devfile (as specified in the spec.appModelRepository.url if applicable)

## Component CR Update

Component model update can be done by updating an existing Component CR directly. Component CR update is handled by the Component Controller. Only the mutable fields listed in the required fields in the Application CR can be updated.

When an Component CR is being updated, the Component Controller will:
1. Check to make sure all changed fields are mutable. Any changes on the immutable fields will result in an error in the Component CR Update.
2. Update the component devfile (as specified in the status.data if applicable)
3. For changes that require GitOps repo changes, call the HAS internal Push function to update the GitOps repository to reflect the model change for fields.

## Usage of Devfile in Applications and Components

The git source repo may or may not have the devfile physically stored within the repo. In case the repo has a devfile exists, it may not be the latest version. Future plan is to provide a way for creating PRs to put the latest devfile in the user’s source repo, the user may not accept the PR. Therefore, the devfile within the Application CRs and Component CRs will always be the latest and any action that needs to use the devfile stored in the Component CR to make sure it is using the latest version of the devfile, e.g. build pipeline and GitOps resource generation.

## Build Service Integration

For the Build Service integration, The HAS Component controller will create a webhook url during the Component creation process. A TriggerTemplate and an EventListener will be created as per the documentation AppStudio Build Service Architecture

The webhook URL will only be created with a user provided Git repository. If the user chooses to import from a Devfile Registry sample, the user would need to clone the sample and import it via HAC to enable webhooks for the Git repository.

The webhook URL would be displayed on HAC and the user is expected to manage it manually via Git.

## GitOps Service Integration

For the GitOps service integration, the HAS controller will create the GitOps repository when Application CRs are created. And when Component CRs are created/updated, will generate and push the corresponding GitOps resources for that component to the repository (as outlined above for Application and Component create/update).

A webhook will be registered on the GitOps repository that the GitOps service can listen to on the repository, to be notified when to deploy components.

## GitOps Repo Structure

The GitOps repository stores the following information:
1. GitOps resources in the form of kustomization files that are required by the GitOps services to do the Application deployment:
   1. [Sample Generated GitOps Repo](https://github.com/redhat-appstudio/gitops-repository-template) - where we wanted to generate in the future
   2. [Sample Generated GitOps Repo](https://github.com/elsony/gitops-repo-template) - previous version generated by HAS (before environment support)
2. HAS Component specific information like Deployment, Service, Route, Ingress and other Kubernetes resources.

In the beginning, the GitOps repository will be stored under the private org https://github.com/redhat-appstudio-appdata that is owned by AppStudio. The user will not be able to access the data under that org directly. For each application, a unique GitOps repository will be generated under that GitHub org for storing the GitOps repository specific data. For GitOps repository that is stored under that private org, the lifecycle of that repository will follow the lifecycle of the application, i.e. when the application is being deleted, the corresponding GitOps repository will be deleted automatically.

In the future, the user can bring their own users repo to store those GitOps resources. By that time, AppStudio will need to support the user editing the GitOps resources directly. The lifecycle of the GitOps repository may not follow the lifecycle of the application since it is a user owned resource. We may need to prompt the user for the option to delete the corresponding GitOps repository when the user deletes the application, i.e. when the Application CR is deleted.
