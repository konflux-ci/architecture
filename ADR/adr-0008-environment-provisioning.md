## References

-   [<u>Discussion recording,
    > 2022-12-07</u>](https://drive.google.com/file/d/1UWIefLzFb2rYnz8mvvWkNKJyuWy-_nhm/view)

## Context

In our old KCP architecture, we had [<u>a
design</u>](https://docs.google.com/document/d/1WKd1FVHAxaNQKCIzIW-vUQRgsoOP9T-8rYozAMDpYc0/edit#)
for provisioning a new deployment target in support of new Environments.
This design was to be implemented in
[<u>GITOPSRVCE-228</u>](https://issues.redhat.com/browse/GITOPSRVCE-228)
by an environment controller that would create and manage sub-workspaces
of the user’s main AppStudio workspace, and that would provide a
serviceaccount to Argo in order to deploy the user’s application to
those sub-workspaces. Now, without KCP, we need a new design.

The Environment CR serves two purposes:

-   First, it represents a request from the user for HAS and the GitOps
    > service to **recognize a new destination** for deployments. A new
    > Environment (when bound to an Application and a Snapshot) causes
    > HAS to write a new directory matching the Environment in the
    > gitops repo, which in turn causes Argo to deploy content from that
    > directory somewhere.

-   Second, it represents a request from the user to **provision a new
    > deployment target**. Back in the KCP design, a new Environment
    > caused the environment controller(s) to create a new
    > sub-workspace, initialize it, and report back a serviceaccount
    > kubeconfig to be used by Argo to administer it.

Some use cases to consider for Environments:

1.  As a part of the StoneSoup workspace initialization process, the
    > user should find that both a **dev and stage environment** with
    > corresponding deployment targets are ready for them
    > ([<u>STONE-180</u>](https://issues.redhat.com/browse/STONE-180)).
    > In our post-KCP architecture, these will be backed by
    > **namespaces** on a devsandbox member cluster.

2.  The user will want to manually create **additional** Environments
    > (for example, a prod environment). The user may want to use our
    > compute resources provided in the form of a new **namespace on a
    > devsandbox member cluster** for this
    > ([<u>STONE-183</u>](https://issues.redhat.com/browse/STONE-183))
    > or they may want to **bring their own cluster** as a target
    > ([<u>STONE-162</u>](https://issues.redhat.com/browse/STONE-162)).

3.  The integration-service expects to be able to create **ephemeral**
    > Environments for automated testing purposes
    > ([<u>STONE-114</u>](https://issues.redhat.com/browse/STONE-114)).
    > For our short-term goals, the automated testing use case requires
    > the same kind of compute as for the dev and stage Environments
    > (devsandbox member cluster namespaces), but will expand to include
    > other kinds of deployment targets in the future - like hypershift
    > clusters
    > ([<u>STONE-185</u>](https://issues.redhat.com/browse/STONE-185)).

## Decision

Amend the Environment API to include an explicit provider, requested by
the user to provide their deployment target. We will implement support
for different providers as extensions to the environment controller.

The bring your own cluster scenario is supported by a user providing
their own target explicitly, and setting provider to a special no-op
provider.

### Example - DevSandbox

Our initial MVP case is to support environments backed by namespaces in
devsandbox member clusters.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: Environment<br />
metadata:<br />
name: staging<br />
spec:</p>
<p>displayName: “Staging”</p>
<p>deploymentStrategy: AppStudioAutomated</p>
<p>parentEnvironment: dev</p>
<p>tags: [staging]</p>
<p>configuration:</p>
<p>provider:</p>
<p>name: devsandbox</p>
<p>env: # env vars shared between all applications deploying to Env<br />
- name: (...)<br />
value: (...)</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

The environment controller sees this new staging environment, sees that
it is requesting devsandbox to provide the deployment target, and it
uses the [<u>proposed SpaceRequest
API</u>](https://docs.google.com/document/d/1uqgghk1lN9dyoBLsvn5YD443TwKrsKHU6fvfUuo84Hs/edit#)
to procure a new namespace with the name “**team-a–staging**”.

The space controller sees the new SpaceRequest and reconciles it to
create the namespace. When done, it updates the SpaceRequest status to
indicate that the new target namespace is ready and in the user’s
appstudio namespace it writes a Secret with a kubeconfig for a
serviceaccount to connect to and administer the new target namespace.

The environment controller waits while its SpaceRequest stabilizes. Once
it has, it modifies the staging Environment CR to include information
about the target namespace from the SpaceRequest and it attaches a
reference to the Secret containing the kubeconfig. Argo eventually will
use this to deploy to the namespace.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: Environment<br />
metadata:<br />
name: staging<br />
spec:</p>
<p>displayName: “Staging”</p>
<p>deploymentStrategy: AppStudioAutomated</p>
<p>parentEnvironment: dev</p>
<p>tags: [staging]</p>
<p>configuration:</p>
<p>provider:</p>
<p>name: devsandbox</p>
<p># The target details are supplied by the environment controller</p>
<p>target:</p>
<p>kubernetesCredentials:<br />
defaultNamespace: team-a--staging<br />
apiURL: …</p>
<p>clusterCredentialsSecret: team-a--staging-secret</p>
<p>env: # env vars shared between all applications deploying to Env<br />
- name: (...)<br />
value: (...)</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

#### Use case descriptions

-   **During onboarding** - when a user requests a new appstudio tier
    > namespace, the tier template includes two Environments, both of
    > which include the provider block but do not specify the target
    > block. On creation, the environment controller (and space
    > controller behind it) provision the target namespaces and
    > eventually supply the target block.

-   **For manual creation of new Environments** - a user submits a form
    > in HAC which creates a new Environment CR with a provider block
    > set to “devsandbox”. Some options to be provided in the form to
    > select between different providers. See section at the bottom for
    > more.

-   **For automated testing in ephemeral environments** - a user
    > specifies an IntegrationTestScenario CR with an existing
    > Environment to clone. After a build completes, but before it
    > executes tests, the integration-service creates a new Environment
    > CR with a devsandbox provider specified, and an empty target. The
    > environment controller (and space controller behind it) provision
    > the target namespace and supply the target block back. When it
    > sees the target block appear, the integration-service knows the
    > Environment is ready and it proceeds to deploy the app via HAS and
    > gitops service, and then ultimately execute tests against that
    > instance of the app. When it is done, integration-service deletes
    > the Environment which causes the environment controller to delete
    > the SpaceRequest, which causes the spacerequest controller to
    > ultimately delete the target namespace.

### Example - BYOC

Eventually, we’ll need to support a “bring your own cluster” (BYOC)
experience. In this scenario, the user should specify a “byoc” or “null”
provider (we can debate a good value to use here) and should supply the
target information themselves.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: Environment<br />
metadata:<br />
name: prod<br />
spec:</p>
<p>displayName: “Production for Team A”</p>
<p>deploymentStrategy: AppStudioAutomated</p>
<p>parentEnvironment: staging</p>
<p>tags: [prod]</p>
<p>configuration:</p>
<p>provider:</p>
<p>name: byoc</p>
<p># The target details are supplied by the user</p>
<p>target:</p>
<p>kubernetesCredentials:<br />
defaultNamespace: my-production<br />
apiURL: …</p>
<p>clusterCredentialsSecret: user-provided-secret-reference</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Here, the environment controller should see that the expected provider
is “byoc”, and do nothing. No reconciliation and procurement of external
resources.

Argo will use the cluster credentials provided by the Secret referenced
in the target that the user provided.

If the user provides invalid credentials or connection details \<some
process> should update the status of the Environment with a warning for
the user.

#### Use case descriptions

-   **During onboarding** - No BYOC environments are created during
    > onboarding.

-   **For manual creation of new Environments** - a user submits a form
    > in HAC which creates a new Environment CR with a provider block
    > set to “byoc”, which they select from some element in the form - a
    > dropdown likely (TBD). See section at the bottom for more.
    > Selecting a “byoc” provider in the form requires them to also
    > specify target details before the api request to create the
    > Environment CR is sent. We could possibly present the user with a
    > list to pick from (powered by OCM?) and/or provide a kubeconfig or
    > credentials either manually or from a
    > [<u>Sources</u>](https://docs.google.com/document/d/1SPYpbrr3VPicQCJgfanU5Nn27idUcT459SeuqcLksMo/edit#)
    > source.

-   **For automated testing in ephemeral environments** - if a user
    > specifies that an IntegrationTestScenario should clone a byoc
    > Environment for testing, it should ….

### Example - Hypershift

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: Environment<br />
metadata:<br />
name: testrun-f6863f30<br />
spec:</p>
<p>parentEnvironment: null</p>
<p>tags: [ephemeral]</p>
<p>configuration:</p>
<p># The provider configuration is used by the environment controller to provision<br />
provider:</p>
<p>name: hypershift</p>
<p>secretRef: secret-containing-provider-specific-credentials</p>
<p># The target details are supplied by the environment controller</p>
<p>target:</p>
<p>kubernetesCredentials:<br />
defaultNamespace: default<br />
apiURL: …</p>
<p>clusterCredentialsSecret: cluster-f6863f30-kubeconfig-secret</p>
<p>env: # env vars shared between all applications deploying to Env<br />
- name: (...)<br />
value: (...)</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Similar to the devsandbox provider example at the beginning, in this
example the user instructs the environment controller to provision a
deployment target for them via a different external service. Here, the
user is requesting an entire new hypershift cluster for their
deployment.

Unlike in the devsandbox example above, the compute here is not free or
provided as a part of the offering. Instead, the user needs to supply
their own credentials to be used by the environment controller’s
provisioner extension.

When the environment controller sees an Environment with a provider
block that looks like the above, it uses some to-be-determined process
to begin provisioning of a fresh hypershift cluster on the user’s
behalf, using credentials provided in the referenced secret in the
user’s namespace. Once that provisioning process is complete, the
environment controller supplies connection details to the new cluster,
including a reference to a secret that contains a kubeconfig to connect
to and administer the new cluster. Argo will use this secret to carry
out deployments.

#### Use case descriptions

-   **During onboarding** - No hypershift or other external environments
    > are created during onboarding.

-   **For manual creation of new Environments** - a user submits a form
    > in HAC which creates a new Environment CR with a provider block
    > set to “hypershift”. Selecting a “hypershift” provider in the form
    > requires them to also upload or select hypershift provisioning
    > credentials before the api request to create the Environment CR is
    > sent. HAC should link the secret containing those credentials to
    > the provider block in the Environment on submission.

-   **For automated testing in ephemeral environments** - if a user
    > specifies that an IntegrationTestScenario should clone a
    > hypershift Environment for testing, it should (like in the
    > devsandbox case) make a copy of the Environment, deleting its
    > target block but preserving its provider block. The new
    > Environment should cause the environment controller to generate a
    > new request for a new hypershift cluster and to provide connection
    > details for that cluster back in the target block, once
    > provisioning is complete.

### Cleanup the type field

The “type” field looks like it was meant to control different kinds of
provided environments, but it is redundant with the proposal here. Let’s
drop it from the next iteration of the Environment CRD.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: Environment<br />
metadata:<br />
name: prod<br />
spec:</p>
<p># Let’s drop the “type” and replace it with a “provider” above. Redundant?</p>
<p># type: poc | non-poc</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

## Other Options

While working on this ADR, we spent time thinking about how to not hide
the provider behind the Environment API but ended up discarding that
option. The complexity of requesting and especially waiting for
fulfillment of external requests from multiple sources (devsandbox, OCM)
was what settled it. Both HAC and integration-service would have to deal
with that complexity. Decision: encapsulate that in the environment
controller, but we have to be careful not let the Environment API become
a leaky abstraction, where too many provider details are exposed.

## Consequences

-   Each time we want to expand to include a new Environment provider,
    > we need to plumb this through the Environment API and extend the
    > environment controller to support whatever that new backend is.
    > We’ll get some consistency in the way those are exposed and
    > provided, at the cost of introducing a potential development
    > bottleneck in the environment controller, which will need to
    > manage the complexity of multiple backends.

# Emulate storage management APIs

In a comment thread earlier in this doc, Gal Ben Haim drafted an
alternative proposal to follow the concepts of storage management in k8s
(see
[<u>persistent-volumes</u>](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
and
[<u>design.md</u>](https://github.com/kubernetes-csi/external-provisioner/blob/master/doc/design.md)).

Miro board describing some aspects of this proposal
([<u>link</u>](https://miro.com/app/board/uXjVP77ztI4=)).

## CRDs

### DeploymentTarget (DT)

A deployment target, usually a K8s api endpoint. The credentials for
connecting to the target will be stored in a secret which will be
referenced in the clusterCredentialsSecret field. A DT Can be created
manually by a user, or dynamically using a provisioner.

**Immutable object**: no

**Scope**: namespace

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: DeploymentTarget<br />
metadata:<br />
name: prod-dt<br />
spec:</p>
<p>deploymentTargetClassName: isolation-level-namespace</p>
<p>kubernetesCredentials:</p>
<p>defaultNamespace: team-a--prod-dtc<br />
apiURL: …</p>
<p>clusterCredentialsSecret: team-a--prod-dtc--secret</p>
<p>claimRef:</p>
<p>name: prod-dtc</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### DeploymentTargetClaim (DTC)

Represents a request for a DeploymentTarget. The phase field indicates
if there is a DT that fulfills the requests of the DTC and whether it
has been bound to it.

**Immutable object**: no

**Scope**: namespace

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: DeploymentTargetClaim<br />
metadata:<br />
name: prod-dtc<br />
spec:</p>
<p>deploymentTargetClassName: isolation-level-namespace</p>
<p>status:</p>
<p>phase: Bound</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### DeploymentTargetClass (DTCLS)

Referred from a DeploymentTarget and DeploymentTargetClaim. Defines
DeploymentTarget properties that should be abstracted from the
controller/user that creates a DTC and wants a DT to be provisioned
automatically for it.

In the example below you can see a class that represents a DT that
grants the requestor access to a namespace. The requestor isn’t aware of
the actual location the DT is going to be provisioned. The parameters
section can be used to forward additional information to the
provisioner. The reclaimPolicy field will tell the provisioner what to
do with the DT once its corresponding DTC is deleted, the values can be
Retain or Delete.

**Immutable object**: yes

**Scope**: cluster

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: DeploymentTargetClass<br />
metadata:<br />
name: isolation-level-namespace<br />
spec:</p>
<p>provisioner: appstudio.redhat.com/devsandbox</p>
<p>parameters: {}</p>
<p>reclaimPolicy: Delete</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### Environment

Environment objects refer to a DTC using the deploymentTargetClaim
field. The environment controller will wait for the DTC to get to the
“bound” phase, once it is bound, it will reach the DT and read the
target's connection details from the kubernetesCredentials field and
configure Argo/Gitops services to use them.

**Immutable object**: no

**Scope**: namespace

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: Environment<br />
metadata:<br />
name: prod<br />
spec:</p>
<p>displayName: “Production for Team A”</p>
<p>deploymentStrategy: AppStudioAutomated</p>
<p>parentEnvironment: staging</p>
<p>tags: [prod]</p>
<p>configuration:</p>
<p>target:</p>
<p>deploymentTargetClaim:</p>
<p>claimName: prod-dtc</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

## Controllers

### DeploymentTargetBinder

Binds DeploymentTargetClaim to a DeploymentTarget that satisfies its
requirements.

It watches for the creation of new DTC and tries to find a matching DT
for each one of them.

A DT that we created dynamically for a specific DTC will always be
attached to it.

DT and DTC have one to one bindings.

### DeploymentTargetProvisioner

Watch for the creation of a new DTC. If the DTCLS of the DTC matches a
DTCLS the provisioner was configured for, it reads the parameters from
that class, provisions the target and creates a DT object which
references the DTC that started the process.

When a DTC is deleted, if it was bound to a DT created by the
provisioner, it reclaims the DT and the actual cluster that was created
for it based on the reclaimPolicy configuration.

### EnvironmentController

| *User,Controller/CRD* | **DT**                | **DTC**               | **DTCLS** | **Environment**      |
|-----------------------|-----------------------|-----------------------|-----------|----------------------|
| **Binder**            | watch/list/get/update | watch/list/get/update |           |                      |
| **Provionser**        | create/delete         | watch                 | get       |                      |
| **Environment**       | get                   | get                   |           | watch                |
| **Integration**       |                       | create                |           | create/delete        |
| **User**              | create/delete         | create/delete         |           | create/delete/update |

## Use Case Descriptions

-   **During onboarding** - when a user requests a new appstudio tier
    > namespace, the tier template includes two Environments, and two
    > DTCs. The Environments reference the DTCs. The DTCs bear a request
    > for the “devsandbox” DTCLS. The devsandbox provisioner responds to
    > that request and generates a SpaceRequest, ultimately resulting in
    > a new namespace for each environment. The SpaceRequest is marked
    > ready by the spacerequest controller. The devsandbox deployment
    > target provisioner controller sees that and marks the devsandbox
    > DT as ready. The deployment target binder sees that, and attaches
    > the new DTs to the DTCs. The environment controller sees this and
    > marks the Environments as ready.

-   **For manual creation of new Environments** - a user submits a form
    > in HAC which creates a new Environment CR and a new DTC CR. The
    > Environment CR references the DTC CR, which is reconciled as in
    > the previous bullet.

-   **For automated testing in ephemeral environments** - a user
    > specifies an IntegrationTestScenario CR with an existing
    > Environment to clone. After a build completes, but before it
    > executes tests, the integration-service creates a new Environment
    > CR and a new DTC CR with the devsandbox DTCLS as above, and
    > references the DTC from the Environment. The integration-service
    > should delete the DTC once the environment isn’t needed anymore
    > for the test.

-   **BYO cluster** - A user creates a DT and a DTC and Secret. The DT
    > has the details and a reference to the secret used to connect to
    > his/hers cluster. In addition, it contains the name of the DTC it
    > should be bounded to. The user then refer to the DTC from the
    > Environment that should use it.

## Mutating DeploymentTargets and Claims

Users may mutate existing DeploymentTargets and DeploymentTargetClaims
in order to, for instance, request that their provisioned cluster is
scaled up to include more resources. However, implementation of resource
request changes is provided on a per-provisioner basis. Some may support
it, and some may not. Most all of our provisioners in the MVP will make
no changes to a DeploymentTarget’s external resources in the event of a
resource request change to either the DeploymentTargetClaim or the
DeploymentTarget.

In the rare case that a provisioner does support resizing external
resources - the user should request resource changes on the
DeploymentTargetClaim, which should then cause the provisioner to resize
the external resources modeled by the DeploymentTarget. Lastly, the
provisioner should update the resources in the spec of the
DeploymentTarget to reflect the external change.

## Consequences

-   Better load distribution between the development teams. An addition
    > of a new provisioner type doesn’t require changing any of the
    > existing controllers.

-   Encapsulate the logic of provisioning/deleting a DeploymentTarget
    > within the provisioner that is responsible for it.

-   Opens the possibility to create DeploymentTargetClaims in advance
    > and by that reducing the waiting time for an ephemeral environment
    > for testing.

-   The design is similar to the design of storage in k8s, so it should
    > look familiar to developers and users.

-   We have a larger API surface than we might ultimately need. Users
    > won’t experience this in the UI, but API-based users will face
    > apparent complexity. The fact that this design emulates the
    > concepts in the k8s storage API should reduce the cognitive load
    > this might impose on users and our engineers.

## Phases

### Phase 0 (Path to MVP)

A note about what features can be left out until later iterations.

-   At minimum, create the CRDs and make them available, with no binder
    > or provisioner controllers behind them.

-   Next, modify the Environment CRD and teach the gitops service how to
    > navigate from the linked DTC to the DT in order to find the Secret
    > that it needs for Argo.

Minimal functionality looks like the BYOC case: No provisioners
necessary - and even the binder can be omitted in this first pass.

-   On workspace initialization, have the NsTemplateTier:

    -   Create Spaces with fixed -dev and -stage suffixes manually as a
        > part of the appstudio tier

    -   Create serviceaccounts with rolebindings to administer the
        > namespaces

    -   Create DeploymentTargets to match and reference Secrets that
        > will be created to contains tokens for the serviceaccounts in
        > the previous steps.

    -   Create DeploymentTargetClaims to match.

    -   Create Environments to match.

-   As long as the secret names generated by the SpaceRequests are
    > predictable, then it should be possible to specify all of these
    > objects up front.

### Phase 1 (Service Preview)

The result of this phase is an automation that binds DT and DTC and
automatically provisioned environment on the Sandbox cluster (using the
[<u>SpaceRequest
API</u>](https://docs.google.com/document/d/1uqgghk1lN9dyoBLsvn5YD443TwKrsKHU6fvfUuo84Hs/edit#))
and creates a DT.

The following controllers should be implemented:

-   Binding controller.

-   Sandbox provisioner.

-   Adjusting the integration service controller to create and delete a
    > DTC

### Phase 2 (need more grooming and clear requirement from the PM)

The result of this phase is the ability to specify parametes that are
needed from the deployment target, such has memory, CPU, CPU
architecture and the number of nodes.

-   The DT, DTC an DTCLS would need to extended to support the new
    > parameters.

    -   **DTCLS - allowTargetResourceExpansion** - represents whether or
        > not the underlying provisioner allows targets to be resized.
        > I.e., for a whole cluster provided by the "hypershift" ocm
        > provider - can it have its number or size of nodes increased
        > without having to delete it and create a new one.

    -   DTC - **Immutable object**: no, for bound claims, only the
        > resources map can be updated. When updating a resource, its
        > new value can’t be less than the previous value.

-   The Sandbox provisioner should be extended to use the properties
    > mentioned above (when those applicable) when creating external
    > resources and a DT.

-   The matching algorithm in the binding controller will need to take
    > into account the added parameters.

#### DeploymentTarget (DT)

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: DeploymentTarget<br />
metadata:<br />
name: prod-dt<br />
spec:</p>
<p>deploymentTargetClassName: isolation-level-namespace</p>
<p>resources:</p>
<p>requests:</p>
<p>memory: 16Gi</p>
<p>cpu: 8m</p>
<p>limits:</p>
<p>memory: 16Gi</p>
<p>cpu: 8m</p>
<p>arch: x86–64</p>
<p>kubernetesCredentials:</p>
<p>defaultNamespace: team-a--prod-dtc<br />
apiURL: …</p>
<p>clusterCredentialsSecret: team-a--prod-dtc--secret</p>
<p>claimRef:</p>
<p>name: prod-dtc</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

#### DeploymentTargetClaim (DTC)

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: DeploymentTargetClaim<br />
metadata:<br />
name: prod-dtc<br />
spec:</p>
<p>deploymentTargetClassName: isolation-level-namespace</p>
<p>resources:</p>
<p>requests:</p>
<p>memory: 16Gi</p>
<p>cpu: 8m</p>
<p>limits:</p>
<p>memory: 16Gi</p>
<p>cpu: 8m</p>
<p>arch: x86–64</p>
<p>status:</p>
<p>phase: Bound</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

#### DeploymentTargetClass (DTCLS)

Hypershift cluster with 3 nodes example:

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: DeploymentTargetClass<br />
metadata:<br />
name: isolation-level-cluster-small<br />
spec:</p>
<p>provisioner: appstudio.redhat.com/hypershift</p>
<p>parameters:</p>
<p>numOfNodes: 3</p>
<p>reclaimPolicy: Delete</p>
<p>allowTargetResourceExpansion: false</p></th>
</tr>
<tr class="odd">
<th></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

### Phase 3

The result of this phase is to automatically provisioning of Hypershift
cluster using Stonesoup credentials. We call it “provided compute”
(compute that we provide, not the user) and it’s included as part of the
offering. This compute can be used for both long lived clusters and for
ephemeral clusters used by the integration service.

For long lived clusters, the maintenance model for them is yet to be
determined.

#### DeploymentTargetClass (DTCLS)

Hypershift cluster with 3 nodes example:

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: DeploymentTargetClass<br />
metadata:<br />
name: isolation-level-cluster-small<br />
spec:</p>
<p>provisioner: appstudio.redhat.com/hypershift</p>
<p>parameters:</p>
<p>numOfNodes: 3</p>
<p>reclaimPolicy: Delete</p>
<p>allowTargetResourceExpansion: false</p></th>
</tr>
<tr class="odd">
<th></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Hypershift cluster with 6 nodes example:

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p>apiVersion: appstudio.redhat.com/v1alpha1<br />
kind: DeploymentTargetClass<br />
metadata:<br />
name: isolation-level-cluster-large<br />
spec:</p>
<p>provisioner: appstudio.redhat.com/hypershift</p>
<p>parameters:</p>
<p>numOfNodes: 6</p>
<p>reclaimPolicy: Delete</p>
<p>allowTargetResourceExpansion: false</p></th>
</tr>
<tr class="odd">
<th></th>
</tr>
</thead>
<tbody>
</tbody>
</table>
