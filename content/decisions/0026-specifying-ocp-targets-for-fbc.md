---
title: Specifying OCP targets for File-based Catalogs
number: 26
---
# Specifying OCP targets for File-based Catalogs

* Date 2023-06-08

## Status

Accepted

## Context

One of the supported component types within Konflux are [File-based Catalogs (FBC)].
These catalogs can either be used in isolation with a version of `opm` packaged in the container
itself or in conjunction with other catalog configurations via a service such as
[IIB Image Builder]. Red Hat OpenShift Container Platform (OCP) is one example of a platform that
leverages FBCs for defining the operator graphs. In order to enable operator support to vary on a
version-by-version basis, Red Hat maintains one catalog per OpenShift version.

In order to support being able to target FBC components to specific versions of Red Hat OpenShift,
Konflux needs to be able to keep track of the specific targeted version. In addition to the concerns
around releasing FBC components to OpenShift, the version of `opm` used by each version of OpenShift
may differ, so the Konflux integration process will need to ensure that tests are run using an appropriate
binary version.

## Decision

All FBC components intending to be released to OCP will be built using a OCP-specific parent image containing
the target version number as a tag. This will result in a `FROM` instruction like

```
# The base image is expected to contain
# /bin/opm (with a serve subcommand) and /bin/grpc_health_probe
FROM registry.redhat.io/openshift4/ose-operator-registry:v4.12
```

While the annotation "org.opencontainers.image.base.name" is populated by buildah, any additional image build
processes for the FBC components will also need to include this annotation indicating the pullspec of the base
image. The annotation will enable all components to use `skopeo` to inspect the artifact to retrieve the pullspec:

```bash
$ skopeo inspect --raw docker://quay.io/hacbs-release-tests/managed-release-team-tenant/sample-fbc-application/sample-fbc-component@sha256:da4bf45ba45b72aa306dc2889572e92bbac43da08de0a0146e2421f506c5517e | jq
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.manifest.v1+json",
  "config": {
    "mediaType": "application/vnd.oci.image.config.v1+json",
    "digest": "sha256:c83abcfb3af92d9b8ccea573fce6560a90919e77a8024c8269969b7799a2385c",
    "size": 21327
  },
  "layers": [
    [...]
  ],
  "annotations": {
    "org.opencontainers.image.base.digest": "sha256:e5a07eff6865b2761889ee275d9fc940237c90d05d63b00f60350841ecf42df2",
    "org.opencontainers.image.base.name": "registry.redhat.io/openshift4/ose-operator-registry:v4.12"
  }
}
```

The target Red Hat OpenShift version will then be able to be pulled from the image tag on the
"org.opencontainers.image.base.name" annotation. If a task within the Konflux pipeline needs to access
an appropriate `opm` binary for performing validation, it can determine the base image and use the binary from
that container if it is trusted (for example, if it is an image from the
`registry.redhat.io/openshift4/ose-operator-registry` repository), or fail if the base image isn't trusted.


## Consequences

* Konflux services should be able to avoid directly using the `opm` version packaged in FBC components
  to prevent the execution of untrusted binaries by a process in the trusted control plane.
* No additional kubernetes objects need to be created to track the target OCP versions
* There is a desire to use [FBC templates] within Konflux in the future. The current decision can be
  re-evaluated if and when that functionality is introduced.

[FBC templates]: https://olm.operatorframework.io/docs/reference/catalog-templates/
[File-based Catalogs (FBC)]: https://olm.operatorframework.io/docs/reference/file-based-catalogs/
[IIB Image Builder]: https://github.com/release-engineering/iib
