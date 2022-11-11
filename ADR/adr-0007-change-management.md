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

Incremental code changes that are fully tested by automated tests, which will not cause an outage or a significant change to functionality, will follow the normal code review process in their respective code repositories. To deploy such a change to staging and production, there will be a pull request opened against the infra-deployments repo or the App Interface repo with the requested change.  Then the change must follow our normal code review process.

### Normal code review process

A developer or our deployment automation will open a pull request with the requested change, against the affected Github repository.  The CI test automation on the repository must run, and tests must pass.  At least one other developer with merge permissions on the repository must approve the change.

### When is a change request required?
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

TBD
