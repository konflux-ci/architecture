# 58. Maven Build Pipelines

Date: 2025-12-08

## Status

Implementable

## Context

Currently, Konflux lacks a native Java build experience, forcing developers to use Containerfiles
for Java builds. The results are pushed as container images, which cannot be easily consumed by
dependent Java projects.

Apache [Maven](https://maven.apache.org/index.html) is the most widely adopted build tool for Java
projects, although it is not hold and exclusive position. Java projects with Maven are distributed
through [Maven Repositories](https://maven.apache.org/repositories/index.html), whose model has
adopted by other Java build tools like [Gradle](https://gradle.org/).

### Goals for this feature

- Provide a primary build experience for Java projects using Maven within Konflux.
- Enable developers to specify custom Maven commands ("goals") during the build process, as well as
  input parameters/arguments.
- Facilitate the publication of Java artifacts (JAR, WAR, POM) to a configured Maven repository for
  use in a wider Konflux Application (or `ComponentGroup`).


### Key Requirements

- Developers must be able to select a base builder image containing a desired OpenJDK and Maven
  version. Red Hat provides OpenJDK builders bundled with Maven 3.x through its UBI8 and UBI9
  catalogs.
- The pipeline must invoke a reasonable default set of `mvn` commands (`mvn clean deploy`) to a
  "dev" repository when code is merged. Code should not be deployed to a Maven repository for pull
  request builds.
- Developers must be able to provide arguments and CLI flags to the `mvn` command.
- The build must produce OCI artifact references (`*_IMAGE_URL` and `*_IMAGE_DIGEST` or `IMAGES`)
  for Tekton Chains to generate provenance and signatures.
- Support for [multi-module](https://maven.apache.org/guides/mini/guide-multiple-modules.html)
  projects is required.

### Non-Goals

- Support for [Maven 4](https://maven.apache.org/whatsnewinmaven4.html).
- Support for Gradle.
- Support for Kotlin, Scala, or other JVM-based programming languages.
- Provision Maven repositories for Java projects.

These can all be addressed through follow-up ADRs.

## Decision

The build pipeline will execute up to two "deployments":

- The pipeline will first deploy Maven artifacts to a container registry using ORAS.
- The pipeline will optionally execute a second deployment to a real Maven repository, if one is
  configured.

The core pipeline task, `maven-deploy-oras`, performs the following steps:

1. **analyze:** Determine if deployment/snapshot repositories are configured and if the project
   version is a `-SNAPSHOT`.
2. **build-maven:** Execute the following to build the Maven project and stage the built artifacts
   locally:
   
   ```
   mvn clean ${MAVEN_EXTRA_GOALS} deploy ${MAVEN_EXTRA_OPTS} \
     -DaltDeploymentRepository=local::file:./target/stage-deploy
   ```

3. **deploy-maven (Conditional):** If a real Maven repository is configured, perform a second
   `mvn deploy` to the appropriate remote Maven repository.
4. **Deploy-ORAS:** Use the ORAS CLI to push the full local staging directory tree to the container
   registry:

   ```
   oras push ${IMG_URL} ./target/stage-deploy \
     --artifact-type application/vnd.apache.maven.repository.v2.tar+gzip \
     --export-manifest manifest-out.
   ```

   The artifact type `application/vnd.apache.maven.repository.v2.tar+gzip` communicates that this
   image is non-runnable, with contents compressed with `gzip`. The output manifest is used for
   Tekton Chains signing.

The pipeline will also include the following tasks:

- `generate-sbom`: this will generate the required component-level Software Bill of Materials from
  multiple sources, aggregated with [Mobster](https://github.com/konflux-ci/mobster):
  - The [CycloneDX Maven Plugin](https://github.com/CycloneDX/cyclonedx-maven-plugin) if the Maven
    project has configured its use.
  - [Syft](https://github.com/anchore/syft)
  - Hermeto once Maven is supported as a package manager (design is
    [under discussion](https://github.com/hermetoproject/hermeto/pull/1046))
- `build-source-container`: this will build a source container, using existing tasks in the Konflux
  catalog.
- `scan-xxxx`: these will be additional scanning tasks, using tools in the Konflux catalog. Tools
  that do not support scanning of OCI artifacts or a direct local directory will be excluded.

## Consequences

### Positive Consequences

- Aligns with Konflux's current container image building methodology, making integration easier.
- Directly addresses the user stories and goals by providing a native Maven experience, artifact
  publication, and required security attestations (SBOM, provenance).
- Does not require teams to provision a Maven repository manager, though this practice is highly
  recommended.

### Drawbacks (Negative Consequences)

- **Double Deploy:** This process performs a "double deploy" when a real Maven repository is used,
  consuming double the required storage capacity.
- **SNAPSHOT Version Mismatch:** The generated timestamp version for `-SNAPSHOT` releases published
  to the container registry will differ from the one published to the real Maven repository. The
  file contents, however, will have the same checksums.
- **Large Artifacts:** The output is a single OCI artifact containing an entire Maven repository,
  which can be very large (over 100 binary artifacts for some projects).
- **SBOM Size:** The combined SBOM for multi-module projects can be enormous and potentially not
  applicable to products at runtime.
- **Scanning Limitations:** Due to the output not being a runnable container image, not all
  existing scanning tools (like Clair, Clamav, Coverity) are likely to support it.

### Rejected Alternatives

**Push to Pulp**: Pulp has an OCI storage integration that allows uploaded artifacts to have an
associated OCI artifact digest. This alternative was rejected for several reasons:

- Although Pulp has some support for [Maven repositories](https://pulpproject.org/pulp_maven/docs/user/guides/deploy/),
  its plugin is missing critical features needed to be used in a production environment.
- This would create a hard dependency on Pulp in the build pipeline. As a general rule, Konflux
  pipelines should utilize industry standards for publishing artifacts when one is available. This
  allows adopters to bring their infrastructure of choice.
- The number of artifacts to sign and attest could become enormous depending on the project being
  built. Some projects, like [Apache Camel](https://github.com/apache/camel), can produce hundreds
  of artifacts in a single build. The sheer volume of image references in the required Tekton task
  result could potentially hit etcd storage limitations.

**Push to Registry Only:** This alternative was rejected because Maven projects are not natively
capable of consuming content directly from a container registry; they require a package repository
that exposes the expected Maven APIs. Adoptees should not be forced to consume everything though
a container registry.
