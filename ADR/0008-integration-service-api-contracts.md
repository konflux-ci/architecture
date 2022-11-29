# 8. HACBS Test Stream - API contracts

Date: 2022-11-28

## Status

Accepted

## Context

The Hybrid Application Cloud Build Service being developed aims to serve Red Hat teams but also partners and customers. This requires a level of adaptability to avoid recreating custom flows and Tasks for each stakeholder.

In this respect Tasks developed by HACBS test stream should allow swapping external systems to accommodate different environments. This swap should not induce the complete recreation of pipelines.

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

### Results and Records

The output of each Tekton task will be provided in two forms:
- As a minimized [Tekton result](https://tekton.dev/docs/pipelines/tasks/#emitting-results) in JSON format listing all test failures
  - The name of the result will be **HACBS_TEST_OUTPUT**
- As a Test output JSON file with full test information that’s saved in the Tekton Pipeline Workspace
  - The name of the file will be in snake case and will be in the form of **test_name_output.json**

The maximum size of a [Task's Results](https://tekton.dev/vault/pipelines-v0.17.3/tasks/#emitting-results) is limited by the container [termination message](https://kubernetes.io/docs/tasks/debug/debug-application/determine-reason-pod-failure/#customizing-the-termination-message) feature of Kubernetes.

App Studio builds are structured as [a shared Persistent Volume per App Studio Workspace](https://docs.google.com/document/d/1IPlihVjkJ4Kb9tdhsk7iz3bn5rkT_SvJCNQhyXzK3aI/edit#bookmark=id.gefgys3vno2). This allows teams to share builds, implement caching and other shared volumes. A single persistent volume is mapped to each default build pipeline. Builds are passed a directory specific to their builds.

#### Tekton Result Format

The Test output of the Tekton result will be a JSON object that includes the context about the test along with the list of check names for all failed checks

The output will provide the following information about the overall test result:
- **result** - The outcome of the testing task, can be `SUCCESS`, `FAILURE`, `WARNING`, `SKIPPED` or `ERROR`
- **namespace** - Optional, the rego namespace of the test policy
- **timestamp** - An UNIX epoch timestamp of the test completion time
- **successes** - The number of successful checks in the form of an integer
- **note** - Optional, a short note providing additional information about the test
- **failures** - The number of failed checks in the form of an integer
- **warnings** - The number of warning checks in the form of an integer

Example contents of the test result output file (**HACBS_TEST_OUTPUT**) for a failed run:
```
{ 
    "result": "FAILURE",
    "namespace": "image_labels",
    "timestamp": "1649148140",
    "successes": 12, 
    "note": "",
    "failures": 2
}
```
Example for a successful run:
```
{
    "result": "SUCCESS",
    "timestamp": "1649843611",
    "namespace": "required_checks",
    "successes": 16,
    "note": "",
    "failures": 0
}
```
Example for a skipped run:
```
{
    "result": "SKIPPED",
    "note": "<skipped message>",
    "timestamp": "1649842004"
}
```
Example for a run with an error:
```
{
    "result": "ERROR",
    "timestamp": "1649842004"
}
```

##### Proposed Adapted Tekton Result Format for Xunit Tests Results

- Existing Mapped:

  - **Namespace** == **name** attribute of all of the **TestSuite** elements 

  - **Failures** == **name** attribute for all the **TestCase** elements that have the attribute **status=Failed**

- New Key:

  - **Skipped** == the number of skipped test in integer format from the **TestSuite** attribute **skipped** or from **TestCase** attribute **skipped**

Some Junit XML files generate a **TestSuites** xml element that contains N number of **TestSuite** elements. In this case it maybe simply best to augment our Task Result Schema to be a JSON List of Task Results 

Example output
```
[
    {
        "result": "FAILURE",
        "namespace": "Red Hat App Studio E2E tests",
        "timestamp": "1649148140",
        "successes": 75,
        "skipped": 14,
        "note": "",
        "failures": [
            "[It] [release-suite test-demo] Creation of the 'Happy path' resources Create an ApplicationSnapshot."
        ]
    },
    {
        "result": "SUCCESS",
        "timestamp": "1649843611",
        "namespace": "Demo Tests",
        "successes": 12,
        "skipped": 0,
        "note": "",
        "failures": []
    }
]
```

#### Full Test Output JSON

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

Example full JSON test output for a Tekton task that tests the container image labels:
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

### Information injection

Whenever possible, resources like ConfigMaps or Secrets will be used to inject configuration into Tasks. This is preferred to templates and patches as it fits well with Kubernetes declarative and GitOps approaches.
tf
ConfigMaps and Secrets will be mounted into the Task pod to inject file-based information like certificates.
Environment variables may be injected from ConfigMaps.

Variables directly configured in the Pod definition are discouraged.

Side note: Secrets and ConfigMaps should be made [immutable](https://kubernetes.io/docs/concepts/configuration/secret/#secret-immutable)


### Information format

[Clearly define the format of input parameters and results](https://github.com/tektoncd/catalog/blob/main/recommendations.md#clearly-define-the-format-of-input-parameters-and-results).

Atomic information may be passed as a simple parameter. Non binary encoded complex information should be exchanged through [JSON format](https://github.com/tektoncd/catalog/blob/main/recommendations.md#use-composable-parameter-formats) between Tasks.

#### Image references

Tags are not uniquely identifying an image so that we cannot rely on them. They do not guarantee that the scanning is for the image built as part of the PipelineRun if there is a race with a parallel build. As such, image digests will be used for image references.

#### Logging

In containers, logs are usually written to the standard output and collected by the container engine. Then OpenShift Fluentd, Splunk agent or any other tool can forward them to a central aggregator. Using [structured logging](https://docs.openshift.com/container-platform/4.9/logging/cluster-logging-enabling-json-logging.html) with a common format would provide additional value.

Common fields (draft):
- Timestamp, for instance: "2022-02-20T00:28:47.125906354Z"
- Workspace, for instance: "user-1"
- Pipeline, for instance: "test"
- PipelineRun, for instance: "test-wc05gl"
- Task, for instance: "img-scan"
- TaskRun, for instance: "img-scan-er02es"
- CompName, for instance: "hco-bundle-registry-container"
- CompVers, for instance: "v4.10.0"
- CompRel, for instance: "709"

Today NVR is largely used for tracking, for instance hco-bundle-registry-container-v4.10.0-709.

The idea is that the common fields listed above would be populated for each log entry when the information is available.

It is advisable to limit the number of structured fields as it impacts indexing. Fields that are common to multiple tasks should be preferred. Before a field specific to a task is added it is worth thinking whether it is really needed and whether the same information can be conveyed through a more generic field. Information that does not need to be “searchable” can be recorded in an unstructured way.

## Consequences


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
- **Programming language**: Tekton supports “choosing the right language for the right task”. That said, from an operational point of view it is beneficial to limit the number of programming languages needed to support HACBS. Defining “default” languages helps with limiting the skills required to support the platform. This also helps with avoiding knowledge islands where only a few people are able to maintain some Tasks.
- **Failure behavior**: A retry mechanism with configurable timeout and exponential backoff needs to be implemented for technical or functional recoverable failures. A scenario example: An image may not have been completely indexed when the result of the security scan is interrogated. In such a case the Task should have a retry mechanism that may wait till completion of the indexing or time out.
- **Repositories**: Whenever there is no sensitive information we aim to have the PoC sources in a public repository. Is there a public GitHub organization for that? Can we use [this](https://github.com/redhat-appstudio)? When a Task is specifically for Red Hat’s infrastructure it should be kept in a private repository.  Is there a private GitLab group for that?


## References

Originally drafted in a [google document](https://docs.google.com/document/d/1FJX7TH5wBTcWdU2VYuecmkY5O69DGpItN52A-JaoCtU/edit#)
