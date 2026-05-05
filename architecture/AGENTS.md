# Architecture Document Index

Document map with line counts for context cost estimation.
Use `overview:` frontmatter in service docs to filter before reading.

## System overview

| File | Lines | Purpose |
|------|------:|---------|
| index.md | 424 | Full system overview with diagrams (read only when 3+ services involved) |

## Core services

| File | Lines | Scope |
|------|------:|-------|
| core/build-service.md | 285 | Build pipelines, Tekton PipelineRun definitions, Component builds |
| core/enterprise-contract.md | 198 | Policy enforcement, attestation validation, release gating |
| core/hybrid-application-service.md | 371 | Validation webhooks for Application and Component CRs |
| core/index.md | 175 | Core Services |
| core/integration-service.md | 225 | Test orchestration, snapshot creation/validation, promotion logic |
| core/konflux-ui.md | 20 | Web UI for Konflux platform (minimal architecture docs in this repo) |
| core/pipeline-service.md | 134 | Foundational Tekton APIs, Pipelines as Code, Chains (signing), Results (archival) |
| core/release-service.md | 147 | Release orchestration, privileged pipelines, cross-namespace releases |

## Add-on services

| File | Lines | Scope |
|------|------:|-------|
| add-ons/image-controller.md | 216 | Image repository setup, robot account management, secret linking to ServiceAccounts |
| add-ons/index.md | 239 | Add-ons |
| add-ons/internal-services.md | 141 | Remote cluster polling for executing internal jobs across network boundaries |
| add-ons/kubearchive.md | 99 | Archival and lifecycle management of ephemeral Kubernetes resources |
| add-ons/mintmaker.md | 161 | Automated dependency updates using Renovate for Konflux components |
| add-ons/multi-platform-controller.md | 275 | Dynamic VM provisioning for multi-architecture builds (arm64, ppc64le, s390x) |
| add-ons/project-controller.md | 190 | Project and development stream management via templating system |
| add-ons/pulp-access-controller.md | 217 | Automated Pulp domain and secret provisioning for artifact storage |
