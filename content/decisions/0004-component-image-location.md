---
date: Oct 29, 2022T00:00:00Z
title: Out-of-the-box image repository for StoneSoup users
number: 4
---
# Out-of-the-box image repository for StoneSoup users

## Status

Accepted

## Approvers

* Alexey Kazakov
* Gorkem Ercan

## Reviewers

* Alexey Kazakov
* Gorkem Ercan
* Parag Dave
* Ralph Bean
* Andrew McNamara


## Context

**Problem**
StoneSoup does not have a internal registry where images could be pushed to as an intermediate step before being deployed as a container.
As an application centric experience, StoneSoup should not make it mandatory for its users to specify where the image ( built from source code ) needs
to be pushed to.


**Goals**:
* Provide an out-of-the-box location for users’ images to be pushed after being built from source.


**Non-Goals**:
* Define the user experience for users bringing existing images from other image registry services.
* Provide users an option to choose what the out-of-the-box location for images would be.
* Define the user experience for users who are willing to configure additional credentials for pushing to an image registry of their choice.

**Design Goals**
* Use Quay.io as the out-of-the-box image registry in order to avoid getting into the business of maintaining an internal registry.
* Align user permissions in an StoneSoup workspace with those in Quay.io
* Maintain the right levels of isolation between images being expected of a multi-tenant system.
* Security:
  * Leverage short-lived Quay.io API tokens for repo/org management on Quay.io
  * Leverage robot accounts for pushing images from CI/Build pipelines.



## Decision

### What

* Per workspace called "david", setup a new org “quay.io/unique-org-david/…”
* Per component, setup a new new repo “quay.io/unique-org-david/unique-component-repo”
* Use User’s Quay.io API token to manage the org/repo. Short-term, we'll use a pre-configured Quay.io API token associated with StoneSoup to create the org/repo till we
 figure out how to determinstically map a user in StoneSoup to a user in Quay.io.
* Generate a robot account token scoped to the relevant repository and persist it in the user's workspace for the image build and push process to consume.


### How - Design

#### Quay.io API token Configuration

1. Setup a Quay.io organization to host the OAuth app.
2. Create an OAuth Application in the Quay.io organization.
3. Geneate a token for the OAuth Application. This token would act as the 'service account' using which Quay.io resources would be created. Important to note, the token acts on behalf of the user who is requesting it - but uses the explicit scopes specified at the time of token generation.
4. Allowlist user 'shbose' to be create organizations using non-user-tokens using the Quay.io API.

| Syntax      | Description |
| ----------- | ----------- |
| Quay.io organization      | quay.io/redhat-user-workloads       |
| OAuth Application  name | Created, name redacted        |
| Account used to generate token | `shbose` , `mkovarik` |
| Scope | Administer organizations, Adminster repositories, Create Repositories |

<img width="1313" alt="image" src="https://user-images.githubusercontent.com/545280/212758440-5807cd4e-11b1-43bc-aa03-385b9284cb9e.png">


#### Organization and Image Repository creation

When a user creates a Component, a StoneSoup service would need to generate the image repository for consumption by the
build, test and deployment services.

* For each user, create a new Quay.io org “quay.io/unique-org-david”
* For each `Component` 'foo', create a new image repo “quay.io/unique-org-david/appname/componentname”
* Configure the robot account “redhat-<resource-uuid>” in “quay.io/unique-org-david” to be able to push to “quay.io/unique-org-david/appname-foo”
* Configure a `Secret` in the user's namespace with the robot account token.
* Annotate the `Component` with the name of the image repository and the name of the `Secret` containing the robot account token.

The following deviations from this design would be implemented:

Until the capability to progammatically create organizations in Quay.io is activated:
* Images repositories would be created in quay.io/redhat-user-workloads
* Isolation would continue to be maintained the same way - every image repository would have a scoped robot account that would be rotatable using Quay.io API for the same https://docs.quay.io/api/swagger/#!/robot/regenerateUserRobotToken.

Until the capability to determine the associated user/tenant/Space a Component is implemented,
* The quay.io repository created with use the format   quay.io/org-name/namespace-name/application-name/component-name. Example, https://quay.io/repository/redhat-user-workloads/shbose/applicationname/automation-repo

#### Lifecycle of the Quay.io resources

* Token generation:
    * Robot account token: At the moment, the controller responsible for generating the Quay.io resources would be responsible for rotating the tokens https://docs.quay.io/api/swagger/#!/robot/regenerateUserRobotToken
    * Quay.io API token: No programmatic way to regenerate this token is known at this point of time. This would be a manual activity to begin with.

* Upon deletion of an `Application`/`Component` from StoneSoup,
    * The controller/finalizer would delete the the relevant Quay.io resources namely, the image repository and the robot account.
    * The controller/finalizer would delete the linked `Secret` from the user's namespace. Most likely, this should be a mere `ownerReference`-based garbage collection.

* Upon removal of a user from Stonesoup,
    * The empty Quay.io organization associated with the user or the user's Space may not be deleted instantly, but would be scheduled for a delayed cleanup.
* PR-based tags are to be deleted on a regular basis. Image tags associated with `main` may remain un-pruned for now.


### How - Implementation

The implementation of the above design will be improved overtime with the possible introduction of new CRDs/APIs. At the moment, no new API is being planned till the need for it arises.


To request the Image controller to setup an image repository, annotate the `Component` with `image.redhat.com/generate: 'true'`.


```
apiVersion: StoneSoup.redhat.com/v1alpha1
kind: Component
metadata:
  annotations:
    image.redhat.com/generate: 'true'
  name: billing
  namespace: image-controller-system
spec:
  application: city-transit
  componentName: billing
```

The `Image controller` creates the necessary resources on Quay.io and writes out the details of the same into the `Component` resource as an annotation, namely:

* The image repository URL.
* The name of the Kubernets `Secret` in which the robot account token was written out to.

```
{
   "image":"quay.io/redhat-user-workloads/image-controller-system/city-transit/billing",
   "secret":"billing",
}
```

```
apiVersion: StoneSoup.redhat.com/v1alpha1
kind: Component
metadata:
  annotations:
    image.redhat.com/generate: 'false'
    image.redhat.com/image: >-
      {"image":"quay.io/redhat-user-workloads/image-controller-system/city-transit/billing","secret":"billing"
      }
  name: billing
  namespace: image-controller-system
  resourceVersion: '86424'
  uid: 0e0f30b6-d77e-406f-bfdf-5802db1447a4
spec:
  application: city-transit
  componentName: billing
```




## Open Questions

- What would be a progammatic way to regenerate the main Quay.io API token ?
- Since the long-term goal is to have the Quay.io organizations owned by the user, how do we build a frictionless experience to map the user's
  account with the user's Quay.io account ?
- Considering the above is figured out, we would need to add existing users as members of the relevant organizations. This is a backend job that
  would need to be designed and executed at an appropriate time.



## Consequences

- We will be able to deprecate the use of https://quay.io/repository/redhat-appstudio/user-workload for storing users' container images.
- Users will not be forced to put in an image repository location when they use StoneSoup to import and deploy source code.
- The image repository used could conditionally be made available to users outside of StoneSoup.
- Given that scoped Quay.io robot account tokens would be available in user's workspaces for pushing/pulling images, the principle of minimum privilege
  would be met.

## References

* Originally drafted in an internal [document](https://docs.google.com/document/d/1KcXWZ8VGUg_iR0RjdGuDYedP8ZW63XCgF26KZUNgpeQ/edit)
* Implementation: https://github.com/redhat-appstudio/image-controller
