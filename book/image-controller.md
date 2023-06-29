# Image Controller

## Overview

The Image Controller for AppStudio helps set up container image repositories
for AppStudio Components. It watches Components to take actions according to
the deletion event and the value set to specific annotations.

External services are able to interact with image controller via these two
annotations:

- `image.redhat.com/generate`: if set, image controller starts to set up image
  repository on Quay.io for a Component, or attempts to switch repository
  visibility if the repository exists already.

- `image.redhat.com/image`: information of created resources is set to this
  annotation as a JSON string. Error message will also be set to here if there
  is.

## Set up image repository

To request the controller to setup an image repository, annotate the Component
CR with `image.redhat.com/generate: '{"visibility": "public"}'` or
`image.redhat.com/generate: '{"visibility": "private"}'` depending on desired
repository visibility.

Here is an example that a component is annotated for creating a public image
repository:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  annotations:
    image.redhat.com/generate: '{"visibility": "public"}'
  name: billing
  namespace: image-controller-system
spec:
  application: city-transit
  componentName: billing
```

As a result, when the setup succeeds,

- A public image repository is created on Quay.io.
- A robot account is created and associated with the repository properly.
- A Kubernetes Secret is created alongside the Component CR, to which the
  robot account token is written out.
- Annotation `image.redhat.com/image` is set on Component CR with value:

  ```json
  {
    "image": "quay.io/redhat-user-workloads/image-controller-system/city-transit/billing",
    "visibility": "public",
    "secret":" secret-name"
  }
  ```

  the Component CR YAML looks like:

  ```yaml
  apiVersion: appstudio.redhat.com/v1alpha1
  kind: Component
  metadata:
    annotations:
      image.redhat.com/image: "{\"image\":\"quay.io/redhat-user-workloads/image-controller-system/city-transit/billing\",\"visibility\":\"public\",\"secret\":\"secret-name\"}"
    name: billing
    namespace: image-controller-system
  spec:
    application: city-transit
    componentName: billing
  ```

Note that, annotation `image.redhat.com/generate` is removed already.

## Cleanup on deletion of Component CR

Image controller deletes the image repository and robot account from Quay.io
when Component CR is requested to be deleted.

## Switch Visibility

The corresponding image repository can be set as public or private by setting
annotation `image.redhat.com/generate` on Component CR. Visibility value must
be `public` or `private`.

Here is an example that makes the repository private by setting `visibility` to
`private`.

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  annotations:
    image.redhat.com/generate: '{"visibility": "private"}'
    image.redhat.com/image: "{\"image\":\"quay.io/redhat-user-workloads/image-controller-system/city-transit/billing\",\"visibility\":\"public\",\"secret\":\"secret-name\"}"
  name: billing
  namespace: image-controller-system
spec:
  application: city-transit
  componentName: billing
```

As a result, repository becomes private on Quay.io and `visibility` changes to
`private` in annotation `image.redhat.com/image`:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  annotations:
    image.redhat.com/image: "{\"image\":\"quay.io/redhat-user-workloads/image-controller-system/city-transit/billing\",\"visibility\":\"private\",\"secret\":\"secret-name\"}"
  name: billing
  namespace: image-controller-system
spec:
  application: city-transit
  componentName: billing
```

## Error report

If something went wrong during the requested operation, annotation
`image.redhat.com/image` will include a field `Message` with the corresponding
error message.

