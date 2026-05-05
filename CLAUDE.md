# CLAUDE.md - Konflux Architecture Documentation

Architecture documentation, ADRs, and diagrams for the Konflux platform. Documentation-only repository — no application code.

## Finding Information

For a complete document map with line counts, see `AGENTS.md`. Use it to estimate context cost before loading files.

Service docs have structured `overview:` frontmatter (scope, key_crds, related_services, related_adrs, key_concepts). ADRs have `status:`, `applies_to:`, and `topics:` frontmatter. Grep frontmatter to find relevant files, then read matched sections only.

- Service docs: `architecture/core/*.md` and `architecture/add-ons/*.md` (20–371 lines each)
- ADRs: `ADR/NNNN-*.md` (65 files, 29–765 lines — use frontmatter to filter)
- ADR template: `ADR/0000-adr-template.md` (31 lines)
- System overview: `architecture/index.md` (424 lines — read only when 3+ services involved)

## Core Architectural Constraints

- **API Model**: Kubernetes API server (controllers + CRDs), no REST APIs
- **Async-only**: All operations asynchronous, no synchronous operations
- **Tekton-based**: User-extensible operations executed via Tekton pipelines
- **OCI artifacts**: Primary deliverable format for all builds
- **Cluster isolation**: Each cluster independent (unit of sharding/tenancy)
- **Resource flow**: Application → Component → Snapshot → IntegrationTestScenario → ReleasePlan → Release
