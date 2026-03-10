# CLAUDE.md - Konflux Architecture Documentation

Architecture documentation, ADRs, and diagrams for the Konflux platform. Documentation-only repository — no application code.

## Finding Information

Service docs have structured `overview:` frontmatter (scope, key_crds, related_services, related_adrs, key_concepts). ADRs have `status:`, `applies_to:`, and `topics:` frontmatter. Grep frontmatter to find relevant files, then read matched sections only.

- Service docs: `architecture/core/*.md` and `architecture/add-ons/*.md`
- ADRs: `ADR/NNNN-*.md` (60+ files — use frontmatter to filter)
- ADR template: `ADR/0000-adr-template.md`
- System overview: `architecture/index.md` (large — read only when 3+ services involved)

## Core Architectural Constraints

- **API Model**: Kubernetes API server (controllers + CRDs), no REST APIs
- **Async-only**: All operations asynchronous, no synchronous operations
- **Tekton-based**: User-extensible operations executed via Tekton pipelines
- **OCI artifacts**: Primary deliverable format for all builds
- **Cluster isolation**: Each cluster independent (unit of sharding/tenancy)
- **Resource flow**: Application → Component → Snapshot → IntegrationTestScenario → ReleasePlan → Release
