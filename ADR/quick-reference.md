_NOTE: This file is NOT published_

# ADR Index - Quick Reference

**Purpose:** Find relevant ADRs by topic without reading full documents.

**Usage:**
- Search this file for keywords (grep/search)
- Note the ADR number and read the summary (extracted from Decision section)
- Use a subagent to process the full ADR if potentially relevant:
  - Pass context about what you're investigating
  - Subagent determines if ADR is relevant
  - If relevant, subagent returns pertinent sections

---

## ADR Catalog (by number)

### ADR-0001: Pipeline Service Phase 1
- **Status**: Replaced (Superseded by ADR-0009)
- **Summary**: Tekton APIs and services will be provided through a separate Pipeline Service, with App Studio and HACBS as initial customers.
- **Topics**: tekton, pipeline, kcp, deployment

### ADR-0002: Feature Flags
- **Status**: Replaced
- **Summary**: Use API discovery to control the enablement of individual features in individual workspaces through APIBinding resources.
- **Topics**: feature-flags, kcp, configuration, workspace

### ADR-0003: Interacting with Internal Services
- **Status**: Implemented
- **Summary**: Use a controller running in a private cluster to watch and reconcile Request custom resources in workspaces, enabling secure communication with internal services.
- **Topics**: internal-services, controller, security, integration

### ADR-0004: Out-of-the-box image repository for StoneSoup users
- **Status**: Implemented
- **Summary**: Per workspace, setup a new Quay.io org; per component, setup a new repo within that org, using robot account tokens for image push operations.
- **Topics**: image-repository, quay, registry, component

### ADR-0006: Log Conventions
- **Status**: Implemented
- **Summary**: Controller logs will use structured log messages formatted in JSON with key-value pairs for timestamps, levels, logger names, messages, and actions.
- **Topics**: logging, observability, monitoring, json

### ADR-0007: Change Management Process
- **Status**: Accepted
- **Summary**: Incremental code changes fully tested by automated tests will follow normal code review process; infrastructure and software deployments require changes to infra-deployments or App Interface repos.
- **Topics**: change-management, security, compliance, deployment

### ADR-0008: Environment Provisioning
- **Status**: Replaced (Superseded by ADR-0032)
- **Summary**: Split the Environment CR into two purposes: Environment for recognizing deployment destinations, and new DeploymentTarget/DeploymentTargetClaim APIs for provisioning deployment targets.
- **Topics**: environment, deployment, provisioning, kcp

### ADR-0009: Pipeline Service via Operator
- **Status**: Implemented
- **Summary**: All Tekton APIs will be provided using the stock OpenShift Pipelines operator with candidate nightly releases deployed in a service-first manner.
- **Topics**: tekton, pipeline, operator, openshift

### ADR-0010: Namespace Metadata
- **Status**: Accepted
- **Summary**: Apply standardized labels for namespace types, billing/telemetry, and operators; plus annotations to enable OVN network logging for outgoing traffic.
- **Topics**: namespace, metadata, labels, annotations

### ADR-0011: Roles and Permissions for Konflux
- **Status**: Accepted (Related to ADR-0050)
- **Summary**: Use the built-in Kubernetes RBAC system mapping four roles (Viewer, Contributor, Maintainer, Admin) to specific permissions on Konflux resources.
- **Topics**: rbac, roles, permissions, security

### ADR-0012: Namespace Name Format
- **Status**: Accepted
- **Summary**: Every namespace for a top-level workspace will use format `<workspace-name>-tenant`; environment sub-workspace namespaces will use format `<sub-workspace-name>-env`.
- **Topics**: namespace, naming, workspace, format

### ADR-0013: Konflux Test Stream - API contracts
- **Status**: Deprecated (Deprecated by ADR-0030)
- **Summary**: Tekton task output will be provided in two forms: minimized Tekton Task Results in JSON format (HACBS_TEST_OUTPUT and CLAIR_SCAN_RESULT) and Full Test Output JSON.
- **Topics**: testing, api, contracts, tekton

### ADR-0014: Let Pipelines Proceed
- **Status**: Accepted (Related to ADR-0013, ADR-0030, ADR-0032)
- **Summary**: All scanning and linting TaskRuns should succeed even if they find problems, using the TEST_OUTPUT result convention to expose results and render them for users.
- **Topics**: pipeline, testing, scanning, enterprise-contract

### ADR-0015: The Two-phase Architecture of the Integration Service
- **Status**: Superseded (Superseded by ADR-0036)
- **Summary**: Integration service will leverage a two-phase approach (Component phase and optional Composite phase) to protect against race conditions when testing component builds.
- **Topics**: integration, testing, snapshot, race-condition

### ADR-0016: Promotion logic in the Integration Service
- **Status**: Superseded (Superseded by ADR-0032, ADR-0036)
- **Summary**: Consolidate promotion logic for both HACBS and AppStudio into integration-service, updating GCL with component images upon successful test completion and ensuring Releases are associated with passing Snapshots.
- **Topics**: integration, promotion, deployment, snapshot

### ADR-0017: Use our own pipelines
- **Status**: Accepted (Related to ADR-0007, ADR-0027)
- **Summary**: Use our own pipelines to build and scan Konflux components, though not yet via the Konflux UI with configured Application and Components.
- **Topics**: pipeline, security, sdlc, dogfooding

### ADR-0018: Continuous Performance Testing (CPT) of Apps in Konflux
- **Status**: In consideration
- **Summary**: Use single Horreum instance per control plane cluster for performance testing, with pipelines uploading JSON test data to Horreum for analysis and PASS/FAIL determination.
- **Topics**: performance, testing, horreum, metrics

### ADR-0019: Customize URLs Sent to GitHub
- **Status**: Accepted
- **Summary**: Konflux components providing PipelineRun result links to GitHub must provide URLs accessible to registered end users with permission to view the requested PipelineRun resource.
- **Topics**: github, ui, pipelines-as-code, urls

### ADR-0020: Source Retention
- **Status**: Accepted (Related to ADR-0007)
- **Summary**: Source history of branches used to build Konflux components must not be overwritten or deleted, supported by enabling branch protection rules prohibiting force pushing and branch deletion.
- **Topics**: security, compliance, source-code, retention

### ADR-0021: Partner Tasks in Build/Test Pipelines
- **Status**: Accepted
- **Summary**: Setup a new directory in build-definitions for partners to contribute Tasks, with CI validation and optional OCI artifact generation for consumption in Tekton Pipelines.
- **Topics**: tekton, tasks, partner, integration

### ADR-0022: Secret Management For User Workloads
- **Status**: Accepted (Related to ADR-0032)
- **Summary**: Use RemoteSecret CRD to link SecretData stored in permanent SecretStorage with DeploymentTargets and Kubernetes Secrets, allowing separation of secret upload and delivery to targets.
- **Topics**: secrets, security, deployment, environment

### ADR-0023: Git references to furnish Integration Test Scenarios
- **Status**: Approved
- **Summary**: Integration service migrates to new IntegrationTestScenario CRD supporting different Tekton resolvers (bundles, cluster, hub, git), allowing users to specify test locations via GitHub URL and Git options.
- **Topics**: integration, testing, git, tekton-resolvers

### ADR-0024: Release Objects Attribution Tracking and Propagation
- **Status**: Accepted
- **Summary**: Use an admission webhook to capture and track user information from Kubernetes requests, validating against Red Hat's SSO for accountability of changes delivered to production.
- **Topics**: release, attribution, security, compliance

### ADR-0025: appstudio-pipeline Service Account
- **Status**: Accepted
- **Summary**: Konflux will provide a service account named `appstudio-pipeline`, with Pipeline Service owning the ClusterRole and CodeReadyToolchain managing ServiceAccount creation and role grants.
- **Topics**: serviceaccount, security, rbac, pipeline

### ADR-0026: Specifying OCP targets for File-based Catalogs
- **Status**: Accepted
- **Summary**: All FBC components for OCP will be built using OCP-specific parent images containing target version numbers, with org.opencontainers.image.base.name annotation indicating the base image pullspec.
- **Topics**: fbc, operator, openshift, ocp

### ADR-0027: Availability Probe Framework
- **Status**: Accepted
- **Summary**: Probes' availability will be provided as Prometheus metrics with labels differentiating probes, computed based on CronJob exit status and aggregated into standardized metrics.
- **Topics**: availability, monitoring, metrics, cronjob

### ADR-0027: Container Image Management Practice
- **Status**: Proposed (Related to ADR-0017)
- **Summary**: Component Teams are responsible for onboarding to PaC service for continuous builds and scans, with defined responsibilities for automated scanning, vulnerability patching, and image updates.
- **Topics**: container-images, security, patching, vulnerability

### ADR-0028: Handling SnapshotEnvironmentBinding Errors
- **Status**: Superseded (Superseded by ADR-0032)
- **Summary**: Integration service has reconciler that cleans up errored SnapshotEnvironmentBindings with ErrorOccured condition true and LastUpdateTime over five minutes old as unrecoverable.
- **Topics**: integration, deployment, error-handling, binding

### ADR-0029: Component Dependencies
- **Status**: Accepted
- **Summary**: Introduce `build-nudges-ref` field on Component to declare dependencies forming a DAG, with integration-service handling nudging components specially and build-service proposing updates to nudged repositories.
- **Topics**: component, dependencies, build, integration

### ADR-0030: Tekton Results Naming Convention
- **Status**: Accepted (Related to ADR-0013, ADR-0014)
- **Summary**: Pipeline tasks must succeed even when finding problems; two result format standards defined for test-like and scan-like tasks with unique result names and formats.
- **Topics**: tekton, testing, results, api-contracts

### ADR-0031: Sprayproxy
- **Status**: Accepted (Superseded by ADR-0039)
- **Summary**: Service validates incoming GitHub webhook requests using shared secret and payload size limits, then forwards validated requests to all backend clusters with exported metrics.
- **Topics**: proxy, pipelines-as-code, webhook, multi-cluster

### ADR-0032: Decoupling Deployment
- **Status**: Accepted (Related to ADR-0014, ADR-0022, Supersedes ADR-0008, ADR-0016, ADR-0028)
- **Summary**: Decouple deployment from build/test/release by deprecating Environment/SnapshotEnvironmentBinding/GitOpsDeploymentManagedEnvironment, stopping gitops-service deployment, and promoting renovatebot/dependabot for propagating releases to self-managed gitops repos.
- **Topics**: deployment, gitops, decoupling, architecture

### ADR-0033: Enable Native OpenTelemetry Tracing
- **Status**: Accepted
- **Summary**: Enable native tracing in Konflux by leveraging pre-existing capabilities, specifically Tekton's OpenTelemetry support, using an OpenTelemetry Collector for collection with flexibility to forward traces to any frontend.
- **Topics**: tracing, observability, opentelemetry, debugging

### ADR-0034: Project Controller for Multi-version support
- **Status**: Proposed
- **Summary**: Define two new CRs: Project resources for large projects with multiple development streams, and ProjectDevelopmentStream resources for individual streams linked via Kubernetes owner references.
- **Topics**: project, versioning, multi-version, application

### ADR-0035: Continuous Chaos Testing of Apps in AppStudio
- **Status**: Accepted
- **Summary**: Users can leverage Krkn chaos testing framework within IntegrationTestScenarios, using ephemeral clusters for isolated testing with optional Prometheus metrics gathering.
- **Topics**: chaos-testing, resilience, testing, krkn

### ADR-0035: Provisioning Clusters for Integration Tests
- **Status**: Accepted (Supersedes ADR-0008, parts of ADR-0032)
- **Summary**: Use CaaS Operator to orchestrate provisioning OpenShift clusters via ClusterTemplateInstances created by Tekton tasks, prioritizing Hypershift templates for cost-effectiveness and faster provisioning.
- **Topics**: provisioning, testing, hive, hypershift

### ADR-0036: Trusted Artifacts
- **Status**: Accepted
- **Summary**: Sharing files between Tasks is done via Trusted Artifacts backed by OCI storage.
- **Topics**: security, trusted-artifacts, tekton, oci

### ADR-0037: Integration service promotes components to GCL immediately after builds complete
- **Status**: Accepted (Supersedes ADR-0015, ADR-0016, Superseded by ADR-0038)
- **Summary**: Integration service will promote Snapshots to GCL immediately after creation instead of waiting for tests to pass, but still only creates Releases for Snapshots passing all required tests.
- **Topics**: integration, promotion, gcl, deadlock

### ADR-0038: Integration service removes composite snapshots and logic around them
- **Status**: Accepted
- **Summary**: Introduction of override snapshots replaces composite snapshots with simpler concept; override snapshots are manually created by users and update GCL for all contained components if tests pass.
- **Topics**: integration, snapshot, override, simplification

### ADR-0039: Workspace Deprecation
- **Status**: Implemented (Supersedes ADR-0031)
- **Summary**: Remove Workspace abstraction and use standard Kubernetes namespaces directly, recommend existing policy engines like Kyverno/Gatekeeper, and expose namespace creation wizard in UI for users with permissions.
- **Topics**: workspace, namespace, kubernetes, kubesaw

### ADR-0041: Konflux should send cloud events all system events
- **Status**: Proposed
- **Summary**: All Konflux components shall generate cloud events for significant events.
- **Topics**: cloud-events, eventing, integration, extensibility

### ADR-0044: SPDX SBOM support
- **Status**: Accepted
- **Summary**: Tekton tasks should implement sbomType attribute to specify expected SBOM format for input/output, allowing tools to be tested with SPDX before entire pipeline transitions.
- **Topics**: sbom, spdx, security, supply-chain

### ADR-0046: Build a common Task Runner image
- **Status**: Implementable
- **Summary**: Build and maintain a common Task Runner image including all commonly needed tools, built/released via Konflux with documented tool versions and proper semver versioning.
- **Topics**: tekton, container-images, tooling, tasks

### ADR-0047: Caching for container base images used during builds
- **Status**: Implementable
- **Summary**: Implement caching layer for container base images using Squid HTTP proxies deployed via Helm chart into dedicated proxy namespace with well-known service endpoint.
- **Topics**: caching, performance, squid, proxy

### ADR-0048: Attestable Build-Time Tests in Integration Service
- **Status**: Proposed
- **Summary**: Add support for attestations from integration pipelines, with test pipelines generating task-specific attestations using referrer's API and Chains tracking them via *_ARTIFACT_OUTPUTS results.
- **Topics**: testing, attestation, integration, security

### ADR-0049: Verification Summary Attestations for Release Policies
- **Status**: Proposed
- **Summary**: Adopt SLSA Verification Summary Attestations (VSAs) for recording SDL policy check results as input to release pipeline Conforma checks, distributed as signed OCI artifacts.
- **Topics**: attestation, vsa, slsa, conforma

### ADR-0050: Exclude Kubernetes Events API from User RBAC Roles
- **Status**: Implemented (Related to ADR-0011)
- **Summary**: Exclude the Kubernetes events API from all Konflux user RBAC roles.
- **Topics**: rbac, security, kubernetes-events, permissions

### ADR-0051: KITE Architecture and Components
- **Status**: Implementable
- **Summary**: Implement KITE as distributed system with Bridge Operator pattern monitoring Kubernetes resources (PipelineRuns), detecting state changes, and reporting failures to backend service for persistence.
- **Topics**: kite, issues-dashboard, monitoring, automation

### ADR-0052: GitOps Onboarding Redesign
- **Status**: Accepted
- **Summary**: Redesign onboarding to converge UI and GitOps into single Git-centric flow, deprecating UI-based tenant resource configuration in favor of Kubernetes or GitOps configuration.
- **Topics**: gitops, onboarding, argocd, ui

### ADR-0053: Trusted Tasks model after build-definitions decentralization
- **Status**: Accepted (Related to ADR-0021)
- **Summary**: Adopt rule-based model for Trusted Tasks, giving policy authors ability to allow/deny sets of Tasks based on criteria via trusted_task_rules alongside existing trusted_tasks data.
- **Topics**: trusted-tasks, security, conforma, tekton

### ADR-0054: Start versioning Tekton Tasks responsibly
- **Status**: Accepted (Related to ADR-0053)
- **Summary**: Mark each meaningful change with version update following Semantic Versioning for Tasks 1.0+, recording version via org.opencontainers.image.version annotation and tagging released bundles.
- **Topics**: versioning, tekton, tasks, semver

### ADR-0055: SLSA Source Provenance Verification
- **Status**: Accepted
- **Summary**: Verify SLSA source provenance through a chained attestation approach that leverages the movable test pattern, with verification tasks reading source VSAs from git notes and publishing them to OCI registries for Conforma verification.
- **Topics**: slsa, source-provenance, attestation, vsa, security
