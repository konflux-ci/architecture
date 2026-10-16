---
title: "72. Include Container health index check before release"
status: Proposed
applies_to:
  - integration-service
  - enterprise-contract
  - release-service
topics:
  - vulnerability-scanning
  - container-health-index
  - release-gating
---

# 72. Include Container health index check before release

Date: 2026-10-16

## Status

Proposed

## Context

90.9% of Red Hat container images built in Konflux have vulnerability scanning disabled due to broken legacy functionality. A recent audit found that 22 of 135 container images (16.3%) shipped to customers with known Critical or Important vulnerabilities that had fixes already available. This is a direct security and reputational risk. Manual oversight cannot scale. An automated fix is required.
Important note is that the behavior is expected to be present in two places: integration service, collectors pipeline.
Those differ in many ways from each other, meaning the task implementation will be individual, we can however make an agreement on standardizing things like task-names and result-names.
This ADR is a Phase #1 - No gating(applies to CHI-score-based release gating only, not infrastructure availability issues), task creation, dates evaluation, data representation, policies creation.

## Decision

### Integration-service side

The general idea is to provide a task that is capable of fetching the critical and important vulnerability RHSA, then providing the information about the safe dates(whether it is past due or within it).
Important: Task is optional, it is not requested to be run before release.
The task should be located within the build-definitions pipeline after ACS scan.
ACS scan needs to provide both types of RHSA in a format suitable for next processing.

**Format suggestion**:

```json
{"CRITICAL": ["RHSA-2026:58936","RHSA-2026:52036", "RHSA-2025:58936"],
"IMPORTANT": ["RHSA-2026:55440", "RHSA-2026:55230", "RHSA-2026:55964","RHSA-YYYY:NNNNN"]}
```

**Naming suggestion**:

tekton result: **ACS_RHSAS**

This JSON format is easy to process and interprets data well.
Down below you can see the flowchart representing the proposed solution.

![](../diagrams/ADR-0072/flowchart.png)

The case might occur where ACS is not available, unable to provide scan output. In this case, we want ACS scan not to fail. Instead provide an error message to the logs and create tekton result **ACS_RHSAS** with following format:

```json
{"ACS_UNREACHABLE":true}
```

calculate-safe-dates will then check for the "ACS_UNREACHABLE" fields first from **ACS_RHSAS**, in case they are detected, provide an error message informing about such fact. calculate-safe-dates must forward {ACS_UNREACHABLE:true} as its SAFE_DATES result when ACS is unreachable.
Retries for the pipeline will be handled in [KONFLUX-12121](https://redhat.atlassian.net/browse/KONFLUX-12121).


New task **calculate-safe-dates** is expected to be located within a build-definitions pipeline. It receives data (RHSA JSON) from ACS scan, then fetches all the corresponding RHSA release_dates for each one. It then calculates dates on following logic:

**critical_safe_date** = RHSA released_on + 30 days
**important_safe_date** = RHSA released_on + 90 days

The Expected output from this task will be in the tekton **result** data type named **SAFE_DATES**.

**Format suggestion**:

```json
{"CRITICAL":[{"RHSA-2026:58936":{"released_on":"2026-08-03T14:37:22Z", "safe_until": "2026-09-02T14:37:22Z", "block": true} 
 },{"RHSA-2026:52036":{"released_on":"2026-10-03T14:37:22Z", "safe_until": "2026-11-02T14:37:22Z", "block": false}}],

"IMPORTANT":[{"RHSA-2026:55440": {"released_on":"2026-10-01T14:37:22Z", "safe_until": "2026-12-30T14:37:22Z", "block": false}}]}
```

Task is also capable of providing estimated CHI for users. There are currently three grades of CHI:
**PASS**, **WARN**, **BLOCK**. 
Include information about estimated CHI based on those grades.
Grades description are following:

- **PASS**: This image does not contain known unapplied errata that fix Critical or Important flaws.

- **WARN**: This image may be missing Critical or Important security errata, provided no missing Critical flaw is older than 30 days and no missing Important flaw is older than 90 days.

- **BLOCK**: This image is missing Critical flaws older than 30 days or Important flaws older than 90 days

Task will provide CHI estimation following way:
- Provide info message as the last part of the task/step:
**ESTIMATED CONTAINER HEALTH INDEX: PASS/WARN/BLOCK** 
Estimation in the task/step plays informative role for the user, final evaluation is done by conforma, however the evaluation logic is the same as for the task/step making the info message relevant.

### Collectors-pipeline side

There is a collectors specific pipelinerun definition that runs ACS scan inside **run-collector**, in the cve collector. 

The idea remains the same as for the integration-service one, with one big difference > Collectors pipeline will run(**mandatory**) for each user before release, integration-service(**optional**) is not required for release.

The case might occur where ACS is not available, unable to provide scan output. In this case, we want collectors pipeline to fail.
Retries for the pipeline will be handled in [KONFLUX-12121](https://redhat.atlassian.net/browse/KONFLUX-12121).

The implementation approach will be following:
- New step(instead of task) will be added in collectors pipeline, right after **run-collectors** step.
- Outputs will be stored in results as described in **integration-service** side
- Safe date evaluation will be covered in a new step, providing **SAFE_DATES** result

Logic will be the same as for the flowchart above with the location difference, instead of build pipeline, new step will be located within collectors pipeline.


### Conforma side

The key role is to evaluate whether to gate or not. Conforma part in this comes once the task is present and provides all the required information. 
Expecting following format for the **SAFE_DATES** result:

```json
{"CRITICAL":[{"RHSA-2026:58936":{"released_on":"2026-08-03T14:37:22Z", "safe_until": "2026-09-02T14:37:22Z", "block": true} 
 },{"RHSA-2026:52036":{"released_on":"2026-10-03T14:37:22Z", "safe_until": "2026-11-02T14:37:22Z", "block": false}}],

"IMPORTANT":[{"RHSA-2026:55440": {"released_on":"2026-10-01T14:37:22Z", "safe_until": "2026-12-30T14:37:22Z", "block": false}}]}
```
#### Required logic development
Conforma checks for individual RHSAids values and blocks in case the RHSA is past the date range or ACS_UNREACHABLE value in **SAFE_DATES** is detected. Conforma violation(gating) should reflect the reason behind blocking the release(whether RHSA is past date or ACS_UNREACHABLE occured). The situation might occur that during the time of the scan(on integration and collectors side) the RHSA is within a time range, conforma runs afterwards making the date not alligned with current time. This means we require conforma to run the same logic for date evaluation as for previous (integration, collectors) services to make the check most precise. 
This does not mean that previous calculations are not valid, it only means we want to provide the most accurate check.
Crutial data are stored under **released_on** key against wthich should run the calculation. Block field can be ignored by conforma.
Conforma evaluation should consume SAFE_DATES from both integration-service and collectors pipeline, but gating will be enabled only for collectors pipeline (phase #2).

In case conforma recieves following content in **SAFE_DATES** tekton result:

```json
{"ACS_UNREACHABLE":true}
```
It must block the release(raise violation).

Gating decision is made according to the grades described in previous section and the grade itself is computed downstream.
Conforma will create CHI-score-based gating logic (PASS/WARN/BLOCK evaluation) but will not enable it in Phase #1.

Gating that should happen from conforma in phase #1 is only in case that ACS is unreachable by detecting ACS_UNREACHABLE.


## Consequences

### Positive

- Clear security report at built time
- Informative benefit letting users know if their image release is going to be blocked beforehand

### Negative

- New task to maintain, release
- Upstream inaccessibility to the ACS scan

## References

- [KONFLUX-15693](https://redhat.atlassian.net/browse/KONFLUX-15693) —
  feature Enforce CHI-like rules for container release pipelines
- [STONEINTG-1868](https://issues.redhat.com/browse/STONEINTG-1868) —
  epic Support enforcing CHI based CVE Release Gating
