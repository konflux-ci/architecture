# 34. Workspace Experience

## Status

WiP

## Context

We inherited the "workspace" concept from our early days when we expected to be integrated with the [KCP] project. Long ago (over a year at the time of this writing), we decided to remove [KCP] from the architecture of the Konflux project - but, we have never revisited the workspace and defined and decided what we want it to be and what we want it to mean.

Workspaces are an important concept in the Konflux user experience today. The user onboards into a workspace of their own. A team member of theirs may add them to a team workspace. As a platform administrator, if you hear about a user having trouble, you'll ask them what workspace they're working in.

Workspace roles give a way to describe who has what rights in the workspace.

Workspaces happen to be our mechanism for managing quota - a fact inherited from the [kubesaw] stack.

Workspaces provide a kind of transparent multi-cluster for us. A user's workspace may be allocated to one cluster or another - but our proxy layer keeps the user blissfully unaware of this. Workspaces can be placed on clusters either automatically (using [kubesaw] mechanisms) or manually by a platform administrator.

Workspaces also provide a kind of general user-management today. Workspaces and users are mixed up - we can't tell which workspaces correspond with real users and which workspaces are team-based workspaces. They all look like users. However, they _do_ give us a concrete representation of a user, which we can use to power the invite dialog to add other users to your workspace.

### Some changes

Some relevant changes that have occurred or are ongoing.

* We made a decision (now long ago) to drop [KCP] from our architecture, which initially introduced the workspace concept. Both transparent multi-cluster as a feature and workspaces as a concept came from KCP. Are they still goals?
* We made the decision (at Red Hat) to stop trying to offer a managed service interface for Konflux. The user signup, waitlist, and workspace provisioning interfaces made a lot of sense there. Do they still make sense?
* For [konflux-ci], we want everything to work on vanilla kubernetes - no OpenShift required. But, [kubesaw] brings along OpenShift Templates for workspace provisioning. Are we going to work around that?i

### Some challenges

* Recently, we find ourselves being asked by users to provide service accounts. Our existing proxy layer doesn't support service accounts and we're having to come up with workarounds - breaking the existing abstraction.
* We find users requesting quota increases, but the tier system provided by our existing workspace quota management tooling doesn't permit us to adjust the quota of individual workspaces. We have to increase the whole tier, or add a new tier.
* We worry that new contributors will find the proxy layer confusing and offputting - more complex than it needs to be. "Is something more than just kubernetes in play here?"

## Decision

TBD - what do we want to do?

## Consequences

TBD - describe here both the benefits and the consequences of whatever decision we document here.
