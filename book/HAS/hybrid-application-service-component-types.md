# Hybrid Application Service (HAS) Component Types

HAS supports a variety of user repositories for Components. User repositories can contain just a single component, or it may contain multiple components.

## Supported Runtimes

The following runtimes are supported by AppStudio:
- NodeJS
- Springboot
- Quarkus
- Python
- Go

Repositories with components that are not one of the supported runtime types, can still be imported into AppStudio, if the following conditions are met:
1) The Component has a Dockerfile present
2) The Dockerfile can be detected
3) **If** a Devfile is present, the Devfile contains references for valid Kubernetes and Dockerfile components. See [below](#devfile-requirements) for specific Devfile requirements

These Components will be listed as having a “Dockerfile” runtime.


## Detecting Components

Before a repository is added to an Application in AppStudio, if no Devfiles or Dockerfiles were specified for the Component resource, HAS will use alizer to attempt to detect the components that exist within the repository. Each component that corresponds to a supported runtime type (or Dockerfile type), will be detected.

If a runtime exists at the top level of the repository, HAS will treat the repository as a single component, and will not attempt to detect components below that level.

## Runtime-Specific Requirements

Some runtime types may have specific requirements in order to be detected by HAS:

Quarkus
- If a .dockerignore file is present, make sure that a wildcard, *, entry is not present, as AppStudio builds the application source as part of the Container build

Python
- Pip is used to manage dependencies for AppStudio Python projects. Make sure that your project has a requirements.txt at the root

NodeJS
- HAS expects NodeJS based components to have a package.json at the component's base folder

## Devfile Requirements

As mentioned before, if a Devfile is present in a Component, it must be valid in order to be detected:

1) The Devfile must contain an "image component" referencing the Dockerfile that will build the application. For example:
   ```yaml
    components:
    - name: image-build
      image:
        imageName: java-quarkus-image:latest
        dockerfile:
        uri: src/main/docker/Dockerfile.jvm.staged
        buildContext: .
        rootRequired: false
   ```

2) The Devfile must contain a "Kubernetes component" referencing the deployment artifacts for your component:
   ```yaml
    components:
        - name: kubernetes-deploy
          attributes:
            deployment/replicas: 1
            deployment/cpuRequest: 10m
            deployment/memoryRequest: 10Mi
            deployment/container-port: 8081
          kubernetes:
            uri: deploy.yaml
            endpoints:
            - name: http-8081
              targetPort: 8081
              path: /
    ```
An example of a valid devfile can be found [here](https://github.com/devfile-samples/devfile-sample-go-basic/blob/main/devfile.yaml)
