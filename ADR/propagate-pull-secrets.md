# 0. Support deploying images from Private Quay.io repositories

Date: 2023-03-16

## Status

Provisional

## Context

* As a user, I would expect StoneSoup to generate a private Quay.io image repository if my source code repository is  private.
* As a user, I would expect StoneSoup to gracefully deploy images that were pushed to private Quay.io repositories in every relevant environment.


## Decision

#### 1. Scenario: When a new Environment is defined

1. The image-controller creates the registy `Secret` in the target cluster's namespace for every Component in the workspace/namespace.
2. The image-controller links the `secret` to the `deployer` `serviceAccount`. If the `deployer` `serviceAccount` is absent, the `Secret` 
    would be linked to the `default` `serviceAccount` to account for distributions of Kubernetes which do not have a `deployer` `serviceAccount`.
3. At a heartbeat of 24 hours, the `Secret` in the target cluster's namespace is reconciled.

#### 2. Scenario: When a new Component is created

1. As part of the existing 'daily chores' of the image-controller, a new Quay.io image repository and robot account token is made available in the 
   namespace for 
 builds to be able to push to.
2. The image-controller iterates over every Environment that's present on the workspace/namespace.
3. For each Environment, the image-controller creates/updates the relevant `Secret` in the target cluster's namespace and links it to the `deployer`
   (or `default` `sa`).

#### 3. Scenario: Recovering from a disaster / credentials' exposure

1. Request re-generation of the Quay.io robot account token by setting the annotation `image.redhat.com/generate: 'true'`. 
  The resulting Quay.io API call automatically revokes the old token.
2. Continue to *Scenario 2: When a new Component is created*


## Consequences

1. The reference to the `Secret` is not visible in the GitOps repo.
2. The 'disaster recovery' scenario would bank on requesting a re-creation of the image repository credentials, which would then be propagated to the relevant Environments.
3. This process doesn't yet use a secret storage mechanism like SPI / Vault and the tech debt needs to be factored into future plans for improvement.
