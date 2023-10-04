# Hybrid Application Service (HAS) Kubernetes API

## Overview

The official Hybrid Application Service (HAS) APIs are listed in the AppStudio [API Reference](https://redhat-appstudio.github.io/book/ref/application-environment-api.html#application).  The APIs Specific to HAS are:

* [Application](https://redhat-appstudio.github.io/book/ref/application-environment-api.html#application)
* [Component](https://redhat-appstudio.github.io/book/ref/application-environment-api.html#component)
* [ComponentDetectionQuery](https://redhat-appstudio.github.io/book/ref/application-environment-api.html#componentdetectionquery)

The topics below offer a more detailed explanation of the API usage with examples.

- [Hybrid Application Service (HAS) Kubernetes API](#hybrid-application-service-has-kubernetes-api)
  - [Overview](#overview)
  - [References](#references)
    - [Application CRD](#application-crd)
      - [Create Application](#create-application)
        - [Example](#example)
      - [Update Application](#update-application)
      - [Delete Application](#delete-application)
    - [Component CRD](#component-crd)
      - [Create Component](#create-component)
        - [Example](#example-1)
      - [Update Component](#update-component)
      - [Delete Component](#delete-component)
    - [ComponentDetectionQuery CRD](#componentdetectionquery-crd)
      - [Create ComponentDetectionQuery](#create-componentdetectionquery)
        - [Example](#example-2)


## References

* [HAS Glossary](has-glossary.md)
* [Sample Generated GitOpsRepo](https://github.com/jgwest/gitops-repository-template)


### [Application CRD](hybrid-application-service-crds.md#application)

#### Create Application
<ul>

To create an application with HAS, create an `Application` resource. Once the Application resource has been created, the HAS Controller will generate an application model (a devfile) and store it in the resource’s status field.
If no repository is set in the appModelRepository and gitOpsRepository fields, the controller will generate a repository to use.

</ul>

<ul>

##### Example
<ul>

Click on the following links to compare the contents of the Application CR before and after creation

[Application Before Creation](https://github.com/yangcao77/has-kube-samples/blob/master/001-create-application/input-hasApplication.yaml)

A successful creation of the resource will result in the controller generating the devfile model for the application and storing it in the `status.devfile` field.

[Application After Creation](https://github.com/yangcao77/has-kube-samples/blob/master/001-create-application/output-hasApplication.yaml#L74C13-L83)

</ul>
</ul>



#### Update Application
<ul>

To update an application in HAS, simply change one of the mutable fields in the Application resource (such as the application name or description) and apply the new changes. The controller will regenerate the application model accordingly. The controller will have webhooks to prevent you from changing any of the immutable fields (like gitops repo).

</ul>


#### Delete Application
<ul>

To delete an application in HAS, simply delete the Application resource corresponding to the application. If there are any services (Component) associated with the application, those resources, e.g. the application GitOps repo, will also be deleted by the controller. If any git webhooks were set up for the application, they will be deleted as well. The application repo containing the app model will not be deleted.

</ul>

### [Component CRD](hybrid-application-service-crds.md#component)

#### Create Component
<ul>

To add a component to a given application, create a Component resource, specifying a componentName, a src(git or image), and what application to add it to.

When the component is created, the HAS controller retrieves the component’s devfile from the specified source (a git repo, a container image, or an external URL). The Application resource for the component’s application also has its model updated to reference the component (via its status.devfile field). The controller also adds labels for the component name and application CR name to the resource.

</ul>

<ul>

##### Example
<ul>

Click on the following links to compare the contents of the Component CR before and after creation.

[Component Before Creation](https://github.com/yangcao77/has-kube-samples/blob/master/003-add-component-from-sample/input-hasComponent.yaml)

Upon successful creation, the CR `status.devfile` will be populated with the flattened devfile retrieved from the specified samples repository.

[Component After Creation](https://github.com/yangcao77/has-kube-samples/blob/master/003-add-component-from-sample/output-hasComponent.yaml#L125-L222)

Once a component has been created, the application devfile model will be updated to include the name of the newly created component and its corresponding git source sample repo.

[Updated Application After Component Creation](https://github.com/yangcao77/has-kube-samples/blob/master/003-add-component-from-sample/output-hasApplication.yaml#L83-L87)

</ul>
</ul>

#### Update Component
<ul>

To update a given component in HAS, find the component that you would like to update (each component has annotations and labels with its name, and corresponding app uuid). Then make changes to the mutable fields, as desired (such as component name) and apply the changes.

The HAS controller will update the component’s model, and make any necessary changes to the component’s reference in the application model.

</ul>

#### Delete Component
<ul>

To delete a given component in HAS, just delete its corresponding Component. The HAS controller will then remove the reference to the component from the Application model in the corresponding Application resource. Any component bindings connected to the component will be deleted as well. The component’s source repository will not be deleted.

</ul>

### [ComponentDetectionQuery CRD](hybrid-application-service-crds.md#componentdetectionquery)

#### Create ComponentDetectionQuery
<ul>

Traverses the git repository and detects the language and project type of the component. If a devfile or dockerfile is present, it considers the git repository as a single component repository, and gets the information from the devfile and dockerfile. Otherwise, the repository will be considered as a multi-component repository, and all one-level sub-directories will be scanned and analyzed. If no devfile is present in the sub-dir, the component will be analyzed to predict the language and project type, so that a specific devfile from the devfile registry can be used. A `Component` resource stub is returned for each detected component.

When a component detection query gets created, the `Processing` status condition is added to the resource. A follow-up status condition, `Completed` will be added when the query has finished (either successfully or unsuccessfully).

If the detection cannot figure out the language and project type, the return value will be empty, and it will be up to the user to either ignore that directory/component or to tell us what devfile is to be used.

</ul>

<ul>

##### Example
<ul>

Click on the following links to compare the contents of the ComponentDetectionQuery CR before and after creation.

[ComponentDetectionQuery Before Creation](https://github.com/yangcao77/has-kube-samples/blob/master/004-detect-service/input-serviceDetectionQuery.yaml)

After the detection request finishes, its status will be set to success/unsuccessful. If it was successful, the `status.componentDetected` field will be populated with the detected language, project type (and if necessary) matching devfile of each component

[ComponentDetectionQuery After Creation](https://github.com/yangcao77/has-kube-samples/blob/master/004-detect-service/output-serviceDetectionQuery.yaml#L100-L143)

</ul>


**Default Values**:
<ul>

The componentResourceStub for each component will have the Component CR stub. This stub will contain the values from either the devfile or certain defaults.

For example, if a devfile has cpuLimit and memoryLimit, these values will be returned with the componentResourceStub. However, if the devfile does not have cpuLimit or memoryLimit, default values of 500m and 1Gi will be used respectively.

targetPort will not have a default value, since it would be difficult to ascertain the port for different samples/frameworks. In this case, it would depend on an input from the user during creation of the component with the Component CR.

</ul>
</ul>


