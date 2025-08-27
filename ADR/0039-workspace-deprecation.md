# 39. Workspace Deprecation

Some of the text was taken from - https://github.com/konflux-ci/architecture/pull/187

* Date: 2024-09-22

## Status

Implemented


Supersedes [ADR 31. Sprayproxy](0031-sprayproxy.html)

## Context

The purpose of this ADR is to revisit the workspace concept, understand the purpose
of it, and offer an alternative implementation based on native Kubernetes APIs
and other successful cloud native open source projects.


Today, Workspaces are an important concept in the Konflux user experience. The user onboards into a workspace of their own. A team member of theirs may add them to a team workspace. As a platform administrator, if you hear about a user having trouble, you'll ask them what workspace they're working in.

A Workspace is an abstraction of a namespace. Each workspace has a single namespace
which backs it.

Workspaces are required by [kubesaw] for providing a transparent multi-cluster communication for us. A user's workspace may be allocated to one cluster or another - but our proxy layer keeps the user blissfully unaware of this. Workspaces can be placed on clusters either automatically (using [kubesaw] mechanisms) or manually by a platform administrator.

Workspace roles give a way to describe who has what rights in the workspace.

Workspaces happen to be our mechanism for managing quota - a fact inherited from the [kubesaw] stack.

### Some changes

Some relevant changes that have occurred or are ongoing.

* We want to make Konflux a successful open source projects that fits into the
cloud native apps ecosystem. We want everything to work on vanilla Kubernetes - no OpenShift required.

* We had our [first upstream Konflux release](https://github.com/konflux-ci/konflux-ci) which doesn't use [kubesaw] or relying
on the Workspace abstraction, and is deployable on vanilla Kubernetes.

* We made a decision (now long ago) to drop [KCP] from our architecture, which initially introduced the workspace concept. Both transparent multi-cluster as a feature and workspaces as a concept came from KCP.

* We made the decision (at Red Hat) to stop trying to offer a managed service interface for Konflux. The user signup, waitlist, and workspace provisioning interfaces made a lot of sense there.

## Decision

1. We will remove the Workspace abstraction from Konflux and use standard Kubernetes namespaces
directly for providing a place for users to run their pipelines and store their configurations
and secrets.

2. Konflux won't provide its own policy engine for enforcing policies related to
creating/deleting namespaces. It will instead recommend user to use existing open source projects
such as [Kyverno](https://kyverno.io/docs/introduction/) and [Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/) for this task.

3. We will stop using the term Workspace, and start to use the term Namespace.

4. The Konflux UI will expose a wizard for creating a new namespace. This
wizard will be visible to any user that has permissions to create namespaces.

5. Konflux won't be opinionated about the mechanism for initializing/maintaining namespaces with
supporting resources such as ResourceQuota and LimitRange. Konflux will defer
this responsibility to other tools which are specialized in this task such as 
(but not limited to) [Kyverno](https://kyverno.io/policies/best-practices/add-ns-quota/add-ns-quota/) and [ArgoCD](https://github.com/konflux-ci/namespace-generator).

6. Konflux will provide a thin [backend service](https://github.com/konflux-ci/workspace-manager) for listing the namespaces where the user has at least view access
to the Konflux CRDs. This list will be used by the namespace switcher in the UI.
This is required since the Kubernetes API doesn't let the user to list a subset
of namespace. The user gets permissions to list all namespace or none.

7. Konflux will provide ClusterRoles that will grant permissions to the Konflux
and Tekton CRDs. Those will be (aggregated)[https://github.com/konflux-ci/konflux-ci/issues/440] to the built-in Kubernetes roles (`view`, `edit`, `admin`).

8. Public viewer access will be provided by assigning the `view` role (see above) to the
`system:authenticated` built-in group that contains all the authenticated users.

9. Same as Kubernetes, Konflux won't have a resource for representing a user. Instead,
it will use external Identity providers.

10. Konflux won't provide a way for creating a ephemeral namespaces. It will defer this
task to another tool.

11. The `join the waitlist` button will be removed from the Konflux UI.

12. Konflux won't provide a transparent multi-cluster deployment.
If required, existing open source projects that handle multi-cluster deployments
should be explored and Konflux should integrate with them.

## Consequences

1. By removing the Workspace abstraction, and delegating namespace management tasks to other open source tools,
the Konflux developers will have more attention for developing features related to to Konflux' core mission.

2. Operating Konflux will become easier for users who already familiar with Kubernetes built in resources such as namespaces.

3. Konflux operators (people who run Konflux) can use their preferred way to manage namespaces on their clusters without the need to learn about a new concept (they
might already use tools such as `ArgoCD`, `Kyverno`, `Gatekeepr`), or
writing code for extending the Workspace abstraction.

4. Konflux integrates with other open source cloud native tools, which can improve Konflux
fit in the the cloud native apps ecosystem.

5. Konflux doesn't have a dependency on [kubesaw].
