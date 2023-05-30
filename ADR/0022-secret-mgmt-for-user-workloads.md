# Secret Management For User Workloads

Date: 2023-03-25

## Status

Accepted

## Context

* When user workloads are deployed to environments, the system should be able to provide a way to inject values that are specific to the environment. Currently, this is done through environment variables that are managed as overlays on the GitOps repository for the application. However, this method does not provide a good way to manage `Secret`. This ADR addresses the secret management of user workloads for different environments.
* As a StoneSoup component, I expect to have the ability to securely upload a secret, associate it with the component, and propagate it to the target environment.
* It is important to distinguish the process of uploading confidential information and deploying it in the destination environment. This should/can be performed by different roles: first, creating a searchable `RemoteSecret` with linked `SecretData` that is stored remotely on `SecretStorage`, and second, finding this `RemoteSecret` and creating a working Secret with `SecretData` linked to it.
* It should be possible to set multiple destination targets.
* Any consumer should be able to perform a search of existing `RemoteSecret` by target environment/component/application.

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

The proposed solution is to create a new Kubernetes Custom Resource (CR) called `RemoteSecret`. It serves as a representation of the Kubernetes Secret that is stored in permanent storage, which is also referred to as `SecretStorage`. This Custom Resource includes references to targets, like Kubernetes namespaces, that may also contain the required data to connect to a remote Kubernetes. To perform an upload to permanent storage, a temporary **Upload Secret** is utilized, which is represented as a regular Kubernetes Secret with special labels and annotations that the SPI controller recognizes. Different `SecretStorage` implementations, like AWS Secret Manager or HashiCorp Vault, can be used. It is simpler to create the RemoteSecret first and then use the linked **Upload Secret** to upload secret data. However, in simple cases, the **Upload Secret**  can be used to perform both uploading and the creation of RemoteSecret in a single action. It's worth noting that the **Upload Secret** is not a core component of the framework, but rather a convenient way of creating secrets. In the future, it is possible that new methods of uploading SecretData to RemoteSecret may be added.



#### Example: If the working Secret should be created along with RemoteSecret.
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: test-remote-secret
    namespace: default
spec:
    secret:
        generateName: secret-from-remote-
        linkedTo:
            - serviceAccount:
                  managed:
                      generateName: sa-from-remote-
    targets:
        - namespace: "test-target-namespace"
        - namespace: "test-target-namespace"
        - namespace: "test-target-namespace"
        - namespace: "test-target-namespace"
          apiUrl: "over-the-rainbow"
          clusterCredentialsSecret: "team-a--prod-dtc--secret"
status:
    TBD
```
> :warning: **Note for this and following:** `RemoteSecret` is not Ready, `SecretData` referenced to it has to be uploaded. See `Uploading secret data to RemoteSecret` example. There are two meanings of the term "Ready" for `RemoteSecret`. First, it could refer to the readiness of the stored `SecretData`. In this case, "Ready" means that the data has been successfully stored in the `SecretStorage` and is ready to be used by the `RemoteSecret`. Second, it could refer to the readiness of the `SecretData` for each target. In this case, "Ready" means that the kubernetes secret has been created for each target and is ready to be used by the business logic.

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

#### Example:If multiple working Secrets should be created along with RemoteSecret.
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: test-remote-secret-secret
spec:
    secret:
        name: test-remote-secret-secret
    target:
        - namespace: jdoe-test-ns
        - namespace: jdoe-prod-ns
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
    secret:
        name: test-remote-secret-secret
    target:
        - namespace: jdoe-test-ns
        - namespace: jdoe-prod-ns
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
        appstudio.redhat.com/environment: prod
        appstudio.redhat.com/component: m-service
        appstudio.redhat.com/application: coffee-shop
spec:
    secret:
        name: test-remote-secret-secret
    target:
        - namespace: jdoe-tenant
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
        appstudio.redhat.com/component: m-service
        appstudio.redhat.com/application: coffee-shop
spec:
    secret:
        name: test-remote-secret-secret
    target:
        - namespace: jdoe-tenant
status:
    TBD
```
> **Note :** The component that will keep the connection between Environments and RemoteSecret's target should track all environments including the one that can be created after RemoteSecret creation.

#### Example: Uploading secret data to RemoteSecret
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: test-remote-secret
spec:
    secret:
        name: test-remote-secret-secret
    target:
        - namespace: jdoe-tenant
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
