---
date: 2023-01-30T00:00:00Z
title: Konflux Test Stream - API contracts
number: 13
---
# Konflux Test Stream - API contracts

## Status

Deprecated by [ADR 30. Tekton Results Naming Convention](0030-tekton-results-naming-convention.html).

Relates to [ADR 14. Let Pipelines Proceed](0014-let-pipelines-proceed.html)

## Context

The Konflux project being developed aims to serve Red Hat teams but also partners and customers. This requires a level of adaptability to avoid recreating custom flows and Tasks for each stakeholder.

In this respect Tasks developed by Konflux test stream should allow swapping external systems to accommodate different environments. This swap should not induce the complete recreation of pipelines.

This and the idea of providing a homogeneous experience, which is easier to comprehend and navigate complex systems, leads to the definition of `API contracts`. These contracts need to be understood as guidance that may evolve with time and experience while keeping the aim of building a flexible homogeneous system.

Tasks from the test stream may exchange information through

1. Parameters passed at the time of the trigger of a PipelineRun (that is user, git repository, etc)
2. Output of upstream elements of the Pipeline which may be needed for performing the Task (that is build artifacts, container image, etc)
3. Providing whether the Task was successful or not
4. Output of the Task that may be needed for processing subsequent Tasks of the pipeline
5. Output of the Task that need to be stored for auditing and troubleshooting (that is summarized results of a validation or a scan, etc)
6. Communication with external systems that are needed for performing the Task (that is container image repository, image scanner, etc)
7. Connection details and credentials that may be required for the above

Related to [PLNSRVCE-41](https://issues.redhat.com/browse/PLNSRVCE-41) investigations in regards to [Tekton results](https://github.com/tektoncd/results). The investigations are documented [here](https://docs.google.com/document/d/1WGWx6MllVs-BwRLd0PP5QTQHgGp0fW2dOYRKRAKWiwo/edit#heading=h.bpyxfhyud4dv).

## Decision

Related to [PLNSRVCE-41](https://issues.redhat.com/browse/PLNSRVCE-41) investigations in regards to [Tekton results](https://github.com/tektoncd/results). The investigations are documented [here](https://docs.google.com/document/d/1WGWx6MllVs-BwRLd0PP5QTQHgGp0fW2dOYRKRAKWiwo/edit#heading=h.bpyxfhyud4dv). The output of each Tekton task will be provided in two forms: **Tekton Task Results** and **Full Test Output JSON**.

### Tekton Task Results

The output of each Tekton task will be provided in a minimized [Tekton result](https://tekton.dev/docs/pipelines/tasks/#emitting-results) in JSON format listing all test failures. The name of the result will be **HACBS_TEST_OUTPUT**.

To display count of found vulnerabilities and make it easy to understand and evaluate the state of scanned image, the additional output of Tekton task `clair-scan` will be provided in a minimized [Tekton result](https://tekton.dev/docs/pipelines/tasks/#emitting-results) in JSON format listing. The name of the result will be **CLAIR_SCAN_RESULT**.

The maximum size of a [Task's Results](https://tekton.dev/vault/pipelines-v0.17.3/tasks/#emitting-results) is limited by the container [termination message](https://kubernetes.io/docs/tasks/debug/debug-application/determine-reason-pod-failure/#customizing-the-termination-message) feature of Kubernetes.

App Studio builds are structured as [a shared Persistent Volume per Konflux Workspace](https://docs.google.com/document/d/1IPlihVjkJ4Kb9tdhsk7iz3bn5rkT_SvJCNQhyXzK3aI/edit#bookmark=id.gefgys3vno2). This allows teams to share builds, implement caching and other shared volumes. A single persistent volume is mapped to each default build pipeline. Builds are passed a directory specific to their builds.

#### Tekton Result Format for `HACBS_TEST_OUTPUT`

The Test output of the Tekton result **HACBS_TEST_OUTPUT** will be a JSON object that includes the context about the test along with the list of check names for all failed checks

The output will provide the following information about the overall test result:
- **result** - The outcome of the testing task, can be `SUCCESS`, `FAILURE`, `WARNING`, `SKIPPED` or `ERROR`
- **namespace** - The rego namespace for the test policy. If not set, it will be assumed to have the value `default`
- **timestamp** - An UNIX epoch timestamp of the test completion time
- **successes** - The number of successful checks in the form of an integer
- **note** - A short note provided by test workstream to provide additional information about the test
- **failures** - The number of failed checks in the form of an integer
- **warnings** - The number of warning checks in the form of an integer

Example contents of the test result output file (**HACBS_TEST_OUTPUT**) for a failed run:
```
{
    "result": "FAILURE",
    "namespace": "image_labels",
    "timestamp": "1649148140",
    "successes": 12,
    "note": "Task fbc-related-image-check failed: Command skopeo inspect could not inspect images. For details, check Tekton task log.",
    "failures": 2,
    "warnings": 0
}
```
Example for a successful run:
```
{
    "result": "SUCCESS",
    "timestamp": "1649843611",
    "namespace": "required_checks",
    "successes": 16,
    "note": "Task fbc-related-image-check succeeded: For details, check Tekton task result HACBS_TEST_OUTPUT.",
    "failures": 0,
    "warnings": 0
}
```
Example for a skipped run:
```
{
    "result": "SKIPPED",
    "note": "We found 0 supported files",
    "timestamp": "1649842004",
    "successes": 0,
    "note": "Task sast-snyk-check skipped: Snyk code test found zero supported files.",
    "failures": 0,
    "warnings": 0
}
```
Example for a run with an error:
```
{
    "result": "ERROR",
    "timestamp": "1649842004",
    "successes": 0,
    "note": "Task fbc-validation failed: $(workspaces.source.path)/hacbs/inspect-image/image_inspect.json did not generate correctly. For details, check Tekton task result HACBS_TEST_OUTPUT in task inspect-image.",
    "failures": 0,
    "warnings": 0
}
```


#### Tekton Result Schema Validation
The test output of the Tekton result **HACBS_TEST_OUTPUT** will be validated using the [jsonschema validator package](https://github.com/santhosh-tekuri/jsonschema).
The schema is configured as follows:

```
{
  "$schema": "http://json-schema.org/draft/2020-12/schema#",
  "type": "object",
  "properties": {
    "result": {
      "type": "string",
      "enum": ["SUCCESS", "FAILURE", "WARNING", "SKIPPED", "ERROR"]
    },
    "namespace": {
      "type": "string"
    },
    "timestamp": {
      "type": "string",
      "pattern": "^[0-9]{10}$"
    },
    "successes": {
      "type": "integer",
      "minimum": 0
    },
    "note": {
      "type": "string",
    },
    "failures": {
      "type": "integer",
      "minimum": 0
    },
    "warnings": {
      "type": "integer",
      "minimum": 0
    }
  },
  "required": ["result", "timestamp", "successes", "failures", "warnings"]
}
```


#### Tekton Result Format for `CLAIR_SCAN_RESULT`
The Test output of the Tekton result **CLAIR_SCAN_RESULT** will be a JSON object that includes the following information about the found vulnerabilities scanned by Clair. Refer to [Red Hat Vulnerability documentation](https://access.redhat.com/articles/red_hat_vulnerability_tutorial) for more context on the vulnerability severity ratings.

```
{
  "vulnerabilities": {
    "critical": 1,
    "high": 0,
    "medium": 1,
    "low":0
  }
}
```

### Detailed Conftest Output JSON

Test output JSON file with detailed test information is saved in the Tekton Pipeline Workspace. The name of the file will be in snake case and will be in the form of **test_name_output.json**

The Test Tekton tasks will use a standardized manner of displaying testing information. This information will be saved in the form of a JSON file. The contents of this file will relay results of validation by the [Open Policy Agent](https://www.openpolicyagent.org/) policies as executed by the [Conftest](https://www.conftest.dev/) tool and saved in its JSON output format.

Each test will have a standardized short name in snake case, e.g. `release_label_required`, `architecture_label_required`, `architecture_label_deprecated` etc.

The output will provide the following information about the overall test result:
- **filename** - Name of the file that was inspected by the Tekton task
  - This will reflect the data that the test was executed on, such as `image-inspect.json`, `clair-vulnerabilities.json` etc.
- **namespace** - The rego namespace of the test policy.
- **successes** - The number of successful checks in the form of an integer
- **failures** - A JSON list containing objects describing each failure

The **failures** list of objects will provide the following information about each check:
- **name** - Name of the individual check written in [snake case](https://en.wikipedia.org/wiki/Snake_case)
- **msg** - Message about what went wrong with the check
- **description** - The explanation about why the check is significant (Why the label is used, why the vulnerabilities are checked etc.)
- **url** - link to the further documentation on the individual check (or that type of check)

Example detailed JSON test output for a Tekton task that tests the container image labels:
```
[
    {
        "filename": "image-inspect.json",
        "namespace": "image_labels",
        "successes": 19,
        "failures": [
            {
                "msg": "The 'architecture' label is required",
                "metadata": {
                    "details": {
                        "description": "Architecture the software in the image should target.",
                        "name": "architecture_label_required",
                        "url": "https://source.redhat.com/groups/public/container-build-system/container_build_system_wiki/guide_to_layered_image_build_service_osbs#jive_content_id_Labels"
                    }
                }
            }
          ]
    }
]
```

```
[
    {
        "filename": "image_inspect.json",
        "namespace": "fbc_checks",
        "successes": 1
    }
]
```

### Information injection

Whenever possible, resources like ConfigMaps or Secrets will be used to inject configuration into Tasks. This is preferred to templates and patches as it fits well with Kubernetes declarative and GitOps approaches.

ConfigMaps and Secrets will be mounted into the Task pod to inject file-based information like certificates.
Environment variables may be injected from ConfigMaps.

Variables directly configured in the Pod definition are discouraged.

Side note: Secrets and ConfigMaps should be made [immutable](https://kubernetes.io/docs/concepts/configuration/secret/#secret-immutable)


### Information format

[Clearly define the format of input parameters and results](https://github.com/tektoncd/catalog/blob/main/recommendations.md#clearly-define-the-format-of-input-parameters-and-results).

Atomic information may be passed as a simple parameter. Non binary encoded complex information should be exchanged through [JSON format](https://github.com/tektoncd/catalog/blob/main/recommendations.md#use-composable-parameter-formats) between Tasks.

#### Image references

Since tags can be moved from one image to another, they should not be relied on as a reference. In order to guarantee that any scanning is performed on an image built as part of a PipelineRun, the immutable image digest reference will be used instead.

## Consequences

As a result of the decision here to summarize results in a **HACBS_TEST_OUTPUT** result and store the larger test output as a file named **test_name_output.json**, we should find that:
* Other components in Konflux can leverage information exposed by TaskRuns - notably the UI (HAC), integration-service, and enterprise-contract - enabling features for the larger system that need to depend on some data from inside a variety of TaskRuns.
* We'll be able to have PipelineRuns that _succeed_ and continue, even if they have tasks whose payloads fail and expose errors. This enables a progressive model where the user can get a build and a functional test and a deployment to their development Environment, even if a linter or scanner in their build pipeline emits an error.
* By having chosen a convention that has "HACBS" in the name, we're going to have trouble integrating third-party Task providers in the future. In order to have its output respected by our system, a hypothetical vendor of a third-party scanner will need to add a "HACBS_TEST_OUTPUT" result on their Task, which is oddly specific to our system. At some point in the future, we should revise this decision to instead align to a common upstream convention that gains traction in the broader tekton ecosystem. See also [HACBS-1563](https://issues.redhat.com/browse/HACBS-1563).

## Additional Recommendations

### Convention over Configuration
https://en.wikipedia.org/wiki/Convention_over_configuration

Tasks should assume default locations for locating information, external systems or output storage. This aims to reduce the amount of information that needs to be configured for running a pipeline.

See: [API Contract - Create a new Build](https://docs.google.com/document/d/1IPlihVjkJ4Kb9tdhsk7iz3bn5rkT_SvJCNQhyXzK3aI/edit#heading=h.bbjyylwvwfej)

### Naming convention
It is advantageous to have naming conventions for parameters, files, and locations. Considering the multiple options: `flatcase`, `camelCase`, `PascalCase`, `dash-case`, `snake_case`, `UPPER_CASE`, `TRAIN-CASE` and the possibility to use [domain-scoped names](https://github.com/tektoncd/community/blob/main/teps/0080-support-domainscoped-parameterresult-names.md) here are the proposed naming conventions for Tasks

- Parameter names: dash-case (already used in build Tasks)
- Resource names: As per [Kubernetes recommendations](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/) resource names will follow  [RFC 1123](https://datatracker.ietf.org/doc/html/rfc1123)
- Environment variables: Following [Kubernetes](https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/) and bash practices environment variables should be defined in UPPER_CASE
- Labels: Labels names will follow Kubernetes practices: prefix with dot `.` as separator and dash-case for names. Prefixes and names are separated by a slash `/`. In addition to the [labels automatically created by Tekton Kubernetes standard labels or custom labels](https://tekton.dev/vault/pipelines-v0.14.3/labels/#automatically-added-labels) could be leveraged to further qualify the resources. Possible groupings:
  - Pipeline part: Build, Test, Release, etc.
  - Application/Product being built: AMQ Streams, EAP, RHSSO, etc.

### DRY

Information, which relates to an environment like connection details and credentials should be configured once at the environment level and not passed as parameters for every PipelineRun. On the other hand, information, which is specific to a run like a container image digest, may be passed as a parameter.


## Appendix

- **Task recommendations**: This document focuses (it was at least the original intention) on API contracts but there are more recommendations regarding Task developments. The following ones have been collected by the Tekton project: https://github.com/tektoncd/catalog/blob/main/recommendations.md
- **Programming language**: Tekton supports “choosing the right language for the right task”. That said, from an operational point of view it is beneficial to limit the number of programming languages needed to support Konflux. Defining “default” languages helps with limiting the skills required to support the platform. This also helps with avoiding knowledge islands where only a few people are able to maintain some Tasks.
- **Failure behavior**: A retry mechanism with configurable timeout and exponential backoff needs to be implemented for technical or functional recoverable failures. A scenario example: An image may not have been completely indexed when the result of the security scan is interrogated. In such a case the Task should have a retry mechanism that may wait till completion of the indexing or time out.
- **Repositories**: Whenever there is no sensitive information we aim to have the PoC sources in a public repository. Is there a public GitHub organization for that? Can we use [this](https://github.com/redhat-appstudio)? When a Task is specifically for Red Hat’s infrastructure it should be kept in a private repository.  Is there a private GitLab group for that?


## References

Originally drafted in a [google document](https://docs.google.com/document/d/1FJX7TH5wBTcWdU2VYuecmkY5O69DGpItN52A-JaoCtU/edit#)
