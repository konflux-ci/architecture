_NOTE: This file is NOT published_

# ADR Index - Quick Reference

**Purpose:** Find relevant ADRs by topic without reading full documents.

**Usage:**
- Search this file for keywords (grep/search)
- Note the ADR number
- Read ADR head/tail only (first 30 + last 20 lines)
- Only read full ADR if critical

---

## ADR Catalog (by number)

### ADR-0001: Pipeline Service Phase 1
- **Status**: Replaced (Superseded by ADR-0009)
- **Summary**: App Studio initially ran on a single cluster and provisioned Tekton controllers.
- **Topics**: tekton, pipeline, kcp, deployment

### ADR-0002: Feature Flags
- **Status**: Replaced
- **Summary**: We know we need some way for processes to recognize that they're working in a HACBS context or in an App Studio context.
- **Topics**: feature-flags, kcp, configuration, workspace

### ADR-0003: Interacting with Internal Services
- **Status**: Implemented
- **Summary**: Many organizations, including Red Hat, possess numerous internal services that help productize their software.
- **Topics**: internal-services, controller, security, integration

### ADR-0004: Out-of-the-box image repository for StoneSoup users
- **Status**: Implemented
- **Summary**: StoneSoup does not have a internal registry where images could be pushed to as an intermediate step before being deployed as a container.
- **Topics**: image-repository, quay, registry, component

### ADR-0006: Log Conventions
- **Status**: Implemented
- **Summary**: We need log conventions to make our offering easier to operate and maintain.
- **Topics**: logging, observability, monitoring, json

### ADR-0007: Change Management Process
- **Status**: Accepted
- **Summary**: Red Hat's ESS requirement SEC-CHG-REQ-1 (Change Management) states that "All applications/systems/platforms/services must follow Change Management process and procedures, as applicable / appropriate."
- **Topics**: change-management, security, compliance, deployment

### ADR-0008: Environment Provisioning
- **Status**: Replaced (Superseded by ADR-0032)
- **Summary**: In our old KCP architecture, we had a design for provisioning a new deployment target in support of new Environments.
- **Topics**: environment, deployment, provisioning, kcp

### ADR-0009: Pipeline Service via Operator
- **Status**: Implemented
- **Summary**: kcp is no longer being used as a control plane for Konflux.
- **Topics**: tekton, pipeline, operator, openshift

### ADR-0010: Namespace Metadata
- **Status**: Accepted
- **Summary**: We need metadata on our namespaces to make Konflux easier to operate and maintain.
- **Topics**: namespace, metadata, labels, annotations

### ADR-0011: Roles and Permissions for Konflux
- **Status**: Accepted (Related to ADR-0050)
- **Summary**: Konflux is using Kubernetes as the control plane for managing its resources.
- **Topics**: rbac, roles, permissions, security

### ADR-0012: Namespace Name Format
- **Status**: Accepted
- **Summary**: The OSD-based control plane provisions one namespace in the target member cluster for every workspace (internally represented by a Space CR) which is created for a Konflux user.
- **Topics**: namespace, naming, workspace, format

### ADR-0013: Konflux Test Stream - API contracts
- **Status**: Deprecated (Deprecated by ADR-0030)
- **Summary**: The Konflux project being developed aims to serve Red Hat teams but also partners and customers.
- **Topics**: testing, api, contracts, tekton

### ADR-0014: Let Pipelines Proceed
- **Status**: Accepted (Related to ADR-0013, ADR-0030, ADR-0032)
- **Summary**: The user's build pipeline includes scanning and linting tasks that operate on the source code and the built image (SAST, antivirus, clair, etc..).
- **Topics**: pipeline, testing, scanning, enterprise-contract

### ADR-0015: The Two-phase Architecture of the Integration Service
- **Status**: Superseded (Superseded by ADR-0036)
- **Summary**: The Integration Service is in charge of running integration test pipelines by executing the Tekton pipeline for each user-defined IntegrationTestScenario.
- **Topics**: integration, testing, snapshot, race-condition

### ADR-0016: Promotion logic in the Integration Service
- **Status**: Superseded (Superseded by ADR-0032, ADR-0036)
- **Summary**: Before the merge of HACBS & AppStudio, the Konflux build-service created the ApplicationSnapshot and promoted the content to the user's lowest environment as soon as the build was completed and once the environment was built.
- **Topics**: integration, promotion, deployment, snapshot

### ADR-0017: Use our own pipelines
- **Status**: Accepted (Related to ADR-0007, ADR-0027)
- **Summary**: The maintainers of Konflux components need to demonstrate evidence of practices that support a secure software development lifecycle (for example scanning, manifesting, vulnerability detection, etc.)
- **Topics**: pipeline, security, sdlc, dogfooding

### ADR-0018: Continuous Performance Testing (CPT) of Apps in Konflux
- **Status**: In consideration
- **Summary**: In general, performance testing is just another form of testing that helps application teams to ensure there are no regressions in their code and that their application behaves as expected.
- **Topics**: performance, testing, horreum, metrics

### ADR-0019: Customize URLs Sent to GitHub
- **Status**: Accepted
- **Summary**: When we run builds and tests on PRs (see STONE-134), developers need to be provided a link to the Konflux UI so they can see the details of their PipelineRuns.
- **Topics**: github, ui, pipelines-as-code, urls

### ADR-0020: Source Retention
- **Status**: Accepted (Related to ADR-0007)
- **Summary**: Red Hat's SSML requirements "SSML.PS.1.1.1 Securely Store All Forms of Code" requires that "The revision and its change history are preserved indefinitely and cannot be deleted, except when subject to an established and transparent policy for obliteration, such as a legal or policy requirement."
- **Topics**: security, compliance, source-code, retention

### ADR-0021: Partner Tasks in Build/Test Pipelines
- **Status**: Accepted
- **Summary**: As a Red Hat Partner, I would like to offer our service's capability as a Tekton Task that would be executed in a user's build/test Pipeline on StoneSoup.
- **Topics**: tekton, tasks, partner, integration

### ADR-0022: Secret Management For User Workloads
- **Status**: Accepted (Related to ADR-0032)
- **Summary**: When user workloads are deployed to environments, the system should be able to provide a way to inject values that are specific to the environment.
- **Topics**: secrets, security, deployment, environment

### ADR-0023: Git references to furnish Integration Test Scenarios
- **Status**: Approved
- **Summary**: Up to now, the Integration service has only supported setting the Tekton bundle (Bundle string `json:"bundle"`) in the IntegrationTestScenario [CR] as a reference for the integration tests, in order to run the Tekton PipelineRuns.
- **Topics**: integration, testing, git, tekton-resolvers

### ADR-0024: Release Objects Attribution Tracking and Propagation
- **Status**: Accepted
- **Summary**: It is imperative to know, given a change that has been delivered to a production environment, which individual it can be attributed to, in order to have accountability for that change.
- **Topics**: release, attribution, security, compliance

### ADR-0025: appstudio-pipeline Service Account
- **Status**: Accepted
- **Summary**: A default service account must be provided to allow Konflux components to run pipelines.
- **Topics**: serviceaccount, security, rbac, pipeline

### ADR-0026: Specifying OCP targets for File-based Catalogs
- **Status**: Accepted
- **Summary**: One of the supported component types within Konflux are File-based Catalogs (FBC).
- **Topics**: fbc, operator, openshift, ocp

### ADR-0027: Availability Probe Framework
- **Status**: Accepted
- **Summary**: As an Konflux developer building functionality for the platform, I want to be able to easily visualize and comprehend the stability and availability of deployed systems in order to inform and influence future work towards improving the overall system reliability.
- **Topics**: availability, monitoring, metrics, cronjob

### ADR-0027: Container Image Management Practice
- **Status**: Proposed (Related to ADR-0017)
- **Summary**: The purpose of this document is to establish container image management practices for Konflux container images that are deployed in the staging and production environments.
- **Topics**: container-images, security, patching, vulnerability

### ADR-0028: Handling SnapshotEnvironmentBinding Errors
- **Status**: Superseded (Superseded by ADR-0032)
- **Summary**: It is currently not possible to determine whether a SnapshotEnvironmentBinding (SEB) is stuck in an unrecoverable state.
- **Topics**: integration, deployment, error-handling, binding

### ADR-0029: Component Dependencies
- **Status**: Accepted
- **Summary**: As an Konflux user, I want to be able to build and test multiple coupled components which depend on each other by digest reference.
- **Topics**: component, dependencies, build, integration

### ADR-0030: Tekton Results Naming Convention
- **Status**: Accepted (Related to ADR-0013, ADR-0014)
- **Summary**: In order to Let Pipelines Proceed, the default interface of a Tekton Task's status code becomes an unsuitable API contract for communicating the successes and failures of tasks.
- **Topics**: tekton, testing, results, api-contracts

### ADR-0031: Sprayproxy
- **Status**: Accepted (Superseded by ADR-0039)
- **Summary**: Konflux has multiple member (backend) clusters.
- **Topics**: proxy, pipelines-as-code, webhook, multi-cluster

### ADR-0032: Decoupling Deployment
- **Status**: Accepted (Related to ADR-0014, ADR-0022, Supersedes ADR-0008, ADR-0016, ADR-0028)
- **Summary**: Since the beginning of our project, we've had an emphasis on providing an integrated experience for the user, automating all steps through build, test, deployment, and release to higher environments.
- **Topics**: deployment, gitops, decoupling, architecture

### ADR-0033: Enable Native OpenTelemetry Tracing
- **Status**: Accepted
- **Summary**: Konflux is a tool under active development and, therefore, unforeseen issues may arise.
- **Topics**: tracing, observability, opentelemetry, debugging

### ADR-0034: Project Controller for Multi-version support
- **Status**: Proposed
- **Summary**: Konflux began its way as "App Studio", which was mainly designed to facilitate the development of online managed services.
- **Topics**: project, versioning, multi-version, application

### ADR-0035: Continuous Chaos Testing of Apps in AppStudio
- **Status**: Accepted
- **Summary**: The chaos engineering strategy enables users to discover potential causes of service degradation.
- **Topics**: chaos-testing, resilience, testing, krkn

### ADR-0035: Provisioning Clusters for Integration Tests
- **Status**: Accepted (Supersedes ADR-0008, parts of ADR-0032)
- **Summary**: This decision clarifies how integration test environments will be dynamically provisioned.
- **Topics**: provisioning, testing, hive, hypershift

### ADR-0036: Trusted Artifacts
- **Status**: Accepted
- **Summary**: One of the properties of Konflux is that users should be allowed to include their own Tekton Tasks in a build Pipeline, e.g. to execute unit tests, without jeopardizing the integrity of the build process.
- **Topics**: security, trusted-artifacts, tekton, oci

### ADR-0037: Integration service promotes components to GCL immediately after builds complete
- **Status**: Accepted (Supersedes ADR-0015, ADR-0016, Superseded by ADR-0038)
- **Summary**: In the initial implementation of the Integration Service, when a single component image is built, the Integration Service tests the application by creating a Snapshot.
- **Topics**: integration, promotion, gcl, deadlock

### ADR-0038: Integration service removes composite snapshots and logic around them
- **Status**: Accepted
- **Summary**: Composite snapshots main goal was to prevent race condition when teams merged multiple PRs to multiple components of the same application at nearly the same time.
- **Topics**: integration, snapshot, override, simplification

### ADR-0039: Workspace Deprecation
- **Status**: Implemented (Supersedes ADR-0031)
- **Summary**: The purpose of this ADR is to revisit the workspace concept, understand the purpose of it, and offer an alternative implementation based on native Kubernetes APIs and other successful cloud native open source projects.
- **Topics**: workspace, namespace, kubernetes, kubesaw

### ADR-0041: Konflux should send cloud events all system events
- **Status**: Proposed
- **Summary**: Konflux had made the architectural decision to not use cloud events.
- **Topics**: cloud-events, eventing, integration, extensibility

### ADR-0044: SPDX SBOM support
- **Status**: Accepted
- **Summary**: SPDX SBOM format enables additional features not available in cyclondedx like multiple purl attributes per component.
- **Topics**: sbom, spdx, security, supply-chain

### ADR-0046: Build a common Task Runner image
- **Status**: Implementable
- **Summary**: Tekton Tasks often depend on specific CLI tools.
- **Topics**: tekton, container-images, tooling, tasks

### ADR-0047: Caching for container base images used during builds
- **Status**: Implementable
- **Summary**: Konflux builds container images using tools like Buildah.
- **Topics**: caching, performance, squid, proxy

### ADR-0048: Attestable Build-Time Tests in Integration Service
- **Status**: Proposed
- **Summary**: Some of the security scans run during the build pipeline take a long time to run.
- **Topics**: testing, attestation, integration, security

### ADR-0049: Verification Summary Attestations for Release Policies
- **Status**: Proposed
- **Summary**: We are facing several challenges with our current approach to Conforma verification and software development lifecycle (SDL) checks.
- **Topics**: attestation, vsa, slsa, conforma

### ADR-0050: Exclude Kubernetes Events API from User RBAC Roles
- **Status**: Implemented (Related to ADR-0011)
- **Summary**: Konflux users require RBAC permissions to interact with various Kubernetes resources through our defined roles (Viewer, Contributor, Maintainer, Admin).
- **Topics**: rbac, security, kubernetes-events, permissions

### ADR-0051: KITE Architecture and Components
- **Status**: Implementable
- **Summary**: The KITE is a proof-of-concept designed to detect, create, and track issues that block application releases in Konflux.
- **Topics**: kite, issues-dashboard, monitoring, automation

### ADR-0052: GitOps Onboarding Redesign
- **Status**: Accepted
- **Summary**: Currently, Konflux offers two distinct onboarding paths that create friction and complexity for developers.
- **Topics**: gitops, onboarding, argocd, ui

### ADR-0053: Trusted Tasks model after build-definitions decentralization
- **Status**: Accepted (Related to ADR-0021)
- **Summary**: Conforma has the concept of Trusted Tasks which Konflux policies rely on extensively when verifying the compliance of artifacts built through Konflux Pipelines.
- **Topics**: trusted-tasks, security, conforma, tekton

### ADR-0054: Start versioning Tekton Tasks responsibly
- **Status**: Accepted (Related to ADR-0053)
- **Summary**: The upstream Tasks that Konflux releases today typically do not follow a sensible versioning scheme, leading to opaque updates for users.
- **Topics**: versioning, tekton, tasks, semver
