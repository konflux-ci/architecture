# 58. Maven Build Pipelines

Date: 2025-12-08

## Status

Implementable

## Context

Currently, Konflux lacks a native Java build experience, forcing developers to use Containerfiles
for Java builds. The results are pushed as container images, which cannot be easily consumed by
dependent Java projects. Konflux should provide validated build pipelines for Java projects to
expand its relevance beyond the container/Cloud Native ecosystem.

There are multiple build tools, frameworks, and even programming languages within the Java
ecosystem. Apache [Maven](https://maven.apache.org/index.html) is the most widely adopted build
tool for "standard" Java projects, although it is not the only one. Java projects built with Maven
are often distributed through [Maven Repositories](https://maven.apache.org/repositories/index.html),
whose model has been adopted by other Java build tools like [Gradle](https://gradle.org/).

### Goals for this feature

- Provide a primary build experience for Java projects using Maven within Konflux.
- Enable developers to specify custom Maven commands ("goals") during the build process, as well as
  input parameters/arguments.
- Facilitate the publication of Java artifacts (JAR, WAR, POM) to a configured Maven repository for
  use in a wider Konflux `Application` (or `ComponentGroup`).

### Key Requirements

- Developers must be able to select a base builder image containing a desired OpenJDK and Maven
  version. Red Hat provides OpenJDK builders bundled with Maven 3.x through its UBI8 and UBI9
  catalogs.
- The pipeline must invoke a reasonable default set of `mvn` commands (`mvn clean deploy`) to build
  and publish Maven content. The pipeline should support two modes of distribution:
    - Package the Maven content as an OCI artifact, which can be pushed and pulled to a container
      registry using compatible tools such as [ORAS](https://oras.land).
    - Publish the content to one or more "dev" Maven repositories. One of these "dev" Maven
      repositories must be treated as a source of truth for Renovate to "nudge" dependent Konflux
      `Components`, and should not be polluted with pull request builds.
- Developers must be able to provide arguments and CLI flags to the `mvn` command.
- The build must produce OCI artifact references (`*_IMAGE_URL` and `*_IMAGE_DIGEST` or `IMAGES`)
  for Tekton Chains to generate provenance and signatures.
- Support for [multi-module](https://maven.apache.org/guides/mini/guide-multiple-modules.html)
  projects is required. The pipeline must be able to build and publish multiple Java artifacts
  within a single build invocation using standard Maven commands/procedures. The pipeline does not
  need to publish an OCI artifact for each built Java artifact.

### Non-Goals

- Support for [Maven 4](https://maven.apache.org/whatsnewinmaven4.html). At present, Maven 4 is
  undergoing a lengthy "beta" testing cycle and has not released a generally available 4.0 vesion.
  Maven 4 introduces several internal changes that will likely impact build and deploy processes.
- Support for [Gradle](https://gradle.org/). This is a separate build tool that is not distributed
  as part of Red Hat's UBI catalog. In the future, Konflux may need to obtain a build of Gradle
  from a separate trusted source or rebuild it themselves.
- Rebuild of the Maven build tool. For the interim, Konflux will consider the Red Hat UBI build of
  Maven and OpenJDK as a "trusted source."
- Support for [Scala](https://www.scala-lang.org/), [Kotlin](https://kotlinlang.org/), or other
  JVM-based programming languages. These have separate build tooling and compilers, which Konflux
  must obtain from a trusted source or likewise rebuild.
- Provision Maven repositories for Java projects. This capability would need to be considered an
  "add-on" and specific to a Maven repository provider (ex: Pulp, JFrog Artifactory, etc.).
- Release artifacts to a Maven repository. Promoting Maven artifacts by copying/mirroring is not
  well supported by the Maven command line tool. Release promotion processes are supported by some
  artifact repository vendors (see examples for [JFrog Artifactory](https://jfrog.com/help/r/jfrog-artifactory-documentation/move-and-copy-artifacts)
  and [AWS CodeArtifact](https://docs.aws.amazon.com/codeartifact/latest/ug/copy-package.html#copying-a-maven-package)).

These can all be addressed through follow-up ADRs.

## Decision

### Build Pipeline

Konflux will provide one or more build pipelines for Maven which will execute up to two "deployments":

- The pipeline will first deploy Maven artifacts to a container registry using [ORAS](https://oras.land).
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
4. **deploy-oras:** Use the ORAS CLI to push the full local staging directory tree to the container
   registry:

   ```
   oras push ${IMG_URL} ./target/stage-deploy \
     --artifact-type application/vnd.apache.maven.repository.v2.tar+gzip \
     --export-manifest manifest-out.txt
   ```

   The artifact type `application/vnd.apache.maven.repository.v2.tar+gzip` communicates that this
   image is non-runnable, with contents compressed with `gzip`. The output manifest is used for
   Tekton Chains signing.

5. `generate-sbom`: this will generate the required component-level Software Bill of Materials from
   multiple sources, aggregated with [Mobster](https://github.com/konflux-ci/mobster):
   - The [CycloneDX Maven Plugin](https://github.com/CycloneDX/cyclonedx-maven-plugin) if the Maven
     project has configured its use.
   - [Syft](https://github.com/anchore/syft)
   - Hermeto once Maven is supported as a package manager (design is
     [under discussion](https://github.com/hermetoproject/hermeto/pull/1046)).

The pipeline will also build the source container, using existing tasks in the Konflux catalog.
This artifact can be used to perform static code analysis against the source code used to compile
the Java artifacts (see below).

### Security Scanning

Security scanning tasks will be omitted from the pipeline. These should be executed as part of an
`IntegrationTestScenario` pipeline in accordance with [ADR-0048](./0048-movable-build-tests.md).
Scanning tasks should do the following:

1. Pull the Maven "repository" contents in the build pipeline. By default the contents will be
   extracted to the designated output directory.

   ```sh
   oras pull ${IMG_URL} -o /konflux/scan-targets
   ```

2. Run the selected scanning tool against the extracted content. Example below for
   [Snyk](https://docs.snyk.io/supported-languages/supported-languages-list/java-and-kotlin), which
   has support for Java:

   ```sh
   cd /konflux/scan-targets && snyk code test --sartif-file-output=snyk-results-code.sarif
   ``` 

Scanning tools may require access to the source code used to produce the Java artifacts in order to
be effective, in which case the source artifact from the build pipeline should be used as input.

### Consuming Maven Artifacts

Java artifacts produced by the Maven build pipeline can be consumed by downstream ("nudged")
components in one of two ways:

#### Maven Repository Pattern

In this pattern, downstream components reference dependencies as they would for any Maven artifact
hosted outside of Maven Central. For Maven artifacts with `-SNAPSHOT` versions, downstream
components should use a timestamped version number so that it can be updated by Renovate:

```xml
<!-- pom.xml -->
  <repositories>
    <repository>
      <id>konflux-user-workloads</id>
      <name>Konflux User Workloads Repository</name>
      <url>https://{repository-host}/user-workloads</url>
      <snapshots>
        <enabled>true</enabled> <!-- Most teams will use SNAPSHOT versions during dev -->
      <snapshots>
      <releases>
        <enabled>false</enabled> <!-- Can be enabled if SNAPSHOT versions are not used -->
      <releases>
  </repositories>
  ...
  <dependencies>
    <dependency>
      <groupId>group.id.for.component</groupId>
      <artifactId>artifact-id</artifactId>
      <version>1.0.0-20251216.185533-1<version> <!-- Timestamped build version, managed by Renovate -->
    </dependency>
    ...
  <dependencies>

```

#### OCI Artifact

In this pattern, the OCI artifact from the build is pulled and referenced in the consumer's build
process. This may require multiple code changes; below is an example for a container build:

1. Modify the consuming component's build configuration (ex: `pom.xml`) to reference a local
   directory containing the extracted OCI artifact contents:

   ```xml
   <!-- pom.xml -->
   <repositories>
     <repository>
       <id>konflux-component-{name}</id>
       <name>Konflux Component {name} Extracted Repository</name>
       <url>file:.konflux/maven/konflux-component-{name}</url>
       <snapshots>
         <enabled>true</enabled> <!-- Most teams will use SNAPSHOT versions during dev -->
       </snapshots>
       <releases>
         <enabled>true</enabled> <!-- Can be enabled if SNAPSHOT versions are not used -->
       </releases>
     </repository>
   </repositories>
   ```

2. Update the `Containerfile` to extract the OCI artifact

   ```
   FROM quay.io/konflux-ci/oras:latest@sha256:... AS maven-content
   ARG MAVEN_IMAGE=quay.io/redhat-user-workloads/...
   WORKDIR /konflux-build
   RUN oras pull ${MAVEN_IMAGE} --output maven

   FROM registry.redhat.io/ubi9/openjdk-17:latest
   # For openjdk images, WORKDIR is set to a non-root "default" user home
   COPY . /home/default/app-src
   COPY --from=maven-content /konflux-build/maven /home/default/app-src/.konflux/maven/konflux-component-{name}
   RUN mvn clean install
   ...
   ```

## Consequences

### Required Infrastructure

- Create a new GitHub repository within the `konflux-ci` organization: `java-build-pipelines`. This
  repository will host validated build pipelines for all Java or JVM-based build systems. In the
  future, this can host build piplines for additional tools such as [Gradle](https://gradle.org/),
  [Ivy](https://ant.apache.org/ivy/), [Scala](https://www.scala-lang.org/), and [Kotlin](https://kotlinlang.org/).
- Onboard build pipelines and tasks to our "dogfooding" Konflux instance, creating the necessary
  `Application` and `Components` as needed. This process should take advantage of the Image
  Controller to create `quay.io` repositories within the `konflux-ci` organization.

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
  applicable to individual Java artifacts at runtime.
- **Scanning Limitations:** Due to the output not being a runnable container image, not all
  existing scanning tools (like Clair, Clamav, Coverity) are likely to support it. Scanning tools
  may not be capable of analyzing Java bytecode, and may need to scan the associated source code of
  the build instead.

### Rejected Alternatives

**Push to Pulp**: [Pulp](https://pulpproject.org/pulp_maven/) has a plugin for Maven, as well as an
[OCI storage integration](https://pulpproject.org/pulp_container/docs/admin/guides/change-allowed-artifacts/?h=oci).
This integration allows uploaded artifacts to have an associated OCI artifact digest. This
alternative was rejected for several reasons:

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
