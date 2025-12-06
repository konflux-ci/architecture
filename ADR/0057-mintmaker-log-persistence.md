# MintMaker log persistence

## Status
Ongoing discussion

## Context and Problem Statement

As part of the UI functionality, we want to serve MintMaker logs to the users. This will enable them to check how the runs went.

The challenge is how to do so while still having fine grained control over permissions: currently, the pipelineruns that execute our jobs are in MintMaker's namespace, and standard RBAC rules would only allow us to either allow access to all users outside our namespace or to none.

We would like to serve the log files following the same permissions as the component namespace. That is: users with permission in component A namespace should be able to see the logs for component A, but not for component B.

## Considered Options

* An extra SAR verification step
* CRD for log files + copying to component namespace

## Pros and Cons of the Options

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

## Decision Outcome

[STILL ONGOING]

Chosen option: "{title of option 1}", because {justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

<!-- This is an optional element. Feel free to remove. -->
### Consequences

* Good, because {positive consequence, e.g., improvement of one or more desired qualities, …}
* Bad, because {negative consequence, e.g., compromising one or more desired qualities, …}
* … <!-- numbers of consequences can vary -->



We are aiming to serve log files in the UI, so users can see how MintMaker runs went.

Solution 1:
Solution 2:


Proposal
We are more propense to adopt solution 2, as it seem more natural and requires less infra to be maintained from MintMaker's side.
Please give us your input on this, it will be very invaluable for us to reach the best decision.
Thank you!
