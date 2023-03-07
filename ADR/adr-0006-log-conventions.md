# ADR-0006 Log Conventions

Date: 2022-November-11

## Status

Accepted

## Approvers

* Ann Marie Fred
* Gorkem Ercan

## Reviewers

## Context

We need log conventions to make our offering easier to operate and maintain. These will also make it possible for us to create queries that cross components in our logs.

## Decision: Log conventions

In our controller logs, we will use structured log messages, partially formatted in JSON with key-value pairs as described below.

```
TIMESTAMP LOG_LEVEL LOGGER MESSAGE ADDITIONAL_JSON_DATA
```

For example:

```
2023-03-07T11:32:29.167Z    INFO    controllers.Component   updating devfile component name kubernetes-deploy ...   {"resource": "samburrai-tenant/go-net-http-hello-prqx", "kind": "Component"}
2023-03-07T11:32:29.020Z    INFO    controllers.Component   API Resource changed: UPDATE {"namespace": "samburrai-tenant", "audit": "true", "resource": "go-net-http-hello-prqx", "kind": "Component", "action": "UPDATE"}
```

The meaning of **timestamp** and log level should be self evident. The **logger** name helps your team understand which part of your controller is emitting the log (usually `Log.WithName` from `zap`). The **message** is a human readable string describing the event being logged. The **json data** contains additional fields useful for searching.

### 1. When did it happen?

Encode timestamps in UTC/ISO-8601 format.

### 2. What happened?

Use the key `action` with possible values `VIEW, ADD, UPDATE, DELETE`.

### 3. Where did it happen?

There is no need to identify which stonesoup subsystem the log is coming from (i.e., HAS, SPI, or
GitOps).

Consider: if an engineer is looking at logs directly in the namespace where a controller is
deployed, then you know which service you are looking at. If an engineer is looking at logs
centralized in cloudwatch or splunk, then the namespace from which the log came will be included
automatically as `namespace_name`, which is sufficient to determine what stonesoup subsystem
produced the log. See section on automatically added logs below.

### 4. Who was involved?

Use the key `namespace` when logging the namespace of the *targeted resource* that is being modified
or interacted with. (Note that the `namespace_name` key is automatically added by the fluent
collectors and reflects the namespace in which the controller is running. See section on
automatically added logs below.)

Include a `user_id` if one exists and is applicable for the event being logged.

### 5. Where it came from?

Use the key `kind` with possible resource kind values determined by the component team.  For example, for HAS this can be `CDQ`, `Application`, `Component`, etc.

Use the key `resource` with the name of the resource being acted upon.

Optionally, use the key `source` to direct developers to the source code where the action occurred.

### Controller audit logs

For the specific types of audit logs required by SSML.PW.5.1.4 Perform Event Logging, one of the key-value pairs in the log entry should be `audit: true`. This makes it easier to query aggregated logs to find these special log entries.

More details can be found in [SSML-8093](https://issues.redhat.com/browse/SSML-8093), and a good example of a working implementation can be found in the [GitOps code](https://github.com/redhat-appstudio/managed-gitops/blob/c962ae99ec50e273c8cdf90d8f3a07f7a8944dc5/backend-shared/util/log.go#L28) implemented for [this story](https://issues.redhat.com/browse/GITOPSRVCE-186).

### Automatically added fields

Note that fluentd and Fluent Bit will annotate your log messages with the following information automatically:

* `namespace_name`
* `container_name`
* `pod_name`
* `container_image`
* `pod_ip`
* `host`
* `hostname`
* `namespace_labels`
* `message`
* `level`
* `time`
* and more.

The cluster, node, pod and container names are also part of the log stream name.  For example, under `/aws/containerinsights/<Cluster_Name>/application`:

* Fluent Bit optimized configuration sends logs to `<kubernetes-nodeName>-application.var.log.containers.<kubernetes-podName>_<kubernetes-namespace>_<kubernetes-container-name>-<kubernetes-containerID>`
* Fluentd sends logs to `<kubernetes-podName>_<kubernetes-namespace>_<kubernetes-containerName>_<kubernetes-containerID>`

For more details on Fluentd vs. Fluent Bit logs, see [Set up Fluent Bit as a DaemonSet to send logs to CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-setup-logs-FluentBit.html).

It is best to avoid using the same key as the log collectors in our controller logs, to avoid confusion.

### TaskRun logs

TaskRun logs are specifically out of scope of this ADR. Those logs are typically meant to be viewed
and interpreted by users. Use human-readable strings for most logs in that context.

## Consequences

* It should become easier to create queries that cross components in our logs.
* Individual teams should still be able to include key value pairs in their controller logs that are
  not mentioned in this doc, enabling debugging methods unique to that controller.
