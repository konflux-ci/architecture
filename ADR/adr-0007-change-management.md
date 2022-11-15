# 1. Record architecture decisions

Date: 2016-02-12

## Status

Accepted

## Approvers

* Ann Marie Fred
* Gorkem Erkan

## Reviewers

## Context

Red Hat's ESS requirment SEC-CHG-REQ-1 (Change Management) states that "All applications/systems/platforms/services must follow Change Management process and procedures, as applicable / appropriate." Change management is important in order to ensure no unauthorized changes are made to systems or applications, in order to help prevent the purposeful or accidental introduction of security vulnerabilities and an increase in threat attack surface.

Because App Studio is using a continuous delivery model, we need to ensure that we use lightweight change management processes when it's appropriate, and follow a more intensive change management process when needed.

This change management process will go into effect when App Studio goes into a 24x7 support mode; this will likely correspond to its GA date.

## Decision

Incremental code changes that are fully tested by automated tests, which will not cause an outage or a significant change to functionality, will follow the normal code review process in their respective code repositories. 

To deploy an infrastructure change or a new version of software to staging and production, a developer will make the required change to the infra-deployments repo or the App Interface repo.  Then the change must follow our normal code review process.

### Normal code review process

While a ticket (Jira ticket or Github issue) is In Progress, a developer will make their code changes and write automated tests in a Git feature branch.  The developer will raise a Github Pull Request (PR) when they need other team members to review their work. This review could be for work in progress or when the developer feels the work is completed. For a PR that reflects completed work, the ticket should be put into the Review stage to indicate that active development is complete.

In Github, if the developer wants a code review but feels that their work is not ready to be deployed yet, they will add the "do-not-merge/work-in-progress" label to the PR. We also recommend adding "WIP" to the pull request title.

The developer should choose one or two reviewers for their PR and add them to the PR directly. A PR without any reviewers assigned might never be reviewed. Reviewers should be chosen based on their background and familiarity with the code under review. It is also sometimes worthwhile to use a PR review to help another developer get up to speed with some code.

If you have been asked to review another developer’s PR, it’s good practice to decide if you can fit that review into your current workload. Timely PR review helps keep our velocity high, and if it might take more than a couple of days for you to review the code, contact the PR author and let them know they might need to depend on another person.

As a reviewer, you should move the review along by testing the PR yourself, and providing comments in Github for suggested changes. Typically we want to focus on potential security or privacy issues, test automation, maintainability factors and overall correctness of the code. Stylistic or preference-based changes should not be a focus of the review.

We also require that all of our repositories be instrumented with CI test automation that runs when a PR is raised, and after each new commit. All CI checks must pass before performing a Merge to the main branch as this updates the staging environment and makes the code available for deployment into production.

When the review is completed and tests have passed, the approver should Approve the PR in GitHub and the PR author will then Merge the code. 

For changes to the infra-deployments repo, we recommend that the PR author add the "lgtm" (looks good to me) label to the PR rather than clicking on the Merge button. This will trigger the Prow/Tide deployment automation to create a batch of approved changes and test and deploy them together, usually within an hour. Batching changes likes this avoids merge race conditions.

The ticket should be set to Closed once the code is released downstream or deployed to production.

### When is a formal change request required?
There are a few cases where we need to use Red Hat's formal Change Enablement process:
* If your work can or will result in a production service becoming unavailable or degraded during service hours.
* If the functionality of the service is changing.
* If you are releasing new software, or a new major version of existing software.
* If you are updating firmware or applying patches to existing infrastructure.

This is not meant to be a complete list.  Most activities that impact production environments require a change request to be filed.  

### Change Sensitivity or EOQ Sensitivity
Change Sensitivity is a period of time where specific applications or services need to remain stable. Sometimes this could be to major public events (such as Red Hat Summit), and other times it's related to financial close and reporting, such as End of Quarter Sensitivity (EOQ Sensitivity). 

During these periods, which are tracked in the Pipeline Temperature status in the App Studio Program Calls, if a change will impact production infrastructure, sales, financial close, analysis, and financial reporting, the change will need to be approved by additional reviewers as described in the Change Enablement docs. 

To avoid duplication of evolving documents, refer to the internal document on [Change Enablement](https://source.redhat.com/departments/it/itx/service_management_automation_platforms/change_enablement) for details about the process for Normal Changes (Low Risk, Medium Risk, High Risk), Standard Changes, Latent Changes, and Accelerated Changes.  Also see the [Change Management FAQ](https://source.redhat.com/departments/it/itx/service_management_automation_platforms/change_enablement/change_enablement_wiki/change_management_faq).

## Consequences

Our normal code review process will ensure that all changes are properly tested, reviewed and recorded.

When it's needed, the formal change request process will add additional paperwork burden and delay the code release to production.  Conversely, failure to invoke the formal process when it's necessary could lead to poor outcomes including outages during peak usage times, developers called in to fix outages on company holidays, failure to meet Service Level Agreements, demo failures, angry customers, or lost revenue.
