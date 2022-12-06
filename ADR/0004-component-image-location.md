# 4. Out-of-the-box image repository for AppStudio users 

Date: Oct 29, 2022 

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
* Ann Marie Fred

## Context

**Problem**
AppStudio does not have a internal registry where images could be pushed to as an intermediate step before being deployed as a container.
As an application centric experience, AppStudio should not make it mandatory for its users to specify where the image ( built from source code ) needs
to be pushed to.


**Goals**: 
* Provide an out-of-the-box location for users’ images to be pushed after being built from source.


**Non-Goals**: 
* Define the user experience for users bringing existing images from other image registry services.
* Provide users an option to choose what the out-of-the-box location for images would be. 
* Define the user experience for users who are willing to configure additional credentials for pushing to an image registry of their choice.

**Design Goals**
* Use Quay.io as the out-of-the-box image registry in order to avoid getting into the business of maintaining an internal registry.
* Align user permissions in an AppStudio workspace with those in Quay.io
* Maintain the right levels of isolation between images being expected of a multi-tenant system.
* Security:
  * Leverage short-lived Quay.io API tokens for repo/org management on Quay.io
  * Leverage robot accounts for pushing images from CI/Build pipelines.



## Decision

### What

* Per workspace called "david", setup a new org “quay.io/unique-org-david/…”
* Per component, setup a new new repo “quay.io/unique-org-david/unique-component-repo”
* Use User’s Quay.io API token to manage the org/repo. Short-term, we'll use a pre-configured Quay.io API token associated with AppStudio to create the org/repo till we 
 figure out how to determinstically map a user in AppStudio to a user in Quay.io.
* Generate a robot account token scoped to the relevant repository and persist it in the user's workspace for the image build and push process to consume.


### How

#### Long-term
* (One-time) Use an OAuth flow to get David’s Quay.io API token if not previously pulled
* Create a new Quay.io org owned by David using David’s API token “quay.io/unique-org-david”
* Create a new image repo for “foo” using David’s API token “quay.io/unique-org-david/appname-foo”
* Configure the robot account “appstudio” in “quay.io/unique-org-david” to be able to push to “quay.io/unique-org-david/appname-foo” Invalidate/Delete/Prune David’s API token. 


#### Short-term

##### Setup
* Configure a pre-configured Quay.io API token for repo/org management, also known as the OAuth Access token. From a security perspective, this would be treated as a typical service account token
  belonging to AppStudio. This token would be shortlived and rotated *as frequently as practically possible*  .

##### When a user creates a Component
1. Create a new Quay.io org owned by David using the pre-configured AppStudio-wide API token `quay.io/unique-org-david`
2. Create a new image repo for Component “foo” using the the pre-configured David’s API token `quay.io/unique-org-david/unique-component-foo`
3. Configure a robot account  `quay.io/unique-org-david` to be able to push to `quay.io/unique-org-david/unique-component-foo`


##### Long-term

The fundamental design does not change in the long-term except that we wouldn't bank on the pre-configured Quay.io API token for repo/org management.
We would use the user's API token for working with the relevant Quay.io organizations and repositories.


## Open Questions

- Since the long-term goal is to have the Quay.io organizations owned by the user, how do we build a frictionless experience to map the user's 
  account with the user's Quay.io account ?
- Considering the above is figured out, we would need to add existing users as owners to the relevant organizations. This is a backend job that 
  would need to be designed and executed at an appropriate time.
- In the HACBS context, giving ownership of the image repo to users is not a problem for provenance, because integrity of images is based on attestations which are only treated as valid if signed by pipeline-service (by tekton chains). While users can in theory push images built on their laptop, the [release-service](../book/release-service.md) won't treat them as if they were built by the [pipeline-service](https://github.com/openshift-pipelines/pipeline-service). They will fail to pass the [enterprise contract](../book/enterprise-contract.md).


## Consequences

- We will be able to deprecate the use of https://quay.io/repository/redhat-appstudio/user-workload for storing users' container images.
- Users will not be forced to put in an image repository location when they use AppStudio to import and deploy source code.
- The image repository used will be made available to users outside of AppStudio.
- Given that scoped Quay.io robot account tokens would be available in user's workspaces for pushing/pulling images, the principle of minimum privilege
  would be met.

## References

Originally drafted in an internal [document](https://docs.google.com/document/d/1KcXWZ8VGUg_iR0RjdGuDYedP8ZW63XCgF26KZUNgpeQ/edit)
