# Image Controller

# Overview
Image controller sets up and manages container image repositories in configured quay.io organization.
It works either for general purpose image repository or [Component](https://konflux-ci.dev/architecture/ref/application-environment-api.html#component)-specific image repository.

The image controller can perform multiple actions with use of ImageRepository custom resources.

- **Setup image repository**: create an image repository and a robot accounts
  which are specific to that repository for image push and pull.
  A Kubernetes Secret objects are also created with push and pull robot account tokens,
  in order to make it available for build PipelineRun via service account.

- **Modify repository visibility**: switch an image repository's visibility between public and private.

- **Rotating credentials for repository**: rotate repository credentials, and update relevant secrets.

- **Verify and fix secrets linked to ServiceAccount**: verify and fix linking of secrets to ServiceAccount.

- **Cleanup**: When a Component CR is requested to be deleted, image controller will remove
  component's image repository (Component owns ImageRepository) and robot account from the remote registry
  (it is possible to skip repository removal).
  The Kubernetes Secret will be removed along with the Component CR eventually due to the
  ownership established between them (ImageRepository owns Secret).

# Dependencies

Image controller does not depend on other Konflux services, but a remote image registry.
Konflux services are able to use the resources prepared by image controller,
e.g. ServiceAccount with linked Secrets is available to every build PipelineRun of a component
for pushing image.

## Controllers

The Image Controller contains these controllers:
- Image controller
  - Monitors ImageRepository CRs and creates image repository, robot accounts and
    links secret to service accounts.
- Application controller
  - Monitors Application CRs, creates application specific service account `$APPLICATION_NAME-pull`
    and links there (to both `secrets` and `imagePullSecrets` sections) all pull secrets from
    all Components in the Application.

# Interface

## ImageRepository CR

The ImageRepository CR is the interface to interact with image controller to create and manage image repositories in a registry.

### To create an general purpose image repository, apply this YAML code:
```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: ImageRepository
metadata:
    name: imagerepository-for-component-sample
    namespace: test-ns
```
As a result, a public image repository `quay.io/my-org/test-ns/imagerepository-for-component-sample`
will be created, based on `$DEFAULT_REGISTRY_ORG/$USER_NAMESPACE/$IMAGE_REPOSITORY_NAME`.
- DEFAULT_REGISTRY_ORG - is taken from quay secret in the cluster
- USER_NAMESPACE - is taken from ImageRepository `.metadata.namespace`
- IMAGE_REPOSITORY_NAME - is taken from ImageRepository `.metadata.name`

Two robot accounts and corresponding Kubernetes Secrets for push and pull are created.

### To create an image repository for a Component, apply this YAML code:
```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: ImageRepository
metadata:
    name: imagerepository-for-component-sample
    namespace: test-ns
    annotations:
        image-controller.appstudio.redhat.com/update-component-image: 'true'
    labels:
        appstudio.redhat.com/component: my-component
        appstudio.redhat.com/application: my-app
```
As a result, a public image repository `quay.io/my-org/test-ns/my-component` will be created,
based on `$DEFAULT_REGISTRY_ORG/$USER_NAMESPACE/$COMPONENT_NAME`.
- DEFAULT_REGISTRY_ORG - is taken from quay secret in the cluster
- USER_NAMESPACE - is taken from ImageRepository `.metadata.namespace`
- COMPONENT_NAME - is taken from Component `.metadata.name`

Two robot accounts and corresponding Kubernetes Secrets for push and pull are created.

It will also link push secret to component specific service account `build-pipeline-$COMPONENT_NAME`
used for build pipelines (`secrets` section).

And it will also link pull secret to application specific service account `$APPLICATION_NAME-pull`
(to both `secrets` and `imagePullSecrets` sections).

Annotation `image-controller.appstudio.redhat.com/update-component-image` is required when using
ImageRepository with Component, as it will set Component's `spec.containerImage` allowing
Build service controller to continue.

### User defined repository name
One may request custom image repository name by setting `spec.image.name` field upon
the ImageRepository object creation, but it will always be prepended by
`$DEFAULT_REGISTRY_ORG/$USER_NAMESPACE`.

e.g. when `spec.image.name` is set to `my-repository` final repository url will be
`$DEFAULT_REGISTRY_ORG/$USER_NAMESPACE/my-repository`.

Note, it's not possible to change image repository name after creation.
Any changes to the field will be reverted by the operator.

### Setting quay.io notifications
Notifications can be set with:
```yaml
spec:
  notifications:
  - config:
      url: https://bombino.api.redhat.com/v1/sbom/quay/push
    event: repo_push
    method: webhook
    title: SBOM-event-to-Bombino
```

### Changing repository visibility
By default, a public image repository is created.
To change the image repository visibility, set `public` or `private` to `.spec.image.visibility`.

### Credentials rotation for repository
To regenerate tokens push and pull, set `true` to `.spec.credentials.regenerate-token`, it will also re-create secrets.

After token rotation, the `spec.credentials.regenerate-token` section will be deleted and
`status.credentials.generationTimestamp` updated.

### Verify and fix secrets linked to ServiceAccount
- It will link secret to service account if link is missing.
- It will remove duplicate links of secret in service account.
- It will remove secret from imagePullSecrets in service account.

To perform verification and fix, set `true` to `.spec.credentials.verify-linking`.

After verification, the `spec.credentials.verify-linking` section will be deleted.

### Skip repository deletion
By default, if the ImageRepository resource is deleted, the repository it created in registry
will get deleted as well.

In order to skip the removal of the repository, set `true` to `image-controller.appstudio.redhat.com/skip-repository-deletion` annotation.

### Status explanation
ImageRepository CR has `.status` which includes all final information about an image repository:

```yaml
status:
  credentials:
    generationTimestamp: '2025-03-21T14:28:59Z'
    pull-robot-account: test_pull
    pull-secret: imagerepository-for-test-image-pull
    push-robot-account: test_push
    push-secret: imagerepository-for-test-image-push
  image:
    url: quay.io/redhat-user-workloads/test-tenant/test
    visibility: public
  notifications:
    - title: SBOM-event-to-Bombino
      uuid: aaaaa-......
  state: ready
```
- `.status.credentials` includes info about credentials.
  - `generationTimestamp` timestamp from when credentials were updated.
  - `pull-robot-account` robot account name in configured registry organization with read permissions to the repository
  - `pull-secret` Secret of `dockerconfigjson` type that contains image repository pull robot account token with read permissions.
  - `push-robot-account`robot account name in configured registry organization with write permissions to the repository
  - `push-secret`  Secret of `dockerconfigjson` type that contains image repository push robot account token with write permissions.
- `.status.image` includes the full repository URL and current visibility.
- `.status.notification` shows info about notifications.
- `.status.state` shows whether image controller responded last operation request successfully or not.

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
