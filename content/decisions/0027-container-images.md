---
date: 2023-06-30T00:00:00Z
title: Container Image Management Practice
number: 27
---
# Container Image Management Practice

## Status

Proposed

* Relates to [ADR 17. Use our own pipelines]({{< relref "0017-use-our-pipelines.md" >}})

## Context

The purpose of this document is to establish container image management practices for Konflux container images that are deployed in the staging and production environments.  The goal is to ensure that Konflux is continuously maintaining secure operations that are in accordance with the ESS SEC-PATCH-REQ-2 (OS Patching) requirements.

### Scope
* The scope of this process is limited to the images found in our [quay.io/organization/redhat-appstudio](https://quay.io/organization/redhat-appstudio) repository.
* Images from dependencies that fall outside of this Konflux process should follow the [ESS Security Patching at Application/OS Level (requirements 27 and 28)](https://drive.google.com/file/d/1P6-q2HJxA3yZhykaI29gF2IV4avzxtjM/view).  It is up to the component teams to ensure they are adhering to these requirements.
* Images that are not intended for the staging and/or production environments are out of scope.


## Decision

### Role

**Component Team**: Develops and maintains components that are built as images and deployed as part of Konflux


### Responsibilities

#### Automated Build and Scanning
###### Onboard to Pipelines As Code (PaC)

Component Teams are responsible for ensuring their container images are continuously built and scanned for vulnerabilities by following the
[Extending the Service](https://redhat-appstudio.github.io/infra-deployments/docs/deployment/extending-the-service.html) process to onboard their component to the PaC service.

***
#### Container Images <br>

###### Trigger Builds
Under the PaC service, images are rebuilt when there are updates to the component’s git repository but additional configuration is needed in the Dockerfile to ensure the underlying base (UBI) images are updated with the latest packages (see the [HAS example](https://github.com/redhat-appstudio/application-service/blob/main/Dockerfile#L24])) or at the very least, the latest [security updates](https://developers.redhat.com/articles/2021/11/11/best-practices-building-images-pass-red-hat-container-certification#best_practice__5__include_the_latest_security_updates_in_your_image).   This will minimize the gap between patching and should meet our CVE timelines as long as the repository is active.

Component teams are encouraged to install [renovatebot](https://github.com/renovatebot/renovate) to keep their dependencies up to date.

###### Scheduled Builds

Since image updates are based on how active our repos are, there is the risk that over time, as code stabilizes and/or enters maintenance mode, the triggers for rebuilds will be less frequent which will cause the images to degrade.  To avoid this, component teams should also ensure there are scheduled, weekly builds or builds driven by renovatebot or dependabot in place.


###### New Components
Newly onboarded components are required to use a fully supported and patched major version release for their base images per ESS SEC-PATCH-REQ-2 requirement #3.  Installing [renovatebot](https://github.com/renovatebot/renovate) can
help achieve this requirement.

***

#### Vulnerability Alerts

It is recommended that component teams set up notifications to receive vulnerability alerts that are at least **_medium_** severity.  This can be done in a couple of ways:

* Set up an [alert in quay.io](https://docs.quay.io/guides/notifications.html) which supports email and Slack integration
* Use the following github action to report vulnerabilities under the action tab.
You can copy this [workflow](https://github.com/openshift-pipelines/pipeline-service/blob/main/.github/workflows/periodic-scanner-quay.yaml) and this [script](https://github.com/openshift-pipelines/pipeline-service/blob/main/ci/images/vulnerability-scan/scan.sh) onto your repo and set the variables

***

#### Remediation

While our automation process will ensure that component teams are keeping their images updated, security scanners are not perfect.  Vulnerabilities can be reported through other channels, in which case, component teams must assess the severity of these findings and remediate according to the Infosec Remediation Guidelines

***

#### End of Life Base Images (EOL)

Component teams should be aware of the lifecycle policy for their base images by referring to the RedHat [Product Lifecycle page](https://access.redhat.com/product-life-cycles/update_policies).   Any base image version that is within 3 months of retiring must be updated to the latest patched major release. This should be supported by the [deprecated-base-image](https://github.com/redhat-appstudio/build-definitions/blob/main/task/deprecated-image-check/0.2/deprecated-image-check.yaml#L11-L12) check in the PAC pipeline.

***
#### Exception Process

The Red Hat Product Security Exception Process must be followed in the event that images cannot be patched or updated within the remediation timelines.  Some example scenarios:

* A fix that poses a risk to our service is not being provided by the vendor within the remediation timeline
* A deployed container image containing an EOL base image
* An image that cannot be scanned due to an unsupported manifest


## Consequences

In summary, component teams should have the following in place in order to meet ESS requirements:

* Onboard and integrate with PaC
* Ensure their container images are built regularly relying on both PR triggers and scheduled builds
* Ensure the base image layer is also updated with every image rebuild
* Set up vulnerability alerts
* Understand and follow the remediation timelines
* Understand and follow the exception process
* Images deployed from dependencies must not have vulnerabilities

See also [RHTAP-828](https://issues.redhat.com/browse/RHTAP-828).
