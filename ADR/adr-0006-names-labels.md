# 1. Record architecture decisions

Date: 2022-November-11

## Status

Accepted

## Approvers

* Ann Marie Fred
* Gorkem Ercan

## Reviewers

## Context

We need naming standards in various contexts, to make App Studio easier to operate and maintain.

## Decision 1: Namespace labels

We will apply the following labels to App Studio namespaces, to make them easier to find.

- `appstudio.redhat.com/namespacetype: "controller"` for namespaces containing App Studio controllers
- `appstudio.redhat.com/namespacetype: "user-workspace-data"` for User workspaces where Applications, Components, and so on are defined
- `appstudio.redhat.com/namespacetype: "user-deployments"` for the namespaces where GitOps deploys applications for users
- `appstudio.redhat.com/namespacetype: "user-builds"` for the namespaces where the Pipeline Service has PipelineRuns

## Decision 2: Log conventions

In our controller logs, we will use structured, JSON-formatted audit log messages with key-value pairs as described below.

Fluentd and Fluent Bit annotate log messages with the following information automatically: `namespace_name`, `container_name`, `pod_name`, `container_image`, `pod_ip`, `host`, `hostname`, `namespace_labels`, `message`, `level`, `time`, and more. The cluster, node, pod and container names are also part of the log stream name.  For example:
  Under /aws/containerinsights/`Cluster_Name`/application
  - Fluent Bit optimized configuration sends logs to `kubernetes-nodeName`-application.var.log.containers.`kubernetes-podName`_`kubernetes-namespace`_`kubernetes-container-name`-`kubernetes-containerID`
  - Fluentd sends logs to `kubernetes-podName`_`kubernetes-namespace`_`kubernetes-containerName`_`kubernetes-containerID`

For more details on Fluentd vs. Fluent Bit logs, see [Set up Fluent Bit as a DaemonSet to send logs to CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-setup-logs-FluentBit.html).

It is best to avoid using the same key as the log collectors in our controller logs, to avoid confusion.

### 1. When did it happen? 

Timestamps will be in UTC/ISO-8601 format.

### 2. What happened?

Use the key `action` with possible values `ADD, UPDATE, DELETE`.

### 3. Where did it happen?

Use the key `appstudio-component` with possible values `HAS, SPI, GITOPS`, etc. Here is [sample code](https://github.com/redhat-appstudio/application-service/blob/9f25d1f6832568598c718423b1e2f7d9161ad790/controllers/component_controller.go#L549) from the HAS component.

- GitOps Service: `GITOPS`
- Pipeline Service: PLNSRVCE
- Build Service: BUILD
- Workspace and Terminal Service: TBD
- Service Provider Integration: `SPI`
- Hybrid Application Service: `HAS`
- Enterprise Contract: EC
- Java Rebuilds Service: JAVA
- Release Service: TBD
- Integration Service: TBD

### 4. Who was involved?

Use the key `namespace` when logging the namespace of the targeted resource that is being modified.

### 5. Where it came from? 

Use the key `kind` with possible resource kind values determined by the component team.  For example, for HAS this can be `CDQ, Application, Component`, etc. 

Use the key `resource` with the name of the resource being acted upon.

Optionally, use the key `source` to direct developers to the source code where the action occurred. 

### Application audit logs

For the specific types of audit logs required by SSML.PW.5.1.4 Perform Event Logging, one of the key-value pairs in the log entry should be `audit: true`. This makes it easier to query aggregated logs to find these special log entries.

More details can be found in [SSML-8093](https://issues.redhat.com/browse/SSML-8093), and a good example of a working implementation can be found in the [GitOps code](https://github.com/redhat-appstudio/managed-gitops/blob/c962ae99ec50e273c8cdf90d8f3a07f7a8944dc5/backend-shared/util/log.go#L28) implemented for [this story](https://issues.redhat.com/browse/GITOPSRVCE-186).

## Consequences

TBD
