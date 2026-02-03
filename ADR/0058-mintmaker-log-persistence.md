# MintMaker log persistence

## Status
Ongoing discussion

## Context and Problem Statement

As part of the UI functionality, we want to serve MintMaker logs to the users. This will enable them to check how the runs went.

This ADR regards the persisting of the log files and the permission scheme we will use to serve them to the UI and to the users.

## Considered Options

* An extra SAR verification step
* CRD for log files + copying to component namespace
* Running pipelineruns in user namespaces
* Giving read access to pipelineruns and logs to all the cluster

## Pros and Cons of the Options

Before we get into the options themselves, it's worth mentioning that we envision all of them using Kubearchive, to persist the log files while not overloading cluster's etcd.

### Extra SAR verification step
In this solution we leave the log files in MintMaker's namespace, and perform an extra SAR check to verify if a certain user has access in a certain component namespace.

This extra step could be either in Konflux UI's side, before sending the request for the log file to MintMaker's backend, or in MintMaker's backend side, after receiving that request.

* Good, because this might prevent data leaks (CVE updates information) from misconfigurations in component namespaces
* Neutral: this is the more centralized option
* Bad, bacause it requires extra infra in MintMaker's backend to serve Konflux UI
* Bad, because it will demand more maintenance from MintMaker's team
* Bad, because it introduces more points of failure with the extra infra
* Bad, because it allows for less granularity
* Bad, because it would require MintMaker team to set the same persistence rules to all components/repositories
* Bad, because it could become throw-away work if we later decide to run Mintmaker pipelineruns in users namespace

### CRD for log files + copying to component namespace
In this solution, once MintMaker's pipelineruns are finished, we copy their log files to the corresponding component namespace.

After this, standard RBAC rules will take care of the permissions as usual.
We could also create a CRD for MintMaker log files, to increase granularity in the access control.

* Good, because it more natural (uses more things that are already in place)
* Good, because it allows for greater granularity with the extra CRD
* Good, because it requires no extra infra in MintMaker's backend
* Neutral: more decentralized option
* Bad, because it involves copying data around
* Bad, because it might allow for more data leaks from misconfigurations in component namespaces
* Bad, because it could become throw-away work if we later decide to run Mintmaker pipelineruns in users namespace

### Running pipelineruns in user namespaces
* Good, because it doesnt require extra infra
* Good, because it doesnt require copying data around
* Good, because it is perhaps the most natural solution
* Bad, because has many implications to MintMaker, that need to be duely mapped (this is an architectural change)
* Bad, because running things in the user namespace might increase support requests to the MintMaker team
* Bad, because it will not be easy to operationalize at the current moment

### Giving read-access to MintMaker pipelineruns and logs across all the cluster
* Good, because it doesnt require extra infra
* Good, because it doesnt require copying data around
* Good, because it doesnt create throw-away work
* Bad, because it gives broad access to logs and info about updates to all users in the cluster; however this is not too bad, and is the solution adopted in other subservices as well (nudging, releases)

## Decision Outcome

Chosen option: "give read-access across all the cluster", because it is the option that is actionable and is the least likely to result in throw-away work, with the understanding that the preferred long-term solution is to run MM pipelines in user namespaces.

### Consequences

* Good, because it will solve the immediate priority for the project
* Good, because it will imply in no throw-away work when we switch to the best long-term solution
* Bad, because it gives the broadest access of information to all users
* In particular, mintmaker is aware of all namespaces. This gives all users the ability to discover the names of all namespaces, components and source repositories registered on the cluster, including those of sensitive tenant namespaces.
* Mintmaker has access to secrets in tenant namespaces. Today, it does not log the contents of those secrets. But, if in the future, a bug is introduced that causes it to log them, then the contents of those secrets for every tenant will be exposed to every user. This would necessitate a major token rotation to be coordinated with all users of a cluster.
