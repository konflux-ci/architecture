# CLAUDE.md - Konflux Architecture Documentation

## Context Loading Rules

**Read selectively. Never read all files. Use grep before reading.**

### Core Services (`/architecture/core/`)
- `build-service.md` - Build pipelines, compilation, container image builds
- `enterprise-contract.md` - Policy enforcement, compliance validation, supply chain security
- `hybrid-application-service.md` - Git webhooks, application/component validation
- `integration-service.md` - Testing orchestration, snapshots, promotion logic
- `konflux-ui.md` - Web UI (minimal architecture docs, see repository)
- `pipeline-service.md` - Tekton infrastructure, pipeline execution foundation
- `release-service.md` - Release automation, deployment to production environments

**Note:** `/architecture/core/index.md` exists (~175 lines) but should NOT be read directly. Use grep to search for service relationships and interaction patterns only when understanding multi-service workflows.

### Add-ons (`/architecture/add-ons/`)
- `image-controller.md` - Image repository management and configuration
- `internal-services.md` - Internal job execution via remote cluster polling
- `mintmaker.md` - Automated dependency updates using Renovate
- `multi-platform-controller.md` - Multi-architecture build orchestration
- `project-controller.md` - Project and development stream management via templating

**Note:** `/architecture/add-ons/index.md` exists (~180 lines) but should NOT be read directly. Use grep to search for service relationships and interaction patterns only when understanding multi-service workflows.

### Loading Process

1. Map feature → 1-2 services (don't read yet)
2. Read service frontmatter only (start with the first 15 lines) and look at the overview to determine if information is relevant
3. Grep for keywords in service file
4. Read matched sections only (not entire file)
5. Search `/ADR/quick-reference.md` for relevant ADRs
6. Use a subagent to process relevant ADRs:
   - Pass summary of what you're trying to understand
   - Subagent reads full ADR and determines relevance
   - If relevant, subagent returns pertinent sections
7. Read `/architecture/index.md` only if 3+ services involved

### Core Architectural Constraints (Always Apply)

- **API Model**: Kubernetes API server (controllers + CRDs), no REST APIs
- **Async-only**: All operations asynchronous, no synchronous operations
- **Tekton-based**: User-extensible operations executed via Tekton pipelines
- **OCI artifacts**: Primary deliverable format for all builds
- **Cluster isolation**: Each cluster independent (unit of sharding/tenancy)
- **Resource flow**: Application → Component → Snapshot → IntegrationTestScenario → ReleasePlan → Release

### Repository Structure

- `/architecture/` - Service documentation and full system overview
  - `/core/` - Core service markdown files
  - `/add-ons/` - Optional service markdown files
  - `index.md` - Complete architecture overview (LARGE - use sparingly)
- `/ADR/` - Architecture Decision Records (50+ files - use INDEX.md for discovery)
- `/diagrams/` - Architecture diagrams in SVG format (draw.io)
- `/ref/` - API references (auto-generated during publish)

### Key Resource Definitions

- **Application** - Functionally coherent set of Components
- **Component** - Git repository/branch that produces OCI artifacts
- **Snapshot** - Immutable collection of OCI artifacts mapped to Components
- **IntegrationTestScenario** - Test definitions executed against Snapshots
- **ReleasePlan** - Release pipeline definition for promoting Snapshots
- **Release** - Actual release request for specific Snapshot artifacts


### Notes

- This is a **documentation-only repository** (no code, builds, tests, or linters)
- Diagrams created with draw.io, stored as SVG in `/diagrams/`
- ADRs follow template in `/ADR/0000-adr-template.md`
- All changes require peer-reviewed pull requests