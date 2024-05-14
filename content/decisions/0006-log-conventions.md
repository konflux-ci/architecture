---
title: Log Conventions
number: 6
---
# Log Conventions

* Date started: 2022-11-11
* Date revised: 2023-03-08
* Date revised: 2023-03-29

## Status

Accepted

## Context

We need log conventions to make our offering easier to operate and maintain. These will also make it possible for us to create queries that cross components in our logs, which supports [STONE-201](https://issues.redhat.com/browse/STONE-201).

We initially decided to require log messages formatted by the `console` encoder, thinking that it would be advantageous to be able to consume logs in a human readable format directly from our controller pods (2023-03-08), but on [subsequent review](https://redhat-internal.slack.com/archives/C02C3SE8QS2/p1680074942662149?thread_ts=1680071345.179399&cid=C02C3SE8QS2) we realized that this bears an undesirable cost in configuration of our logging: the default encoder for the "production" profile in zap is the `json` encoder (2023-03-29).

## Decision: Log conventions

In our controller logs, we will use structured log messages, formatted in JSON with key-value pairs as described below.

For example:

```
{"ts": "2023-03-07T11:32:29.167Z", "level": "info", "logger": "controllers.Component", "msg": "updating devfile component name kubernetes-deploy ...", "namespace": "samburrai-tenant", "name": "go-net-http-hello-prqx", "controllerKind": "Component"}
{"ts": "2023-03-07T11:32:29.020Z", "level": "info", "logger": "controllers.Component", "msg": "API Resource updated", "namespace": "samburrai-tenant", "audit": "true", "name": "go-net-http-hello-prqx", "controllerKind": "Component", "action": "UPDATE"}
```

The **ts** field stands for "timestamp" (encoded as UTC/ISO-8601) and the meaning of log **level** should be self evident. The **logger** name helps your team understand which part of your service is emitting the log (usually `Log.WithName` from `zap`). The **msg** is a human readable string describing the event being logged. Further **json** key value pairs contain additional fields useful for searching. See full list of fields in the [Appendix](#appendix).

The opinionated logging mechanism from the controller-runtime framework already conforms to this scheme. Care should be taken to make sure specific key/value pairs are logged.

### 1. When did it happen?

**Included in:** `ts`

Encode timestamps in UTC/ISO-8601 format.

### 2. What happened?

**Included in:** `msg` and `action`

Use the key `action` with possible values `VIEW`, `ADD`, `UPDATE`, and `DELETE`, if applicable.

Optionally, also describe the action in the human-readable `msg`.

### 3. Where did it happen?

**Included in:** _none_

There is no need to identify which Konflux subsystem the log is coming from (i.e., HAS, SPI, or
GitOps).

Consider: if an engineer is looking at logs directly in the namespace where a controller is
deployed, then you know which service you are looking at. If an engineer is looking at logs
centralized in cloudwatch or splunk, then the namespace from which the log came will be included
automatically as `namespace_name`, which is sufficient to determine what Konflux subsystem
produced the log. See section on automatically added logs below.

### 4. Who was involved?

**Included in:** `msg` and `namespace`

Use the key `namespace` when logging the namespace of the *targeted resource* that is being modified
or interacted with. (Note that the `namespace_name` key is automatically added by the fluent
collectors and reflects the namespace in which the controller is running. See section on
automatically added logs below.)

Optionally, also refer to the namespace of the *targeted resource* in the human-readable `msg`.

### 5. Where it came from?

**Included in:** `msg`, `controllerKind`, `name`, `logger`, and `caller`

Use the key `controllerKind` with possible resource kind values determined by the component team. For example, for HAS this can be `Application`, `Component`, etc. For SPI this can be `SPIAccessToken`. The `controllerKind` key is automatically added to the log context by operator-sdk.

Use the key `name` with the name of the resource being acted upon. The `name` of the resource is
automatically added to the log context by operator-sdk.

Optionally, use the key `logger` to describe the part of your controller that is emitting the log.

Optionally, use the key `caller` to direct developers to the line of source code where the event was logged ([example in SPI](https://github.com/redhat-appstudio/service-provider-integration-operator/blob/6444c804324e550fdb5492e1d744a76558e7d623/pkg/logs/logs.go#L51)).

Optionally, refer to these in the human-readable `msg`.

### Controller audit logs

**Included in:** `audit`

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

### Out of Scope

**TaskRun logs** are specifically out of scope of this ADR. Those logs are typically meant to be
viewed and interpreted by users. Use human-readable strings for most logs in that context.

**Upstream controllers** are also out of scope. Where possible, influence upstream controllers to
align to this ADR. It would just be nice. But it would be unreasonable to try to bring all of our
dependencies under the same log scheme.

**User application** logs are out of scope. Obviously, we cannot control their log format, nor do we
want to for the goals of this ADR.

## Consequences

* Since (almost) all of our controllers (operators) are based on the controller-runtime framework
  (e.g. via operator-sdk), and it has an opinionated logging mechanism (utility function in
  `sigs.k8s.io/controller-runtime/pkg/log`, log frontend is logr, log backend is zap), and since this
  logging mechanism already conforms to the prescribed format, and can be used, it should be
  _easier_ for teams to conform to this ADR than would be otherwise.

  For example, using the standard controller-runtime logging mechanism will produce a json string in
  the prescribed format:

```go
logger "sigs.k8s.io/controller-runtime/pkg/log"

func f() {
    log = logger.FromContext(ctx)

    log.Info("log message", "jsonfield1", "jsonfield1value", etc... )
}
```

* By using structured logs that are formatted entirely as JSON, we lose "easy readability" of
  production controller pod logs, in exchange for simplifying the zap configuration of our services
  between development and production. It should still be easy for human engineers to read logs in
  centralized log aggregators (like CloudWatch) which is the primary use case we want to support.
* Individual teams should still be able to include key value pairs in their controller logs that are
  not mentioned in this doc, enabling debugging methods unique to that controller.
* We decided to omit including a `user_id` for situations where one is relevant. This would be
  helpful for audit purposes (see "Who was involved?" above). But, the user id in our system is the
  same as the username, which constitutes PII - which we do not want to log and forward to other
  systems. If we decide that we do need a `user_id` for audit purposes in the future, then we will
  need to revisit this decision.
* The `namespace` (the namespace of the targetted resource under reconciliation) today is of the
  form `<username>-tenant`. Today, it contains PII. As a part of the implementation work to align
  subsystems with this ADR we should include requests to update the scheme for naming new user
  workspaces to be something that does not include PII, for instance `<hash(username)>-tenant`. See
  also [ADR 10]({{< relref "0010-namespace-metadata.md" >}}) and [ADR 12]({{< relref "0012-namespace-name-format.md" >}}).

## Appendix

### JSONSchema

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "ts": {
      "description": "Timestamp of the event",
      "type": "string"
    },
    "level": {
      "description": "Level of the log event (debug, info, etc..)",
      "type": "string"
    },
    "logger": {
      "description": "Name of the logger used to produce the event",
      "type": "string"
    },
    "msg": {
      "description": "Human-readable description of the logged event",
      "type": "string"
    },
    "action": {
      "description": "Indicates what action the log event is responding to",
      "type": "string",
      "enum": ["VIEW", "ADD", "UPDATE", "DELETE"]
    },
    "namespace": {
      "description": "Indicates the target namespace of the resource being reconciled",
      "type": "string"
    },
    "controllerKind": {
      "description": "The kind of the resource being reconciled",
      "type": "string"
    },
    "name": {
      "description": "The name of the resource being reconciled",
      "type": "string"
    },
    "caller": {
      "description": "A reference to the line of source code that is emitting this log",
      "type": "string"
    },
    "audit": {
      "description": "Set to true for specific types of audit logs required by SSML.PW.5.1.4",
      "type": "boolean"
    }
  },
  "additionalProperties": true,
  "required": ["ts", "level", "msg"],
  "not": {
    "required": [
      "namespace_name",
      "container_name",
      "pod_name",
      "container_image",
      "pod_ip",
      "host",
      "hostname",
      "namespace_labels",
      "message",
      "level",
      "time"
    ]
  }
}
```
