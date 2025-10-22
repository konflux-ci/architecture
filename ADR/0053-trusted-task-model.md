# 53. Trusted Tasks model after build-definitions decentralization

Date: 2025-09-30

## Status

Accepted

Relates to [ADR 21. Partner Tasks in Build/Test Pipelines](0021-partner-tasks.md).
The concept of Partner Tasks is no longer relevant after decentralization. The model
proposed in this ADR provides a flexible way to define the trust in Tasks, which
could help replace Partner Tasks.

## Context

Conforma has the concept of [Trusted Tasks]. Konflux policies rely on this concept
extensively when verifying the compliance of artifacts built through Konflux Pipelines.

Today, the mechanism for trusting Tasks is driven by the `trusted_tasks` data format,
which lists every acceptable revision of every version of every trusted Task. Konflux
publishes the [quay.io/konflux-ci/tekton-catalog/data-acceptable-bundles][data-acceptable-bundles]
artifact, which is an OCI wrapper around a YAML file that provides `trusted_tasks`:

```yaml
---
trusted_tasks:
  oci://quay.io/konflux-ci/tekton-catalog/task-buildah:0.4:
    - ref: sha256:9bedc54bbf756aee2cf9601892d1174e65dd6bc9a2cd350e7c9711acac4661e1
    - expires_on: "2025-11-16T00:00:00Z"
      ref: sha256:e44cc80f58cbf5a8c5130bcc5ab27efca87533e949dbbeb5541c3114e2610462
  oci://quay.io/konflux-ci/tekton-catalog/task-buildah:0.5:
    - ref: sha256:9ac12870766a980e1f7ae7ddd0852f767da000d8a6d24f5b37e906eb14932355
    - expires_on: "2025-11-25T00:00:00Z"
      ref: sha256:69f6f1324f8fed2aa47df49914956d3d316bc864e6369f934bce986142fad8bb
  git+https://github.com/konflux-ci/build-definitions.git//task/buildah/0.4/buildah.yaml:
    - ref: 4b23c64bd48914a6c4768b4b3e005ecc31e5b8d1
    - expires_on: "2025-11-16T00:00:00Z"
      ref: 3eb9f7f26921c9aa59f66a2908efa5c108a4bb03
  git+https://github.com/konflux-ci/build-definitions.git//task/buildah/0.5/buildah.yaml:
    - ref: c7ede1ce1ea6f8b0255ba419b746181bc9104a64
    - expires_on: "2025-11-25T00:00:00Z"
      ref: 11e3d556db9109c0547499968694585be469fc49
  # ...
```

This approach worked fine while <https://github.com/konflux-ci/build-definitions>
was the only possible source of trusted Tasks. On each merge to the main branch,
the push pipeline would release all the modified Tasks to `quay.io/konflux-ci/tekton-catalog`
and bulk-update the `data-acceptable-bundles` artifact to include the new references.

Scaling this approach to a decentralized setting, where teams maintain separate
Task repositories, is problematic. Currently, the Konflux release pipeline for Task
bundles updates the `data-acceptable-bundles` artifact. But the update mechanism
was not designed to handle parallel updates. When multiple releases run in parallel,
the simultaneous updates can corrupt the content of `data-acceptable-bundles`. The
original plan to avoid this problem was that there would be many "acceptable bundles"
artifacts, one for each repository. But that doesn't solve the problem. Each Task
bundle is a separate Konflux component, a repository can contain many Task bundles,
their releases can run in parallel.

Konflux needs a new model for trusting Tasks after decentralization.

## Decision

### Adopt a rule-based model for Trusted Tasks

In addition to the `trusted_tasks` data, Conforma will gain the ability to trust
Tasks based on `trusted_task_rules`. The rules will give policy authors the ability
to allow/deny sets of Tasks based on some criteria.

If the current logic for trusting Tasks is as follows (pseudocode):

```text
is_on_trusted_tasks_list(task_reference)
and not expired_on_trusted_tasks_list(task_reference)
```

Then, with the addition of `trusted_task_rules`, it becomes:

```text
(
  is_on_trusted_tasks_list(task_reference)
  or is_allowed_by_trusted_task_rules(task_reference)
)
and not expired_on_trusted_tasks_list(task_reference)
and not is_denied_by_trusted_task_rules(task_reference)
```

Note:

- Both the `trusted_tasks` and the `trusted_task_rules` mechanisms should be supported,
  at least until decentralization is complete
- Denial takes priority
  - Even if a Task is on the `trusted_tasks` list, a deny rule should be able to
    make it untrusted.
  - Even if an allow rule makes a Task trusted, if it's expired according to the
    `trusted_tasks` list, it should be considered untrusted.

This ADR doesn't mandate a specific format for `trusted_task_rules`, but does
come with an example of what it could look like - see the [Appendix](#appendix).

### Trust upstream Konflux Tasks based on bundle URL

A policy author who wants to trust all the upstream Konflux Tasks should do so by
defining a rule that allows all task bundles from `quay.io/konflux-ci/tekton-catalog/*`
with no further conditions. The `trusted_task_rules` mechanism must support this.

### Start signing upstream Konflux tasks with a common release key

Trusting all task bundles from `quay.io/konflux-ci/tekton-catalog/*` is not a strong
trust model (but isn't weaker than the current one - see [Consequences](#consequences)).
To let policy authors define a stronger trust model, we should aim to start signing
the upstream Konflux task bundles with a common release key and extend the
`trusted_task_rules` mechanism to support signature verification.

## Consequences

### `data-acceptable-bundles` no longer blocks decentralization

Decentralized Konflux Tasks are trusted implicitly, as long as they release to the
right location.

### Strength of trust model for upstream Konflux Tasks

Current trust model, in theory:

- We place trust in the `quay.io/konflux-ci/tekton-catalog/data-acceptable-bundles`
  artifact
  - Only those who can write to this artifact can make Tasks trusted

Current trust model, in practice:

- Who can write to `quay.io/konflux-ci/tekton-catalog/data-acceptable-bundles`:
  - Release pipelines in the Red Hat deployment of Konflux
  - The CI pipelines for build-definitions
  - The CI pipelines for other repos that happen to use the same OpenShift namespace
    as build-definitions
  - Privileged users in the `quay.io/konflux-ci` organization

The proposed trust model, without signing key verification:

- We implicitly trust all tasks in `quay.io/konflux-ci/tekton-catalog/*`
- We trust anyone who can write to any of those repositories
  - Which is the same list as for `data-acceptable-bundles`

With signing key verification:

- We trust only the release pipelines in the Red Hat deployment of Konflux

### Decentralized Tasks lose the trust in their Git references

*...For now.*

In the current model, any change that gets merged to build-definitions is considered
trusted, so the `trusted_tasks` data includes both `git` references and `oci` bundle
references.

The new trust model for upstream Konflux Tasks is based around trusting the bundles
released through Red Hat's deployment of Konflux. Initially, we should not try to
establish trust for the `git` references to the source code for those tasks, because
there will be no way to know whether the reference passed release-time verifications
or not.

In the future, we could look at options to enable trust in `git` references again.
For example:

- The release pipeline pushes signed tags to the source repository
- The release pipeline pushes task definitions to a centralized repository where
  nobody but the release pipeline has write access, and signs the commits

### Decentralized Tasks lose the automated expiry mechanism

Currently, it's common for Konflux Tasks to release over and over again with the
same version tag. When the version tag moves to a new revision of the Task, the
older revision automatically begins its 60 day expiry period.

Such a mechanism would be difficult to replicate with the rule-based model.

An alternative automated expiry mechanism could be version based. This ADR does not
define the mechanism, because the current versioning practices do not allow a
version based expiry to be effective. This will be addressed, along with the expiry
mechanism, in a future ADR about Task versioning. The example in the Appendix
does at least illustrate how the expiry could work.

Note that Conforma also supports [setting Task expiry] manually via the
`build.appstudio.redhat.com/expires-on` annotation. This will still work.

## Appendix

### Example `trusted_task_rules` mechanism

The `trusted_task_rules` mechanism should:

- Support allowing all `quay.io/konflux-ci/tekton-catalog/*` references unconditionally
- Support time-based rules (Conforma's `expires_on`/`effective_on` concept)
- Be flexible and extensible

This is an attempt to illustrate how such a mechanism could look.

```yaml
trusted_task_rules:
  allow:
    - name: Implicitly trust all tasks from konflux-ci/tekton-catalog
      pattern: oci://quay.io/konflux-ci/tekton-catalog/*

    - name: Require common signing key  # starting in 2026
      pattern: oci://quay.io/konflux-ci/tekton-catalog/*
      signing_key: <common public key for konflux-ci Tasks>
      effective_on: 2026-01-01
  deny:
    - name: Deprecate the old reference for task-build-image-index
      pattern: oci://quay.io/konflux-ci/tekton-catalog/task-build-image-manifest
      message: >
        The task was renamed to 'build-image-index',
        please replace the task reference with an equivalent one from
        https://quay.io/konflux-ci/tekton-catalog/task-build-image-index
      effective_on: 2025-10-26

    - name: Expire all buildah task versions below 0.5
      pattern: oci://quay.io/konflux-ci/tekton-catalog/task-buildah*
      versions:
        - '<0.5'
      effective_on: 2025-11-15

    - name: Expire all buildah task versions below 0.5.1
      pattern: oci://quay.io/konflux-ci/tekton-catalog/task-buildah*
      versions:
        - '<0.5.1'
      effective_on: 2025-11-29  # (later than 0.5)

    - name: Expire the older 2.x versions of task-foo without affecting 1.x
      pattern: oci://quay.io/konflux-ci/tekton-catalog/task-foo
      versions:
        - '>=2,<2.1.0'
      effective_on: 2025-10-30
```

`is_allowed_by_trusted_task_rules(task_reference)`:

The task reference matches at least one `allow` rule and meets the criteria in all
matching `allow` rules with an `effective_on` date not in the future.

`is_denied_by_trusted_task_rules(task_reference)`:

The task reference meets the criteria in any matching `deny` rule with an `effective_on`
date not in the future.

[Trusted Tasks]: https://conforma.dev/docs/policy/trusted_tasks.html
[data-acceptable-bundles]: https://quay.io/repository/konflux-ci/tekton-catalog/data-acceptable-bundles
[setting Task expiry]: https://conforma.dev/docs/policy/tasks.html#_setting_task_expiry
