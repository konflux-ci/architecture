---
date: 2022-12-09T00:00:00Z
title: Namespace Metadata
number: 10
---
# Namespace Metadata

## Status

Accepted

## Approvers

* Ann Marie Fred
* Gorkem Ercan

## Reviewers

* Matous Jobanek
* Ralph Bean
* Alexey Kazakov

## Context

We need metadata on our namespaces to make Konflux easier to operate and maintain. Standardizing namespace metadata will make it easier for us to search our logs and metrics across clusters. It will also allow us to enable logging for outgoing network traffic, one of our security requirements.

## Namespace labels

We will apply the following labels to Konflux namespaces, to make them easier to identify programmatically. One namespace can have multiple types/labels:

- `appstudio.redhat.com/namespacetype: "controller"` for namespaces containing controllers developed for Konflux. For example, we would annotate the `gitops-service-argocd` namespace but not the `openshift-gitops` namespace.
- `appstudio.redhat.com/namespacetype: "user-workspace-data"` for User workspaces where Applications, Components, and so on are stored
- `appstudio.redhat.com/namespacetype: "user-deployments"` for the namespaces where GitOps deploys applications for users
- `appstudio.redhat.com/namespacetype: "user-builds"` for the namespaces where the Pipeline Service manages users' PipelineRun resources

The following labels are used for billing and telemetry. Values can be left blank if they are not defined yet:

- `appstudio.redhat.com/workspace_name: "test_workspace"` a name for the workspace (unique identifier)
- `appstudio.redhat.com/external_organization: 11868048` the Red Hat orgId of the user account that created the workspace
- `appstudio.redhat.com/product_variant: "Stonesoup"` identifier for the type of product (allows tracking multiple variants in the same metric)
- `appstudio.redhat.com/sku_account_support: "Standard"` Standard, Premium, or Self-Support. Must match the value from the SKU.
- `appstudio.redhat.com/sku_env_usage: "Production"` Development/Test, Production, or Disaster Recovery. Must match the value from the SKU
- `appstudio.redhat.com/billing_model: "marketplace"` must be set to marketplace to indicate this service instance is billed through marketplace. This allows you to mark some instances as billed via marketplace (and some as not billed through marketplace)
- `appstudio.redhat.com/billing_marketplace: "aws"` which marketplace is used for billing
- `appstudio.redhat.com/billing_marketplace_account: 123456789012` the customer account identifier (numeric AWS identifier). Necessary because a customer can have more than one AWS account.

The following labels are used by required operators:

- `argocd.argoproj.io/managed-by: gitops-service-argocd` is added by the GitOps Service, and is reconciled by the OpenShift GitOps operator. This label enables a (namespace-scoped) Argo CD instance in the `gitops-service-argo` Namespace to deploy to any Namespace with this label.

## Namespace annotations

We will apply the following annotation to namespaces installed and maintained by Konflux on the clusters that Red Hat manages.  This will enable OVN network logging to log outgoing network traffic:

metadata:
  annotations:
    k8s.ovn.org/acl-logging: '{"deny": "info", "allow": "info"}'

## Consequences

We might have to migrate `appstudio.redhat.com` to another product name in the future, but it's the best option we have right now.
