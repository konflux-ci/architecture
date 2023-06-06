# 26. Common labels for objects associtated to Applications

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

The deployments, pods, configmaps, secrets, etc. that together compose AppStudio itself will have the usual common suggested set of labels such as:
* `app.kubernetes.io/name = has`
* `app.kubernetes.io/part-of = appstudio`

The more important part, though, is to identify the supporting objects defining the application model within AppStudio. This proposal establishes the 3 basic labels that can identify objects that are related to the most important parts of the model - application, environment and component:

* `appstudio/application`
* `appstudio/environment`
* `appstudio/component`

The "domain" part is kept intentionally very short yet unique not to unnecessarily add to the size of the Kubernetes object.

## Consequences

For this to make sense, all components that interact with and build upon the model objects need to consistently label the related objects they manage with the above labels.

Additionally, having the names of the application, environment and component as label values restricts their length to 63 characters.
