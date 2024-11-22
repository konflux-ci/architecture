# 47. Creating pending pipeline runs

Date: 2024-11-21

## Status

Accepted

## Context

When pipelines start, the time is immediately being taken away from the configured timeout (even if their pods are waiting for resources). While this behavior is likely sufficient when fewer concurrent pipelines are running, timeouts are more likely to be exceeded when bulk builds are triggered (i.e. a Renovate job updating common dependencies). While the speed at which a pipeline completes is important, a delayed and completed pipeline will likely finish quicker than an immediately and timeout-killed pipeline. Futhermore, having multiple pipelines running at the same time may starve other concurrent pipelines from acquiring the necessary resources resulting in fewer completed pipelines.

So say you started 300 pipeline runs on Friday evening and you expect to see 300 new images by Monday morning.
You have resource quota for 20 concurrent builds, so 20 builds get started, when they finish 20 more and so on.
But because all 300 pipeline runs started (from Tekton point of view) when they were created, after few iterations all the remaining pipeline runs will be cancelled (due to a timeout).

When many pipelines are triggered across multiple namespaces, there is also an increased load on etcd which may degrade the cluster's overall performance.

## Decision

We will use idea of creating pipeline runs in pending state and having a standalone controller that would implement any custom logic on when to start each pending pipeline:

1. We add `.spec.status: "PipelineRunPending"` to pipeline run YAMLs.
1. We will implement controller, that will contain code that will decide when to start (by just nulling `.spec.status` field - then Pipelines Controller takes over) what pipeline run. Some possibilities come to mind:
   1. Controller will keep an eye on current number of concurrently running pipeline runs in the cluster (using Prometheus metric `avg(tekton_pipelines_controller_running_pipelineruns)`), and if that is below given threshold, it starts the pipeline run(s).
   1. If pipeline run have `prsstarter.example.com/mpc_platforms: linux/arm64,linux/ppc64le,linux/s390x` annotation, controller checks if MPC have free capacity (using max for the pool and Prometheus metric `multi_platform_controller_running_tasks`) for mentioned platforms and if so, will start it.

## Consequences

With this we should be able to create a stable queue of pipeline runs, stabilize cluster at peak times and provide higher builds reliability.

If we implement upper concurrent pipeline runs cap, it will make sure we do not attempt to run more builds on the cluster than what the cluster can handle, it will help solve currently seen etcd outages.

If we implement MPC limiting, it will make sure pipeline runs are not timeouting because of MPC pool being used by builds started earlier.

### Example

This is an example of controller that +- implements this MPC limiting log:

```
2024-11-20 14:04:44,646 prs_starter Thread-3 (my_capacity_counter) INFO Loaded MPC capacity: {'linux/arm64': 7, 'linux/ppc64le': 32, 'linux/s390x': 0}
2024-11-20 14:04:49,659 prs_starter.my_reconciler Thread-2 (my_reconciler) DEBUG Reconciling my-comp-2-on-push-zz6sw/jhutar-tenant (429faf3a-620d-4ccd-ac89-c7ba4db11c90)
2024-11-20 14:04:49,659 prs_starter.my_reconciler Thread-2 (my_reconciler) DEBUG Missing capacity for my-comp-2-on-push-zz6sw/jhutar-tenant (429faf3a-620d-4ccd-ac89-c7ba4db11c90) on linux/s390x
2024-11-20 14:04:49,659 prs_starter.my_reconciler Thread-2 (my_reconciler) DEBUG Reconciling my-comp-3-on-push-hj5bw/jhutar-tenant (ba328d32-e912-4a2c-98e8-506937577912)
2024-11-20 14:04:49,659 prs_starter.my_reconciler Thread-2 (my_reconciler) DEBUG Missing capacity for my-comp-3-on-push-hj5bw/jhutar-tenant (ba328d32-e912-4a2c-98e8-506937577912) on linux/s390x
2024-11-20 14:04:57,309 prs_starter Thread-3 (my_capacity_counter) INFO Loaded MPC capacity: {'linux/arm64': 7, 'linux/ppc64le': 32, 'linux/s390x': 1}
2024-11-20 14:04:59,659 prs_starter.my_reconciler Thread-2 (my_reconciler) DEBUG Reconciling my-comp-2-on-push-zz6sw/jhutar-tenant (429faf3a-620d-4ccd-ac89-c7ba4db11c90)
2024-11-20 14:04:59,660 prs_starter.my_reconciler Thread-2 (my_reconciler) INFO Capacity available for my-comp-2-on-push-zz6sw/jhutar-tenant (429faf3a-620d-4ccd-ac89-c7ba4db11c90) on all considered platforms
2024-11-20 14:04:59,660 prs_starter.my_reconciler Thread-2 (my_reconciler) INFO Starting my-comp-2-on-push-zz6sw/jhutar-tenant (429faf3a-620d-4ccd-ac89-c7ba4db11c90)
2024-11-20 14:05:00,529 prs_starter.my_reconciler Thread-2 (my_reconciler) INFO The my-comp-2-on-push-zz6sw/jhutar-tenant (429faf3a-620d-4ccd-ac89-c7ba4db11c90) was started, not watching it anymore
2024-11-20 14:05:00,529 prs_starter.my_reconciler Thread-2 (my_reconciler) DEBUG Reconciling my-comp-3-on-push-hj5bw/jhutar-tenant (ba328d32-e912-4a2c-98e8-506937577912)
2024-11-20 14:05:00,529 prs_starter.my_reconciler Thread-2 (my_reconciler) DEBUG Missing capacity for my-comp-3-on-push-hj5bw/jhutar-tenant (ba328d32-e912-4a2c-98e8-506937577912) on linux/s390x
```

This is what was happening:

* at 2024-11-20 14:04:44,646, we checked MPC capacity and s390x was fully used, so reconciling pipeline runs (that are in pending state) `my-comp-2-on-push-...` and `my-comp-3-on-push-...` did not started them
* at 2024-11-20 14:04:57,309, we noticed MPC freed the capacity for s390x
* at 2024-11-20 14:04:59,660 pipeline run `my-comp-2-on-push-...` was started, no luck for `my-comp-3-on-push-...` though

Currently this is POC code only and besides lots of other things, we know about these issues that would need to happen:

* [KFLUXBUGS-1474](https://issues.redhat.com/browse/KFLUXBUGS-1474) - metric `multi_platform_controller_running_tasks` can give negative numbers
* [KFLUXINFRA-1062](https://issues.redhat.com/browse/KFLUXINFRA-1062) - MPC metric showing pool size for individual platforms
