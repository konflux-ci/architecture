# 26. Common labels for objects associated to Applications

Date: 2023-06-02

## Status

Accepted

## Context

There is a growing number of CRDs and other objects that together describe the application and its constituent parts. We need to use a consistent set of labels to describe to which
part of the application certain supporting objects belong. This is not a functional requirement as such but a consistent set of labels supports troubleshooting efforts as well
as general hygiene in the cluster (by being able to answer the questions like "what are all the objects associated with this environment?").

Consistent set of labels will also enable finding related objects when co-operation between several components is required yet directly referencing the related objects in the specs or statuses of
other objects is not feasible or practical.

## Decision

To identify the supporting objects defining the application model within AppStudio, this proposal establishes the 3 basic labels that can identify objects that are related to the most important parts of the model - application, environment and component. This list can grow whenever we find that multiple AppStudio components (controllers) are deriving their own objects based on the state of some part of the application model.

For the basic constituent parts of the application, the following labels are defined.

* `appstudio/application`
* `appstudio/environment`
* `appstudio/component`

The "domain" part is kept intentionally very short yet unique not to unnecessarily add to the size of the Kubernetes object.

It is not mandatory to have all 3 labels defined if it is not necessary or even possible for certain use cases. For example, the images are being built for application components, but they're common to all environments. Therefore, it doesn't make sense to specify an environment when referring to component builds.

Note that this proposal doesn't solve the situation where more than one application "part" needs to be associated (e.g. an object associated with 2 environments). The label values are limited to 63 characters and the label selectors don't support substring matching so any form delimiter-separated value wouldn't have much utility.

## Consequences

For this to make sense, all components that interact with and build upon the model objects need to consistently label the related objects they manage with the above labels.

Additionally, having the names of the application, environment and component as label values restricts their length to 63 characters (https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set).
