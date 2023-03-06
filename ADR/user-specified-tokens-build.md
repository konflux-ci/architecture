# Enable users to configure tokens/credentials for a Build/Test Pipeline

Date: 2023-03-03

## Status

Provisional


## Context

As a user, I would like to configure sensitive information/tokens/credentials for the build/test pipeline to consume as part of a partner task.


## Decision

1. UI will take in sensitive information as form input and upload it to SPI using the user's authentication token. See https://github.com/redhat-appstudio/service-provider-integration-operator/blob/main/docs/USER.md#uploading-access-token-to-spi-using-kubernetes-secret .
2. In the above form, the user should be able to choose the name of the `Secret` from a dropdown. 
The dropdown would be a pre-populated list of `Secret` names associated with known partner integrations. The user should also be allowed to provide a name barring the ones that already exist in the namespace.
3. The UI will create an `SPIAccessTokenBinding` CR that would create and link the secret with the _pipeline_ `serviceaccount`. See https://github.com/redhat-appstudio/service-provider-integration-operator/blob/main/docs/USER.md#linking-a-secret-to-a-pre-existing-service-account .
 


## Consequences

* Users would be able to create custom secrets that partner Tasks could consume.
* Partner Tasks would need to support reading the token from linked service account, instead of it being passed as a pipeline parameter.
* As a consequence of the above, follow-up work needs to be done to support Tasks which need the name of the `secret` passed as a parameter.
