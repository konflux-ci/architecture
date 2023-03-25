# Secret Management For User Workloads

Date: 2022-10-28

## Status

Accepted

## Context

* When user workloads are deployed to environments, the system should be able to provide a way to inject values that is specific to the environment. Today, this is done through environment variables that are managed as overlays on the GitOps repository for the application. However, this method does not provide a good way to manage `Secret`. This ADR addresses the secret management of user workloads for different environments.
* As a StoneSoup's component, I would expect to have the ability to securely upload `Secret` associate it with the component, and propagate it to the target `Environment`.

## Decision

### Terminology

- UploadSecret - short-lived k8s secret used to deliver confidential data to permanent storage and link it to `RemoteSecret` CR
- SecretData  - is an object stored in permanent `SecretStorage`. Valid `SecretData` is always linked to `RemoteSecret` CR
- RemoteSecret - CR object that appears during upload and links `SecretData` + `DeploymentTarget`(s) + K8s Secret. `RemoteSecret` is linked to one (or zero) `SecretData` and manages its deleting/updating.
- K8s Secret   - is what appears at the output and is used by consumers
- SecretId - unique identifier of SecretData in permanent `SecretStorage`
- SecretStorage - a database eligible for storing SecretData (such as Hashicorp Vault, AWS Secret Manager).


### Architecture Overview

The idea is to have a new CR `RemoteSecret`. It is k8s representation of  K8s Secret that is stored in permanent storage `SecretStorage`. This CR contains the reference to the destination: k8s namespace or `Environment`. `UploadSecret` is used to perform an upload to the permanent storage. It is represented as regular k8s secret with special labels and annotations recognised by spi-controller. Different implementation of `SecretStorage` can be used such as: AWS Secret Manager or Hashicorp Vault.



#### Example: If destination is `Environment`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: jdbc-connection-parameter
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
  name: jdbc-connection-parameter
spec:
  secret:
    environment: prod
    name: jdbc-connection-parameter
 ...
```

#### Example: If destination is `Namespace` and secret has to be linked to SA
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: jdbc-connection-parameter
  annotations:
      spi.appstudio.redhat.com/secret-linkedto-serviceAccount-name: sa-star
  labels:
    spi.appstudio.redhat.com/upload-secret: secret
    spi.appstudio.redhat.com/target-namespace: ns-9459039345
type: Opaque
data:
 ...
```



```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
  name: jdbc-connection-parameter
spec:
  secret:
    namespace: ns-9459039345
    name: jdbc-connection-parameter
    linkedTo:
    - serviceAccount:
        reference:
          name: sa-star
```

### Integration with Other Services

#### Application Service
Application Service provides an API like the one that it provides for environment variables that similarly updates the secrets. Unlike environment variables, the secret provided by users is saved to the secret management backend.

### Security and Access Control

Only workspace maintainers can create and update secrets on a workspace on the default secret management backend.

### Monitoring and Auditing

For the default backend and the REST API

* Monitoring of access and usage of secrets: The `SecretStorage` should monitor and track access and usage of secrets to detect and prevent unauthorized access or misuse. This may include monitoring of user and application access to secrets, as well as tracking of secret usage and access patterns.

* Auditing of secret access and usage: The `SecretStorage` should maintain an audit log of all secret access and usage, to provide a record of who accessed and used secrets, when, and for what purpose.

* Alerting and notification of security issues: The `SecretStorage` should provide alerting and notification mechanisms to alert security administrators and other stakeholders of potential security issues or incidents. This may include alerts for unauthorized access or misuse of secrets, as well as alerts for other security-related events or issues.

## Consequences

* A new UI is going to be made available to create/update the secret values for components and provide environment-specific overrides to them.

## Missing parts and todos
 - It is not very well-defined yet how to determine exact target namespace in case if `Environment` name is used as a destination for `K8s Secret`. Potentially it could be taken from `Environment` -> `DeploymentTargetClaim` -> `DeploymentTarget`-> kubernetesCredentials.defaultNamespace.
 - The trigger when the `K8s Secret` has to be delivered. It should be not too early and namespace has to exist. And not too late for the User's deployment. Potentially: Argocd's [Resource Hooks](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/) can help with that.
