
Enterprise Contract
===================

Overview
--------

The Enterprise Contract's purpose is to ensure container images produced by
Konflux meet certain clearly defined requirements before they are considered
releasable. Should a container image not meet the requirements the Enterprise
Contract will produce a list of the reasons why so they can be addressed as
required to produce a releasable build.

Enterprise Contract requirements fall broadly into two categories, "built-in
requirements"[^1] and "rule-based requirements".

### Built-in requirements

The built-in requirements are as follows:

- The container image is signed with a known and trusted key
- The image has an attestation, also signed with a known and trusted key

### Rule-based requirements

The rule-based requirements are based on the content of the pipeline run
attestation and are defined using [Rego](https://tekton.dev/docs/chains/), the
[Open Policy Agent](https://tekton.dev/docs/chains/) query language.

Some examples of rule-based requirements are:

- Tasks used in the pipeline run were defined in known and trusted task bundles
- A defined set of tests were run during the pipeline build with passing results

The technique of checking for a specific task result from a specific known and
trusted task definition is a useful way to create a robust policy rule. The
rego language is flexible and expressive so it's easy to create arbitrary
policy rules based on anything exposed in pipeline run attestation.


Components
----------

### EC CLI

The ec-cli is a command line utility written in Go. Its primary purpose is to
perform the EC policy validation, which it does as follows:

- For each image included in the release[^2]
    - Confirm the image is signed and verify the signature
    - Confirm the image has a signed and verifiable attestation
    - For each "policy source group"[^3] defined in the ECP CRD config:
        - Download all defined policy (rego) sources
        - Download all defined data sources
        - Run [Conftest](https://www.conftest.dev/) against the image's attestation using those policies and data
- Output results in JSON format showing details about failures, warnings or violations produced

The ec-cli also supports other related functions. For more information on
ec-cli refer to the
[documentation](https://enterprise-contract.github.io/ec-cli/main/reference.html)
and the [code](https://github.com/enterprise-contract/ec-cli).

### EC Task Definition

The EC Task Definition defines how the ec-cli command should be run in a
Tekton task. It handles the task inputs and outputs and calls the ec-cli as
needed to perform the EC validation.

The task is defined
[here](https://github.com/enterprise-contract/ec-cli/blob/main/task/0.1/verify-enterprise-contract.yaml).

### EC Policy CRD

The ECP CRD defines a Kubernetes CR which is used to hold the configuration
needed for running a specific instance of the Enterprise Contract. This
includes the public key required to verify signatures, the list of policy
and data sources, and any other required configuration.

You can view the source code for the ECP CRD
[here](https://github.com/conforma/crds) and
see its documentation [here](https://enterprise-contract.github.io/ecc/main/).
See also the related
[API Reference](https://redhat-appstudio.github.io/architecture/ref/enterprise-contract.html)

### EC Policies

The reference set of policy rules for Konflux is defined
[here](https://github.com/enterprise-contract/ec-policies/) and documented
[here](https://enterprise-contract.github.io/ec-policies/). It includes rules for a
range of different policies that are considered useful for Konflux.

There are Conftest bundles containing the latest version of these policies
available in [quay.io
here](https://quay.io/repository/enterprise-contract/ec-release-policy?tab=tags).


Related Components
------------------

### Tekton Chains

Tekton Chains is a dependency for EC since EC works by examining attestations
created by Tekton Chains when Konflux build pipelines are running.

For more information on Tekton Chains refer to the
[documentation](https://tekton.dev/docs/chains/), and the GitOps configuration
[here](https://github.com/openshift-pipelines/pipeline-service/tree/main/operator/gitops/argocd/tekton-chains).

### The Release Pipeline

The Konflux Release Pipeline contains an instance of the EC Task which is used
to gate the release. If the EC task fails the release should be blocked. This
functionality is handled by the Release Pipeline.

For more information, see [Konflux Release Service
Bundles](https://github.com/redhat-appstudio/release-service-bundles).

### EC and Renovate Bot

To verify that tasks used in the build pipeline are from known and trusted
Tekton bundles, EC requires a list of those bundles.

Konflux users can leverage the [Renovate
Bot](https://github.com/renovatebot/renovate#readme) service to keep such
Tekton bundle lists up to date. The service can be configured to run
periodically, and provide pull requests with updated references.
Alternatively, users can run their own instance of Renovate either as a
service or on-demand.


Additional Resources
--------------------

- [Konflux Documentation](https://redhat-appstudio.github.io/docs.appstudio.io)
- [Enterprise Contract Documentation](https://enterprise-contract.github.io/)
- [Architecture of Konflux](https://redhat-appstudio.github.io/architecture/)



[^1]: Not sure about the terminology here. Do we have a better term for
    requirements enforced by ec-cli that are not defined by rego rules?

[^2]: The list of images in a release is defined in a Snapshot CRD. The input
    to EC is a JSON formatted representation of this image list, but a
    single image is also supported.

[^3]: Not sure about this terminology either. Conceptually the "source group"
    consists of one or more policy sources and zero or more data sources.


<!---
Notes and todos
---------------

- Once we have the new EC task Tekton bundle and push automation stable we
  should mention it here.
- As per [^4] the pipeline definition validation is not mentioned, but
  it probably should be since that is a key feature of EC.
- IIUC there is an instance of the EC task that is triggered after every build,
  i.e. well before the release pipeline is started. This doc should probably
  mention it and describe it.
- It seems like there should be a link to docs with more details on how
  Renovate could be used, but I'm not sure if we have any yet.
- Once we decide on some of the terminology footnotes ^1 and ^3 can be
  removed.
- Note that the source group stuff has not yet been implemented. I'm
  describing how I think it will work in the future, so we should review
  later and remove this note.
- Would some diagrams be useful? What would they look like?
- Currently this document doesn't mention Rekor, but perhaps it should, even
  though we are not currently using Rekor.

--->
