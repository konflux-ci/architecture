# 0. Support Secrets to be propagated to the multiple Environments.

Date: 2023-03-16

## Status

Provisional

## Context


* As a StoneSoup's component, I would expect to have the ability to securely upload `Secret` associate it with the component, and propagate it to the target `Environment`.
* As an admin user, I would expect StoneSoup to provide a place where I can securely upload/update sensitive information for later use in components on different `Environments`.

## Decision

### Overview

This proposal builds on the StoneSoup capabilities to provide different [Environments](https://github.com/redhat-appstudio/book/blob/main/ADR/0008-environment-provisioning.md) for the user's workload.

#### 1. Scenario: When a new Environment is defined and StoneSoup's component knows the secret content

1. The StoneSoup's component generates secrets with special labels `spi.appstudio.redhat.com/upload-secret: secret` and  `spi.appstudio.redhat.com/target-environment: prod`.   This feature is similar to [token upload feature](https://github.com/redhat-appstudio/service-provider-integration-operator/blob/main/docs/USER.md#uploading-access-token-to-spi-using-kubernetes-secret)
2. The spi-controller copies the `Secret` from the user's namespace into permanent storage (AWS secret manager, Vault). Instead of the original `Secret` spi-controller creating a new CR `RemoteSecret`, it includes the reference to the target `Environment` in the spec.
3. The spi-controller copies `Secret` to the target `Environment` each time then content is updated.

#### 2. Scenario: When an admin user want's to upload secret from UI

1. The UI generates CR `RemoteSecret` in the user's namespace.
2. The spi-controller provides a link that can be used to upload the `Secret`.
3. The spi-controller copies `Secret` to the target Environment each time then the content is updated.

#### Examples


```yaml
apiVersion: v1
kind: Secret
metadata:
  name: upload-secret
  labels:
    spi.appstudio.redhat.com/upload-secret: secret
    spi.appstudio.redhat.com/target-environment: prod
type: Opaque
data:
 ...
```



```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
  name: test-access-token-binding
spec:
  environment:
  - prod
  - staging
  secret:
    name: jdbc-connection-parameter
    linkedTo:
     - serviceAccount:
         managed:
           generateName: test-sa-
 ...
```
## Consequences

1. Real `Secrets` have to be somehow removed from the target user deployment to ensure that there is no race on creating/removing `Secrets` between ARGO and spi-controller.
