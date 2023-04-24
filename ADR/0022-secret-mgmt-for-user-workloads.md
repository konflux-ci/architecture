# Secret Management For User Workloads

Date: 2023-03-25

## Status

Accepted

## Context

* When user workloads are deployed to environments, the system should be able to provide a way to inject values that are specific to the environment. Currently, this is done through environment variables that are managed as overlays on the GitOps repository for the application. However, this method does not provide a good way to manage `Secret`. This ADR addresses the secret management of user workloads for different environments.
* As a StoneSoup component, I expect to have the ability to securely upload a secret, associate it with the component, and propagate it to the target environment.
* It should be possible to distinguish in time the process of uploading confidential information and deploying it in the destination environment. For example, image-controller creates an image pull secret after `Component` is created, and deploys it after `Environment` is made.
* It should be possible to set multiple destination targets.
* The UI should be able to perform a search of existing RemoteSecret by target environment/component/application.

## Decision

### Architecture Overview
#### Terminology

- **Upload Secret**: A short-lived Kubernetes `Secret` used to deliver confidential data to permanent storage and link it to the `RemoteSecret` CR. The Upload Secret is not a CRD.
- `SecretData`: An object stored in permanent SecretStorage. Valid SecretData is always linked to a RemoteSecret CR.
- `RemoteSecret`: A CRD that appears during upload and links `SecretData` + `DeploymentTarget(s)` + K8s `Secret`. `RemoteSecret` is linked to one (or zero) SecretData and manages its deleting/updating.
- K8s `Secret`: What appears at the output and is used by consumers.
- `SecretId`: A unique identifier of SecretData in permanent SecretStorage.
- `SecretStorage`: A database eligible for storing `SecretData` (such as HashiCorp Vault, AWS Secret Manager). That is an internal mechanism. Only spi-operator will be able to access it directly.

#### Architecture

![](../diagrams/secret-mgmt.excalidraw.svg)
TODO update diagram

The proposed solution is to create a new Kubernetes Custom Resource (CR) called `RemoteSecret`. It serves as a representation of the Kubernetes Secret that is stored in permanent storage, which is also referred to as `SecretStorage`. This Custom Resource includes references to targets, like Kubernetes namespaces, that may also contain the required data to connect to a remote Kubernetes. To perform an upload to permanent storage, a temporary **Upload Secret** is utilized, which is represented as a regular Kubernetes Secret with special labels and annotations that the SPI controller recognizes. Different `SecretStorage` implementations, like AWS Secret Manager or HashiCorp Vault, can be used. It is recommended to create the RemoteSecret first and then use the linked Upload Secret to upload secret data. However, in simple cases, the Upload Secret can be used to perform both uploading and the creation of RemoteSecret in a single action.



#### Example: If the destination is `Namespace`
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    namespace: jdoe-tenant
spec:
    target:
        - namespace: spi-test-target
          secretName: test-remote-secret-secret-5bmq9
status:
    TBD

```

#### Example: If RemoteSecret has to be created and uploaded without setting any target

```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    namespace: jdoe-tenant
spec:
    target:
status:
  TBD
```

#### Example: If RemoteSecret has to be created with multiple target namespaces
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: test-remote-secret-secret
spec:
    target:
        - namespace: jdoe-test-ns
          secretName: test-remote-secret-secret-5bmq9
        - namespace: jdoe-prod-ns
          secretName: test-remote-secret-secret-5bmq9
status:
    TBD
```

#### Example: If RemoteSecret has to be created with multiple target namespaces including BYC use-case
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: test-remote-secret-secret
spec:
    target:
        - namespace: jdoe-test-ns
          secretName: test-remote-secret-secret-5bmq9
        - namespace: jdoe-prod-ns
          secretName: test-remote-secret-secret-5bmq9
          apiURL: https://somedomain.copm:443
          clusterCredentialsSecret: team-a--prod-dtc--secret
status:
    TBD
```

#### Example: If RemoteSecret has to be created with target namespace and Environment
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: test-remote-secret-secret
    labels:
        appstudio.redhat.com/remotesecret-target-environment: prod
        appstudio.redhat.com/remotesecret-target-component: m-service
        appstudio.redhat.com/remotesecret-target-application: coffee-shop
spec:
    target:
        - namespace: jdoe-tenant
          secretName: test-remote-secret-secret-5bmq9
status:
    TBD
```

#### Example: If RemoteSecret has to be created all Environments of certain component and application
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: test-remote-secret-secret
    labels:
        appstudio.redhat.com/remotesecret-target-component: m-service
        appstudio.redhat.com/remotesecret-target-application: coffee-shop
spec:
    target:
        - namespace: jdoe-tenant
          secretName: test-remote-secret-secret-5bmq9
status:
    TBD
```

#### Example: Uploading secret data to RemoteSecret
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: test-remote-secret
spec:
    target:
        - namespace: spi-test-target
          secretName: test-remote-secret-secret-5bmq9
status:
    TBD

```
```yaml
apiVersion: v1
kind: Secret
metadata:
    name: test-remote-secret-secret
    labels:
        spi.appstudio.redhat.com/upload-secret: remotesecret
    annotations:
        spi.appstudio.redhat.com/remotesecret-name: test-remote-secret
type: Opaque
stringData:
    a: b
    c: d
```

Since the determination of concrete namespace/k8s clusters from the environment is not trivial and is in process of evolution the concrete controller or process that transforms RemoteSecret's annotations to concrete values of `spec.target` is TBD.


### Security and Access Control

* Access to the secret management backend should be restricted to authorized users and components. See the table for the access levels for different roles.
* The default backend should use authentication and authorization mechanisms provided by the underlying service, such as Kubernetes or AWS IAM.
* Workspace maintainers should have the ability to create and update secrets for their workspace on the default secret management backend.
* Access to the secret management backend should be audited to detect and prevent unauthorized access or misuse.

#### Additions to Roles and Permissions

| Role        | Permissions  | API Groups           | Verbs                                   | Resources    |
|-------------|--------------|----------------------|-----------------------------------------|--------------|
| Contributor | RemoteSecret | appstudio.redhat.com | get, list, watch                        | remotesecret |
| Maintainer  | RemoteSecret | appstudio.redhat.com | get, list, watch, create, update, patch | remotesecret |
| Admin       | RemoteSecret | appstudio.redhat.com | *                                       | remotesecret |

Only roles with `create` privileges to `Secret`s can create and update secrets. At the time if this ADR this is limited to Admin role only.



### Monitoring and Auditing

* The secret management system should be monitored and audited to detect and prevent unauthorized access or misuse.
* Access and usage of secrets should be monitored and tracked to identify potential security issues or incidents.
* An audit log of all secret access and usage should be maintained to provide a record of who accessed and used secrets, when, and for what purpose.
* The secret management system should also provide alerting and notification mechanisms to alert security administrators and other stakeholders of potential security issues or incidents. This may include alerts for unauthorized access or misuse of secrets, as well as alerts for other security-related events or issues.

## Consequences

* The new secret management system will provide a more secure and scalable way for users to manage secrets for their workloads. It will also require some additional work to integrate with existing systems and processes. A new UI will need to be created to allow users to create and update secret values for their components and provide environment-specific overrides to them.
* Further work to be addressed, mechanisms for determining the exact target namespace in case if Environment name is used as a destination for K8s Secret, and determining the trigger when the K8s Secret has to be delivered. The use of ArgoCD's Resource  ArgoCD's [Resource Hooks](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/) may be helpful in this regard.
