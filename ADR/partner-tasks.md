# Partner Tasks in Build/Test Pipelines

Date: 2023-03-06

## Status

Provisional

## Context

* As a Red Hat Partner, I would like to offer our service's capability as a Tekton Task that would be executed in a user's build/test Pipeline on StoneSoup.
* As a StoneSoup maintainer, I would like to provide a way to ensure the above Tekton Task is validated and approved for use in the build/test Pipeline on StoneSoup.

Associated business ask
https://issues.redhat.com/browse/STONE-549

## Decision

### Plumbing

1. Setup a new Git repository.
2. Define a directory structure for Task submissions as manifests in the yaml format.
3. Configure a CI job that validates the Tasks upon opening of a pull request.
4. Configure a CI job that generates an OCI artifact consumable in a Tekton Pipeline.

### Day-to-day operations
1. Partner opens a PR with a new/updated Task.
2. Upon approval from the Build/Test team, the changes are merged.
3. Manually/Automatically, a PR is opened to the https://github.com/redhat-appstudio/build-definitions repository

## Consequences

* We have a mechanism to take in Tekton Tasks from Partners with due diligence.
* We do build up a little tech-debt because this process needs to be merged with the official Red Hat certification process in the future.
