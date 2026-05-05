# ADR Document Index

64 ADR files totaling 10430 lines. Use frontmatter to filter:
`grep -l 'applies_to:' *.md` or `grep -l 'topics:' *.md`.

Status key: Ac=Accepted, Im=Implemented, Ib=Implementable,
Pr=Proposed, Ap=Approved, Rp=Replaced, Ss=Superseded,
Dp=Deprecated, Ic=In consideration

| ADR | Status | Lines | Title |
|-----|--------|------:|-------|
| 0000 | Im | 31 | Record architecture decisions |
| 0001 | Rp | 58 | Pipeline Service Phase 1 |
| 0002 | Rp | 157 | Feature Flags |
| 0003 | Im | 79 | Interacting with Internal Services |
| 0004 | Im | 201 | Out-of-the-box image repository for StoneSoup users |
| 0006 | Im | 249 | Log Conventions |
| 0007 | Ac | 89 | Change Management Process |
| 0008 | Rp | 482 | Environment Provisioning |
| 0009 | Im | 84 | Pipeline Service via Operator |
| 0010 | Ac | 69 | Namespace Metadata |
| 0011 | Ac | 148 | Roles and Permissions for Konflux |
| 0012 | Ac | 32 | Namespace Name Format |
| 0013 | Dp | 292 | Konflux Test Stream - API contracts |
| 0014 | Ac | 68 | Let Pipelines Proceed |
| 0015 | Ss | 121 | The Two-phase Architecture of the Integration Service |
| 0016 | Ss | 107 | Promotion logic in the Integration Service |
| 0017 | Ac | 56 | Use our own pipelines |
| 0018 | Ic | 95 | Continuous Performance Testing (CPT) of Apps in Konflux |
| 0019 | Ac | 127 | Customize URLs Sent to GitHub |
| 0020 | Ac | 50 | Source Retention |
| 0021 | Rp | 92 | Partner Tasks in Build/Test Pipelines |
| 0022 | Ac | 450 | Secret Management For User Workloads |
| 0023 | Ap | 94 | Git references to furnish Integration Test Scenarios |
| 0024 | Ac | 97 | Release Objects Attribution Tracking and Propagation |
| 0025 | Ac | 51 | appstudio-pipeline Service Account |
| 0026 | Ac | 88 | Specifying OCP targets for File-based Catalogs |
| 0027 | Pr | 109 | Container Image Management Practice |
| 0028 | Ss | 29 | Handling SnapshotEnvironmentBinding Errors |
| 0029 | Ac | 192 | Component Dependencies |
| 0030 | Ac | 273 | Tekton Results Naming Convention |
| 0031 | Rp | 43 | Sprayproxy |
| 0032 | Ac | 254 | Decoupling Deployment |
| 0033 | Ac | 56 | Enable Native OpenTelemetry Tracing |
| 0034 | Im | 524 | Project Controller for Multi-version support |
| 0035 | Ac | 59 | Continuous Chaos Testing of Apps in AppStudio |
| 0036 | Im | 67 | Trusted Artifacts |
| 0037 | Ac | 74 | Integration service promotes components to GCL immediately after builds complete |
| 0038 | Ac | 47 | Integration service removes composite snapshots and logic around them |
| 0039 | Im | 126 | Workspace Deprecation |
| 0040 | Ac | 142 | Availability Probe Framework |
| 0041 | Ac | 58 | Konflux should send cloud events all system events. |
| 0042 | Ac | 259 | Provisioning Clusters for Integration Tests |
| 0044 | Im | 308 | SPDX SBOM support |
| 0046 | Im | 157 | Build a common Task Runner image |
| 0047 | Ib | 70 | Caching for container base images used during builds |
| 0048 | Ac | 92 | Attestable Build-Time Tests in Integration Service |
| 0049 | Ac | 106 | Verification Summary Attestations for Release Policies |
| 0050 | Im | 52 | Exclude Kubernetes Events API from User RBAC Roles |
| 0051 | Ib | 491 | KITE Architecture and Components |
| 0052 | Ac | 271 | GitOps Onboarding Redesign |
| 0053 | Ac | 290 | Trusted Tasks model after build-definitions decentralization |
| 0054 | Ac | 459 | Start versioning Tekton Tasks responsibly |
| 0055 | Ac | 145 | SLSA Source Provenance Verification |
| 0056 | Ib | 765 | Revised Component Model |
| 0057 | Ib | 66 | Pipeline Caching Feature Flag Configuration |
| 0058 | Ib | 87 | MintMaker log persistence |
| 0059 | Ib | 66 | Backend Usage Telemetry Collection from Konflux Clusters |
| 0060 | Pr | 294 | ComponentGroups |
| 0061 | Ib | 115 | VCS Info Specification for Container Images |
| 0062 | Ib | 154 | Distributed Tracing |
| 0063 | Ib | 370 | Generalized Build and Release Pipelines |
| 0064 | Ib | 126 | Package Registry Proxy Configuration for Hermeto |
| 0065 | Im | 39 | Adopt KubeArchive for resource lifecycle management |
| 0066 | Ac | 128 | Ecosystem-Native Distribution for Non-OCI Artifacts |
