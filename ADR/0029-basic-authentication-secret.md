# 0. Record architecture decisions

Date: 2023-08-25

## Status

Proposed

## Context

- As a user, I would like to configure sensitive information/tokens/credentials for the build/test pipeline to consume as part of a TaskRun.
- As a user, I would like to provide credentials to access my source code on GitHub for the analyses of project structure, devfile analyses.
- As a user, I expect to have a place where I can list already provided credentials and adjust them it if needed.

## Decision
### How would the sensitive information be persisted and made available to the RHTAP?

1. The UI would take in sensitive information as form input and subsequently, the UI would create an `RemoteSecret` CR
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
2. `RemoteSecret.data` would be intercepted by webhook, sealed in permanent storage and removed from `RemoteSecret` CR.

### How would the sensitive information are made available to the RHTAP's components?
1. If any RHTAP's component want to consume sensitive information it is performing a search for an appropriate `RemoteSecret` by label `appstudio.redhat.com/sp.host`.
2. For the necessary `RemoteSecret`s  RHTAP's components has to expand target with desired secret name,label and annotations.
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
3. `RemoteSecret`s controller deliver `secretData` from permanent storage to the desired location.
4. After secret is no longer needed (example: `Task` finished) RHTAP's components removes `RemoteSecret`s target.

### How would a user specify that credentials a fine-grained and belong to a specific provider's resource?
1. UI provide an ability for the user to specify a concrete resource names.
2. UI add extra comma separated annotation to the `RemoteSecret` CR

```yaml
apiVersion: appstudio.redhat.com/v1beta1
kind: RemoteSecret
metadata:
    name: github-com-token
    namespace: myns
    annotations:
        appstudio.redhat.com/sp.resource:   "redhat/secret, redhat/opera"
    labels:
        appstudio.redhat.com/sp.host: github.com
spec:
    secret:
        type: kubernetes.io/basic-auth
```
3. When RHTAP's component performs a `RemoteSecret` search they have to take this annotation into consideration.

### How would these tokens/secrets be rotated ?

1. The user revokes the secret outside RHTAP.
2. The user generates a new credential outside RHTAP.
3. The user overwrites the secret in RHTAP with a new one using our UI.


## Consequences

See Michael Nygard's article, linked above.
