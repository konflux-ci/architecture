---
date: 2023-03-06T00:00:00Z
title: Partner Tasks in Build/Test Pipelines
number: 21
---
# Partner Tasks in Build/Test Pipelines

## Status

Accepted

## Context

* As a Red Hat Partner, I would like to offer our service's capability as a Tekton Task that would be executed in a user's build/test Pipeline on StoneSoup.
* As a StoneSoup maintainer, I would like to provide a way to ensure the above Tekton Task is validated and approved for use in the build/test Pipeline on StoneSoup.

Associated business ask
https://issues.redhat.com/browse/STONE-549

## Decision

### Plumbing

1. Setup a new Git high-level directory in https://github.com/redhat-appstudio/build-definitions for partners to contribute Tasks to.
2. Define a directory structure for Task submissions as manifests in the yaml format.
3. Configure a CI job that validates the Tasks upon opening of a pull request.
4. Optionally, configure a CI job that generates an OCI artifact consumable in a Tekton Pipeline.

### Day-to-day operations

#### Adding/Updating a Task

1. Partner opens a PR with a new/updated Task.
2. CI tests do the due diligence on the changes proposed in the PR. Success/Failures are reported in a way that the PR author can take reasonable
action to resolve the issue.
3. Upon approval from the Build/Test team, the changes are merged.

#### Revoking a Task
1. Open a PR to delete the Task.
2. The Build/Test team reviews the PR and merges it.
3. The Build/Test team updates the https://github.com/redhat-appstudio/build-definitions to remove references to the Task's OCI image whenever it is reasonable to do so.

#### Definition of a valid Task

The due diligence is a transparent-to-the-Task-contributor CI job that's running on the repository that validates the Task before we merge it in.

Please see the following as prior art:
1. See CI Results in https://github.com/tektoncd/catalog/
2. https://github.com/k8s-operatorhub/community-operators/
2. https://github.com/openshift-helm-charts/charts

A non-exhaustive list of checks that would be run on a Task is:

* Linting
* Scanning
* No privilege escalation / or no requirements that need unreasonable privileges.
* Should be integratabtle into the build pipeline, ie, works with the inputs/outputs we have today.
* Should work with reasonable defaults.
* Should be skip-able if credentials/tokens are missing.
* *TBD*

## Out-of-scope

* Supporting validation of Tasks inside Stonesoup before submission would be out-of-scope. However, partners should be able to import a
Component into StoneSoup, customize their Pipeline definition in the .tekton directory and have the changes validated in a PipelineRun execution in StoneSoup. To be able to be productive with this flow, they'd need to be able to do https://github.com/redhat-appstudio/architecture/pull/64 .

## Alternatives

* ~Use the github.com/redhat-appstudio/build-definitions for Task submissions by partners : This is being considered in the short-term, either way, the day-to-day operations will not quite change~ - this has been promoted to be the primary design.
* Use Tekton Hub for host Tasks : Tekton Hub is being deprecated.


## Consequences

* We have a mechanism to take in Tekton Tasks from Partners with due diligence.
* We should also be able to take in Tekton Tasks from Red Hat teams with the same level of validation/diligence that Red Hat Partners would have to go through.
* We do build up a little tech-debt because this process needs to be merged with the official Red Hat certification process in the future.
