# Java Virtual Machine Build Service

## Overview

The Java Virtual Machine Build Service (JBS, or JVM Build Service) is a controller that will rebuild Java and other JVM Language based dependencies from source.

The end user documentation is located [here](https://redhat-appstudio.github.io/docs.appstudio.io/Documentation/main/how-to-guides/Secure-your-supply-chain/proc_java_dependencies/) and contains background information.

The Java ecosystem uses a binary distribution model, where binary jar files are downloaded from central repositories (such as Maven Central). This means that the only way to ensure an application is completely built from source is to rebuild all its component libraries from source in a trusted environment. Unfortunately due to the nature of the Java ecosystem this is not an easy process and would normally require a large amount of manual toil.

Although the Java binary distribution model is very convenient, it does mean that you will inevitably use untrusted dependencies with unknown provenance maintained by external communities. In general, you don't know who has uploaded these artifacts, the environment that was used to build them, or how that build environment might be compromised. Building from source in a secure environment means that you can be be completely sure as to where the code you are running has come from.

JBS automates this process as much as possible, making it much less time-consuming to create builds that are build from source in a controlled environment.

### Dependencies

JBS depends on Tekton, but is otherwise largely independent of the rest of Konflux. Given the right configuration it can be deployed outside of Konflux, which is mainly used for testing and development.

## Architecture

### Flow Overview

The JVM Build service can be enabled on a specific namespace by creating a [`JBSConfig`](#jbsconfig) object, with `enableRebuilds: true` specified. This will trigger the controller to create a deployment of the local Cache in the namespace. This cache has a number of purposes, but the primary one is to cache artifacts from Maven central to speed up Java builds.

Once it is enabled and the cache has started the JVM Build Service will watch for `PipelineRun` objects with the `JAVA_COMMUNITY_DEPENDENCIES` results. This will be present on end user builds that have dependencies from untrusted upstream sources.

When one of these `PipelineRun` objects is observed JBS will extract the dependency list, and attempt to rebuild all the listed JVM artifacts from source.

The first stage of this process is to create an [`ArtifactBuild`](#artifactbuild) object. This object represents a Maven `group:artifact:version` (GAV) coordinate of the library that needs to be built from source.

Once the `ArtifactBuild` object has been created JBS will then attempt to try and build it. This first step is to attempt to find the relevant source code.

Once the source code location has been discovered a [`DependencyBuild`](#dependencybuild) object is created. There are generally less `DependencyBuild` objects than there are `ArtifactBuild`, as multiple artifacts can come from the same build. The controller will then try and build the artifact, first it will run a build discovery pipeline, that attempts to determine possible ways of building the artifact. Once discovery is complete it uses this information to attempt to build the artifact in a trial and error manner.

The dependency discovery pipeline can check both configured shared repositories and the main repository
(for example a Quay.io repository) for pre-existing builds. If a prior build is found, the pipeline will shortcut
to avoid building the artifact and will instead refer to the found build artifacts instead.

If a build is successful the results are stored in a container image and the state is marked as complete, otherwise it is marked as failed and manual effort is required to fix the build.


### Components

JBS consists of the following components:

**Controller**

The controller is a Kubernetes controller written in go that orchestrates all aspects of the rebuild process. This will kick off all build related pipelines, and manage the state of the relevant Kubernetes objects.

**Cache**

The cache is a Quarkus Java application that caches artifacts from upstream repositories such as maven central. It also performs the following additional functions:

- Handles container image based dependencies that have been rebuilt
- Injects tracking metadata into class files to detect contaminated builds
- Looks up source and build information from the build recipe database

All dependency rebuilds are configured to only get their artifacts from the cache.

**Build Request Processor**

This is a multipurpose Quarkus CLI based app that performs quite a few different functions depending on the parameters it is invoked with. This is packaged up into an image, and then run in different parts of various pipelines by the operator.

In essence any custom logic that is needed in a pipeline goes in here, and then the operator will invoke it with the correct arguments. This is a single container image that can perform a whole host of different functions, based on the parameters that it is invoked with. It's functions include:

- Analysing a build and looking up its build information in the recipe database
- Checking for pre-existing builds
- Preprocessing a build to fix common problems, such as removing problematic plugins
- Verifying the results of a build match what is expected upstream
- Checking if a build has been contaminated by upstream class files
- Deploying the build to an image repository

**Recipe Database**

This is a git repository that contains information on where to find sources and how to build various projects. It is located at https://github.com/redhat-appstudio/jvm-build-data.

For full information on the format of this repository please see the documentation located inside the repository itself.

**Builder Images**

The builder images are maintained at the [builder images repository](https://github.com/redhat-appstudio/jvm-build-service-builder-images/).

**CLI**

This is a Quarkus application provided for end users to interact with the system.

## Resource Details

The JVM Build service provides the following CRDs. All CRDs are located in the [JVM Build Service repo](https://github.com/redhat-appstudio/jvm-build-service/tree/main/deploy/crds/base). They are generated from goang objects that reside [here](https://github.com/redhat-appstudio/jvm-build-service/tree/main/pkg/apis/jvmbuildservice/v1alpha1).

### `ArtifactBuild`

This represents a request to rebuild an artifact. Creating this object will kick off the JVM Build Service rebuild process. We should have one of these objects for every upstream GAV we want to rebuild.

These have the following states.

**ArtifactBuildNew**

Object has just been created.

**ArtifactBuildDiscovering**

The JVM Build Service is running a discovery pipeline to determine where the source code for this artifact is located.

**ArtifactBuildMissing**

We failed to find the source code location. The source code information must be added to the recipe database and the build retried.

**ArtifactBuildFailed**

The build failed.

**ArtifactBuildComplete**

The build was a success.

### `DependencyBuild`

This represents a repository + tag combination we want to build. These are created automatically by the JVM Build Service Operator after it has looked up how to build.

Once these have been created the operator first runs a 'discovery' pipeline, that attempts to figure out how to build the repo, which both examines the code base, and also pulls in build information from the Build Recipe Repository. The result of
this is a list of build recipes that the operator will attempt one after the other. This object has the following states:

**DependencyBuildStateNew**

The object has just been created.

**DependencyBuildStateAnalyzeBuild**

The operator is running a pipeline to attempt to discover how to build the repository.

**DependencyBuildStateBuilding**

A build pipeline is running.

**DependencyBuildStateComplete**

The build was a success.

**DependencyBuildStateFailed**

All attempts to build this repository have failed.

**DependencyBuildStateContaminated**

This state means that the build was a success, but community artifacts were shaded into the output of the build. The operator
will attempt to fix this automatically, by creating new `ArtifactBuild` objects for everything that was shaded into the output.
Once these have completed the build is automatically retried. A good example of this is the Netty build, which gets contaminated
by JCTools. If these artifact builds fail then the `DependencyBuild` will stay in this state indefinitely.

### `RebuiltArtifact`

This represents a GAV that has been built and deployed to the image repo. It is mainly for internal bookkeeping purposes.

### `JBSConfig`

This object is used to configure all aspects of the JVM Build Service. The creation of this object is what triggers the creation of the Cache deployment for the namespace,
and is required for any rebuilds to happen in a given namespace.

A minimal `JBSConfig` for rebuilding artifacts would be as follows:

```yaml
apiVersion: jvmbuildservice.io/v1alpha1
kind: JBSConfig
metadata:
  name: jvm-build-config
spec:
  enableRebuilds: "true"
```

In order to avoid multiple rebuilds of the same artifact, a user may configure a shared registry explicitly within the
`JBSConfig` custom resource or by using the provided CLI. A shared registry is one that may be shared by many users.

For example:

```yaml
apiVersion: jvmbuildservice.io/v1alpha1
kind: JBSConfig
metadata:
  name: jvm-build-config
spec:
  enableRebuilds: "true"
  registry:
      owner: an-owner
  sharedRegistries:
      - host: quay.io
        insecure: true
        owner: my-team-owner
        repository: test-jvm-namespace/jvm-build-service-artifacts
```

This assumes that another user has configured their registry to deploy builds to `my-team-owner`. For example:

```yaml
spec:
  registry:
    owner: my-team-owner
```

### `SystemConfig`

This is a singleton object that configures the JVM Build System. The main configuration it provides is the builder images to use.
