# Hybrid Application Service (HAS) Kubernetes CRDs

[Application]({{< relref "hybrid-application-service-crds.md#application" >}})

[Component]({{< relref "hybrid-application-service-crds.md#component" >}})

[ComponentDetectionQuery]({{< relref "hybrid-application-service-crds.md#componentdetectionquery" >}})

## Application
The Application resource defines an Application in Konflux. The fields in the resource are relatively bare, just the name of the resource (a UUID), an annotation with the application’s name, a description for the Application, and its git repository.

When the resource is created, the `status.devfile` field is populated with the Application model for the app (a Devfile). When the Application resource is updated, or Components are added to the Application, the Application model in this resource is updated accordingly.


### Required CR fields

| Name             | Type   | Description                                       | Example               | Immutable |
|------------------|--------|---------------------------------------------------|-----------------------|-----------|
| metadata.name    | String | A unique identifier for the Application resource  | john-petclinic-323433 | Yes       |
| spec.displayName | String | The display name of the Application to be created | pet-clinic, DemoApp   | No        |


### Optional Fields

| Name                            | Type   | Description                                                                                                                                                                                                    | Example                                              | Immutable |
|---------------------------------|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|-----------|
| spec.description                | String | A description of the Application                                                                                                                                                                               | “application definition for petclinic-app”           | No        |
| spec.appModelRepository.url     | URL    | The URL of the app model repository (app model, etc) that will be used for the Application. If not specified, it will use the generated GitOps repo under the org https://github.com/redhat-axppstudio-appdata | https://github.com/organization/application-repo.git | Yes       |
| spec.appModelRepository.branch  | String | The branch in the app model repository to use                                                                                                                                                                  | main                                                 | Yes       |
| spec.appModelRepository.context | String | The path within the app model repository to use                                                                                                                                                                | test/folder                                          | Yes       |
| spec.gitOpsRepository.url       | URL    | The URL of the GitOps repository for the Application. If not specified, it will use the generated  GitOps repo under the org https://github.com/redhat-appstudio-appdata                                       | https://github.com/organization/gitops-repo.git      | Yes       |
| spec.gitOpsRepository.branch    | String | The branch in the gitops repository to use                                                                                                                                                                     | main                                                 | Yes       |
| spec.gitOpsRepository.context   | String | The path within the gitops repository to use                                                                                                                                                                   | test/folder                                          | Yes       |


### Status Fields

| Name       | Type               | Description                                 | Example                                                                                                                                                                                                                                                                                                                                                                                                                                     |
|------------|--------------------|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| conditions | []metav1.Condition | A list of description of the CRD conditions | <pre>Conditions:<br/>  Last Transition Time: 2021-12-16T19:04:16Z <br/>  Message: Application has been successfully created <br/>  Reason:OK<br/>  Status:True <br/>  Type:Created </pre>                                                                                                                                                                                                                                                   |
| devfile    | String             | Application model represented by Devfile v2 | <pre>schemaVersion: 2.1.0 <br/>metadata:<br/>attributes:<br/>appModelRepository.url: https://github.com/johnmcollier/petclinic-app <br/>gitOpsRepository.url: https://githubcom/johnmcollier/petclinic-gitops <br/>description: Application definition for petclinic-app <br/>name: petclinic <br/>projects: <br/>- name: backend <br/>  git: <br/>  remotes: <br/>  origin: https://github.com/devfile-samples/devfile-sample-java-springboot-basic |


### Status Conditions

| Type    | Status | Reason | Message    |
|---------|--------|--------|------------|
| Created | True   | OK     | `<string>` |
| Created | False  | Error  | `<string>` |
| Updated | True   | OK     | `<string>` |
| Updated | False  | Error  | `<string>` |


## Component

The Component resource defines an application’s Component in Konflux. The fields in the resource contain the name of the resource, the component’s name, the Application it is linked to (referenced via a label), and the source for the Component (a git repository, container image, or external Devfile URL).

When the Component is created, the HAS controller retrieves the component’s Devfile from the specified source (a git repo, a container image, or an external URL). The Application resource for the Component’s Application also has its model updated to reference the Component (via its `status.devfile` field). The controller also adds labels for the Component name and Application CR name to the resource.

### Required CR Fields
| Name                | Type   | Description                                                                                                                                          | Example                                                             | Immutable |
|---------------------|--------|------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|-----------|
| metadata.name       | String | The unique identifier of the Component resource                                                                                                      | petclinic-app-backend-45345                                         | Yes       |
| spec.componentName  | String | The name of Component to be added to the Application. The componentName should follow DNS-1123 rule                                                  | backend                                                             | Yes       |
| spec.application    | String | The Application to add the Component to.                                                                                                             | john-petclinic-323433                                               | Yes       |
| spec.source.git.url | String | (If importing from git) The repository to create the Component from                                                                                  | https://github.com/devfile-samples/devfile-sample-code-with-quarkus | Yes       |
| spec.containerImage | String | (If importing from image) The container image to create the Component from. (optional if the container image is created during the Component  build) | quay.io/jcollier/test-go:latest                                     | Yes       |


### Optional Fields
| Name                              | Type                | Description                                                                                    | Example                                     | Immutable |
|-----------------------------------|---------------------|------------------------------------------------------------------------------------------------|---------------------------------------------|-----------|
| spec.secret                       | String              | Secret containing a Personal Access Token to clone a sample (if using private repository)      | github-secret                               | Yes       |
| spec.source.git.context           | String              | A relative path inside the git repo containing the Component                                   | frontend/, src/backend/                     | Yes       |
| spec.source.git.devfileURL        | String              | If specified, the Devfile at the URL will be used for the Component.                           | https://registry.devfile.io/devfiles/nodejs | Yes       |
| spec.source.git.dockerfileURL     | String              | If specified, the Dockerfile at the URL will be used for the Component                         | https://github.com/my-repo/Dockerfile       | Yes       |
| spec.source.git.revision          | String              | Specifies a branch/tag/commit id                                                               | main                                        | Yes       |
| spec.resources.limits             | corev1.ResourceList | CPU and/or Memory resource limits                                                              | Memory: 1Gi,CPU: 1M                         | No        |
| spec.resources.requests           | corev1.ResourceList | CPU and/or memory requests                                                                     | Memory: 128Mi, CPU: 0.5M                    | No        |
| spec.replicas                     | Int                 | The number of replicas to deploy the Component with                                            | 3                                           | No        |
| spec.route                        | String              | The route to expose the Component with                                                         | some-url.somedomain.com                     | No        |
| spec.targetPort                   | Int                 | The port to expose the Component over                                                          | 8080                                        | No        |
| spec.env                          | []corev1.EnvVar     | An array of environment variables to add to the Component (ValueFrom not supported atm)        | key: SOMEENV value: test                    | No        |
| spec.containerImage               | String              | The container image that is created during the Component  build                                | quay.io/redhat-appstudio/appa-12345:latest  | No        |
| spec.skipGitOpsResourceGeneration | bool                | Whether or not to skip the generation of gitops resources for the Component. Defaults to false | true                                        | No        |

### Status Fields

| Name                             | Type               | Description                                                             | Example                                                                                                                                                                             |
|----------------------------------|--------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| conditions                       | []metav1.Condition | A list of description of the CRD conditions                             | <pre>Conditions: <br/>  Last Transition Time: 2021-12-16T19:04:38Z <br/>  Message: Component has been successfully created <br/>  Reason: OK <br/>  Status:true <br/>  Type:Created |
| devfile                          | string             | Application model represented by devfile v2                             | (Devfile from the git sample, for example https://github.com/devfile-samples/devfile-sample-java-springboot-basic/blob/main/devfile.yaml)                                           |
| containerImage                   | string             | Stores the associated built container image for the Component           | quay.io/redhat-appstudio/appa-12345:latest                                                                                                                                          |
| webhook                          | string             | Webhook URL generated by the tekton builds                              | component-sample-mycluister.dev.rhcloud.com                                                                                                                                         |
| gitops.repositoryURL             | string             | The GitOps repository URL for the Component                             | https://github.com/redhat-appstudio-appdata/stephanie-app2-yangcao-press-conclude                                                                                                   |
| gitops.branch                    | string             | The branch used for the GitOps repository                               | main                                                                                                                                                                                |
| gitops.context                   | string             | The path within the GitOps repository used for the GitOps               | test/folder                                                                                                                                                                         |
| gitops.commitID                  | string             | The most recent commit ID in the GitOps repository for this Component   | 2b173d4ab298298ec26128b0248a356564fb8f22                                                                                                                                            |
| gitops.resourceGenerationSkipped | bool               | Whether or not GitOps resource generation was skipped for the Component | false                                                                                                                                                                               |

### Status Conditions

| Type                     | Status | Reason        | Message    |
|--------------------------|--------|---------------|------------|
| Created                  | True   | OK            | `<string>` |
| Created                  | False  | Error         | `<string>` |
| Updated                  | True   | OK            | `<string>` |
| GitOpsResourcesGenerated | True   | OK            | `<string>` |
| GitOpsResourcesGenerated | False  | GenerateError | `<string>` |


## ComponentDetectionQuery

### Required Fields
| Name               | Type   | Description                                                            | Example                                              |
|--------------------|--------|------------------------------------------------------------------------|------------------------------------------------------|
| metadata.name      | String | The name of the componentDetection request resource                    | detect-git-test-repo                                 |
| metadata.namespace | String | The namespace to deploy the resource in. Defaults to current namespace | testuser-dev                                         |
| spec.git.url       | String | The URL of the Git repository that will be analyzed for Components     | https://github.com/organization/application-repo.git |


### Optional Fields

| Name                   | Type   | Description                                                                                                                                              | Example                                     |
|------------------------|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| spec.secret            | String | An optional git secret used to access the repository                                                                                                     | github-token                                |
| spec.git.devfileURL    | String | If specified, the devfile at the URL will be used for the Component. <br/><br/>If devfileURL and isMulticomponent mentioned, it will return an err       | https://registry.devfile.io/devfiles/nodejs |
| spec.git.dockerfileURL | String | If specified, the Dockerfile at the URL will be used for the Component. <br/><br/>If dockerfileURL and isMulticomponent mentioned, it will return an err | https://github.com/my-repo/Dockerfile       |
| spec.git.context       | String | A relative path inside the git repo containing the Component.Being returned when there are multiple-component defined under first level sub-dir.         | frontend/, backend/                         |


### Status Fields

| Name              | Type                                     | Description                                                                                                                                 | Example                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|-------------------|------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| conditions        | []metav1.Condition                       | A list of description of the CRD conditions                                                                                                 | <pre>Conditions:<br/>  Last Transition Time:  2022-01-13T19:08:04Z <br/>  Message: ComponentDetectionQuery has been successfully created <br/>  Reason:  OK <br/>  Status:  True <br/>  Type:    Created                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| componentDetected | map[string]ComponentDetectionDescription | Contains a map of the component detected and their description <br/><br/>Check below for the detailed info on ComponentDetectionDescription | <pre>Component Detected: <br/>  Java - Springboot:<br/>    Component Stub: <br/>      Application: <br/>      Build: <br/>        Container Image: <br/>      Component Name:     java-springboot <br/>      Env: <br/>        Name:    FOO <br/>        Value:   foo1 <br/>        Name:    BAR <br/>        Value:   bar1 <br/>      Replicas:  1 <br/>      Resources: <br/>        Limits: <br/>          Cpu:                  2 <br/>          Ephemeral - Storage:  500Mi <br/>          Memory:               500Mi <br/>          Storage:              400Mi <br/>        Requests: <br/>          Cpu:                  700m <br/>          Ephemeral - Storage:  400Mi <br/>          Memory:               400Mi <br/>          Storage:              200Mi <br/>        Route:                    route111 <br/>        Source: <br/>          Git: <br/>            Context:            devfile-sample-java-springboot-basic <br/>            URL:      https://github.com/maysunfaisal/multi-components <br/>        Target Port:  1111 <br/>      Devfile Found:  true <br/>      Language:       java <br/>      Project Type:   springboot |


### Status Conditions

| Type       | Status | Reason  | Message    |
|------------|--------|---------|------------|
| Processing | True   | Success | `<string>` |
| Completed  | True   | OK      | `<string>` |
| Completed  | False  | Error   | `<string>` |


### ComponentDetectionDescription Fields

| Name              | Type                                     | Description                                                                                        | Example                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|-------------------|------------------------------------------|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|DevfileFound|bool| True/False if a Devfile is found for the Component in question                                     | true/false                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|language|string| specifies the language of the Component detected                                                   | Java                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
|projectType|string| specifies the type of project for the Component detected                                           | Spring                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|componentStub|ComponentSpec| Stub of the Component CR detected with all the info gathered from the Devfile or service detection | <pre>Component Stub: <br/>Application:<br/>Container Image: <br/>Component Name:     java-springboot <br/>Env: <br/>  Name:    FOO <br/>  Value:   foo1 <br/>  Name:    BAR <br/>  Value:   bar1 <br/>Replicas:  1 <br/>Resources: <br/>  Limits: <br/>  Cpu:                  2 <br/>  Memory:               500Mi <br/>  Storage:              400Mi <br/>Requests: <br/>  Cpu:                  700m <br/>Route:                    route111 <br/>Source: <br/>  Git: <br/>  URL:      https://github.com/maysunfaisal/multi-components <br/>Target Port:  1111 <br/> |
