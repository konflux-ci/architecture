# 32. Managing Secrets in Managed Workspaces
Date: 2023-11-22

## Status
Accepted

## Context
Currently, secrets are managed in managed workspaces via SPI's RemoteSecrets. This involves creating RemoteSecret resources in addition to creating and uploading Secrets to be linked to the RemoteSecrets. This secret data does not exist in any gitops repos nor within any secret service provider. It only exists locally on one's laptop. This poses a problem when a service or team needs to rotate a secret or even verify if the secret is valid.

## Decision
Managed workspaces will use ExternalSecrets via the External Secrets Operator. This will permit the tight integration with Vault that is already used in other systems.

## Consequence
- Users will need to create and administer workspace secrets using a combination of Vault and ExternalSecret resources.
