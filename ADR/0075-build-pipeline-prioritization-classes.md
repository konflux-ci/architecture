---
title: "75. Build Pipeline Prioritization Classes"
status: Proposed
applies_to:
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

The shared classes, highest value first, are below. The values in this table are an example. An installation sets each value to match its own Kueue classes.

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
A cluster may add its own classes to that copy. This ADR does not place shared classes in a gap a cluster already uses for a local class.
An expression may also keep a `kueue.x-k8s.io/priority-class` label that arrived on the PipelineRun, and that clause is evaluated before the event type.

A post-merge base image, a post-merge product image, and a post-merge utility image all match `konflux-post-merge-build`.
Pull requests collapse the same way onto `konflux-pre-merge-build`. A base image blocks every component that rebuilds from it ([ADR 0029](0029-component-dependencies.md)).
Non-container builds share these classes ([ADR 0063](0063-generalized-build-release-pipelines.md)).
A PipelineRun that Pipelines as Code did not create matches none of the build rows and is admitted as `konflux-default`.
A CVE rebuild has no class above this list.

## Decision

Integration Service's build pipeline controller sets the class of a component build. The same rule admits a Pipelines as Code component build, and a component build Pipelines as Code did not create when `build.konflux-ci.dev/build-event` is `push` or `pull-request`.
It covers a build whose artifact is an RPM, a Python wheel, a Maven package, or another non-container output ([ADR 0063](0063-generalized-build-release-pipelines.md)).

A post-merge CVE build is one of four classes ranked above the existing list. A pre-merge CVE build is one of four classes above other pre-merge builds and below post-merge work.
A critical fix outranks a lower severity, and a root parent outranks another Component of the same severity.
Tests, releases, nudges, and MintMaker keep the classes they have today.

An installation configures the numeric value of each WorkloadPriorityClass so the values match the Kueue classes it already runs. The class names and the order among them stay as this ADR describes. The numbers in the tables are one example of that order. An installation does not place one of these classes in a gap it already uses for a local class.

The priority expression assigns the floor of a component build's band and leaves tests, releases, nudges, and MintMaker on the classes they have today.
The build pipeline controller is part of Integration Service. It reads the namespace [`NudgeConfig`](0067-nudging-relationship-singleton-crd.md) and the metadata already on the build PipelineRun, and it sets `kueue.x-k8s.io/priority-class`. A tenant cannot set a priority field. The standing class follows the component's place in that `NudgeConfig`. Every LocalQueue used for these builds points at the one ClusterQueue, and Kueue orders that queue by priority.

### Standing class

The build pipeline controller reads the namespace `NudgeConfig` named `nudge-config` for the Component named by `appstudio.openshift.io/component`, or by `konflux-ci.dev/component` ([ADR 0067](0067-nudging-relationship-singleton-crd.md)).
It sets `kueue.x-k8s.io/priority-class` on a Pipelines as Code component build, and on a component build Pipelines as Code did not create when `build.konflux-ci.dev/build-event` is `push` or `pull-request`.
A nudge, a test, and a release keep the class the priority expression assigned when they also carry a component reference.

The place of the component in `spec.nudges` selects the row:

- A root parent is named by at least one `spec.nudges[].from` and by no `spec.nudges[].to`. Its build is `high`.
- A branch parent is named by at least one `from` and at least one `to`. Its build is `normal`.
- A branch end is named by at least one `to` and by no `from`. Its build is `background`.
- A component named by no entry, and a namespace with no `NudgeConfig`, is `normal`.

`normal` is today's class. It is not the catch-all class `konflux-default`. `background` waits behind an ordinary build of the same event.

The priority expression assigns the floor of the table below. The nudge, release, and test matches are evaluated before that floor. The MintMaker branch match is evaluated after those matches and before the floor. The controller raises a push or pre-merge component build from that floor.
A push component build starts at `konflux-post-merge-build-background` (640 in the example). A pre-merge component build starts at `konflux-default` (400 in the example). A root parent is raised to the `high` row. A branch parent, and a component in no nudge, are raised to today's class. A branch end stays at the floor. Post-merge work stays above pre-merge work.
Pre-merge still covers pull requests, GitLab merge requests, and `/retest` and `/ok-to-test` comments.
A component build with no Pipelines as Code event type starts at the post-merge floor when `build.konflux-ci.dev/build-event` is `push`, and at the pre-merge floor when that value is `pull-request`. An absent value, or any other value, uses neither row and stays `konflux-default`.

The values in this table are an example.

| Build | Standing class | WorkloadPriorityClass | value |
| --- | --- | --- | --- |
| push | `high` | `konflux-post-merge-build-high` | 760 |
| push | `normal` | `konflux-post-merge-build` | 700 |
| push | `background` | `konflux-post-merge-build-background` | 640 |
| pre-merge | `high` | `konflux-pre-merge-build-high` | 560 |
| pre-merge | `normal` | `konflux-pre-merge-build` | 500 |
| pre-merge | `background` | `konflux-default` | 400 |

The post-merge `high` class stays below post-merge tests. The post-merge `background` class stays above pre-merge tests. The pre-merge `high` class stays below pre-merge tests. Pre-merge `background` uses `konflux-default`, below `konflux-pre-merge-build`. No shared class is added above `konflux-default` and below that build.
`normal` reuses `konflux-post-merge-build` and `konflux-pre-merge-build`. Pre-merge `background` reuses `konflux-default`. One WorkloadPriorityClass has one value, so `konflux-default` stays the catch-all and is not the middle of either band. The post-merge `high`, post-merge `background`, and pre-merge `high` WorkloadPriorityClasses are added to the shared manifest with the example values, which an installation may change. The expression names the post-merge floor and the pre-merge floor. The controller sets the class in the table for a push or pre-merge component build, including the floor when the component is a branch end. `high` is a root parent, `normal` is a branch parent or a component in no nudge, and `background` is a branch end. The `konflux-` prefix stays on the WorkloadPriorityClass name.

The MintMaker branch match stays behind the nudge, release, and test matches, and ahead of the component floor. A build whose `pipelinesascode.tekton.dev/source-branch` starts with `konflux/mintmaker/` stays `konflux-mintmaker-triggered`, including when that component is a root parent. In the example that class is 350. The expression assigns that class, and the controller leaves it in place.
That branch does not add a pull request number, does not remove one, and does not receive `cve-max-severity` from the match.

### CVE rebuilds

A CVE rebuild is a component build of a pull request whose commit subject Integration Service's build pipeline controller has recorded on the Component.
The build may be the git push of that pull request, or a later rebuild that names the same number.
The record is the same for a container image and for any other Component Build Artifact.

Pipelines as Code copies the commit subject, through the first blank line, to the annotation `pipelinesascode.tekton.dev/sha-title`.
On a pre-merge component build, the build pipeline controller reads the start of that annotation.
A subject that starts with `fix(security-critical):` records the pull request under `critical`.
A subject that starts with `fix(security):` records it under `important`. The match is case-insensitive, and `security-critical` is tested first. A `!` immediately before the colon still matches and does not change the key. The description after the colon is ignored.

The number the build pipeline controller records is `pipelinesascode.tekton.dev/pull-request`. It adds that number only when the number is absent. A number already under a key stays on that key.
A `pipelinesascode.tekton.dev/source-branch` that starts with `konflux/mintmaker/` is not recorded, is not removed, and does not receive `cve-max-severity` from the match. A post-merge build does not add a number from the subject. `build.konflux-ci.dev/rebuild-pull-request` does not add a number.

The recorded pull request is stored in the Component CR's `status.cveRebuildPullRequests` field, a new object with one list per severity: `critical`, `important`, `moderate`, and `low`.
Each list holds pull request numbers or GitLab/GitHub/Forgejo merge/pull request numbers. A number should appear under at most one key, and that key is the severity recorded for the pull request.
A repeated number under one key counts once, and order inside a list does not matter. An empty list is omitted. A GitOps sync does not write status, so a spent number stays spent.
The Konflux UI can provide a way to edit the lists from the Component screen. The subject writes `critical` or `important`. The UI may place a number under `moderate` or `low`, and those keys share the class with `important`.

The build pipeline controller sets a CVE class on the component build whose pull request number appears in one of those lists.
It writes `build.konflux-ci.dev/cve-max-severity` from the severity key. The priority expression does not read that annotation.
A number present under more than one key uses the higher key. On a post-merge build, the controller removes the number from every list and sets the CVE class only after that patch succeeds.
On a pre-merge build whose subject matches, the controller adds the number when it is absent and sets the CVE class only after that patch succeeds.
It patches `status.cveRebuildPullRequests` and retries when `resourceVersion` conflicts. When either patch cannot succeed, the controller sets the standing class, leaves the CVE class unset, and reconciles again.
A post-merge patch that cannot succeed leaves the number in place. A pre-merge patch that cannot succeed leaves the number unrecorded. A build whose subject does not match, and whose number is absent, leaves the object unchanged.
A pre-merge build whose number is in the lists leaves every list unchanged. The subject is already on the PipelineRun. The first pre-merge build whose subject matches records the number when that add succeeds. That build takes the pre-merge CVE class when the controller writes before Kueue reserves quota, as does a later commit on the pull request, a `/retest`, and an `/ok-to-test` while the number remains, including a commit whose subject does not match. A run admitted before that write keeps the floor, and the recorded number selects the class of a later PipelineRun.
Pull-request builds, a build whose `pipelinesascode.tekton.dev/source-branch` starts with `konflux/mintmaker/` including a push, nudges, tests, and releases do not remove the PR number from the list.

Pipelines as Code already sets `pipelinesascode.tekton.dev/pull-request` from the event and removes it when the event has no pull request. When that label is set, it is the number the controller matches.
When it is absent, the controller matches `build.konflux-ci.dev/rebuild-pull-request` on a component build. A submitted `cve-max-severity` does not select a class.
On GitHub, Pipelines as Code sets the pull-request label when the push commit is associated with a pull request. A GitLab push does not carry the merge request, and that build is not selected until Pipelines as Code sets the label.
A rebuild that is not a git event is selected when `rebuild-pull-request` names a number still in the lists and `build.konflux-ci.dev/build-event` is `push` or `pull-request`.

`status.cveRebuildPullRequests`, matched against that number, is the only input that selects a CVE class.
The build pipeline controller performs that match. It replaces a submitted `build.konflux-ci.dev/cve-max-severity` annotation and replaces a `kueue.x-k8s.io/priority-class` that arrived on the PipelineRun. A `pipelinesascode.tekton.dev/source-branch` that starts with `konflux/mintmaker/` keeps the expression's class. On the matching component build it writes `cve-max-severity` from the severity key.
The post-merge CVE class applies to a Pipelines as Code push, and to a component build with no Pipelines as Code event type whose `build.konflux-ci.dev/build-event` is `push`. The pre-merge CVE class applies to a pre-merge component build, including one whose `build-event` is `pull-request`.
Integration Service copies annotations prefixed with `build.konflux-ci.dev` from the build PipelineRun onto the component Snapshot, so `cve-max-severity` remains after the PipelineRun is pruned.
A `critical` key uses the critical pair. `important`, `moderate`, and `low` share the other pair. A root parent outranks another Component of the same severity, because the components it nudges cannot pick up that fix until that build exists.

A post-merge CVE build uses the classes above the existing list. The values in this table are an example.

| Severity | Standing class | WorkloadPriorityClass | value |
| --- | --- | --- | --- |
| `critical` | `high` | `konflux-cve-critical-high` | 1500 |
| `critical` | `normal` or `background` | `konflux-cve-critical` | 1400 |
| `important`, `moderate`, or `low` | `high` | `konflux-cve-high` | 1300 |
| `important`, `moderate`, or `low` | `normal` or `background` | `konflux-cve` | 1200 |

All four sit above `konflux-nudge`. In the example that class is 1100. A component that is not a root parent uses the lower class of its pair. The highest post-merge CVE class is reached only by a root parent whose key is `critical`.

A pre-merge CVE build uses a second set. These stay below pre-merge tests and above the pre-merge `high` build, so post-merge work stays ahead of an open security pull request. The values in this table are an example.

| Severity | Standing class | WorkloadPriorityClass | value |
| --- | --- | --- | --- |
| `critical` | `high` | `konflux-pre-merge-cve-critical-high` | 595 |
| `critical` | `normal` or `background` | `konflux-pre-merge-cve-critical` | 585 |
| `important`, `moderate`, or `low` | `high` | `konflux-pre-merge-cve-high` | 575 |
| `important`, `moderate`, or `low` | `normal` or `background` | `konflux-pre-merge-cve` | 565 |

All eight classes are added to the shared WorkloadPriorityClass manifest with the example values. An installation may set different values that keep this order.

### Who sets the class

On PipelineRun CREATE, the `tekton-kueue` webhook marks the run `Pending` and evaluates the priority expression.
The expression is first-match. A clause that keeps an arrived `kueue.x-k8s.io/priority-class` is evaluated first. A label that names one of the eight CVE classes does not satisfy that clause, and the later clauses run.
The nudge, release, and test matches come next, and those builds keep the classes they have today.
The MintMaker branch match comes after those matches. A build whose `pipelinesascode.tekton.dev/source-branch` starts with `konflux/mintmaker/` stays `konflux-mintmaker-triggered`. In the example that class is 350.
The component floor comes after that match. A Pipelines as Code push that carries `appstudio.openshift.io/component` or `konflux-ci.dev/component` starts as `konflux-post-merge-build-background`. In the example that class is 640.
A Pipelines as Code pre-merge build that carries either reference starts as `konflux-default`. In the example that class is 400. A component build with no Pipelines as Code event type starts at that post-merge floor when `build.konflux-ci.dev/build-event` is `push`, and at that pre-merge floor when the value is `pull-request`.
Any other value, including an absent one, stays `konflux-default`. A build with no component reference keeps today's class.

Integration Service's build pipeline controller reconciles a build PipelineRun. It sets the class before the gate that skips Snapshot creation for a new-model build.
It leaves a nudge, a test, and a release on the class the expression assigned, including when that PipelineRun carries a component reference.
A `pipelinesascode.tekton.dev/source-branch` that starts with `konflux/mintmaker/` keeps `konflux-mintmaker-triggered`.
Any other component build on neither the push row nor the pre-merge row keeps `konflux-default`. The controller writes that class and does not assign `high`, `normal`, or `background`.
On a push or pre-merge component build, the controller reads the namespace `NudgeConfig` named `nudge-config`. A missing `NudgeConfig` means the component is in no nudge. It assigns `high` to a root parent, `normal` to a branch parent or a component in no nudge, and `background` to a branch end. When that read fails, the controller leaves the floor in place, leaves the CVE class unset, and reconciles again.
It reads `status.cveRebuildPullRequests` on the Component after that read has produced a row. It reads `pipelinesascode.tekton.dev/event-type`, `pipelinesascode.tekton.dev/source-branch`, `build.konflux-ci.dev/build-event`, `pipelinesascode.tekton.dev/sha-title`, `pipelinesascode.tekton.dev/pull-request`, and `build.konflux-ci.dev/rebuild-pull-request` on the PipelineRun.
When the Component read fails, the controller writes the standing class, leaves the CVE class unset, and reconciles again.
When the Component read succeeds, the controller replaces `kueue.x-k8s.io/priority-class` with the standing class or the CVE class. It sets the CVE class when that write happens before Kueue reserves quota. Kueue copies a changed label onto the Workload.
A Workload that has not reserved quota is ordered by the new value. A Workload that has already reserved quota keeps its slot.

On a pre-merge component build, the controller applies the same subject match to `pipelinesascode.tekton.dev/sha-title`.
The match is case-insensitive, `security-critical` is tested before `security`, and a `!` immediately before the colon still matches. `fix(security-critical):` adds `pipelinesascode.tekton.dev/pull-request` under `critical` when that number is absent. `fix(security):` adds it under `important`.
The controller sets the pre-merge CVE class only after that add succeeds. When the add cannot succeed, the controller sets the standing class, leaves the number unrecorded, and reconciles again.
A `pipelinesascode.tekton.dev/source-branch` that starts with `konflux/mintmaker/` adds nothing, removes nothing, and does not receive `cve-max-severity` from this match. The controller leaves that build on `konflux-mintmaker-triggered`.
A post-merge build adds nothing from the subject. The patch retries when `resourceVersion` conflicts.
When the matched pull request number is in the Component's `status.cveRebuildPullRequests`, a post-merge build removes the number from every list and writes `cve-max-severity` from that key only after the patch succeeds. A pre-merge build whose number is already in the lists writes `cve-max-severity` from that key and does not remove the number.
The matched number is `pipelinesascode.tekton.dev/pull-request` when that label is set, and `build.konflux-ci.dev/rebuild-pull-request` when it is not. A component build with no Pipelines as Code event type is post-merge only when `build.konflux-ci.dev/build-event` is `push`, and pre-merge only when that value is `pull-request`. Any other value, including an absent one, leaves the lists unchanged and does not receive `cve-max-severity` from this match.
When the post-merge patch cannot succeed, the controller sets the standing class, leaves the number in place, leaves `cve-max-severity` unset, and reconciles again. The run stays in the queue at the standing class.

While the controller has not written, Kueue uses the expression's class. For a push or pre-merge component build the controller will raise, that class is the floor, so the run does not take a slot above its standing class. When the controller is unavailable, that build is admitted at the floor. A nudge, a test, a release, and a MintMaker branch keep the expression's class.

Within one class, order is unchanged. A multi-arch build is one PipelineRun and one priority. Admitted work is left running. Under `BestEffortFIFO`, a higher-priority build that does not fit the remaining platform quota does not block a lower-priority build that does.

## Alternatives Considered

* **A `user-facing` value between `high` and `normal`.** The center of each band is the existing build class. A product build and an ordinary build share `normal`.

* **Naming the standing value an image class, or calling the higher value `base`.** The queue admits every build PipelineRun, including the non-container artifacts in [ADR 0063](0063-generalized-build-release-pipelines.md). `high` is a root parent, named by `spec.nudges[].from` and not by `to`, whether or not that build is a container image.

* **Keeping `spec.buildPriorityClass`.** The LocalQueues share one ClusterQueue, so a tenant-chosen `high` would be admitted ahead of other tenants. `background` only moves that tenant's build behind an ordinary build on the same shared queue. The nudge graph selects the row. A root parent is still admitted ahead of other tenants' `normal` builds in that band. The edge that selects it also nudges `spec.nudges[].to`.

* **Having the priority expression choose the standing class and the CVE class.** The expression would read annotations written on CREATE, and a webhook would sit on the admission path of every PipelineRun to supply them. Integration Service's build pipeline controller already reconciles the build PipelineRun, the Component, and the namespace `NudgeConfig`. It sets the class from those objects. Kueue applies that value when the write happens before quota is reserved.

* **Having Build Service set the class.** Build Service would watch build PipelineRuns, or take git events that Pipelines as Code already handles. Integration Service's build pipeline controller reads the PipelineRun Pipelines as Code has already annotated, and the Component it already loads.

* **Treating a missing `build.konflux-ci.dev/build-event` as a push.** A PipelineRun Pipelines as Code did not create would spend a listed pull request whenever it named the number. The push row requires `push`, and the pre-merge row requires `pull-request`.

* **A boolean `cve-rebuild: "true"`.** The next build of the Component would take the class, including a build that is not the CVE fix. `status.cveRebuildPullRequests` names the pull requests whose builds take the class.

* **An annotation holding the pull request numbers.** A GitOps sync that manages the annotation would put a spent number back. Status is left alone by that sync, and `patch` on `components/status` does not include the Component spec.

* **A ClusterQueue per standing class.** Builds, tests, and releases share a queue so a push test stays ahead of a push build. Separate standing-class queues would give up that order.

* **A sticky `cve` value on the Component.** The value would outrank nudges and releases for every later build of that Component.

* **A WorkloadPriorityClass for every severity.** `important`, `moderate`, and `low` would each gain a `high` class and a second class. Critical is the severity that outranks the other CVE rebuilds. Those three keys share `konflux-cve-high` and `konflux-cve`.

* **A flat list of pull request numbers.** The severity would live in a second status field, or only on the PipelineRun after the class is set. The two can drift, and the severity disappears with the number. `status.cveRebuildPullRequests` keeps each number under the severity recorded for that pull request, and the build pipeline controller copies that key to `build.konflux-ci.dev/cve-max-severity` before removing the number.

## Consequences

* A branch parent, and a component in no nudge, keep today's priority once the controller has written. A branch end waits at the floor. Inside one band, a root parent is admitted before `normal`, and `normal` before `background`. The same order applies to a non-container build. `normal` and `background` share the non-`high` CVE class. In the example, `normal` is 700 after the merge and 500 before it, and `konflux-default` is 400. Until that write, a push or pre-merge component build waits at the floor of its band.
* An installation sets the numeric value of each WorkloadPriorityClass. The tables in this ADR are one example that keeps the order above. Another set of values is valid when it keeps that order and does not place one of these classes in a gap the installation already uses.
* A post-merge component build, including a branch end, still runs before a pre-merge build of a root parent. A post-merge test still runs before the post-merge `high` standing class.
* Each listed pull request spends one post-merge build. A later pre-merge build of that pull request, including a new commit and a `/retest`, is admitted in the pre-merge CVE band and leaves the number in place. The first pre-merge PipelineRun whose subject matches records the number when that add succeeds. That run takes the pre-merge CVE class when the controller writes before Kueue reserves quota. A critical `high` post-merge build is admitted ahead of every other CVE rebuild. A critical fix is admitted ahead of an important, moderate, or low fix, and a root parent is admitted ahead of another Component of the same severity. The four post-merge CVE classes are admitted ahead of nudges, releases, tests, and ordinary builds. The four pre-merge CVE classes stay below pre-merge tests and above other pre-merge builds. The build pipeline controller removes that number from every list and writes `build.konflux-ci.dev/cve-max-severity` only after the post-merge patch succeeds. A post-merge patch that cannot succeed leaves the number in place, leaves the CVE class unset, and the controller reconciles again. A pre-merge add that cannot succeed leaves the number unrecorded, leaves the CVE class unset, and the controller reconciles again. The run keeps the standing class. A build that names a different pull request number does not remove the listed number. A build whose subject does not match, and whose number is absent, leaves the object unchanged.
* A run Kueue admits before the controller writes keeps the expression's class. For a push or pre-merge component build that class is the floor, and a later change does not take the slot back. The status write still records the pull request for a later PipelineRun.
* A user who can create a pre-merge component build can set `pipelinesascode.tekton.dev/sha-title` and `pipelinesascode.tekton.dev/pull-request` and add a number under `critical` or `important`. The later push spends that number. `build.konflux-ci.dev/rebuild-pull-request` does not add a number.
* A user who can create a component build can set `build.konflux-ci.dev/rebuild-pull-request` to a number already in `status.cveRebuildPullRequests`. That build spends the number only when it is a push. For a PipelineRun Pipelines as Code did not create, the push is `build.konflux-ci.dev/build-event: push`. The annotation grants a CVE class only when the build pipeline controller finds that number in the Component status. A PipelineRun Pipelines as Code did not create leaves the number in place and stays `konflux-default` when `build-event` is absent, or is neither `push` nor `pull-request`.
* A `kueue.x-k8s.io/priority-class` or a `cve-max-severity` submitted with the PipelineRun does not select a class. On a push or pre-merge component build, the controller replaces both. A MintMaker branch, a nudge, a test, and a release keep the expression's class. An arrived label that names one of the eight CVE classes falls through the priority expression to the later clauses. On a cluster whose expression keeps some other arrived label, that label is the class until the controller writes. The controller replaces it on a push or pre-merge component build, and writes `konflux-default` when that component build is on neither row.
* A full queue still finishes admitted work before the next build starts.
* A steady stream of root-parent builds in a band is admitted before `normal` builds, and `normal` builds before branch ends, in that band. A tenant cannot set a priority field. The tenant edits `NudgeConfig`, and that edit changes the class by changing the graph. An edge nudges `to`. It makes `from` a root parent when no entry names it as `to`, and makes `to` a branch end when no entry names it as `from`. When `to` was a root parent, or when `from` was a branch end, that edge makes it a branch parent. A root parent is admitted ahead of other tenants' `normal` builds in the same band, because those LocalQueues share one ClusterQueue.
* Any user or service who can patch Component status can add a pull request under a severity key. A `critical` key spends the push in `konflux-cve-critical`, or in `konflux-cve-critical-high` when the component is a root parent. Any other key spends it in `konflux-cve`, or in `konflux-cve-high` when the component is a root parent. `build.konflux-ci.dev/cve-max-severity` is set to that key. Integration Service's build pipeline controller ServiceAccount can patch `components/status`. The integration pipeline ServiceAccount cannot patch the Component. Editing the Component spec does not arm a pull request.
* A GitOps sync of the Component does not restore a spent pull request number.
* The matching component build carries `build.konflux-ci.dev/cve-max-severity`. Integration Service copies `build.konflux-ci.dev` annotations from the build PipelineRun onto the component Snapshot.
* Every cluster's copy of the priority expression evaluates the nudge, release, and test matches before the MintMaker branch match, and that branch match before the component floor. It assigns a component push, and a component build with no Pipelines as Code event type whose `build.konflux-ci.dev/build-event` is `push`, to `konflux-post-merge-build-background`. It assigns a component pre-merge build, and a component build whose `build-event` is `pull-request`, to `konflux-default`. An arrived label naming one of the eight CVE classes falls through to those later clauses. The controller sets the standing and CVE classes on a push or pre-merge component build. A nudge, a test, a release, and a MintMaker branch keep the expression's class. User documentation covers a root parent, a branch parent, and a branch end, the subjects `fix(security-critical):` and `fix(security):`, `build.konflux-ci.dev/build-event` (`push` and `pull-request`), `build.konflux-ci.dev/rebuild-pull-request`, and `status.cveRebuildPullRequests`. The Konflux UI can expose the severity lists on the Component screen.
