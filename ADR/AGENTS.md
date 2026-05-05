64 ADRs, 10430 total lines. Filter: grep -l 'applies_to:' ADR/*.md
Status: Ac=Accepted Im=Implemented Ib=Implementable Pr=Proposed Ap=Approved Rp=Replaced Ss=Superseded Dp=Deprecated Ic=In-consideration

0000 Im 31L Record architecture decisions
0001 Rp 58L Pipeline Service Phase 1
0002 Rp 157L Feature Flags
0003 Im 79L Interacting with Internal Services
0004 Im 201L Out-of-the-box image repository for StoneSoup users
0006 Im 249L Log Conventions
0007 Ac 89L Change Management Process
0008 Rp 482L Environment Provisioning
0009 Im 84L Pipeline Service via Operator
0010 Ac 69L Namespace Metadata
0011 Ac 148L Roles and Permissions for Konflux
0012 Ac 32L Namespace Name Format
0013 Dp 292L Konflux Test Stream - API contracts
0014 Ac 68L Let Pipelines Proceed
0015 Ss 121L The Two-phase Architecture of the Integration Service
0016 Ss 107L Promotion logic in the Integration Service
0017 Ac 56L Use our own pipelines
0018 Ic 95L Continuous Performance Testing (CPT) of Apps in Konflux
0019 Ac 127L Customize URLs Sent to GitHub
0020 Ac 50L Source Retention
0021 Rp 92L Partner Tasks in Build/Test Pipelines
0022 Ac 450L Secret Management For User Workloads
0023 Ap 94L Git references to furnish Integration Test Scenarios
0024 Ac 97L Release Objects Attribution Tracking and Propagation
0025 Ac 51L appstudio-pipeline Service Account
0026 Ac 88L Specifying OCP targets for File-based Catalogs
0027 Pr 109L Container Image Management Practice
0028 Ss 29L Handling SnapshotEnvironmentBinding Errors
0029 Ac 192L Component Dependencies
0030 Ac 273L Tekton Results Naming Convention
0031 Rp 43L Sprayproxy
0032 Ac 254L Decoupling Deployment
0033 Ac 56L Enable Native OpenTelemetry Tracing
0034 Im 524L Project Controller for Multi-version support
0035 Ac 59L Continuous Chaos Testing of Apps in AppStudio
0036 Im 67L Trusted Artifacts
0037 Ac 74L Integration service promotes components to GCL immediately after builds complete
0038 Ac 47L Integration service removes composite snapshots and logic around them
0039 Im 126L Workspace Deprecation
0040 Ac 142L Availability Probe Framework
0041 Ac 58L Konflux should send cloud events all system events.
0042 Ac 259L Provisioning Clusters for Integration Tests
0044 Im 308L SPDX SBOM support
0046 Im 157L Build a common Task Runner image
0047 Ib 70L Caching for container base images used during builds
0048 Ac 92L Attestable Build-Time Tests in Integration Service
0049 Ac 106L Verification Summary Attestations for Release Policies
0050 Im 52L Exclude Kubernetes Events API from User RBAC Roles
0051 Ib 491L KITE Architecture and Components
0052 Ac 271L GitOps Onboarding Redesign
0053 Ac 290L Trusted Tasks model after build-definitions decentralization
0054 Ac 459L Start versioning Tekton Tasks responsibly
0055 Ac 145L SLSA Source Provenance Verification
0056 Ib 765L Revised Component Model
0057 Ib 66L Pipeline Caching Feature Flag Configuration
0058 Ib 87L MintMaker log persistence
0059 Ib 66L Backend Usage Telemetry Collection from Konflux Clusters
0060 Pr 294L ComponentGroups
0061 Ib 115L VCS Info Specification for Container Images
0062 Ib 154L Distributed Tracing
0063 Ib 370L Generalized Build and Release Pipelines
0064 Ib 126L Package Registry Proxy Configuration for Hermeto
0065 Im 39L Adopt KubeArchive for resource lifecycle management
0066 Ac 128L Ecosystem-Native Distribution for Non-OCI Artifacts
