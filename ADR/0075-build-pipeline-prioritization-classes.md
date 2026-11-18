---
title: "75. Build Pipeline Prioritization Classes"
status: Proposed
applies_to:
  - build-service
  - integration-service
topics:
  - kueue
  - build-pipelines
  - prioritization
  - vulnerabilities
---

# 75. Build Pipeline Prioritization Classes

Date: 2026-11-18

## Status

Proposed

## Context

The `tekton-kueue` admits most build PipelineRuns through one Kueue ClusterQueue.
Its mutating webhook runs on CREATE, marks the run `Pending`, and evaluates a CEL expression that sets `kueue.x-k8s.io/priority-class` - will be referred to as `the priority expression` in this document.
The priority expression is first-match. The queue uses `BestEffortFIFO` and does not preempt a PipelineRun Kueue has already admitted.
A higher [WorkloadPriorityClass](https://kueue.sigs.k8s.io/docs/concepts/workload_priority_class/) `value` is considered first, and within one value older workloads go first.

The shared classes, highest value first, are:

| Class | value | Match |
| --- | --- | --- |
| `konflux-nudge` | 1100 | build type `nudge` |
| `konflux-release` | 1000 | managed release, and internal-services |
| `konflux-tenant-release` | 900 | tenant release |
| `konflux-post-merge-test` | 800 | test PipelineRun for a push |
| `konflux-post-merge-build` | 700 | push build |
| `konflux-pre-merge-test` | 600 | test PipelineRun for a pull request |
| `konflux-pre-merge-build` | 500 | pull-request or `/retest` build |
| `konflux-default` | 400 | anything else |
| `konflux-mintmaker-triggered` | 350 | tenant build on a `konflux/mintmaker/` branch |
| `konflux-dependency-update` | 300 | PipelineRun in the `mintmaker` namespace |

The MintMaker branch clause is evaluated before the event type, so an automated dependency bump stays below a human build.
Each cluster carries its own copy of the priority expression.
Two clusters add classes in the same list: `kflux-ocp-p01` defines `build-priority-1` through `build-priority-10` at 410–401 and keeps a `kueue.x-k8s.io/priority-class` label that arrived on the PipelineRun, and `kflux-prd-rh03` defines `konflux-hummingbird-automation` at 360.

A post-merge base image, a post-merge product image, and a post-merge utility image all match `konflux-post-merge-build`.
Pull requests collapse the same way at 500. A base image blocks every component that rebuilds from it ([ADR 0029](0029-component-dependencies.md)).
A CVE rebuild has no class above this list.

## Decision

Add the Image class as a second input to the two build clauses.
A CVE push build is one of four classes ranked above the existing list. A critical fix outranks a lower severity, and a base image outranks another image of the same severity.
Tests, releases, nudges, and MintMaker keep the values they have today.

The `tekton-kueue` writes `kueue.x-k8s.io/priority-class` from the priority expression. For a CVE push it reads `build.konflux-ci.dev/cve-max-severity` and `build.konflux-ci.dev/image-class`, which Build Service has written from the Component.

### Standing class

The `Component` CR gains `spec.buildPriorityClass`, a closed enum that defaults to `miscellaneous`:

- `base-image`
- `user-facing`
- `miscellaneous`

Build Service writes that value to the label `build.konflux-ci.dev/image-class` on the component's build PipelineRuns, including the definitions it generates under `.tekton`.

The priority expression reads the label only in the clauses that today assign `konflux-post-merge-build` or `konflux-pre-merge-build`.
An absent label and `miscellaneous` both keep today's class, so an unmarked Component does not move. Post-merge work stays above pre-merge work.
Pre-merge still covers pull requests, GitLab merge requests, and `/retest` and `/ok-to-test` comments.

| Build | Image class | WorkloadPriorityClass | value |
| --- | --- | --- | --- |
| push | `base-image` | `konflux-post-merge-build-base-image` | 760 |
| push | `user-facing` | `konflux-post-merge-build-user-facing` | 730 |
| push | `miscellaneous` or unset | `konflux-post-merge-build` | 700 |
| pre-merge | `base-image` | `konflux-pre-merge-build-base-image` | 560 |
| pre-merge | `user-facing` | `konflux-pre-merge-build-user-facing` | 530 |
| pre-merge | `miscellaneous` or unset | `konflux-pre-merge-build` | 500 |

The post-merge(push) `base-image` class (760) stays below post-merge tests (800). The pre-merge `base-image` class (560) stays below pre-merge tests at 600.
The four new WorkloadPriorityClasses are added to the shared manifest, and each cluster's copy of the expression gains the same branches.

The MintMaker branch match is unchanged. A build on a `konflux/mintmaker/` branch stays `konflux-mintmaker-triggered` at 350 whatever `spec.buildPriorityClass` says.

### CVE rebuilds

A CVE rebuild is a build which results in an image which doesn't contain CVEs that were present on the previously built and pushed image for the given Component. The CVE severity threshold for this will be adjustable.
Any PRs which build such images will be recorded in the Component CR's `status.cveRebuildPullRequests` field, a new object with one list per severity: `critical`, `important`, `moderate`, and `low`.
Each list holds pull request numbers or GitLab/GitHub/Forgejo merge/pull request numbers. A number appears under one key, and that key is the highest severity the pull request fixes.
A repeated number under one key counts once, and order inside a list does not matter. An empty list is omitted.  A GitOps sync does not write status, so a spent number stays spent.
The Konflux UI can provide a way to edit the lists from the Component screen.

The priority expression grants a CVE class only to the push PipelineRun whose `pipelinesascode.tekton.dev/pull-request` appears in one of those lists.
Build Service records that match by writing the annotation `build.konflux-ci.dev/cve-max-severity` before the priority expression runs.
A number present under more than one key uses the higher key. Build Service removes the number from every list before the admission response carries `cve-max-severity`.
It patches `status.cveRebuildPullRequests` and retries when `resourceVersion` conflicts. When that patch cannot succeed, the webhook fails the HTTP request, for example with status 500, so `failurePolicy: Ignore` admits the PipelineRun without the webhook's mutations. An AdmissionReview with `allowed: false` would deny the run.
The number stays for a later push. A push whose number is absent leaves the object unchanged.
Pull-request builds, MintMaker builds, nudges, tests, and releases do not remove the PR number from the list.

Pipelines as Code sets `pipelinesascode.tekton.dev/pull-request` from the event and removes it when the event has no pull request.
On GitHub it records the number when the push commit is associated with a pull request. A GitLab push does not carry the merge request, and that build is not selected until Pipelines as Code records the number.

The `status.cveRebuildPullRequests` field, matched against the number Pipelines as Code recorded, is the only input that selects a CVE class.
Build Service performs that match. It replaces the `build.konflux-ci.dev/cve-max-severity` annotation if it is hardcoded (or otherwise injected) in the submitted pipelineRun definition. On the matching push it writes `cve-max-severity` from the severity key.
The priority expression reads that annotation and `build.konflux-ci.dev/image-class` and sets `kueue.x-k8s.io/priority-class`.
Integration Service copies annotations prefixed with `build.konflux-ci.dev` from the build PipelineRun onto the component Snapshot, so `cve-max-severity` remains after the PipelineRun is pruned.
A `critical` key uses the critical pair. `important`, `moderate`, and `low` share the other pair. A base image outranks another image of the same severity, because dependents cannot pick up that fix until the base exists.

| Severity | Image class | WorkloadPriorityClass | value |
| --- | --- | --- | --- |
| `critical` | `base-image` | `konflux-cve-critical-base-image` | 1500 |
| `critical` | `user-facing`, `miscellaneous`, or unset | `konflux-cve-critical` | 1400 |
| `important`, `moderate`, or `low` | `base-image` | `konflux-cve-base-image` | 1300 |
| `important`, `moderate`, or `low` | `user-facing`, `miscellaneous`, or unset | `konflux-cve` | 1200 |

All four sit above `konflux-nudge` at 1100, and all four are added to the shared WorkloadPriorityClass manifest. An unset image class uses the lower class of its pair. The value 1500 is reached only by an explicit `base-image` whose key is `critical`.

### Finding fixed CVEs

A platform IntegrationTestScenario with context `pull_request` runs after the build Snapshot exists. Its pipeline runs one platform task, and the PipelineRun uses the ServiceAccount `its-pipeline-<component>`.
The scenario resolver stays pointed at the platform task bundle.

The task imports `diffused.differ.VulnerabilityDiffer` from the [`diffused`](https://github.com/konflux-ci/diffused) Python package and calls it the way `compare_component_images` does in [release-service-collectors](https://github.com/konflux-ci/release-service-collectors/blob/main/lib/fixed-cve.py). It passes the two image pullspecs to that class.
The call uses scanner `acs` and scan type `image`, and both images are scanned by the same scanner at that moment. `vulnerabilities_diff` is the set of identifiers present on the previous image and absent on the new one.
The task keeps identifiers that match `CVE-YYYY-NNNN`. That set carries no severity, so the task reads severity from the previous image's ACS scan record and maps it to `critical`, `important`, `moderate`, or `low`.

The task image contains Python 3.9 or newer, the `diffused` package, and `roxctl` on `PATH`. `VulnerabilityDiffer` runs `roxctl image scan` and requires `ROX_ENDPOINT` plus `ROX_API_TOKEN` or `ROX_CONFIG_DIR`.
The published roxctl image supplies `roxctl` alone, so the task image adds Python and `diffused` beside it. The step exchanges the projected ServiceAccount token, audience `rhacs`, with `roxctl central m2m exchange` and points `ROX_CONFIG_DIR` at the resulting config.

A tenant sets `min-severity` with `spec.params` on the IntegrationTestScenario. Integration Service copies those params onto the PipelineRun. The parameter is one of `critical`, `important`, `moderate`, or `low`, and the default is `important`. An identifier counts when its severity is that value or higher.

The task:

- Reads the new image for this component from the Snapshot passed into the pipeline.
- Reads the previous image from that Snapshot spec. When `spec.componentGroup` is set, it uses `lastPromotedImage` for this component and version on the ComponentGroup `status.globalCandidateList` ([ADR 0060](0060-component-groups.md)). When `spec.componentGroup` is empty and `spec.application` is set, it uses `status.lastPromotedImage` on the Component. When both are set, it uses the ComponentGroup. When neither is set, the task fails.
- Treats a missing previous image as a completed diff with an empty list.
- Runs the ACS scan on both the new and the previous image and compares them using the diffused utility.
- Succeeds when the diff completes, including when no CVE counts. It fails when the scan cannot read the new image.

The task outputs the following results:

- `FIXED_CVES`, a JSON array of the CVE identifiers that count. When the array exceeds Tekton's 4096-byte result limit, the task drops trailing identifiers until the value is a valid JSON array within that limit.
- `CVE_MAX_SEVERITY`, one of `critical`, `important`, `moderate`, or `low`, or an empty string when no identifier counts.

Integration Service applies those results while it records the scenario outcome on the Snapshot. It does this only when the scenario resolver points at the platform task bundle. The pull-request number is the one copied onto the test PipelineRun. The scenario is marked passed after the Component patch succeeds.

- A failed task, or a successful task that omits `CVE_MAX_SEVERITY`, leaves `status.cveRebuildPullRequests` unchanged and leaves the scenario unpassed.
- A source branch that starts with `konflux/mintmaker/` leaves the object unchanged. The scenario is still marked passed.
- A successful task with an empty `CVE_MAX_SEVERITY` removes the pull-request number from every key.
- A successful task with a severity places that number under that key and removes it from the other keys.
- The patch contains only `status.cveRebuildPullRequests` and retries when `resourceVersion` conflicts.

The ServiceAccount used for the integration pipeline can `get` Components and ComponentGroups in its namespace.
The task does not patch the Component. The task pod projects a token of audience `rhacs` so the exchange can reach ACS.
The scenario can be set to be `required`, so the git check stays pending until Integration Service marks the scenario passed.

This approach provides three main benefits:

- The build service adds `build.konflux-ci.dev/cve-max-severity` information to build pipelineRuns which allows the prioritizing these builds within Kueue via the priority expression
- Konflux users can immediately see which CVEs (and which overall severities) are remedied by a given PR by checking the results and logs of the new integration test.
- The `build.konflux-ci.dev/cve-max-severity` information also gets propagated to Snapshots. In case of nudging images this will allow the nudging mechanism to make further decisions based on that information.

### Who writes the labels

On PipelineRun CREATE, two mutating webhooks run. Build Service registers one webhook, with `failurePolicy: Ignore`, and a name that sorts before `pipelinerun-kueue-defaulter.tekton-kueue.io`, so `cve-max-severity` is set when `tekton-kueue` evaluates the priority expression.

The Build Service call copies `build.konflux-ci.dev/image-class` from the Component, replacing a value submitted in `.tekton`. It replaces a submitted `build.konflux-ci.dev/cve-max-severity` annotation.
When `pipelinesascode.tekton.dev/pull-request` is in the Component's `status.cveRebuildPullRequests`, it removes the number from every list and writes `cve-max-severity` from that key only after the patch succeeds.
When the patch cannot succeed, the call fails the HTTP request, for example with status 500, so `failurePolicy: Ignore` admits the PipelineRun without the webhook's mutations. An AdmissionReview with `allowed: false` would deny the run.
A successful response clears a priority class that is already `konflux-cve-critical-base-image`, `konflux-cve-critical`, `konflux-cve-base-image`, or `konflux-cve` on every PipelineRun, including a matching push.

`tekton-kueue` then evaluates the priority expression and writes `kueue.x-k8s.io/priority-class`. The CVE clauses sit above the post-merge build clauses and match `cve-max-severity` together with `build.konflux-ci.dev/image-class`.

When the Build Service webhook is unavailable, admission continues. the priority expression uses the image class and `cve-max-severity` submitted with the PipelineRun.

`kflux-ocp-p01` keeps the clause that preserves a Kueue priority label already present on the PipelineRun. That escape hatch stays in front of the image-class clauses and the CVE clauses. The clear runs on a matching push as well as any other, so the clause does not keep a baked-in CVE class ahead of the priority expression.

Within one class, order is unchanged. A multi-arch build is one PipelineRun and one priority. Admitted work is left running. Under `BestEffortFIFO`, a higher-priority build that does not fit the remaining platform quota does not block a lower-priority build that does.

## Alternatives Considered

* **Replacing the event-type classes with the image classes.** Base, user-facing, and miscellaneous would then compete with releases, tests, and nudges, and a base-image pull request would be admitted ahead of a post-merge product build.

* **Having Build Service write `kueue.x-k8s.io/priority-class`.** A write action that happens before the priority expression is overwritten, and a write action after it reimplements the event-type ladder for that one push. The priority expression reads `cve-max-severity` and `image-class`, which Build Service copies from the Component before `tekton-kueue` runs.

* **A boolean `cve-rebuild: "true"`.** The next push of the Component would take the class, including a push that is not the CVE fix. `status.cveRebuildPullRequests` names the pull requests whose push builds take the class.

* **An annotation holding the pull request numbers.** A GitOps sync that manages the annotation would put a spent number back. Status is left alone by that sync, and `patch` on `components/status` does not include the Component spec.

* **A ClusterQueue per image class.** Builds, tests, and releases share a queue so a push test stays ahead of a push build. Separate image-class queues would give up that order.

* **A free-form integer, or reuse of `build-priority-1` through `build-priority-10`.** That band is 401–410, above `konflux-default` and below every pre-merge build. An open integer hands the top of the scale to whoever sets it.

* **A sticky `cve` value on `spec.buildPriorityClass`.** The value would outrank nudges and releases for every later build of that Component.

* **A `min-severity` field on the Component, or a resolver parameter.** The Component field would apply to every scenario that scans the Component, and resolver parameters identify the task bundle. The threshold is the pipeline parameter `min-severity`, default `important`, overridden by `spec.params` on the scenario that runs the scan.

* **A WorkloadPriorityClass for every severity.** `important`, `moderate`, and `low` would each gain a base-image class and a second class. Critical is the severity that outranks the other CVE rebuilds. Those three keys share `konflux-cve-base-image` and `konflux-cve`.

* **Letting the task patch `status.cveRebuildPullRequests`.** The ServiceAccount `its-pipeline-<component>` runs every integration pipeline for the Component, so a status patch on that account would let any scenario arm a pull request, and the task image would carry `kubectl`. Integration Service already writes Component status and already reconciles the finished test PipelineRun before the git check is published.

* **A flat list of pull request numbers.** The severity would live in a second status field, or only on the PipelineRun after admission. The two can drift, and the severity disappears with the number. `status.cveRebuildPullRequests` keeps each number under the highest severity that pull request fixes, and Build Service copies that key to `build.konflux-ci.dev/cve-max-severity` before removing the number.

## Consequences

* Unset Components keep today's priority. Inside one band, `base-image` is admitted before `user-facing`, and both before `miscellaneous`.
* A post-merge utility build still runs before a pre-merge base-image build. A post-merge test still runs before a post-merge base-image build.
* Each listed pull request spends one push build. A critical base image is admitted ahead of every other CVE rebuild. A critical fix is admitted ahead of an important, moderate, or low fix, and a base image is admitted ahead of another image of the same severity. All four CVE classes are admitted ahead of nudges, releases, tests, and ordinary builds. Build Service removes that number from every list and writes `build.konflux-ci.dev/cve-max-severity` only after the patch succeeds. A patch that cannot succeed leaves the number in place, and the webhook fails the HTTP request so `failurePolicy: Ignore` admits the push without `cve-max-severity` from this call. A push that carries a different pull request number, or none, leaves the object in place.
* A pull request number, or a `konflux-cve-critical-base-image`, `konflux-cve-critical`, `konflux-cve-base-image`, or `konflux-cve` priority class baked into `.tekton` does not grant a CVE class. Build Service clears those four classes on every PipelineRun, including a matching push, and replaces a submitted `cve-max-severity` before the priority expression reads it. When that webhook is unavailable, the priority expression uses the submitted annotation.
* The Build Service webhook name has to sort before `pipelinerun-kueue-defaulter.tekton-kueue.io`, so `cve-max-severity` is set when the priority expression runs. A rename that runs `tekton-kueue` first leaves that annotation unset for the priority expression, and the push keeps the ordinary build class.
* A full queue still finishes admitted work before the next build starts.
* A steady stream of `base-image` builds in a band is admitted before `user-facing` and `miscellaneous` builds in that band.
* Any user or service who can patch Component status can add a pull request under a severity key. A `critical` key spends the push in `konflux-cve-critical`, or in `konflux-cve-critical-base-image` when the standing class is `base-image`. Any other key spends it in `konflux-cve`, or in `konflux-cve-base-image` when the standing class is `base-image`. `build.konflux-ci.dev/cve-max-severity` is set to that key. The integration pipeline ServiceAccount cannot patch the Component. Editing the Component spec does not arm a pull request.
* A GitOps sync of the Component does not restore a spent pull request number.
* The new pull-request scenario can be set as required. An ACS outage fails the task, and the git check stays pending until Integration Service records a successful scan.
* `min-severity` decides which disappeared CVEs arm the pull request. The default is `important` and above. A tenant overrides it through `spec.params` on the IntegrationTestScenario.
* The matching push carries `build.konflux-ci.dev/cve-max-severity`. Integration Service copies `build.konflux-ci.dev` annotations from the build PipelineRun onto the component Snapshot.
* Every cluster's copy of the `tekton-kueue` priority expression is updated with the shared classes. User documentation covers the three standing values, the default, and `status.cveRebuildPullRequests`. The Konflux UI can expose the severity lists on the Component screen.
