---
title: Architecture Decision Records
eleventyNavigation:
  key: Architecture Decision Records
  order: 3
  url: /architecture/ADR/
toc: true
---

# Architecture Decision Records

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

| ADR | Status | Created | Updated |
| --- | --- | --- | --- |
|[1. Pipeline Service Phase 1](./0001-pipeline-service-phase-1.md)|🔄 Replaced|2022-10-29|2026-03-12|
|[2. Feature Flags](./0002-feature-flags.md)|🔄 Replaced|2022-10-12|2026-03-12|
|[3. Interacting with Internal Services](./0003-interacting-with-internal-services.md)|✔️ Implemented|2022-10-21|2026-03-12|
|[4. Out-of-the-box image repository for StoneSoup users ](./0004-component-image-location.md)|✔️ Implemented|2023-07-14|2026-03-12|
|[6. Log Conventions](./0006-log-conventions.md)|✔️ Implemented|2022-11-11|2026-03-12|
|[7. Change Management Process](./0007-change-management.md)|✅ Accepted|2022-11-11|2026-03-12|
|[8. Environment Provisioning](./0008-environment-provisioning.md)|🔄 Replaced|2022-12-14|2026-03-12|
|[9. Pipeline Service via Operator](./0009-pipeline-service-via-operator.md)|✔️ Implemented|2023-10-04|2026-03-12|
|[10. Namespace Metadata](./0010-namespace-metadata.md)|✅ Accepted|2022-12-09|2026-03-12|
|[11. Roles and Permissions for Konflux](./0011-roles-and-permissions.md)|✅ Accepted|2023-01-10|2026-03-12|
|[12. Namespace Name Format](./0012-namespace-name-format.md)|✅ Accepted|2023-01-23|2026-03-12|
|[13. Konflux Test Stream - API contracts](./0013-integration-service-api-contracts.md)| Deprecated|2022-11-29|2026-03-12|
|[14. Let Pipelines Proceed](./0014-let-pipelines-proceed.md)|✅ Accepted|2023-01-31|2026-03-12|
|[15. The Two-phase Architecture of the Integration Service](./0015-integration-service-two-phase-architecture.md)| Superseded|2023-02-09|2026-03-12|
|[16. Promotion logic in the Integration Service](./0016-integration-service-promotion-logic.md)| Superseded|2023-02-14|2026-03-12|
|[17. Use our own pipelines](./0017-use-our-pipelines.md)|✅ Accepted|2023-02-10|2026-03-12|
|[18. Continuous Performance Testing (CPT) of Apps in Konflux](./0018-apps-continuous-perf-testing.md)| In|2023-03-10|2026-03-12|
|[19. Customize URLs Sent to GitHub](./0019-customize-url-github.md)|✅ Accepted|2023-03-29|2026-03-12|
|[20. Source Retention](./0020-source-retention.md)|✅ Accepted|2023-04-05|2026-03-12|
|[21. Partner Tasks in Build/Test Pipelines](./0021-partner-tasks.md)|🔄 Replaced|2023-04-03|2026-03-12|
|[22. Secret Management For User Workloads](./0022-secret-mgmt-for-user-workloads.md)|✅ Accepted|2022-12-03|2026-03-12|
|[23. Git references to furnish Integration Test Scenarios](./0023-git-references-to-furnish-integration-test-scenarios.md)| Approved|2023-04-14|2026-03-12|
|[24. Release Objects Attribution Tracking and Propagation](./0024-release-attribution.md)|✅ Accepted|2023-04-26|2026-03-12|
|[25. appstudio-pipeline Service Account](./0025-appstudio-pipeline-serviceaccount.md)|✅ Accepted|2023-05-30|2026-03-12|
|[26. Specifying OCP targets for File-based Catalogs](./0026-specifying-ocp-targets-for-fbc.md)|✅ Accepted|2023-06-08|2026-03-12|
|[27. Container Image Management Practice](./0027-container-images.md)|📝 Proposed|2023-05-26|2026-03-12|
|[28. Handling SnapshotEnvironmentBinding Errors](./0028-handling-snapshotenvironmentbinding-errors.md)| Superceded|2023-08-29|2026-03-12|
|[29. Component Dependencies](./0029-component-dependencies.md)|✅ Accepted|2023-06-27|2026-03-12|
|[30. Tekton Results Naming Convention](./0030-tekton-results-naming-convention.md)|✅ Accepted|2023-05-19|2026-03-12|
|[31. Sprayproxy](./0031-sprayproxy.md)|🔄 Replaced|2023-10-25|2026-03-12|
|[32. Decoupling Deployment](./0032-decoupling-deployment.md)|✅ Accepted|2023-11-05|2026-03-12|
|[33. Enable Native OpenTelemetry Tracing](./0033-enable-native-opentelemetry-tracing.md)|✅ Accepted|2024-02-27|2026-03-12|
|[34. Project Controller for Multi-version support](./0034-project-controller-for-multiversion.md)|✔️ Implemented|2024-05-09|2026-03-12|
|[35. Continuous Chaos Testing of Apps in AppStudio](./0035-apps-continuous-chaos-testing.md)|✅ Accepted|2024-03-05|2026-03-12|
|[36. Trusted Artifacts](./0036-trusted-artifacts.md)|✔️ Implemented|2024-07-15|2026-03-12|
|[37. Integration service promotes components to GCL immediately after builds complete](./0037-integration-service-promotes-to-GCL-immediately.md)|✅ Accepted|2024-06-21|2026-03-12|
|[38. Integration service removes composite snapshots and logic around them](./0038-integration-service-composite-removal.md)|✅ Accepted|2024-07-09|2026-03-12|
|[39. Workspace Deprecation](./0039-workspace-deprecation.md)|✔️ Implemented|2025-08-27|2026-03-12|
|[40. Availability Probe Framework](./0040-availability-probe-framework.md)|✅ Accepted|2023-08-10|2026-03-12|
|[41. Konflux should send cloud events all system events.](./0041-send-cloud-events.md)|✅ Accepted|2024-09-24|2026-03-12|
|[42. Provisioning Clusters for Integration Tests](./0042-provisioning-ephemeral-openshift-clusters.md)|✅ Accepted|2024-06-05|2026-03-12|
|[44. SPDX SBOM support](./0044-spdx-support.md)|✔️ Implemented|2024-10-24|2026-03-12|
|[46. Build a common Task Runner image](./0046-common-task-runner-image.md)|✔️ Implemented|2024-11-22|2026-05-04|
|[47. Caching for container base images used during builds](./0047-caching-for-container-build-layers.md)|🚧 Implementable|2025-09-12|2026-03-12|
|[48. Attestable Build-Time Tests in Integration Service](./0048-movable-build-tests.md)|✅ Accepted|2025-10-08|2026-03-12|
|[49. Verification Summary Attestations for Release Policies](./0049-vsa-support.md)|✅ Accepted|2025-10-08|2026-03-12|
|[50. Exclude Kubernetes Events API from User RBAC Roles](./0050-exclude-events-api-from-user-rbac.md)|✔️ Implemented|2025-10-02|2026-03-12|
|[51. KITE Architecture and Components](./0051-kite-poc-architecture-and-components.md)|🚧 Implementable|2025-10-08|2026-03-12|
|[52. GitOps Onboarding Redesign](./0052-gitops-onboarding-redesign.md)|✅ Accepted|2025-10-08|2026-03-12|
|[53. Trusted Tasks model after build-definitions decentralization](./0053-trusted-task-model.md)|✅ Accepted|2025-10-22|2026-04-28|
|[54. Start versioning Tekton Tasks responsibly](./0054-task-versioning.md)|✅ Accepted|2025-10-22|2026-03-12|
|[55. SLSA Source Provenance Verification](./0055-slsa-source-provenance-verification.md)|✅ Accepted|2025-10-31|2026-03-12|
|[56. Revised Component Model](./0056-revised-component-model.md)|🚧 Implementable|2025-11-21|2026-07-27|
|[57. Pipeline Caching Feature Flag Configuration](./0057-pipeline-caching-feature-flag.md)|🚧 Implementable|2025-12-02|2026-03-12|
|[58. MintMaker log persistence](./0058-mintmaker-log-persistence.md)|🚧 Implementable|2026-02-03|2026-03-12|
|[59. Backend Usage Telemetry Collection from Konflux Clusters](./0059-backend-usage-telemetry-collection.md)|🚧 Implementable|2026-02-24|2026-03-12|
|[60. ComponentGroups](./0060-component-groups.md)|📝 Proposed|2026-02-27|2026-03-12|
|[61. VCS Info Specification for Container Images](./0061-vcs-info-specification.md)|🚧 Implementable|2026-03-10|2026-03-12|
|[62. Distributed Tracing](./0062-distributed-tracing.md)|🚧 Implementable|2026-03-10|2026-03-13|
|[63. Generalized Build and Release Pipelines](./0063-generalized-build-release-pipelines.md)|🚧 Implementable|2026-03-17|2026-04-28|
|[64. Package Registry Proxy Configuration for Hermeto](./0064-hermeto-package-registry-proxy.md)|🚧 Implementable|2026-04-07|2026-04-07|
|[65. Adopt KubeArchive for resource lifecycle management](./0065-kubearchive.md)|✔️ Implemented|2026-04-21|2026-04-21|
|[66. Ecosystem-Native Distribution for Non-OCI Artifacts](./0066-ecosystem-native-distribution.md)|✅ Accepted|2026-05-05|2026-05-05|
|[67. Nudging Relationship Storage via Singleton CRD](./0067-nudging-relationship-singleton-crd.md)|📝 Proposed|2026-06-02|2026-06-02|
|[68. Standardize on konflux-ci.dev as Official API Group](./0068-konflux-ci-dev-api-group.md)|✅ Accepted|2026-06-09|2026-07-07|
|[69. Reproducible Container Builds in Konflux](./0069-reproducible-container-builds.md)|📝 Proposed|2026-06-24|2026-06-24|
|[70. Support for zstd:chunked image compression](./0070-dual-compression-for-container-builds.md)|📝 Proposed|2026-06-29|2026-06-29|
|[71. Replace Appstudio Labels, Annotations, and Finalizers with Konflux equivalents](./0071-konflux-labels-annotations-finalizers.md)|✅ Accepted|2026-07-07|2026-07-07|
|[72. Scan RPM signatures from a build-time artifact](./0072-rpm-signature-scan-from-build-artifact.md)|📝 Proposed|||
