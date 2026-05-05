# AGENTS.md - Konflux Architecture Document Index

> Read CLAUDE.md first. This file provides a detailed map of every
> document in the repository with line counts so you can estimate
> context cost before loading a file.

## How to use this index

1. **Start with CLAUDE.md** (23 lines) for architectural constraints
   and orientation.
2. **Use frontmatter to filter** — grep `applies_to:` or `topics:`
   in ADR files, or `overview:` in service docs, instead of reading
   every file.
3. **Check line counts below** before reading a file. Prefer files
   under 200 lines; files over 300 lines should be read only when
   directly relevant.

## Root files

| File | Lines | Purpose |
|------|------:|---------|
| CLAUDE.md | 23 | Entry point — architectural constraints and navigation |
| CONTRIBUTING.md | 294 | Contribution guidelines, frontmatter reference, lint commands |
| README.md | 28 | Repository overview |

## Architecture — system overview

| File | Lines | Purpose |
|------|------:|---------|
| architecture/index.md | 424 | Full system overview with diagrams (large — read only when 3+ services involved) |

## Architecture — core services

| File | Lines | Scope |
|------|------:|-------|
| architecture/core/index.md | 175 | Core services summary and interaction diagram |
| architecture/core/build-service.md | 285 | Build pipelines, PipelineRun lifecycle |
| architecture/core/enterprise-contract.md | 198 | Policy enforcement, release validation |
| architecture/core/hybrid-application-service.md | 371 | Application/Component lifecycle (large) |
| architecture/core/integration-service.md | 225 | Snapshot testing, IntegrationTestScenario |
| architecture/core/konflux-ui.md | 20 | UI service (stub) |
| architecture/core/pipeline-service.md | 134 | Tekton pipeline infrastructure |
| architecture/core/release-service.md | 147 | Release pipeline orchestration |

## Architecture — add-on services

| File | Lines | Scope |
|------|------:|-------|
| architecture/add-ons/index.md | 239 | Add-on services summary and interaction diagram |
| architecture/add-ons/image-controller.md | 216 | Image repository provisioning |
| architecture/add-ons/internal-services.md | 141 | Internal service request handling |
| architecture/add-ons/kubearchive.md | 99 | Resource lifecycle archival |
| architecture/add-ons/mintmaker.md | 161 | Dependency update automation |
| architecture/add-ons/multi-platform-controller.md | 275 | Multi-arch build orchestration |
| architecture/add-ons/project-controller.md | 190 | Namespace/project provisioning |
| architecture/add-ons/pulp-access-controller.md | 217 | Pulp content access control |

## ADRs (Architecture Decision Records)

> 65 ADR files totaling 10430 lines. Use frontmatter to filter:
> `grep -l 'applies_to:' ADR/*.md` or `grep -l 'topics:' ADR/*.md`.
>
> Status key: Ac=Accepted, Im=Implemented, Ib=Implementable,
> Pr=Proposed, Ap=Approved, Rp=Replaced, Ss=Superseded,
> Dp=Deprecated, Ic=In consideration

| ADR | Status | Lines | Title |
|-----|--------|------:|-------|
| 0000 | Im | 31 | Record architecture decisions |
| 0001 | Rp | 58 | Pipeline Service Phase 1 |
| 0002 | Rp | 157 | Feature Flags |
| 0003 | Im | 79 | Interacting with Internal Services |
| 0004 | Im | 201 | Out-of-the-box image repository |
| 0006 | Im | 249 | Log Conventions |
| 0007 | Ac | 89 | Change Management Process |
| 0008 | Rp | 482 | Environment Provisioning |
| 0009 | Im | 84 | Pipeline Service via Operator |
| 0010 | Ac | 69 | Namespace Metadata |
| 0011 | Ac | 148 | Roles and Permissions |
| 0012 | Ac | 32 | Namespace Name Format |
| 0013 | Dp | 292 | Test Stream API contracts |
| 0014 | Ac | 68 | Let Pipelines Proceed |
| 0015 | Ss | 121 | Integration Service Two-phase Architecture |
| 0016 | Ss | 107 | Integration Service Promotion logic |
| 0017 | Ac | 56 | Use our own pipelines |
| 0018 | Ic | 95 | Continuous Performance Testing |
| 0019 | Ac | 127 | Customize URLs Sent to GitHub |
| 0020 | Ac | 50 | Source Retention |
| 0021 | Rp | 92 | Partner Tasks in Build/Test Pipelines |
| 0022 | Ac | 450 | Secret Management For User Workloads |
| 0023 | Ap | 94 | Git references for Integration Test Scenarios |
| 0024 | Ac | 97 | Release Objects Attribution Tracking |
| 0025 | Ac | 51 | appstudio-pipeline Service Account |
| 0026 | Ac | 88 | Specifying OCP targets for FBC |
| 0027 | Pr | 109 | Container Image Management Practice |
| 0028 | Ss | 29 | Handling SnapshotEnvironmentBinding Errors |
| 0029 | Ac | 192 | Component Dependencies |
| 0030 | Ac | 273 | Tekton Results Naming Convention |
| 0031 | Rp | 43 | Sprayproxy |
| 0032 | Ac | 254 | Decoupling Deployment |
| 0033 | Ac | 56 | Enable Native OpenTelemetry Tracing |
| 0034 | Im | 524 | Project Controller for Multi-version |
| 0035 | Ac | 59 | Continuous Chaos Testing |
| 0036 | Im | 67 | Trusted Artifacts |
| 0037 | Ac | 74 | Integration service promotes to GCL immediately |
| 0038 | Ac | 47 | Integration service composite removal |
| 0039 | Im | 126 | Workspace Deprecation |
| 0040 | Ac | 142 | Availability Probe Framework |
| 0041 | Ac | 58 | Send cloud events for system events |
| 0042 | Ac | 259 | Provisioning Clusters for Integration Tests |
| 0044 | Im | 308 | SPDX SBOM support |
| 0046 | Im | 157 | Common Task Runner image |
| 0047 | Ib | 70 | Caching for container base images |
| 0048 | Ac | 92 | Attestable Build-Time Tests |
| 0049 | Ac | 106 | Verification Summary Attestations |
| 0050 | Im | 52 | Exclude Events API from User RBAC |
| 0051 | Ib | 491 | KITE Architecture and Components |
| 0052 | Ac | 271 | GitOps Onboarding Redesign |
| 0053 | Ac | 290 | Trusted Tasks model |
| 0054 | Ac | 459 | Task versioning |
| 0055 | Ac | 145 | SLSA Source Provenance Verification |
| 0056 | Ib | 765 | Revised Component Model |
| 0057 | Ib | 66 | Pipeline Caching Feature Flag |
| 0058 | Ib | 87 | MintMaker log persistence |
| 0059 | Ib | 66 | Backend Usage Telemetry Collection |
| 0060 | Pr | 294 | ComponentGroups |
| 0061 | Ib | 115 | VCS Info Specification |
| 0062 | Ib | 154 | Distributed Tracing |
| 0063 | Ib | 370 | Generalized Build and Release Pipelines |
| 0064 | Ib | 126 | Package Registry Proxy for Hermeto |
| 0065 | Im | 39 | Adopt KubeArchive |
| 0066 | Ac | 128 | Ecosystem-Native Distribution |
