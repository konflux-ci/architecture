---
date: 2023-09-27T00:00:00Z
title: Tekton Results Naming Convention
number: 30
---
# Tekton Results Naming Convention

## Status

Accepted

Relates to:
* [ADR 13. Konflux Test Stream - API contracts](0013-integration-service-api-contracts.html)
* [ADR 14. Let Pipelines Proceed](0014-let-pipelines-proceed.html)

## Context

In order to [Let Pipelines Proceed](0014-let-pipelines-proceed.html), the default interface of a Tekton Task's status code becomes an unsuitable API contract for communicating the successes and failures of tasks. [ADR 13. Konflux Test Stream - API contracts](0013-integration-service-api-contracts.html) established the first API contract for Tekton result standardization within Konflux for the built-in Task definitions when task failure was not an option. As Konflux onboarding continues, more non-default tasks (partner and user tasks, for example) will be defined and the current standardization's narrow scope may start to confuse task authors. Further compounding this issue is the lack of a concrete guidance or standard from the Tekton community around standard sets of result names. Therefore, the Konflux components should adhere to generic standards for supported results types while still enabling the platform to operate within the Tekton result size limitations.

## Decision

The following decision holds for all Pipeline Tasks denoted as must succeed in the build pipeline

> All scanning and linting TaskRuns should *succeed* even if they find problems in the content they
are evaluating. [[ADR-0014](0014-let-pipelines-proceed.html)]

If tasks exist outside of the build pipeline, they _may_ adhere to the following decisions or they may fall back to the status (failing or succeeding) of a TaskRun.

There are two defined standards for minimized [Tekton result](https://tekton.dev/docs/pipelines/tasks/#emitting-results) formats based on the common task types -- test-like and scan-like tasks. Each of these standards will have a unique result name as well as their own result format.

The standards presented in this ADR supersede those in [ADR 13. Konflux Test Stream - API contracts](0013-integration-service-api-contracts.html). All other standards presented in the previous ADR hold unless _this_ ADR is superseded by an additional ADR that deprecates those standards. These other non-deprecated standards presented include [Detailed Conftest Output JSON](0013-integration-service-api-contracts.html#detailed-conftest-output-json), [Information injection](0013-integration-service-api-contracts.html#information-injection), [Information format](0013-integration-service-api-contracts.html#information-format), and [Image references](0013-integration-service-api-contracts.html#image-references).

### Results for Test-like Tasks
Test-like tasks are those whose results can be immediately classified as successful or failed. If these tests are taken into account in the final suitability of an artifact for promotion or release, then all pass/fail determination would be deferred to the task run.

The output of each Tekton task will be provided in a minimized [Tekton result](https://tekton.dev/docs/pipelines/tasks/#emitting-results) in JSON format listing the categories of reported test results and the count of results within each. The name of the result will be **TEST_OUTPUT**.

For tasks processing multi-arch images, the output should be a single JSON object that aggregates the total number of results across all image manifests of different architectures to represent an overview of the tests performed on the multi-arch image, regardless of the architecture.

#### Tekton Result Format for `TEST_OUTPUT`

The output of the Tekton result **TEST_OUTPUT** will be a JSON object that includes the context about the test along with the list of check names for all failed checks

The output will provide the following information about the overall test result:
- **result** - The outcome of the testing task, can be `SUCCESS`, `FAILURE`, `WARNING`, `SKIPPED` or `ERROR`. For multi-arch images, the *result* value in the aggregated JSON object should reflect the highest priority status encountered, in accordance to the following rank order: `ERROR`, `FAILURE`, `WARNING`, `SKIPPED`, `SUCCESS`.
- **namespace** - The rego namespace for the test policy. If not set, it will be assumed to have the value `default`
- **timestamp** - A RFC3339 formatted timestamp of the test completion time
- **successes** - The number of successful checks in the form of an integer
- **note** - A short note provided by test definition to provide additional information. For multi-arch images, the *note* should correspond to the *result* value that was selected adhering to the rank order mentioned above.
- **failures** - The number of failed checks in the form of an integer
- **warnings** - The number of warning checks in the form of an integer


#### `TEST_OUTPUT` Schema Validation
The output of the Tekton result **TEST_OUTPUT** can be validated using the following schema:

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
      "pattern": "^((?:(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2}(?:\.\d+)?))(Z|[\+-]\d{2}:\d{2})?)$"
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

### Results for Scan-Like Tasks
Scan-like tasks are those that search for issues within the code base or artifact whose results raise concerns (vulnerabilities) according to some internal severity or classification metric. These results are expressly different from test-like results as there may need to be additional criteria applied to the results to determine what vulnerabilities are permissable for the final artifact.

Scan-like results should still use the **TEST_OUTPUT** result for indicating whether the scan has run successfully or if it has errored, but this output should not indicate a failure.

To display count of found vulnerabilities and make it easy to understand and evaluate the state of scanned content, the additional output of scan-like tasks will be provided in a minimized [Tekton result](https://tekton.dev/docs/pipelines/tasks/#emitting-results) in JSON format listing. The name of the result will be **SCAN_OUTPUT**.

While the vulnerability classifications should remain consistent in order to enable easier extensions into other Konflux components (namely the user interface and enterprise contract), it is the responsibility of every scan-like task to inform the user about what criteria fits each vulnerability classification used. The vulnerability classifications from most important/severe to least are **critical**, **high**, **medium**, and **low**. If a vulnerability is classified as **unknown** then the scanner cannot make further judgement about its severity.

Some scanners are additionally aware of whether a specific vulnerability is patched or unpatched (i.e. whether there is a known fix that has been published by the vulnerable package's maintainers). If vulnerabilities are known to be unpatched, the scanner may use the **unpatched_vulnerabilities** object to represent their quantities and severities.

For multi-arch scans, the output should be a single JSON object that aggregates the total number of vulnerabilities per severity across all image manifests of different architectures to represent an overview of the present vulnerabilities in the multi-arch image manifest, regardless of the architecture.

#### Tekton Result Format for `SCAN_OUTPUT`
The output of the Tekton result **SCAN_OUTPUT** will be a JSON object that includes the following information about the found vulnerabilities. While the vulnerability classification may vary based on the scanner used in the task, an example description of vulnerability severity ratings can be found at the [Red Hat Vulnerability documentation](https://access.redhat.com/articles/red_hat_vulnerability_tutorial).

```
{
  "vulnerabilities": {
    "critical": 1,
    "high": 0,
    "medium": 1,
    "low":0,
    "unknown":0
  },
  "unpatched_vulnerabilities": {
    "critical": 0,
    "high": 1,
    "medium": 0,
    "low":1
  }
}
```

#### `SCAN_OUTPUT` Schema Validation
The output of the Tekton result **SCAN_OUTPUT** can be validated using the following schema:

```
{
  "$schema": "http://json-schema.org/draft/2020-12/schema#",
  "type": "object",
  "properties": {
    "vulnerabilities": {
      "type": "object",
      "properties": {
        "critical": {
          "type": "integer",
          "minimum": 0
        },
        "high": {
          "type": "integer",
          "minimum": 0
        },
        "medium": {
          "type": "integer",
          "minimum": 0
        },
        "low": {
          "type": "integer",
          "minimum": 0
        },
        "unknown": {
          "type": "integer",
          "minimum": 0
        }
      },
      "required": ["critical", "high", "medium", "low"]
    },
    "unpatched_vulnerabilities": {
      "type": "object",
      "properties": {
        "critical": {
          "type": "integer",
          "minimum": 0
        },
        "high": {
          "type": "integer",
          "minimum": 0
        },
        "medium": {
          "type": "integer",
          "minimum": 0
        },
        "low": {
          "type": "integer",
          "minimum": 0
        },
        "unknown": {
          "type": "integer",
          "minimum": 0
        }
      },
      "required": ["critical", "high", "medium", "low"]
    }
  },
  "required": ["vulnerabilities"]
}
```

### Results for Tasks that Process Multiple Images

When scans and tests ingest an image reference as input, the actual content that is tested or scanned is ambiguous due to the potential presence of multi-arch images. If the image reference is an Image Manifest, for example, then that image would be known to be scanned. If the image reference is an Image Index, however, the Task could be processing all images referenced (i.e. all platforms/architectures), or just a single Image Manifest such as the one corresponding the the pod's architecture.

In order to disambiguate the image references corresponding to the other Tekton results, a Task may output an additional result indicating the images that have been processed in order to obtain the otherwise specified result(s). The name of the result will be **IMAGES_PROCESSED**.

#### Tekton Result Format for `IMAGES_PROCESSED`
The test output of the Tekton result **IMAGES_PROCESSED** will be a JSON object that includes the context about the image references that have been processed.

In the case that the image processed is an Image Manifest, the result may look like the following:

```
{
  "image": {
    "pullspec": "quay.io/foo/bar:baz",
    "digests": [
      "sha256:bb8[...]"
    ]
  }
}
```

In the case that the image processed is an Image Index, the result may look like the following:

```
{
  "image": {
    "pullspec": "quay.io/foo/bar:baz",
    "digests": [
      "sha256:bb8[...]",
      "sha256:cc9[...]",
      "sha256:dd0[...]"
    ]
  }
}
```


#### `IMAGES_PROCESSED` Schema Validation
The output of the Tekton result **IMAGES_PROCESSED** can be validated using the following schema:

```
{
  "$schema": 'https://json-schema.org/draft/2020-12/schema',
  "type": "object",
  "properties": {
    "image": {
      "type": "object",
      "properties": {
        "pullspec": {
          "type": "string"
        },
        "digests": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "required": [
        "pullspec",
        "digests"
      ]
    }
  },
  "required": [
    "image"
  ]
}
```

## Consequences

* Until a time arrives when a standard is set upstream around the best practices for defining a result API, Konflux will define its own standard for adherence.
* In situations where pipelines do not _need_ to proceed, (**IntegrationTestScenario**s, for example), this API does not need to be leveraged. Instead, the default API of the Task's status of success/failure can be used in lieu of the test-like results.
