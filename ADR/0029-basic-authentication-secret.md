# 29. Basic Authentication Secret

Date: 2023-08-25

## Status

Proposed

## Context

- As a user, I need a secure way to configure sensitive information/tokens/credentials for various components within the RHTAP environment. This includes providing credentials for accessing source code repositories on GitHub and other authentication needs.
- As a user, I expect to have a place where I can list already provided credentials and adjust them it if needed.

## Decision

### Persisting Sensitive Information

We propose that the UI captures sensitive information through form input and creates `RemoteSecret` Custom Resources (CRs) to store this data. The `RemoteSecret.data` will be intercepted by a webhook, securely stored, and removed from the `RemoteSecret` CR to ensure that data is not kept in etcd.
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: github-com-token
    namespace: myns
    labels:
        appstudio.redhat.com/sp.host: github.com
spec:
    secret:
        type: kubernetes.io/basic-auth
data:
  username: Z2VuYQ==
  password: Z2VuYQ==
```
### Accessing Sensitive Information

1. RHTAP components will search for `RemoteSecret` instances based on the `appstudio.redhat.com/sp.host` label.
2. For the required `RemoteSecret`s, the components will expand the targets using the desired secret name, label, and annotations to access the secret data.
3. The controller will retrieve `secretData` from permanent storage and deliver it to the desired location.
4. Once the secret is no longer needed, the components will remove the `RemoteSecret`'s target.
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: github-com-token
    namespace: myns
    labels:
        appstudio.redhat.com/sp.host: github.com
spec:
    targets:
    - namespace: myns
      secret:
        name: tekton-secret
        annotations:
            tekton.dev/git-0: https://github.com
    secret:
        type: kubernetes.io/basic-auth

```
### Fine-Grained Credentials

Users can specify resource names through the UI, which will be added as comma-separated annotation `appstudio.redhat.com/sp.repository` to the `RemoteSecret` CR. RHTAP components will consider these annotations during `RemoteSecret` searches.
```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: github-com-token
    namespace: myns
    annotations:
        appstudio.redhat.com/sp.repository: "redhat/secret,redhat/opera"
    labels:
        appstudio.redhat.com/sp.host: github.com
spec:
    secret:
        type: kubernetes.io/basic-auth
```
### Rotation of Tokens/Secrets

Users can rotate tokens/secrets through these steps:
1. Revoke the secret externally.
2. Generate a new credential externally.
3. Overwrite the secret in RHTAP using the UI.


## Consequences

1. **Minimal Data Exposure**: Secrets that are not actively used by any workload remain in permanent storage without being populated in etcd, reducing potential data exposure.
2. **Audit Trail for Unused Secrets**: In the rare case where secrets remain in etcd for an extended period, there is a potential avenue to identify the intended consumers of these secrets. This can help with security audits and potential investigations.
3. **Extended Credential Usage**: The architecture enables the usage of credentials beyond the current namespaces. This includes scenarios like namespace-backed environments, ephemeral environments, or user-provided clusters (Bring Your Own Cluster - BYOC).
