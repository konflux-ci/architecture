# 11. Roles and Permissions for Konflux

Date: 2023-01-10

## Status

Accepted

## Context
Konflux is using Kubernetes as the control plane for managing its resources. We require a system for managing user roles and permissions in this context. We have defined the following roles for our project: "Contributor", "Maintainer", and "Admin". We need to map these roles to specific permissions in the Kubernetes RBAC system, in terms of API groups, verbs, and resources.

## Decision

We will use the built-in Kubernetes RBAC system for Konflux's role and permissions management, and map the following roles to specific permissions, as described in the table below:

### Roles
**Viewer:** Members who are mainly interested into CI results.
**Contributor:** Members who interact with the workspace mostly through pull requests.
**Maintainer:** Members who manage the workspace without access to sensitive or destructive actions.
**Admin:** Members who have full access to the workspace including sensitive and destruction actions.

### Roles and Permissions Table

|     Role      | Permissions             | API Groups                | Verbs                                           | Resources
|---------------|-------------------------|---------------------------|-------------------------------------------------|----------------------------------------------------------------------
| Viewer        | Workspace               | Access to namespaces that backs workspace                                   |
|               | Application             | appstudio.redhat.com      | get, list, watch                                | applications
|               | Component               | appstudio.redhat.com      | get, list, watch                                | components, componentdetectionqueries
|               | ImageRepository         | appstudio.redhat.com      | get, list, watch                                | imagerepositories
|               | Environment             | appstudio.redhat.com      | get, list, watch                                | promotionruns, snapshotenvironmentbindings, snapshots, environments
|               | DeploymentTarget        | appstudio.redhat.com      | get, list, watch                                | deploymenttargets
|               | DeploymentTargetClaim   | appstudio.redhat.com      | get, list, watch                                | deploymenttargetclaims
|               | *GitOps*                | managed-gitops.redhat.com | get, list, watch                                | gitopsdeployments, gitopsdeploymentmanagedenvironments, gitopsdeploymentrepositorycredentials, gitopsdeploymentsyncruns
|               | PipelineRun             | tekton.dev                | get, list, watch                                | pipelineruns
|               | Pipeline Results        | results.tekton.dev        | get, list                                       | results, records, logs
|               | IntegrationTestScenario | appstudio.redhat.com      | get, list, watch                                | integrationtestscenarios
|               | Enterprise contract     | appstudio.redhat.com      | get, list, watch                                | enterprisecontractpolicies
|               | *Release Service*       | appstudio.redhat.com      | get, list, watch                                | releases, releaseplans, releaseplanadmissions
|               | *JVM Build Service*     | jvmbuildservice.io        | get, list, watch                                | jbsconfigs, artifactbuilds
|               | *Service Access*        | appstudio.redhat.com      | get, list, watch                                | spiaccesstokenbindings, spiaccesschecks, spiaccesstokens, spifilecontentrequests
|               | *Remote Secrets*        | appstudio.redhat.com      | get, list, watch                                | remotesecrets
|               | Build Service           | appstudio.redhat.com      | get, list, watch                                | buildpipelineselectors
|               | Project Controller      | projctl.konflux.dev       | get, list, watch                                | projects, projectdevelopmentstreams, projectdevelopmentstreamtemplates
|               | *Configs*               |                           | get, list, watch                                | configmaps
|               | *Secrets*               |                           |                                                 | secrets
|               | Add User                |
|               | User group (with SSO)   |
|               | CronJob                 | batch                     | get, list, watch                                | cronjobs, jobs
| Contributor   | Workspace               | Access to namespaces that backs workspace                                   |
|               | Application             | appstudio.redhat.com      | get, list, watch                                | applications
|               | Component               | appstudio.redhat.com      | get, list, watch                                | components, componentdetectionqueries
|               | ImageRepository         | appstudio.redhat.com      | get, list, watch                                | imagerepositories
|               | Environment             | appstudio.redhat.com      | get, list, watch                                | promotionruns, snapshotenvironmentbindings, snapshots, environments
|               | DeploymentTarget        | appstudio.redhat.com      | get, list, watch                                | deploymenttargets
|               | DeploymentTargetClaim   | appstudio.redhat.com      | get, list, watch                                | deploymenttargetclaims
|               | *GitOps*                | managed-gitops.redhat.com | get, list, watch                                | gitopsdeployments, gitopsdeploymentmanagedenvironments, gitopsdeploymentrepositorycredentials, gitopsdeploymentsyncruns
|               | PipelineRun             | tekton.dev                | get, list, watch                                | pipelineruns
|               | Pipeline Results        | results.tekton.dev        | get, list                                       | results, records, logs
|               | IntegrationTestScenario | appstudio.redhat.com      | get, list, watch                                | integrationtestscenarios
|               | Enterprise contract     | appstudio.redhat.com      | get, list, watch                                | enterprisecontractpolicies
|               | *Release Service*       | appstudio.redhat.com      | get, list, watch                                | releases, releaseplans, releaseplanadmissions
|               | *JVM Build Service*     | jvmbuildservice.io        | get, list, watch                                | jbsconfigs, artifactbuilds
|               | *Service Access*        | appstudio.redhat.com      | get, list, watch                                | spiaccesstokenbindings, spiaccesschecks, spiaccesstokens, spifilecontentrequests
|               | *Remote Secrets*        | appstudio.redhat.com      | get, list, watch                                | remotesecrets
|               | Build Service           | appstudio.redhat.com      | get, list, watch                                | buildpipelineselectors
|               | Project Controller      | projctl.konflux.dev       | get, list, watch                                | projects, projectdevelopmentstreams, projectdevelopmentstreamtemplates
|               | *Configs*               |                           | get, list, watch                                | configmaps
|               | *Secrets*               |                           |                                                 | secrets
|               | Pulp Access Controller  | pulp.konflux-ci.dev       | get, list, watch                                | pulpaccessrequests
|               | Add User                |
|               | User group (with SSO)   |
|               | CronJob                 | batch                     | get, list, watch                                | cronjobs, jobs
|               | RoleBinding             | rbac.authorization.k8s.io | get, list                                       | rolebindings
| Maintainer    | Workspace               | Access to namespaces that backs workspace                                   |
|               | Application             | appstudio.redhat.com      | get, list, watch, create, update, patch         | applications, snapshots
|               | Component               | appstudio.redhat.com      | get, list, watch, create, update, patch         | components, componentdetectionqueries
|               | ImageRepository         | appstudio.redhat.com      | get, list, watch, create, update, patch         | imagerepositories
|               | Environment             | appstudio.redhat.com      | get, list, watch                                | promotionruns, snapshotenvironmentbindings, environments
|               | DeploymentTarget        | appstudio.redhat.com      | get, list, watch                                | deploymenttargets
|               | DeploymentTargetClaim   | appstudio.redhat.com      | get, list, watch                                | deploymenttargetclaims
|               | *GitOps*                | managed-gitops.redhat.com | get, list, watch                                | gitopsdeployments, gitopsdeploymentmanagedenvironments, gitopsdeploymentrepositorycredentials, gitopsdeploymentsyncruns
|               | PipelineRun             | tekton.dev                | get, list, watch                                | pipelineruns
|               | Pipeline Results        | results.tekton.dev        | get, list                                       | results, records, logs
|               | IntegrationTestScenario | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | integrationtestscenarios
|               | Enterprise contract     | appstudio.redhat.com      | get, list, watch                                | enterprisecontractpolicies
|               | *Release Service*       | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | releases, releaseplans, releaseplanadmissions
|               | *JVM Build Service*     | jvmbuildservice.io        | get, list, watch, create, update, patch         | jbsconfigs, artifactbuilds
|               | *Service Access*        | appstudio.redhat.com      | get, list, watch, create, update, patch         | spiaccesstokenbindings, spiaccesschecks, spiaccesstokens, spifilecontentrequests, spiaccesstokendataupdates
|               | *Remote Secrets*        | appstudio.redhat.com      | get, list, watch                                | remotesecrets
|               | Build Service           | appstudio.redhat.com      | get, list, watch, create                        | buildpipelineselectors
|               | Project Controller      | projctl.konflux.dev       | get, list, watch, create, update, patch         | projects, projectdevelopmentstreams, projectdevelopmentstreamtemplates
|               | *Configs*               |                           | get, list, watch                                | configmaps
|               | *Secrets*               |                           |                                                 | secrets
|               | Pulp Access Controller  | pulp.konflux-ci.dev       | get, list, watch, create, update, patch         | pulpaccessrequests
|               | Add User                |
|               | User group (with SSO)   |
|               | CronJob                 | batch                     | get, list, watch, create, update, patch         | cronjobs, jobs
|               | RoleBinding             | rbac.authorization.k8s.io | get, list                                       | rolebindings
| Admin         | Workspace               | Access to namespaces that backs workspace                                   |
|               | Application             | appstudio.redhat.com      | get, list, watch, create, update, patch, delete, deletecollection | applications
|               | Component               | appstudio.redhat.com      | get, list, watch, create, update, patch, delete, deletecollection | components, componentdetectionqueries
|               | ImageRepository         | appstudio.redhat.com      | get, list, watch, create, update, patch, delete, deletecollection | imagerepositories
|               | Environment             | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | promotionruns, snapshotenvironmentbindings, snapshots, environments
|               | DeploymentTarget        | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | deploymenttargets
|               | DeploymentTargetClaim   | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | deploymenttargetclaims
|               | *GitOps*                | managed-gitops.redhat.com | get, list, watch                                | gitopsdeployments, gitopsdeploymentmanagedenvironments, gitopsdeploymentrepositorycredentials, gitopsdeploymentsyncruns
|               | PipelineRun             | tekton.dev                | get, list, watch, create, update, patch, delete | pipelineruns
|               | Pipeline Results        | results.tekton.dev        | get, list                                       | results, records, logs
|               | IntegrationTestScenario | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | integrationtestscenarios
|               | Enterprise contract     | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | enterprisecontractpolicies
|               | *Release Service*       | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | releases, releaseplans, releaseplanadmissions
|               | Release Admission Plan  | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | releaseplanadmissions
|               | *JVM Build Service*     | jvmbuildservice.io        | get, list, watch, create, update, patch, delete | jbsconfigs, artifactbuilds
|               | *Service Access*        | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | spiaccesstokenbindings, spiaccesschecks, spiaccesstokens,spifilecontentrequests, spiaccesstokendataupdates
|               | *Remote Secrets*        | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | remotesecrets
|               | Build Service           | appstudio.redhat.com      | get, list, watch, create, update, patch, delete | buildpipelineselectors
|               | Project Controller      | projctl.konflux.dev       | get, list, watch, create, update, patch, delete | projects, projectdevelopmentstreams, projectdevelopmentstreamtemplates
|               | *Configs*               |                           | get, list, watch, create, update, patch, delete | configmaps
|               | *Secrets*               |                           | get, list, watch, create, update, patch, delete | secrets
|               | *Exec to pods*          |                           | create                                          | pods/exec
|               | Pulp Access Controller  | pulp.konflux-ci.dev       | get, list, watch, create, update, patch         | pulpaccessrequests
|               | SpaceBindingRequest    | toolchain.dev.openshift.com      | get, list, watch, create, update, patch, delete | spacebindingrequests
|               | Add User                |
|               | User group (with SSO)   |
|               | CronJob                 | batch                     | get, list, watch, create, update, patch, delete | cronjobs, jobs
|               | RoleBinding             | rbac.authorization.k8s.io | get, list, create, update, patch, delete        | rolebindings, roles
|               | ServiceAccount          |                           | get, list, create, update, patch, delete        | serviceaccounts
|               | Token                   |                           | create                                          | serviceaccounts/token

## Consequences

* This decision will allow us to easily integrate with the Kubernetes environment and take advantage of its robust and well-tested RBAC system.
* It will also allow us to assign the appropriate level of permissions to each role, based on the responsibilities and privileges associated with each role in our project.
* The use of the built-in Kubernetes RBAC system will improve the testability of our system, as we can use the well-documented and widely-used Kubernetes APIs for testing and validation.
* Using the built-in Kubernetes RBAC system may require some initial configuration and setup. However, it will likely require less ongoing maintenance and support compared to using a custom solution.
