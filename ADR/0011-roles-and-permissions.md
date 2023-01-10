# 11. Roles and Permissions for Stonesoup

Date: 2023-01-10

## Status

Accepted

## Context
Stonesoup is using Kubernetes as the control plane for managing its resources. We require a system for managing user roles and permissions in this context. We have defined the following roles for our project: "Contributor", "Maintainer", and "Owner". We need to map these roles to specific permissions in the Kubernetes RBAC system, in terms of API groups, verbs, and resources.

## Decision

We will use the built-in Kubernetes RBAC system for Stonesoup's role and permissions management, and map the following roles to specific permissions, as described in the table below:

### Roles
**Contributor:** Members who interact with the workspace mostly through pull requests.
**Maintainer:** Members who manage the workspace without access to sensitive or destructive actions.
**Owner:** Members who have full access to the workspace including sensitive and destruction actions.

### Roles and Permissions Table

|     Role      | Permissions             | API Groups                | Verbs                                   | Resources
|---------------|-------------------------|---------------------------|-----------------------------------------|----------------------------------------------------------------------
| Contributor   | Workspace               | Access to namespaces that backs workspace                           |
|               | Application & Component | appstudio.redhat.com      | get, list, watch                        | applications, components, componentdetectionqueries
|               | Environment             | appstudio.redhat.com      | get, list, watch                        | promotionruns, snapshotenvironmentbindings, snapshots, environments
|               | *GitOps*                | managed-gitops.redhat.com | get, list, watch                        | gitopsdeployments
|               | PipelineRun             | tekton.dev                | get, list, watch                        | pipelineruns
|               | Pipeline Results        | results.tekton.dev        | get, list                               | results, records
|               | IntegrationTestScenario | appstudio.redhat.com      | get, list, watch                        | integrationtestscenarios
|               | Enterprise contract     | appstudio.redhat.com      | get, list, watch                        | enterprisecontractpolicies
|               | Release Strategy        | appstudio.redhat.com      | get, list, watch                        | releases, releasestrategies, releaseplans
|               | Release Admission Plan  | appstudio.redhat.com      | get, list, watch                        | releaseplanadmissions
|               | *JVM Build Service*     | jvmbuildservice.io        | get, list, watch                        | jbsconfigs, artifactbuilds
|               | *Service Access*        | appstudio.redhat.com      | get, list, watch                        | spiaccesstokenbindings, spiaccesschecks, spiaccesstokens, spifilecontentrequest
|               | *Configs*               |                           | get, list, watch                        | configmaps
|               | *Secrets*               |                           |                                         | secrets
|               | Add User                |
|               | User group (with SSO)   |
| Maintainer    | Workspace               | Access to namespaces that backs workspace                           |
|               | Application & Component | appstudio.redhat.com      | get, list, watch, create, update, patch | applications, components, componentdetectionqueries
|               | Environment             | appstudio.redhat.com      | get, list, watch                        | promotionruns, snapshotenvironmentbindings, snapshots, environments
|               | *GitOps*                | managed-gitops.redhat.com | get, list, watch                        | gitopsdeployments
|               | PipelineRun             | tekton.dev                | create, get, list, watch                | pipelineruns
|               | Pipeline Results        | results.tekton.dev        | get, list                               | results, records
|               | IntegrationTestScenario | appstudio.redhat.com      | *                                       | integrationtestscenarios
|               | Enterprise contract     | appstudio.redhat.com      | get, list, watch                        | enterprisecontractpolicies
|               | Release Strategy        | appstudio.redhat.com      | *                                       | releases, releasestrategies, releaseplans
|               | Release Admission Plan  | appstudio.redhat.com      | *                                       | releaseplanadmissions
|               | *JVM Build Service*     | jvmbuildservice.io        | get, list, watch                        | jbsconfigs, artifactbuilds
|               | *Service Access*        | appstudio.redhat.com      | get, list, watch, create, update, patch | spiaccesstokenbindings, spiaccesschecks, spiaccesstokens, spifilecontentrequest
|               | *Configs*               |                           | get, list, watch                        | configmaps
|               | *Secrets*               |                           |                                         | secrets
|               | Add User                |
|               | User group (with SSO)   |
| Owner         | Workspace               | Access to namespaces that backs workspace                           |
|               | Application & Component | appstudio.redhat.com      | *                                       | applications, components, componentdetectionqueries
|               | Environment             | appstudio.redhat.com      | *                                       | promotionruns, snapshotenvironmentbindings, snapshots, environments
|               | *GitOps*                | managed-gitops.redhat.com | get, list, watch                        | gitopsdeployments
|               | PipelineRun             | tekton.dev                | *                                       | pipelineruns
|               | Pipeline Results        | results.tekton.dev        | get, list                               | results, records
|               | IntegrationTestScenario | appstudio.redhat.com      | *                                       | integrationtestscenarios
|               | Enterprise contract     | appstudio.redhat.com      | *                                       | enterprisecontractpolicies
|               | Release Strategy        | appstudio.redhat.com      | *                                       | releases, releasestrategies, releaseplans
|               | Release Admission Plan  | appstudio.redhat.com      | *                                       | releaseplanadmissions
|               | *JVM Build Service*     | jvmbuildservice.io        | get, list, watch                        | jbsconfigs, artifactbuilds
|               | *Service Access*        | appstudio.redhat.com      | *                                       | spiaccesstokenbindings, spiaccesschecks, spiaccesstokens,spifilecontentrequest
|               | *Configs*               |                           | *                                       | configmaps
|               | *Secrets*               |                           | *                                       | secrets
|               | Add User                |
|               | User group (with SSO)   |


## Consequences

* This decision will allow us to easily integrate with the Kubernetes environment and take advantage of its robust and well-tested RBAC system.
* It will also allow us to assign the appropriate level of permissions to each role, based on the responsibilities and privileges associated with each role in our project.
* The use of the built-in Kubernetes RBAC system will improve the testability of our system, as we can use the well-documented and widely-used Kubernetes APIs for testing and validation.
* Using the built-in Kubernetes RBAC system may require some initial configuration and setup. However, it will likely require less ongoing maintenance and support compared to using a custom solution.

