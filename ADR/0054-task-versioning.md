# 54. Start versioning Tekton Tasks responsibly

Date: 2025-10-06

## Status

Accepted

Relates to
[ADR 53. Trusted Tasks model after build-definitions decentralization](0053-trusted-task-model.md).

## Context

The upstream Tasks that Konflux releases today typically do not follow a sensible
versioning scheme. They do have version numbers, but the numbers serve only two
purposes:

- Want to make breaking changes? Bump the minor or major version number so that
  you can add a MIGRATION.md document that users will see in the MintMaker PR that
  updates their Tasks.
- Want to attach a migration script that MintMaker will execute when updating
  users' Tasks? Bump any segment of the version number.

For other kinds of changes, whether they be new features, bug fixes or periodic
dependency updates, Task maintainers leave version numbers unchanged.

This has consequences.

### Users get opaque updates

Most of the time, when a Konflux user receives a PR that updates their Tasks, they
see something like this:

| Package                                                      | Change                 | Notes                                      |
| ---                                                          | ---                    | ---                                        |
| quay.io/konflux-ci/tekton-catalog/task-apply-tags            | `e0de426` -> `f44be1b` |                                            |
| quay.io/konflux-ci/tekton-catalog/task-build-image-index     | `3bf6e4e` -> `79784d5` |                                            |
| quay.io/konflux-ci/tekton-catalog/task-buildah-remote-oci-ta | `0.4` -> `0.5`         | :warning:[migration][migration-1]:warning: |
| quay.io/konflux-ci/tekton-catalog/task-clair-scan            | `0.2` -> `0.3`         | :warning:[migration][migration-2]:warning: |

For the tasks with breaking changes, they get *some* (usually insufficient) information
about what changed.

For those without breaking changes, they get nothing. What changed between
`e0de426` and `f44be1b`? Not even the maintainers know.

It would not be at all unreasonable for a user to refuse to merge these kinds of
PRs (except that Conforma would eventually flag their tasks as outdated.)

### Maintainers cannot easily communicate critical fixes

When a Task maintainer discovers and fixes a critical bug, they typically wish
to announce this publicly, e.g. on the Konflux mailing list.

With the current versioning practices, how does the maintainer go about this?

> We've discovered a bug in task-foo version 0.2. Please upgrade to version 0.2.

Hmm, no, that's not right.

> We've discovered a bug in task-foo:0.2@sha256:baadbaad. Please upgrade to sha256:deadbeef

Better. But a user has 0.2@sha256:baddecaf. Are they affected? Who knows.

> We've discovered a bug in task-foo version 0.2, revisions released between 2025-08-01
  and 2025-10-01. Please upgrade to a sufficiently new revision.

Okay, at least it's an interval now. But are we really going to ask the user to run
`skopeo inspect --no-tags --format '{{.Created}}' docker://${my_task_ref}` to figure
out if they're affected?

> We've discovered a bug in task-foo versions >=0.2.2,<0.2.5. Please upgrade to
  version 0.2.5.

(Is what the maintainer wishes to write, cursing the lack of versioning.)

### Policy authors cannot set requirements for Task versions

The authors of Conforma policies may want to have the ability to require specific
versions of certain Tasks. Today, this desire is expressed in the form of the expiry
mechanism for [Trusted Tasks]:

- Tasks release repeatedly with the same `0.x` version tag.
- The latest revision of each `0.x` version is trusted, until Task maintainers decide
  this particular version should enter the expiry period.
- When the `0.x` version tag moves to a new revision, the older revision (previously
  tagged as `0.x`) begins its expiry period.
- *The same would likely apply to `1.x`, `2.x` etc. We don't know, no Konflux Task
  has made it that far.*

This mechanism is rather clunky and not very flexible. And, for reasons explained
in [ADR 53](0053-trusted-task-model.md), the mechanism will not work after the build-definitions
decentralization.

A more flexible solution would allow the policy author to allow/disallow specific
version ranges. Such a solution cannot work if dozens of different versions of the
same Task share the same version number.

## Decision

### Mark each meaningful change with a version update

For Tasks at version `0.x` (in initial development), you may continue to mark breaking
changes with minor version updates and start marking non-breaking changes with patch
version updates. Make sure to move to version `1.0` when the Task matures.

For Tasks at version `1.0` or greater, follow [Semantic Versioning](https://semver.org/).

When releasing Tasks as OCI bundles:

- Record the version via the `org.opencontainers.image.version` annotation. This
  allows Conforma to read the version and use it for [version-based Trusted Task
  rules](#extend-trusted_task_rules-mechanism-with-version-based-rules).
- Tag the released bundle with the version. This makes MintMaker updates work properly.

> ℹ️
>
> The current build pipeline for Task bundles applies the version annotation automatically.
> The source for the version value is the `app.kubernetes.io/version` label from
> the Task YAML definition.
>
> Task maintainers can configure their ReleasePlanAdmissions to automatically use
> the version annotation as a tag for the released bundle. The repository that holds
> Red Hat release configurations has a CI check which ensures the relevant RPAs are
> configured correctly.

This ADR leaves some freedom to each Task maintainer team to decide how to ensure
changes get versioned. The *suggested* approach would be to version manually
and set up CI in a way that encourages/enforces versioning. See Appendix 1:
[The technicals of Task versioning](#the-technicals-of-task-versioning).

### Don't require Task repositories to follow Tekton Catalog layout

The [Tekton Catalog layout], which places each version of a Task in a separate
`task/${task_name}/${version}/` directory, causes far too much overhead when
updating Task versions. If we're going to require version updates for each meaningful
change, we cannot ask Task maintainers to follow this layout. See Appendix 1:
[The technicals of Task versioning](#the-technicals-of-task-versioning) for more details.

### Keep a changelog

Version numbers on their own are nice, but without an easy way to see what changed
in each version, they're not that useful.

Document the meaningful changes in each version in a CHANGELOG.md file. The changelog
for a specific Task will be at `/task/${task_name}/CHANGELOG.md` in the repository.
See Appendix 3: [CHANGELOG.md format](#changelogmd-format) for details about the
file format.

### MintMaker: don't assume each x.y version has a MIGRATION.md

Today, MintMaker links MIGRATION.md documents in the PRs it sends to Konflux users
(see the example [above](#users-get-opaque-updates)). This feature assumes that each
`major.minor` version comes with a MIGRATION.md document, that this document is
at `/task/${task_name}/${version}/MIGRATION.md` in the source repository and that
the source repository is <https://github.com/konflux-ci/build-definitions>. The
feature will not work after decentralization.

MintMaker will stop trying to link MIGRATION.md files and will instead link the changelog.
In case of breaking changes, the changelog should explain how the user can migrate.

### Extend trusted\_task\_rules mechanism with version-based rules

Extend the mechanism described in [ADR 53. Trusted Tasks model after build-definitions
decentralization](0053-trusted-task-model.md). Give policy authors the ability to
constrain the acceptable Task versions.

Make it possible to:

- Allow a Task only if its version is in the set of allowed version ranges
- Deny a Task if its version is in the set of disallowed version ranges

Like most Conforma rules, the Task version rules should support the `effective_on`
concept. A policy author typically will not want to disallow a version range immediately,
but will want to give users some lead time.

The [Appendix of ADR 53](0053-trusted-task-model.md#appendix) illustrates how the
Task version rules could look.

## Consequences

### Positive

Users get transparent update PRs.

Maintainers can easily communicate critical fixes.

Policy authors can set requirements for Task versions. This can replace the Task
expiry mechanism lost during decentralization.

### Negative

The Tekton Catalog layout gives the git resolver a way to refer to a specific version
of a Task by filepath. Without the catalog layout, users will not be able to specify
exact Task versions when using the git resolver (except by commit revision).

> ℹ️
> As explained in ADR 53, [git references for decentralized Tasks will not initially
> be trusted](0053-trusted-task-model.md#decentralized-tasks-lose-the-trust-in-their-git-references),
> so this is not a big loss. The ADR mentions possible approaches to re-enable trust
> in git references, one of which could offer a straightforward solution: Development
> happens in decentralized repos, which don't have to follow the catalog layout.
> A release pipeline pushes the tasks into a centralized repo that does follow the
> catalog layout.

Requiring a version update for each code change will cause some overhead for
contributors and/or maintainers. You may be thinking the versioning should be
automatic. Appendix 2: [In defense of manual versioning](#in-defense-of-manual-versioning)
argues that automatic versioning is not a good idea.

## Appendix

### The technicals of Task versioning

#### Repository layout

The current versioning practices for Konflux Tasks require a repository layout
with separate directories for each `major.minor` version:

```text
task
└── hello
    ├── 0.1
    │   └── hello.yaml
    ├── 0.2
    │   └── hello.yaml
    ├── 1.0
    │   └── hello.yaml
    └── 1.1
        └── hello.yaml
```

Updating a Task's version involves copy-pasting the Task definition and related resources
into a new directory. This brings problems:

- Reviewing changes is much harder than it should be. The Pull Request doesn't show
  a diff, it shows a whole new file. The PR author can work around this by structuring
  their commits intelligently, but it's a point of friction.
- It's too easy to introduce "regressions" by merging features/bugfixes into the
  wrong Task version. You open a PR for `task/hello/1.1`. In the meantime, someone
  else creates `task/hello/1.2`. Both PRs merge with no conflicts, because as far
  as git is concerned, the files have nothing to do with each other. Version 1.2
  is now missing a bugfix from version 1.1.
- It's enough of a chore to discourage developers from versioning.

The suggested repository layout going forward would be:

```text
task
└── hello
    └── hello.yaml    (version defined only by the app.kubernetes.io/version label)
```

In case you want to maintain more than one "version stream" at a time:

```text
task
└── hello
    ├── 1.x
    │   └── hello.yaml  <- branched off into separate dir when moving to 2.0
    └── hello.yaml      <- latest 2.x
```

#### CI setup

We want to make sure each meaningful change to a Task definition results in a version
update. We may want to leave maintainers/contributors some freedom to skip version
updates for changes they don't consider meaningful (e.g. formatting, description
texts).

A flexible way to achieve that would be to **release Tasks only when their version
number changes** (don't even build the Task bundle otherwise).

The CI should prompt the contributor to consider updating the version and the CHANGELOG.
It should explain that the Task will not get released unless the version changes.

> 💡
> AI code review might work well here. You would want to teach the reviewer to decide
> whether the change is meaningful and post a comment accordingly.

#### Dealing with MintMaker updates

Automated PRs for dependency updates may become a problem. They're already seen
as a chore today by many Task maintainers. If manual action is required before
a MintMaker PR can merge, the most likely outcome is that MintMaker PRs will stop
getting merged.

There's a few options to deal with this:

- Do not consider them meaningful. Merge the PR without updating the changelog or
  the version.
  - This is often accurate. The PRs typically update just the digests of `step` images.
    Maintainers don't really have a chance of knowing what changed.
  - For meaningful PRs (e.g. updating the Hermeto version in the Prefetch Task or
    the Buildah version in the Buildah Task), you would still want to do the edits
    manually.
- Set the MintMaker schedule to a tolerable frequency, e.g. monthly, and do the
  edits manually.
- Have a CI workflow that can auto-update the version and changelog.
  - Doesn't need to be complex, it's enough if it supports MintMaker PRs.

Some combination of the above should be enough to make automated dependency updates
tolerable even with the versioning requirements.

### In defense of manual versioning

Having to manually update the Task version in the source code may feel like
an avoidable chore. Surely we could automate it, right?

> If the Pull Request doesn't update the version, just auto-increment the patch number.

This would allow the version-based Task expiry mechanism to somewhat function. But
would fail spectacularly at most other aspects of software versioning. How do you
maintain a changelog for an auto-incrementing version? How do you make sure contributors
differentiate between bug fixes and new features?

> Okay, let's derive both the version and the changelog from semantic commits.

Hey, that's not a bad idea. It's a pretty common approach with a lot of existing
automation, such as [semantic-release]. It's unlikely any of it would work out
of the box for Konflux Tasks, but surely it wouldn't be hard to build our own.

Let's say you've built this solution. You've taught your contributors to follow
semantic commit conventions responsibly. You've taught your team to review commit
messages as carefully as they review the code. You have a solution that auto-generates
a changelog. You probably employed an LLM to extract the user-facing details out
of the maintainer-facing commits messages, and to fill in the gaps for those commit
messages that don't come with any useful information. It's beautiful. Just one question
left to answer. *When do you run this automation?*

Konflux releases are, by default, automatic - each merge triggers a release. For
a repository where you maintain dozens of Tasks, you probably want to keep it that
way. If you've just spent two weeks building an auto-version + auto-changelog solution,
you definitely don't want releasing to be a manual affair. Since there's no "release
preparation" step, that leaves you one option - run the automation at release time
(or in the merge pipeline that triggers a release immediately upon completion, which
is effectively the same). So the tool has determined the next version, the release
pipeline applied that version and released the Task. The tool also returned the
changelog content. *What do you do with it?*

Taking inspiration from [semantic-release], just dump the changelog into a GitHub
release? Take a look at [semantic-release/releases] and consider if that's the style
of changelog you would want to see. And now remember that this is a changelog for
a single cohesive item - there's only one thing to version. Your repository is a
collection of dozens of Tasks, each versioned separately. No, each Task is going
to need its own CHANGELOG.md. But the changes are already merged, the release is
already happening or about to happen. It's too late to update files in the source
repo. No matter, let's send a PR. Maybe the changelog update will lag behind the
actual release, but that's not a big deal.

So, for every merge, you get an automated PR to update the CHANGELOG.md. You get
the uneasy feeling that the time savings you get from the automation are in the
negative numbers. *If only there was a way to update the changelog in the same PR
that introduces the change.*

And then one day, the automation mis-versions a breaking release because someone
made a typo in the commit message, and you scramble to revert the changes and
re-release them properly. *If only there was a way to vet the version number before
the release goes live.*

The solution to both problems turns out to be simple. Define version numbers statically
in the source code. Ask contributors to update both the version numbers and the
changelog documents manually.

To salvage the failed automation, you at least re-purpose it as a GitHub workflow
that a contributor can optionally invoke by commenting on the Pull Request.

> ℹ️
> In all seriousness, this style of automation could genuinely be helpful, especially
> for [dealing with MintMaker updates](#dealing-with-mintmaker-updates). Though
> something far simpler would likely suffice.

**To summarize:** If you want to go the automation route, feel free to do so, as
long as it doesn't go against the spirit of the [decisions](#decision) in this ADR.
But consider instead keeping it simple.

### CHANGELOG.md format

The CHANGELOG.md must:

- Have a heading for each version, e.g. `## 0.1.0`. The "level" of the heading
  (H2, H3, ...) is not important, but should be consistent throughout the doc.

The CHANGELOG.md should:

- Group the same type of changes together (bug fixes, new features, changes in
  existing behavior...)
  - Consider [Keep a Changelog] for inspiration
- Clearly call out breaking changes.
- Include instructions on how to update to the new version (either inline or by
  linking to a separate document), if there are breaking changes which require action
  from users.

Example:

```markdown
# Changelog

## Unreleased

### Changed

- Something so small that it wasn't worth it to do a release for it. It
  will be released the next time someone updates the version.

## 1.0.0

*With this release, do-something-cool reaches a stable 1.x version!
From now on, breaking changes will result in major version bumps.*

### Removed

- The `coolness_level` parameter. The task now always operates at maximum coolness.
  - This is not a breaking change, since Tekton will just ignore the parameter.
    Do consider removing it from your pipelines though.
- **Breaking**: The `coolness_level` result. If you were previously using this
  result in your pipelines, please remove the usage and assume maximum coolness.

## 0.2.0

### Changed

- **Breaking**: Renamed the `coolnessLevel` result to `coolness_level` to align
  on `snake_case` result naming. Please update the usage of this result in your
  pipelines accordingly.

## 0.1.1

### Fixed

- In some cases, the task could do something uncool.

## 0.1.0

### Added

- The initial version of the do-something-cool task!
```


[migration-1]: https://redirect.github.com/konflux-ci/build-definitions/blob/main/task/buildah-remote-oci-ta/0.5/MIGRATION.md
[migration-2]: https://redirect.github.com/konflux-ci/build-definitions/blob/main/task/clair-scan/0.3/MIGRATION.md
[Trusted Tasks]: https://conforma.dev/docs/policy/trusted_tasks.html
[semantic-release]: https://github.com/semantic-release/semantic-release
[semantic-release/releases]: https://github.com/semantic-release/semantic-release/releases
[Tekton Catalog layout]: https://github.com/tektoncd/catalog?tab=readme-ov-file#catalog-structure
[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/#how
