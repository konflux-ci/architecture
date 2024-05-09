---
date: 2024-02-01T00:00:00Z
title: Project Controller for Multi-version support
number: 34
---
# 0034 Project Controller for Multi-version support

## Status

Proposed.

## Context

Konflux began its way as "App Studio", which was mainly designed to facilitate
the development of online managed services. In order to do that a few major
abstractions such as "Applications" and "Components" were introduced to help
managing the underlying Tekton Pipeline and other lower level objects.

With Konflux shifting focus to serving enterprise development teams requests
had been made to enable using other abstraction metaphors such as "Product" and
"Version" for managing development, build, test and release workflows. As one
user put it:

> As an architect, I need to be able to see all my apps versions in
> one place, so that they are easily accessible by everyone on the
> team and organized in a way that matches the way our team talks
> about them, making my workflow for each app more streamlined.

Some Konflux users have already attempted managing large multi-versioned
products in Konflux. The pattern that emerged for doing so is as follows:

* Create a separate Konflux Application for each product version
* Use branches to track different source code versions within Git repositories
* Use a separate Konflux Components for each buildable piece of code
  (E.g. Dockerfile) in each branch in each repo that is included in a particular
  application version.
* To manage large amounts of components, some users have used multiple
  application objects for a single product version.

As one can expect, creating and managing so many Konflux objects is currently
rather cumbersome. There are a few redundant steps that need to be taken. For
example, access credentials for a Git repository need to be filled-in every time
a component referring to that repository is created, even if other components
referring that repository already exist in the user's workspace.

The intention for the solution proposed in this document is to follow the
pattern described above as far as the Konflux "Application" and "Component"
objects go and provide a higher-level layer for the streamlined management of
large amounts of such objects.

An alternative approach to managing the challenges we have described above is to
modify the way Application and Component object function so that for example:

* A component may encompass multiple versions of similar code across different
  Git branches
* An application may include several sub groups of components so that each could
  be regarded to be defining a different version

We see several benefits to the "high level layer" approach we propose over the
alternative:

* The way Components and Applications work is currently tightly coupled to the
  way the various Konflux services work. Changing it would require changes
  across multiple services and may introduce operational risks.
* There are proposals being discussed for decoupling the various Konflux
  services and possibly deprecating the Component and Application objects.
  Having a separate high-level layer would allow for adjusting it for using
  different underlying objects while continued emphasis on using Application
  and Component object would necessitate continued maintenance of them.

## Decision

### Facilitating product and version based navigation in the UI

We will define two new custom resources:

**Project** resources will define a large project that can have multiple
parallel development streams that may be each released as a different product
version.

**ProjectDevelopmentStream** resources will define a stream of development
within a *Project*. It will be linked to an owning project via a [Kubernetes
owner reference][oref].

*Application*, *Component*, and any other Konflux object that needs to be
created to facilitate the development of a particular project development stream
will be linked to a *ProjectDevelopmentStream* object via an owner reference.

**Note:** The choice was made to use the terms "Project" and "Project
Development Stream" as opposed to "Product" and "Version" because those can be
applied more broadly also to upstream community projects as opposed to
marketable products. Those terms also more accurately describe the environment
in which software development happens. [See here][pvsp] for a more detailed
discussion of these terms.

[oref]: https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/
[pvsp]: https://opensource.com/article/19/11/product-vs-project

### Streamlining version creation from the API/CLI.

We will define the **ProjectDevelopmentStreamTemplate** custom resource. The
*spec* for such a resource will include:

* A **project** element referring to an existing *Project* resource.
* A **variables** element that includes a list of variable names and optional
  default values. The default values of variables my be defined in terms of
  other, previously defined, variables using the Go template syntax.
* A **resources** element that includes a list of resource definitions so that
  each definition may reference variables by using the Go template syntax.

Here is an example for what a *ProjectDevelopmentStreamTemplate* resource may
look like:

```
apiVersion: pvc.konflux.dev/v1alpha1
kind: ProjectDevelopmentStreamTemplate
metadata:
  name: template1
  ...
spec:
  project: project1
  variables:
  - name: foo
  - name: bar
    defaultValue: "baz{{.foo}}"
  resources:
  - apiVersion: appstudio.redhat.com/v1alpha1
    kind: Application
    metadata:
      name: "{{.foo}}-app1"
    spec:
      displayName: "{{.foo}}-app1"
  - apiVersion: appstudio.redhat.com/v1alpha1
    kind: Component
    metadata:
      name: "{{.foo}}-comp1"
    spec:
      application: "{{.foo}}-app1"
      componentName: "{{.foo}}-comp1"
      source:
        git:
          context: ./
          dockerfileUrl: Dockerfile
          revision: "{{.bar}}"
          uri: ...
```

The *spec* section for the *ProjectDevelopmentStream* may include a **template**
section that includes a **name** field for referring to a
*ProjectDevelopmentStreamTemplate* resource and a **values** section to provide
values for the template variables. When this happens, the resources described by
the template get created.

Here is an example for what a *ProjectDevelopmentStream* resource with a
template may look like:

```
apiVersion: pcv.konflux.dev/v1alpha1
kind: ProjectDevelopmentStream
metadata:
  ...
spec:
  template:
    name: template1
    values:
      - name: foo
        value: some-value-here
```

The *values* section must provide values for all template variables without
default values defined, it may also include values for variable that do have
default values defined.

The example above will cause the creation of the "some-value-here-app1"
*Application* resource and the "some-value-here-comp1" *Component* resource.

### Streamlining version cloning from the UI

We will support a process for cloning a *ProjectDevelopmentStream* resource and
all the resources included in it. While the process could be used from the API,
it is primarily meant to be used from the Konflux UI.

*ProjectDevelopmentStream* resource cloning will be done by way of generating a
*ProjectDevelopmentStreamTemplate* resource from an existing
*ProjectDevelopmentStream* resource. This will be done by adding a `toTemplate`
property to the *spec* section of a *ProjectDevelopmentStream* resource naming
the template to be created.

The template would be created with the following characteristics:

* The following procedure will be used to determine the version number that the
  cloned *ProjectDevelopmentStream* defines:

    * If the *ProjectDevelopmentStream* resource has a *pvc.konflux.dev/version*
      annotation, its value serves as the version value.
    * Otherwise, the name of the *ProjectDevelopmentStream* is split by using
      dash ("-") characters and the last element in the split list is used as
      the version value. For example, for a resource names `foo-bar-v1` the
      version value would be `v1`.

* The new *ProjectDevelopmentStreamTemplate* will include a *version* variable
  with no default value.

* All *Application* and *Component* resources that are associated with the
  cloned *ProjectDevelopmentStream* will be copied into the *resources* section
  of the *ProjectDevelopmentStreamTemplate* resource, while *status* and other
  transient properties would be stripped.

* Resource names within the template will be set as following:

    * If the name on the cloned resource ends with the
      *ProjectDevelopmentStream* resource's version value as determined above,
      the value is stripped and the "`{{.version}}`" template string is placed
      instead.
    * Otherwise the "`{{.version}}`" template string is appended to the name.

* The template will include variables for customizing *revision* (branch),
  *dockerfileUrl* and *context* values for all included *Component* resources.
  The default values for the variables will be the existing values from the
  cloned objects. For *revision* properties the default values will be
  determined using the *version* variable in a similar manner to the way
  resource names are determined.

The generated template ends up being able to generate a
*ProjectDevelopmentStream* that is very similar to the one its being generated
from but with many variables that would allow customizing many aspects such as
Git branches being used.

It is intended that a UI screen could be displayed based on the generated
template. It is likely that such screen would need to group variables by the
resource they customize. Variable names will be picked to allow doing so. In
addition, the screen may need to display human friendly descriptions for the
variables or refer to the original resources that the created resources are
cloned from. The "description" property will be added to variables for the
former while a "pvc.konflux.dev/cloned-from" annotation on the template resource
sections will allow for the latter.

The process for cloning a *ProjectDevelopmentStream* from the UI will be as
follows:

1. Let the user select the *ProjectDevelopmentStream* resource to be cloned, set
   the `toTemplate` property on it.
2. Wait for the *ProjectDevelopmentStreamTemplate* resource to be created
3. Remove the `toTemplate` property to prevent further updates to the template
   resource by the controller.
4. Display a screen allowing the user to select a name for the new
   *ProjectDevelopmentStream* resource and values for all the template
   variables. When default values  exist, the screen should display then and let
   the user keep them.
5. Once the user confirms the screen, create a *ProjectDevelopmentStream*
   resource with a 'template' property referring to the template and values for
   the variables as selected by the user.
6. Once all the child resources specified by the template are created (The state
   field on the *ProjectDevelopmentStream* resource should indicate that) delete
   the template.

### Example

Following is an example of a *Project* resource followed by a
*ProjectDevelopmentStream* resource associated with it and *Application* and
*Component* resources nested within it.

```
---
apiVersion: pvc.konflux.dev/v1alpha1
kind: Project
metadata:
  name: my-cool-project
---
apiVersion: pvc.konflux.dev/v1alpha1
kind: ProjectDevelopmentStream
metadata:
  name: my-cool-project-main
  ownerReference:
    apiVersion: pvc.konflux.dev/v1alpha1
    kind: Project
    name: my-cool-project
spec:
  project: my-cool-project
  toTemplate: my-cool-project-stream-template
---
apiVersion: appstudio.redhat.com/v1alpha1
kind: Application
metadata:
  name: "cool-app-main"
  ownerReference:
    apiVersion: pvc.konflux.dev/v1alpha1
    kind: ProjectDevelopmentStream
    name: my-cool-project-main
spec:
  displayName: "Cool App main"
---
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  name: "cool-comp1-main"
  ownerReference:
    apiVersion: appstudio.redhat.com/v1alpha1
    kind: Application
    name: "cool-app-main"
spec:
  application: "cool-app-main"
  componentName: "cool-comp1-main"
  source:
    git:
      context: ./
      dockerfileUrl: Dockerfile
      revision: main
      uri: git@github.com:example/comp1.git
---
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  name: "cool-comp2-main"
  ownerReference:
    apiVersion: appstudio.redhat.com/v1alpha1
    kind: Application
    name: "cool-app-main"
spec:
  application: "cool-app-main"
  componentName: "cool-comp2-main"
  source:
    git:
      context: ./
      dockerfileUrl: Dockerfile
      revision: fixed-rev
      uri: git@github.com:example/comp2.git
```

Since the *ProjectDevelopmentStream* resource has a *toTemplate* property,
following is the *ProjectDevelopmentStreamTemplate* that would be generated
from it (Some extra whitespace was added to the YAML for readability):

```
apiVersion: pvc.konflux.dev/v1alpha1
kind: ProjectDevelopmentStreamTemplate
metadata:
  name: my-cool-project-stream-template
  ownerReference:
    apiVersion: pvc.konflux.dev/v1alpha1
    kind: Project
    name: my-cool-project
spec:
  project: my-cool-project
  variables:
  - name: version
    description: A version number for the new development stream

  - name: cool-comp1-context
    defaultValue: ./
    description: Context directory for cool-comp1 component
  - name: cool-comp1-dockerfileUrl
    defaultValue: Dockerfile
    description: Dockerfile location for cool-comp1 component
  - name: cool-comp1-revision
    defaultValue: {version}
    description: Git revision for cool-comp1 component

  - name: cool-comp2-context
    defaultValue: ./
    description: Context directory for cool-comp2 component
  - name: cool-comp2-dockerfileUrl
    defaultValue: Dockerfile
    description: Dockerfile location for cool-comp2 component
  - name: cool-comp2-revision
    defaultValue: fixed-rev
    description: Git revision for cool-comp2 component

  resources:
  - apiVersion: appstudio.redhat.com/v1alpha1
    kind: Application
    metadata:
      name: "cool-app-{{.version}}"
      annotations:
        pvc.konflux.dev/cloned-from: cool-app1-main
    spec:
      displayName: "Cool App {{.version}}"

  - apiVersion: appstudio.redhat.com/v1alpha1
    kind: Component
    metadata:
      name: "cool-comp1-{{.version}}"
      annotations:
        pvc.konflux.dev/cloned-from: cool-comp1-main
    spec:
      application: "cool-app-{{.version}}"
      componentName: "cool-comp1-{{.version}}"
      source:
        git:
          context: "{{.cool-comp1-context}}"
          dockerfileUrl: "{{.cool-comp1-dockerfileUrl}}"
          revision: "{{.cool-comp1-revision}}"
          uri: git@github.com:example/comp1.git

  - apiVersion: appstudio.redhat.com/v1alpha1
    kind: Component
    metadata:
      name: "cool-comp2-{{.version}}"
      annotations:
        pvc.konflux.dev/cloned-from: cool-comp2-main
    spec:
      application: "cool-app-{{.version}}"
      componentName: "cool-comp2-{{.version}}"
      source:
        git:
          context: "{{.cool-comp2-context}}"
          dockerfileUrl: "{{.cool-comp2-dockerfileUrl}}"
          revision: "{{.cool-comp2-revision}}"
          uri: git@github.com:example/comp2.git
```

Following is a new *ProjectDevelopmentStream* resource making use of the
template above:

```
apiVersion: pvc.konflux.dev/v1alpha1
kind: ProjectDevelopmentStream
metadata:
  name: my-cool-project-main
  ownerReference:
    apiVersion: pvc.konflux.dev/v1alpha1
    kind: Project
    name: my-cool-project
spec:
  project: my-cool-project
  template:
    name: my-cool-project-stream-template
    values:
    - name: version
      value: v1.0.0
    - name: cool-comp1-dockerfileUrl
      value: Dockerfile-rhel10
```

Since the *ProjectDevelopmentStream* resource is referencing a template, here
are the resources that would get created as a result:

```
---
apiVersion: appstudio.redhat.com/v1alpha1
kind: Application
metadata:
  name: "cool-app-v1.0.0"
  ownerReference:
    apiVersion: pvc.konflux.dev/v1alpha1
    kind: ProjectDevelopmentStream
    name: my-cool-project-v1.0.0
  annotations:
    pvc.konflux.dev/cloned-from: cool-app1-main
spec:
  displayName: "Cool App v1.0.0"
---
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  name: "cool-comp1-v1.0.0"
  ownerReference:
    apiVersion: appstudio.redhat.com/v1alpha1
    kind: Application
    name: "cool-app-v1.0.0"
  annotations:
    pvc.konflux.dev/cloned-from: cool-comp1-main
spec:
  application: "cool-app-v1.0.0"
  componentName: "cool-comp1-v1.0.0"
  source:
    git:
      context: ./
      dockerfileUrl: Dockerfile-rhel10
      revision: v1.0.0
      uri: git@github.com:example/comp1.git
---
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  name: "cool-comp2-v1.0.0"
  ownerReference:
    apiVersion: appstudio.redhat.com/v1alpha1
    kind: Application
    name: "cool-app-v1.0.0"
  annotations:
    pvc.konflux.dev/cloned-from: cool-comp2-main
spec:
  application: "cool-app-v1.0.0"
  componentName: "cool-comp2-v1.0.0"
  source:
    git:
      context: ./
      dockerfileUrl: Dockerfile
      revision: fixed-rev
      uri: git@github.com:example/comp2.git
```

## Consequences

With a dedicated controller managing *Project* and *ProjectDevelopmentStream*
resources, it becomes easier for users to manage multiple parallel development
streams in Konflux.

With UI support, using those concepts to navigate data in Konflux also becomes
possible.

Without UI support, this solution is still usable via API, CLI or GitOps. But
obviously data organization and visualization capabilities would not be in
place.

Using this functionality can result in the creation if large amounts of
*Component* and *Application* resources. Navigating a UI based on those can thus
become a bit cumbersome. This indicates the significance of having a project and
development stream based UI.

This solution is planned to be a layer on top of existing elements, to be
optional to use, and to co-exist with using the system as it is used today. This
also means that if we decide at a later time that this was not a sound technical
direction, we can drop the whole thing without extra cost or risk to existing
system elements.
