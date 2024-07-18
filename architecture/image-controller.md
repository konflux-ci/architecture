# Image Controller

# Overview
Image controller sets up and manages container image repositories for an application's components. This enables greater component isolation within Konflux where each component has its own image repository and secret for pushing images built via Konflux.

The image controller can perform three actions on image repositories by working together with [Component](https://konflux-ci.dev/architecture/ref/application-environment-api.html#component)-specific ImageRepository custom resource.

- **Setup image repository**: Image controller creates an image repository for the Component CR in a remote image registry as well as a robot account which is specific to that repository for image push. A Kubernetes Secret object is also created with that robot account token in order to make it available for build PipelineRun.

- **Modify visibility**: Image controller is able to switch an image repository's visibility between public and private.

- **Cleanup**: When a Component CR is requested to be deleted, image controller will remove component's image repository and robot account from the remote registry. The Kubernetes Secret will be removed along with the Component CR eventually due to the ownership established between them.

# Dependencies

Image controller does not depend on other Konflux services, but a remote image registry. Konflux services are able to use the resources prepared by image controller, e.g. Build Service makes the Secret available to every build PipelineRun of a component for image push.

# Interface

## ImageRepository CR

The ImageRepository CR is the interface to interact with image controller to create and manage image repositories in a registry.

To create an image repository for a Component, apply this YAML code:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: ImageRepository
metadata:
    name: imagerepository-for-component-sample
    namespace: test-ns
    labels:
        appstudio.redhat.com/component: my-component
        appstudio.redhat.com/application: my-app
```

By default, a public image repository is created, and two robot accounts and corresponding Kubernetes Secret objects are created for pull and push individually. All these artifacts information are recorded in the `.status` field.

To change the image repository visibility, set `public` or `private` to `.spec.image.visibility`.

To regenerate pull and push token, set `true` to `.spec.credentials.regenerate-token`

To verify if secrets are linked to the ServiceAccount correctly and have a fix if necessary, set `true` to `.spec.credentials.verify-linking`.

`.status` field includes various information about an image repository:

- `.status.credentials` includes pull and push Secrets names.
- `.status.image` includes the repository URL and current visiblity.
- `.status.state` shows whether image controller responded last operation request successfully or not.

For more detailed information of the functionalities, please refer to konflux-ci/image-controller [project document](https://github.com/konflux-ci/image-controller/?tab=readme-ov-file#readme).

## Legacy interaction via Component annotations

Image controller uses annotations to interact with external services.

- `image.redhat.com/generate`: An external service is able to request an image repository for an application component by setting this annotation on the corresponding Component CR. For initial request, the value should include field `visibility` to indicate the visibility of the created image repository in the remote registry, and it can be set again subsequently to change the visibility on demand. Note that, this annotation will be removed once requested operation finishes.

  Here is an example that requests a private image repository:

  ```yaml
  image.redhat.com/generate: '{"visibility": "private"}'
  ```

- `image.redhat.com/image`: image controller provides information of prepared resources to external services via this annotation, which includes the image repository URL, the visibility of that repository, and a secret name pointing to the created Kubernetes Secret.

  If something went wrong during the requested operation, this annotation will include a field `Message` with a corresponding error message.

  Here is an example that shows a public image repository is ready on Quay.io and a Secret named `secret-name` contains a robot account token and is available for image push.

  ```yaml
  image.redhat.com/image: "{\"image\":\"quay.io/redhat-user-workloads/image-controller-system/city-transit/billing\",\"visibility\":\"public\",\"secret\":\"secret-name\"}"
  ```
