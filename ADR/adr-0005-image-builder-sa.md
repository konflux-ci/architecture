# 5. Service Account configuration for image builds in the Pipeline Service 

Date: Oct 5, 2022

## Status

Accepted

## Context

The `serviceAccount` used for running a `PipelineRun` workload in a workload cluster needs to have the right SCCs and linked credentials to be able to successfully execute a container image build. The linked credentials will mostly originate from the KCP workspace where the `PipelineRun` was synced from.
Additionally, the SCC association needed for elevating capabilities required for image builds isn't something we'd prefer to expose the user to.



## Decision

* As a Pipeline Service platform feature, any service/user intending to build a container image would need to create and use the "pipeline-service-image-builder" service account in the KCP workspace. 
Use of any other service accounts will not lead to a successful assembling of the image.

* The AppStudio Build controller would tap into this platform contract to create relevant PipelineRuns for building container images.

* The Pipeline Service Platform would configure the "pipeline-service-image-builder" service account in the execution environment ( ie, the workload cluster ) out-of-the-box.

## Consequences



### Implementation - Pipeline Service 

* The contract/API between users and the platform is the "pipeline-service-image-builder" `serviceAccount` which consumers would be expected to use in the KCP workspace 
for `PipelineRuns` if they wish to build container images. 
* The Pipeline Service platform would configure workload clusters with the `[cluster]rolebindings` necessary to have the "pipeline-service-image-builder" `serviceAccount`. The infrastructure machinery driving the deployment of the `clusterrole`/`clusterrolebinding` should be capable of upgrading the privileges being assigned.
configured with a tailor-made SCC such that they are sufficiently capable of building container images.
* The service account does not necesarily need to be created in advance in the workload cluster by the Pipeline Service platform. Consumers of the Pipeline Service ( as specified in the next section ) would create this service account in the KCP workspace and have the same synced into the workload cluster's namespace. When the service account does get synced, the `[cluster]rolebindings` configured should kick-in to privide the appropriate elevation of privilege.


### Implementation - AppStudio Build Service Controller

* The AppStudio Build controller creates an "pipeline-service-image-builder" service account in the KCP workspace/namespace. This service account needs to be created so that it's made available in the workspace for linking the secrets in the subsequent step. 
* The AppStudio Build controller links the image pull secret ( previously created by SPI ) with the "pipeline-service-image-builder" `serviceAccount` in the KCP workspace/namespace. Upon doing so, the 'updated' "pipeline-service-image-builder" `serviceAccount` would get synced into the workload cluster.
* The AppStudio Build controller creates the PipelineRun referencing the "pipeline-service-image-builder" service account as the one that the PipelineRun/TaskRun `Pods` would run as. Upon doing so, the PipelineRun would get synced into the Pipeline Service Workload cluster.
* And that's it! Since the `[cluster]rolebinding` in the Workload cluster for all "pipeline-service-image-builder" `serviceAccounts` would be pre-configured ( by the Pipeline Service ) with the SCC needed to build container images, the image should be successfully assembled. 
* Additionally, since the service account had 
the linked credentials, the container image should be successfully pushed as well.


### Security considerations

* Users should not be able to alter role bindings in their `workspaces`/`namespaces` in a way that they impact the execution environment in the workload clusters. This will help prevent SCC escalations by the users/services whose workloads would be scheduled on the PipelineService workload cluster.
* Build Controller would have to be granted permissions to create/edit service accounts in the workspace to be to create/update the `pipeline-service-image-builder` service account for linking secrets/credentials. 
* The Pipeline Service platform should be able to disallow usage of this elevated privilege by certain consumers of the service. The design for the same should be addressed in a future ADR.
