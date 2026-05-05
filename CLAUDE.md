# CLAUDE.md - Konflux Architecture Documentation

Architecture documentation, ADRs, and diagrams for the Konflux platform. Documentation-only repository — no application code.

## Finding Information

Each subdirectory has an `AGENTS.md` with document maps and line counts for context cost estimation. Read those before loading files.

- Service docs: `architecture/core/*.md` and `architecture/add-ons/*.md` — see `architecture/AGENTS.md`
- ADRs: `ADR/NNNN-*.md` (64 files) — see `ADR/AGENTS.md`
- ADR template: `ADR/0000-adr-template.md` (31 lines)
- System overview: `architecture/index.md` (424 lines — read only when 3+ services involved)

Use frontmatter to filter: `overview:` in service docs, `status:`/`applies_to:`/`topics:` in ADRs.

## Core Architectural Constraints

- **API Model**: Kubernetes API server (controllers + CRDs), no REST APIs
- **Async-only**: All operations asynchronous, no synchronous operations
- **Tekton-based**: User-extensible operations executed via Tekton pipelines
- **OCI artifacts**: Primary deliverable format for all builds
- **Cluster isolation**: Each cluster independent (unit of sharding/tenancy)
- **Resource flow**: Application → Component → Snapshot → IntegrationTestScenario → ReleasePlan → Release
