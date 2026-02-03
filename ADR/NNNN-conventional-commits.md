# N. Mandate Conventional Commits Across Konflux Repos

Date: 2026-02-03

## Status

Proposed

## Context

Konflux currently lacks a standardized commit message format across its repositories. This inconsistency creates several challenges:

* **Manual changelog generation**: Release notes must be compiled manually by reviewing commit histories, which is time-consuming and error-prone
* **Inconsistent commit quality**: Without guidelines, commit messages vary widely in format and informativeness
* **Difficulty tracking changes**: Understanding what changed between releases requires reading through unstructured commit messages
* **Limited automation opportunities**: Tools that could automate versioning and changelog generation cannot be used effectively

The [Conventional Commits](https://www.conventionalcommits.org/) specification provides a lightweight convention for commit messages that enables automated tooling while remaining human-readable. It structures commits as:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Where `type` indicates the nature of the change (e.g., `feat`, `fix`, `docs`, `chore`).

## Decision

All Konflux repositories will adopt the Conventional Commits specification for commit messages. This decision includes:

### Commit Message Format

Commits must follow the Conventional Commits 1.0.0 specification with the following types:

| Type | Description |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Changes that do not affect the meaning of the code (formatting, etc.) |
| `refactor` | A code change that neither fixes a bug nor adds a feature |
| `perf` | A code change that improves performance |
| `test` | Adding missing tests or correcting existing tests |
| `build` | Changes that affect the build system or external dependencies |
| `ci` | Changes to CI configuration files and scripts |
| `chore` | Other changes that don't modify src or test files |
| `revert` | Reverts a previous commit |

Breaking changes must be indicated by appending `!` after the type/scope or by including `BREAKING CHANGE:` in the footer.

### Enforcement Mechanism

Repositories will enforce conventional commits through CI checks using [commitlint](https://commitlint.js.org/) with the `@commitlint/config-conventional` preset. The enforcement will be implemented as:

1. **PR title validation**: GitHub Actions workflow that validates PR titles follow conventional commit format (for squash-merge workflows)
2. **Commit message validation**: For repositories using merge commits, individual commit messages will be validated
3. **Pre-commit hooks**: Optional local enforcement via Husky and commitlint for developer convenience

### Rollout Timeline

The rollout will proceed in phases:

1. **Phase 1 - Documentation and Tooling**: Publish adoption guide, create reusable GitHub Actions workflow, document PR template updates
2. **Phase 2 - Opt-in Adoption**: Enable enforcement in willing repositories, gather feedback, refine tooling
3. **Phase 3 - Mandatory Adoption**: Enable enforcement across all Konflux repositories, provide migration support for teams

Specific timelines for each phase will be determined based on team capacity and feedback during the adoption process.

### Adoption Guide for Teams

Teams adopting conventional commits should:

1. Add the shared commitlint GitHub Actions workflow to their repository
2. Update PR templates to include conventional commit format guidance
3. Optionally configure local pre-commit hooks for immediate feedback
4. Review the [Conventional Commits specification](https://www.conventionalcommits.org/) and team-specific scope conventions

## Consequences

### Benefits

* **Automated changelog generation**: The [Konflux-CI Installer](https://github.com/konflux-ci/konflux-ci) release notes automation will leverage conventional commits to generate meaningful changelogs that aggregate `feat` and `fix` commits from all upstream Konflux repositories
* **Semantic versioning automation**: Version bumps can be determined automatically based on commit types (feat = minor, fix = patch, breaking = major)
* **Improved commit hygiene**: The required structure encourages more thoughtful, descriptive commit messages
* **Better searchability**: Structured commits are easier to filter and search (e.g., find all `fix` commits)
* **Clearer release communication**: Stakeholders can quickly understand what changed in each release

### Costs

* **Learning curve**: Contributors unfamiliar with conventional commits will need to learn the format
* **Additional CI overhead**: Commit validation adds a small amount of CI time
* **Potential friction**: Invalid commit messages will block PRs until corrected
* **Tooling maintenance**: The shared workflow and commitlint configuration will require ongoing maintenance

### Migration Considerations

* Existing commit history will not be modified; the convention applies to new commits only
* Repositories with existing automation may need to update their tooling to work with the new format
* Teams should establish repository-specific scopes if needed (e.g., `feat(api):`, `fix(ui):`)
