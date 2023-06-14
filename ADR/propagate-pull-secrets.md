# 0. Support deploying images from Private Quay.io repositories

Date: 2023-03-16

## Status

Provisional

## Context

* As a user, I would expect StoneSoup to generate a private Quay.io image repository if my source code repository is  private.
* As a user, I would expect StoneSoup to gracefully deploy images that were pushed to private Quay.io repositories in every relevant environment.


## Decision

### Overview

1. This proposal builds on the capabilties of the [image-controller](https://redhat-appstudio.github.io/book/book/image-controller.html) which sets up a Quay.io image repository per `Component` and 'downloads' a robot account token into the user's namespace for builds to be able to push to it.

2. This proposal builds on the capabilities of SPI's `RemoteSecret` API. See https://github.com/redhat-appstudio/book/pull/70/files


#### When a new `Component` is created

1. The image-controller creates a new Quay.io image repository
2. The image-controller provisions a new robot account token that would only be able to "pull" the `Component`'s image.
3. The image-controller creates a `Secret` in the user's workspace namespace containing the robot account token
4. The integration-service creates a `RemoteSecret` referencing the above `Secret`.

```
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
  conditions:
  - lastTransitionTime: "..."
    message: ""
    reason: AwaitingData
    status: "False"
    type: DataObtained
``` 


#### When recovering from a disaster or credentials' exposure

1. Request re-generation of the Quay.io robot account token by setting the annotation `image.redhat.com/generate: 'true'` on the relevant Components.
  The resulting Quay.io API call automatically revokes the old token.


## Consequences

1. The reference to the `Secret` is not visible in the GitOps repo.
2. The 'disaster recovery' scenario would bank on requesting a re-creation of the image repository credentials, which would then be propagated to the relevant Environments.
3. Image Controller would have to create/generate another secret (mapped to a yet another robot account) that only supports pulling of images. 
