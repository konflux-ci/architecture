# Enable users to configure tokens/credentials for a Build/Test Pipeline

Date: 2023-03-03

## Status

Provisional

## Context

As a user, I would like to configure sensitive information/tokens/credentials for the build/test pipeline to consume as part of a TaskRun.

This enables partner tasks contributed by Red Hat partners ([STONE-549](https://issues.redhat.com/browse/STONE-549)), but it also enables some tasks in our existing build pipeline like the [sast-snyk task in our build-definitions repo](https://github.com/redhat-appstudio/build-definitions/blob/main/task/sast-snyk-check/0.1/sast-snyk-check.yaml) ([STONE-415](https://issues.redhat.com/browse/STONE-415)).

## Decision

### How would the sensitive information be persisted and made available to the PipelineRun ?

1. The UI would take in sensitive information as form input and [upload it to SPI](https://github.com/redhat-appstudio/service-provider-integration-operator/blob/main/docs/USER.md#uploading-access-token-to-spi-using-kubernetes-secret) using the user's authentication token.

2. Subsequently, the UI would create an `SPIAccessTokenBinding` CR with the appropriate name in the `.spec.secret.name` such that the secret appears under a well known name.

3. The PipelineRun must reference the secret by name.


### Do the build-service and integration service controllers directly reference the Secret?

They do not.

### Example

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-upload-secret
  labels:
    spi.appstudio.redhat.com/upload-secret: token
    spi.appstudio.redhat.com/token-name: my-spi-access-token-binding-for-snyk
type: Opaque
stringData:
  spiTokenName: my-spi-access-token-binding-for-snyk
  providerUrl: https://snyk.io/
  # The username is irrelevant, but has to be here for SPI to process this
  userName: my-username-goes-here
  # The tokenData is the actual secret. The secret string.
  tokenData: my-token-goes-here
```

```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: SPIAccessTokenBinding
metadata:
  name: my-snyk-secret-binding
spec:
 repoUrl: https://snyk.io/
 lifetime: "-1"
 secret:
   type: Opaque
   name: snyk-secret
   linkedTo:
    - serviceAccount:
        reference:
            name: pipeline
```

### How would these tokens/secrets be rotated ?

1. The user revokes the secret outside of Stonesoup.
2. The user generates a new credential outside of Stonesoup.
3. The user overwrites the secret in Stonesoup with a new one using our UI.

## Consequences

* The user has to _know_ what secret name is expected by their pipelinerun, and supply that in their
  upload secret through our UI. We can provide suggestions for known partner integrations in our UI,
  but this will need to permit open-ended input from users to permit completely custom user-supplied
  tasks.
* Partner tasks will need to advertise in their documentation what secret _name_ they expect to be
  present in order to function (not unlike our snyk task). If we want to _promote_ a partner task in
  our UI, we'll need to know that secret name in order to suggest it to users in the form where they
  upload their token.
* The build-service and the integration service do not need to be able to read the contents of all secrets in all namespaces.
* If a user wants to configure a secret on multiple workspaces (i.e. for integration tests), they will need to set the secret multiple times, even if the content is the same.

## Out-of-scope

* Making the senstive tokens available in other namespaces or clusters.
* Handling a token rotation strategy. At the moment, as suggested, we will support updating/deletion of the token.
