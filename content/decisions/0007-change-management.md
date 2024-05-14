---
date: 2022-11-22T00:00:00Z
title: Change Management Process
number: 7
---
# Change Management Process

## Status

Accepted

* Relates to [ADR 17. Use our own pipelines]({{< relref "0017-use-our-pipelines.md" >}})
* Relates to [ADR 20. Source Retention]({{< relref "0020-source-retention.md" >}})

## Approvers

* Ann Marie Fred
* Gorkem Ercan
* Ralph Bean

## Reviewers

## Context

Red Hat's ESS requirement SEC-CHG-REQ-1 (Change Management) states that "All applications/systems/platforms/services must follow Change Management process and procedures, as applicable / appropriate." Change management is important in order to ensure no unauthorized changes are made to systems or applications, in order to help prevent the purposeful or accidental introduction of security vulnerabilities and an increase in threat attack surface.

Because Stone Soup is using a continuous delivery model, we need to ensure that we use a lightweight change management process when it's appropriate, and follow a more intensive change management process when needed. The normal code review process is in effect already. The full change request process will be used once our offering goes into a 24x7 support mode.

## Decision

Incremental code changes that are fully tested by automated tests, which will not cause an outage or a significant change to functionality, will follow the normal code review process in their respective code repositories.

To deploy an infrastructure change or a new version of software to staging and production, a developer will make the required change to the infra-deployments repo or the App Interface repo.  Then the change must follow our normal code review process.

### Normal code review process

A developer will make their code changes and write automated tests in a Git feature branch.  The developer will raise a Github Pull Request (PR) when they need other team members to review their work. This review could be for work in progress or when the developer feels the work is completed. If the developer wants a code review but feels that their work is not ready to be deployed yet, they will add the "do-not-merge/work-in-progress" label to the PR. We also recommend adding "WIP" to the pull request title.

At least one developer who is not the PR author must review and approve the code change. The reviewers will provide comments in Github for suggested changes. The reviewer has a responsibility to verify that the code follows our established best practices and "definition of done". From a change management perspective, the reviewer ensures that:
* We continue to meet our security and privacy requirements.
* Code is fully exercised by passing unit tests.
* Proper error and audit logging is in place.
* There are no obvious implementation holes or incorrect logic.
* Code is free of excessive "TODO" items.
* Build/deployment/configuration changes are automated where possible, and they have proper operational documentation.

We also require that all of our repositories be instrumented with CI test automation that runs when a PR is raised, and after each new commit. The CI checks will install the software and run a suite of automated tests.  The CI checks will also run security scans.  All CI checks must pass before performing a Merge to the main branch, as this updates the staging environment and makes the code available for deployment into production.

When the review is completed and CI checks have passed, the approver should Approve the PR in GitHub and the PR author will then Merge the code.

For changes to the infra-deployments repo, the PR author may add the "lgtm" (looks good to me) label to the PR rather than clicking on the Merge button. This will trigger the Prow/Tide deployment automation to create a batch of approved changes and test and deploy them together, usually within an hour. Batching changes avoids merge race conditions.

In the rare case that we must deploy a change that doesn't meet these requirements, we will document the reason for the exception in the PR itself, and Github will keep a record of who approved the change.

See the Engineering Standards and Expectations document for further details.

### When is a formal change request required?
There are a few cases where we need to use Red Hat's formal Change Enablement process:
* If your work can or will result in a production service becoming unavailable or degraded during service hours.
* If the functionality of the service is changing.
* If you are releasing new software, or a new major version of existing software.
* If you are updating firmware or applying patches to existing infrastructure.

This is not meant to be a complete list.  Most activities that impact production environments require a change request to be filed.

A good rule of thumb: consider whether external stakeholders (customers, other service owners, our business owners) would expect advance notice of the change or planned outage. If so, this is the process to notify them.

### Change Sensitivity or EOQ Sensitivity
Change Sensitivity is a period of time where specific applications or services need to remain stable. Sometimes this could be due to major public events (such as Red Hat Summit), and other times it's related to financial close and reporting, such as End of Quarter Sensitivity (EOQ Sensitivity).

During these periods, if a change will impact production infrastructure, sales, financial close, analysis, and financial reporting, the change will need to be approved by additional reviewers as described in the Change Enablement docs.

These dates are tracked in the Developer Tools Pipeline Temperature document and our weekly Program Calls.

To avoid duplication of evolving documents, refer to the internal document on [Change Enablement](https://source.redhat.com/departments/it/itx/service_management_automation_platforms/change_enablement) for details about the process for Normal Changes (Low Risk, Medium Risk, High Risk), Standard Changes, Latent Changes, and Accelerated Changes.  Also see the [Change Management FAQ](https://source.redhat.com/departments/it/itx/service_management_automation_platforms/change_enablement/change_enablement_wiki/change_management_faq).

## Consequences

Our normal code review process will ensure that all changes are properly tested, reviewed and recorded.

When it's needed, the formal change request process will add an additional paperwork burden and delay the code release to production.  Conversely, failure to invoke the formal process when it's necessary could lead to poor outcomes including outages during peak usage times, developers called in to fix outages on company holidays, failure to meet Service Level Agreements, demo failures, angry customers, or lost revenue.
