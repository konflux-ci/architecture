# Image Controller

# Overview
Image controller sets up and manages container image repositories for an application's components. This enables greater component isolation within Konflux where each component has its own image repository and secret for pushing images built via Konflux.

The image controller can perform three actions on image repositories by watching for either specific annotation changes or deletion events of a [Component CR]({{< relref "../ref/application-environment-api.md#component" >}}):

- **Setup image repository**: Image controller creates an image repository for the Component CR in a remote image registry as well as a robot account which is specific to that repository for image push. A Kubernetes Secret object is also created with that robot account token in order to make it available for build PipelineRun.

- **Modify visibility**: Image controller is able to switch an image repository's visibility between public and private.

- **Cleanup**: When a Component CR is requested to be deleted, image controller will remove component's image repository and robot account from the remote registry. The Kubernetes Secret will be removed along with the Component CR eventually due to the ownership established between them.

# Dependencies
Image controller does not depend on other Konflux services, but a remote image registry. Konflux services are able to use the resources prepared by image controller, e.g. Build Service makes the Secret available to every build PipelineRun of a component for image push.

# Interface
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
