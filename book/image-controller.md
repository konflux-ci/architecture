# Image Controller

## Overview

The Image Controller for AppStudio helps set up container image repositories
for AppStudio Components. With image controller, AppStudio ensures one image
repository per Component and each build pipeline will have dedicated secret to
push image. AppStudio provides an isolated environment for users to push and
manage images.

Image controller watches Components to take actions according to the deletion
event and the value set to specific annotations. External services are able to
interact with image controller via annotations:

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

Image controller then creates following resources:

- A public image repository is created on Quay.io.
- A robot account is created and associated with the repository properly.
- A Kubernetes Secret is created alongside the Component CR, to which the
  robot account token is written out.

and writes out the details of the same into the Component as an annotation
`image.redhat.com/image`, namely:

- The image repository URL.
- The image repository visibility.
- The name of the Kubernets Secret.

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

Image controller does not use the created Secret. Currently, Build Service uses
that Secret for the build pipeline so that built images can be pushed to
component's image repository.

## Cleanup on deletion of a Component CR

All the related resources are cleaned up once image controller detects a
component has been requested to be deleted from AppStudio. Image controller is
responsible for removing the corresponding image repository and robot account
from Quay.io, and the Secret will be removed along with the component
eventually due to the established ownership between them.

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

