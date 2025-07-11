# XX. Upstreaming Integration Service

Date: 2023-11-05

## Status

Proposed

## Authors

- Ralph Bean

## Context

This ADR is part of series aiming to address *independent* usage of our controllers and services to
see if they are viable on their own. We have always assumed they would be used together, and
therefore some architectural assumptions need to be identified and changed in order to decouple
them.

See also [Decoupling Deployment] for related context.

Today, [integration-service] does the following things:

- **Snapshot Construction**: When a pipelines-as-code (PaC) PipelineRun completes,
  [integration-service] uses the [Component] API (the "global candidate list") to construct
  a [Snapshot], in order to trigger testing.
- **Test Initiation**: When anything creates a [Snapshot], [integration-service] consults the list
  of available [IntegrationTestScenario] resources provided by the user and takes a series of
  actions to facilitate testing and promotion of that [Snapshot].
- **DeploymentTarget Provisioning**: If any [IntegrationTestScenarios] specify a related
  [Environment], then [integration-service] will clone that environment, in order to provision a new
  bare environment for testing.
- **App Deployment**: If any [IntegrationTestScenarios] specify a related
  [Environment], then after cloning the environment, [integration-service] will initiate deployment
  of a version of the application to be tested. See also [Decoupling Deployment].
- **Snapshot Test Results Recording**: As PipelineRuns corresponding with the [IntegrationTestScenarios]
  complete, [integration-service] updates test results on the [Snapshot].
- **Source Repo Test Results Reporting**: As PipelineRuns corresponding with the [IntegrationTestScenarios]
  complete, [integration-service] updates test results in the source repo service's API (like the
  github "checks" API).
- **Global Candidate List Maintenance**: When all PipelineRuns corresponding with the
  [IntegrationTestScenarios] that are marked as non-optional complete and if the [Snapshot] is
  designated as a post-merge [Snapshot], then [integration-service] updates the "global candidate
  list" by way of the [Component] API.
- **Release Initiation**: When all PipelineRuns corresponding with the [IntegrationTestScenarios]
  that are marked as non-optional complete and if the [Snapshot] is designated as a post-merge
  [Snapshot], and if there is a [ReleasePlan] in the namespace with auto-release enabled, then
  [integration-service] updates the "global candidate list" by way of the [Component] API and
  creates a [Release] CR to initiate a release in [release-service].

Note that **Snapshot Construction** and **Global Candidate List Maintenance** are related: the only
purpose of global candidate list maintenance is to support snapshot construction.

## Decision

- **App Deployment** and **DeploymentTarget Provisioning** will be dropped, per the [Decoupling Deployment] ADR.
- **Release Initiation** will become the responsibility of [release-service]. See more below.
- [integration-service] will continue to own **Test Initiation**, **Snapshot Test Results Recording**,
  and **Source Repo Test Results Reporting**.
- **Snapshot Construction** and **Global Candidate List Maintenance** will remain responsibilities
  of [integration-service], but will undergo some changes to remove dependence on external APIs.

### The Snapshot becomes the TestSubject

[integration-service] will fork the [Snapshot] API to a new resource under its domain
named [TestSubject].

The purpose of this change is to make [integration-service] independent of other APIs. The name
[TestSubject] is chosen to reflect what the [Snapshot] represented *in [integration-service]'s
domain* in our original architecture.

### References to the Application become a label or selector

Today, you can tell which [Application] a [IntegrationTestScenario] and [Snapshot] refer to by way
of an `application` reference in the `spec`. However, with our goal of decoupling
[integration-service] from the rest of the controllers in mind, we need to remove this reference.

Instead of adding an `application` reference to a [TestSubject], use a label called `LABELNAME` to
identify which [IntegrationTestScenarios] it is relevant to.

On the [IntegrationTestScenario], drop the `application` from the spec and replace it with
a [selector] which the user can use to reference the `LABELNAME` label on [TestSubjects]. It should
be possible for the user to specify a selector that references any attribute they wish. The user
should conclude naturally that `LABELNAME` is a good candidate for usage in their selectors. UI and
docs can guide this.

- A new [TestSubject] without a `LABELNAME` label should be mutated by webhook to gain a value of
  "default".
- Attempts to remove the `LABELNAME` label from a [TestSubject] should be rejected (or mutated to
  "default"?)
- Attempts to edit the `LABELNAME` label on a [TestSubject] should be permitted.

### The Global Candidate List becomes the control TestSubject, the last TestSubject to pass testing

Today, the "global candidate list" is a term that we use to refer to the list of all the built-image
pullspecs attached to every [Component] of an [Application]. Replace that implementation
with an identifying *label* on a [TestSubject] in the namespace: `CONTROLLABEL`. Call the [TestSubject] that
carries this `CONTROLLABEL` label the **control** TestSubject for the `LABELNAME` label.

[integration-service] should grow a mutating webhook that *removes* the `CONTROLLABEL` label from
the last control [TestSubject] for the `LABELNAME` label, when the `CONTROLLABEL` label is applied
to a new [TestSubject] bearing the `LABELNAME` label.

The **control** TestSubject is used as the *basis* for new TestSubject construction. See
"TestSubject Construction as optional behavior", below.

[integration-service] should promote a [TestSubject] under test to become the new **control**
TestSubject after it passes all of the required IntegrationTestScenarios with the matching
`LABELNAME` label.

### TestSubject Construction as optional behavior

**Test Initiation** has a clear control plane: the [IntegrationTestScenario] combined with the
[TestSubject]. Meaning, when the user creates an [IntegrationTestScenario] and a [TestSubject], and
the [selector] of the [IntegrationTestScenario] matches the attributes of [TestSubject], then together
they represent intent for the subject to be tested. The user uses these resources to control what
the system does.

Today, control of the **Snapshot Construction** process is mixed up in the [Application] and [Component]
model, and is partly just implied. We *always* construct [Snapshots].

**TestSubject Construction** (called Snapshot Construction in our system today) should have a clear
control plane resource: the [TestSubjectConstructor]. A hypothetical schema for the resource
follows:

```yaml
version: appstudio.redhat.com/v1alpha1
kind: TestSubjectConstructor
metadata:
  name: my-application-test-subject-constructor
spec:
  selector:
    fields:
      match:
        kind: PipelineRun
        version: tekton.dev/v1
    labels:
      match:
        "appstudio.openshift.io/application": my-application
        "pipelinesascode.tekton.dev/state": completed
  extractor:
    image_url: '.status.results.[] | select(.name == "IMAGE_URL").value'
    image_digest: '.status.results.[] | select(.name == "IMAGE_DIGEST").value'
    name: '.metadata.labels."appstudio.openshift.io/component"'
    source:
      git:
        revision: '.metadata.labels."pipelinesascode.tekton.dev/sha"'
        url: '.metadata.labels."pipelinesascode.tekton.dev/repo-url"'
```

Don't take the fields literally. The details will likely change after the ADR has settled. It is
here for illustration purposes.

The `selector` field will be used to identify resources that should trigger the construction of new
[TestSubjects]. When created, the *basis* for the new test subject should always be taken from the
**control** [TestSubject]. The values extracted from the triggering resource by way of the
expressions on the `extractor` resource should be applied to that basis in the construction of a new
[TestSubject]. If there is no **control** [TestSubject], then the new TestSubject should be created
containing only one element: the new pullspec.

In the above example, the constructor will select only pipelineruns which are completed and which
are associated with the app `my-application`. When triggered, it will extract the same image and
source details that we extract today to supply to a new [TestSubject].

### Release Initiation, as owned by the release-service

For the purpose of this ADR, we will only say that release-service will take over the
responsibility of initiating Releases. That will be described in more detail in a subsequent,
forthcoming ADR.

Note, in this pattern, [Release] construction looks a lot like [TestSubject] construction. The
triggered system knows enough about the triggering system to optionally initiate itself.

## Use Cases in Detail

**Using integration-service as a remote API from Jenkins.** A hypothetical platform team might want
to make use of [integration-service] from a jenkins pipeline. For example, perhaps their jenkins job
performs CI on a git repository that contains pullspecs which should be mirrored to some environment
of theirs. Before mirroring, they want to make sure that the same test works against dozens of
different kubernetes configurations on different public clouds. That platform team first
creates tekton pipelines that contains the logic to perform the test, and use [Dynamic Resource
Allocation APIs] to request provisioning of those clusters.
They then configure dozens of [IntegrationTestScenario] resources, one for each kubernetes
configuration they want to target. When a new set of pullspecs is proposed to their git repo,
Jenkins responds. Jenkins then creates a single [TestSubject] in the kubernetes namespace,
representing the new set of images under test. [integration-service] responds, inspecting all of the
defined [IntegrationTestScenarios] and it runs tests of the [TestSubject] against
each. The aggregate results are stored in the `status` of the [TestSubject] for jenkins to monitor
and report back to the platform team in CI.

**Using integration-service with TestSubject automation.** A hypothetical platform team might want
to make use of [integration-service] in conjunction with tekton pipelines that they use for
building images. Imagine, every night they have a cron trigger which rebuilds their images using
a static Dockerfile that installs the latest debian packages available to a base image and then
rebuilds all of their utility images on that new base image. Their pipelines expose the pullspecs of
all of those images as results. The platform team configures a [TestSubjectConstructor] which
instructs the [test-subject-construction-controller] to watch all PipelineRuns in their namespace with
a certain label. As those builds finish, the [test-subject-construction-controller] constructs new
[TestSubjects] by combining the image list from the **control** [TestSubject] with the new pullspec
found in the result with the name described in the [TestSubjectConstructor]. The platform team
benefits from integration-service's [two-phase architecture]. They build reports on the history of
[TestSubjects] to understand when some new debian package has broken their suite of images.

**Using integration-service in AppStudio** From the user's point of view, AppStudio should work like
it does today. Our tier template needs to be modified to put a [TestSubjectConstructor] in place
that instructs [integration-service] to construct [TestSubjects] in response to our [PaC]
PipelineRuns.

## Consequences

- [integration-service] now knows nothing about [Applications], [Components], [Environments],
  [DeploymentTargets], etc. It will now only depend on Tekton APIs.
- We should now be able to tell a story about how someone might want to use [integration-service] on
  a cluster that only carries the Tekton APIs. The purpose of
  integration-service is to trigger *integration tests on collections of container images*. You can
  instruct it to do this on a case by case basis by creating TestSubject resources, or you can
  configure a [TestSubjectConstructor] to instruct it to create its own [TestSubjects].
- [integration-service] today has only one CustomResource of its own: [IntegrationTestScenario].
  After this change, it will have three: [IntegrationTestScenario], [TestSubject], and
  [TestSubjectConstructor] resource.
- We lose some ability to validate references between resources owned by different AppStudio
  controllers. Previously, if an IntegrationTestScenario was created referencing an Application
  which did not exist, we could reject that IntegrationTestScenario early, notifying the user of
  their error. Now that the Application reference is replaced with a `LABELNAME` label, we don't
  have enough information to know if the user has made a typo or not.  This decrease in our ability
  validate is a byproduct of the decoupling.

[Dynamic Resource Allocation APIs]: https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/
[TestSubject]: #
[TestSubjects]: #
[TestSubjectConstructor]: #
[TestSubjectConstructors]: #
[test-subject-constructor-controller]: #
[integration-service]: ../book/integration-service.md
[release-service]: ../book/release-service.md
[pac]: https://pipelinesascode.com/
[two-phase architecture]: https://github.com/redhat-appstudio/book/blob/main/ADR/0015-integration-service-two-phase-architecture.md
[decoupling deployment]: https://github.com/redhat-appstudio/book/pull/147
[selector]: https://kubernetes.io/docs/concepts/overview/working-with-objects/field-selectors/
[Application]: ../ref/application-environment-api.md#application
[Applications]: ../ref/application-environment-api.md#application
[Component]: ../ref/application-environment-api.md#component
[Components]: ../ref/application-environment-api.md#component
[Environment]: ../ref/application-environment-api.md#environment
[Environments]: ../ref/application-environment-api.md#environment
[GitOpsDeploymentManagedEnvironment]: ../ref/application-environment-api.md#GitOpsDeploymentManagedEnvironment
[GitOpsDeploymentManagedEnvironments]: ../ref/application-environment-api.md#GitOpsDeploymentManagedEnvironment
[SnapshotEnvironmentBinding]: ../ref/application-environment-api.md#snapshotenvironmentbinding
[SnapshotEnvironmentBindings]: ../ref/application-environment-api.md#snapshotenvironmentbinding
[Snapshot]: ../ref/application-environment-api.md#snapshot
[Snapshots]: ../ref/application-environment-api.md#snapshot
[Release]: ../ref/release-service.md#Release
[Releases]: ../ref/release-service.md#Release
[ReleasePlan]: ../ref/release-service.md#ReleasePlan
[ReleasePlans]: ../ref/release-service.md#ReleasePlan
[ReleasePlanAdmission]: ../ref/release-service.md#ReleasePlanAdmission
[ReleasePlanAdmissions]: ../ref/release-service.md#ReleasePlanAdmission
[IntegrationTestScenario]: ../ref/integration-service.md#IntegrationTestScenario
[IntegrationTestScenarios]: ../ref/integration-service.md#IntegrationTestScenario
[DT]: ../ref/application-environment-api.md#deploymenttarget
[DTs]: ../ref/application-environment-api.md#deploymenttarget
[DeploymentTarget]: ../ref/application-environment-api.md#deploymenttarget
[DeploymentTargets]: ../ref/application-environment-api.md#deploymenttarget
[DTC]: ../ref/application-environment-api.md#deploymenttargetclaim
[DTCs]: ../ref/application-environment-api.md#deploymenttargetclaim
[DeploymentTargetClaim]: ../ref/application-environment-api.md#deploymenttargetclaim
[DeploymentTargetClaims]: ../ref/application-environment-api.md#deploymenttargetclaim
[DTCls]: ../ref/application-environment-api.md#deploymenttargetclass
[DTClses]: ../ref/application-environment-api.md#deploymenttargetclass
[DeploymentTargetClass]: ../ref/application-environment-api.md#deploymenttargetclass
[DeploymentTargetClasses]: ../ref/application-environment-api.md#deploymenttargetclass
