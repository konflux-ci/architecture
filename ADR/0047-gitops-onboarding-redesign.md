# 47. GitOps Onboarding Redesign

Date: 2024-12-21

## Status

Proposed

## Context

Currently, Konflux offers two distinct onboarding paths that create friction and complexity for developers:

### UI Onboarding
- Very easy to use with good validation and feedback
- Handles secrets, build config, environments through web interface
- Provides immediate feedback but doesn't align with GitOps principles

### GitOps Onboarding
- Requires manually authoring YAML across multiple files
- Validation happens during GitLab CI runs, creating tension between Konflux and GitLab CI workflows
- Secrets must still be created via UI, breaking the GitOps flow
- Onboarding requires manual creation of complex yaml objects
- Merge conflicts are more likely in monorepos, increasing time to onboard
- CI is not under control of the namespace owner
- Users are forced to use a specific git forge that might be different than the one their apps live in

### Current Pain Points
1. **Fragmented experience**: Developers must context-switch between UI and GitOps approaches
2. **Poor experience**: Onboarding / creating new objects requires authoring complex YAML objects by using examples from documentation or other repositories.
3. **Error-prone process**: Manual YAML authoring can lead to frequent failures
4. **Monorepo complexity**: Current GitOps monorepo for tenant configuration creates CODEOWNERS management overhead, requires freqeuent rebases and is prone to merge conflicts
5. **UI improvement limitations**: Despite continuous improvements to the UI, many users still choose GitOps onboarding for its inherent disaster recovery and change management benefits, leaving them unable to benefit from UI enhancements

## Decision

Redesign the onboarding experience to converge UI and GitOps into a single coherent, Git-centric flow through the following architectural changes:

### Alternative Approaches Considered

**Improving the existing UI** was considered but rejected because:
- Despite continuous UI improvements, many users still choose GitOps onboarding for its inherent disaster recovery and change management benefits
- UI enhancements don't address the fundamental issue of maintaining two separate onboarding flows
- Users who prefer GitOps principles cannot benefit from UI improvements, creating a permanent split in the user experience
- Konflux needs a strong disaster recovery story and having Gitops-based tenant configuration is a significant advantage there.

**Chosen approach** replaces both current flows with a unified Git-centric solution that preserves GitOps benefits while providing the usability improvements users expect.

### Core Shift
- **Deprecate ability to configure tenant resources via the UI** Users will configure resources directly via Kubernetes or via Gitops
- **Promot use of Git as the single source of truth** for applications, components, integration test scenarios, releasePlans and RBAC in production environments
- **Preserve the UI for non-configuration activities** including:
  - Monitoring and observability: logs, build inspection, viewing metrics, dashboards
  - Operational actions: triggering builds/tests, starting manual releases, pipeline management
  - Any other runtime actions that don't involve declarative resource configuration
- **Commit to single onboarding flow**: UI-based onboarding will be completely deprecated with no fallback option to minimize maintenance overhead and deliver optimal user outcomes
- **Maintain ease of use and excellent user experience** by providing a VS Code plugin that delivers forms based configuration of validation of tenant resources

### IDE Selection Rationale
VS Code was chosen as the primary IDE target because:
- **Wide adoption**: VS Code is extensively used across development teams
- **Robust plugin ecosystem**: Provides comprehensive APIs for linting, schema validation, and custom tooling
- **Advanced visualization capabilities**: Plugin system supports rich visualizations and can run full, sandboxed React-based applications within webview windows
- **Extensibility**: Enables building sophisticated onboarding wizards and configuration interfaces directly within the familiar IDE environment

### Component Architecture

| Component | Role | Optional |
|-----------|------|----------|
| VS Code Plugin | Main interface for onboarding and configuration | No |
| Git Repos | Source of truth for Konflux config | No |
| GitOps Registration Service | API for automated registration of GitOps repos as tenants | **Yes** (recommended) |
| ArgoCD Service | Continuous GitOps sync and deployment | **Yes** (recommended) |
| Konflux UI | Monitoring, runtime insights, and operational actions (non-configuration) | No |

### VS Code Plugin Design

**Core Features:**
- Forms and wizards to scaffold and edit YAML objects
- Built-in schema-aware YAML editor
- Linting and validation against Konflux schemas
- Git-aware diff view and PR-ready commit generation
- Optional: preview pipeline graph / dependency resolution


**GitOps Flow:**

1. Developer creates an empty git repo with Github, Gitlab, etc.
4. **If first time**: Uses wizard to register repo with Tenant Registration Service (declares namespace name, configures ArgoCD)
5. Developer is prompted by UI to install / open repo in VS Code
3. Launches Konflux plugin and uses it to configure new components, tests, releasePlans
6. Plugin generates YAML objects in repo
7. Developer commits and pushes code (optionally via PR, with CI,reviews etc.)
9. ArgoCD automatically syncs merged changes to the namespace

### Multi-Repo GitOps Model & Optional Services

**GitOps Registration Service (Optional):**
Konflux will optionally provide a **GitOps Registration Service** API that automates the registration and lifecycle of GitOps repositories as first-class tenants. This service is recommended for production deployments but not required for basic Konflux functionality.

**ArgoCD Service (Optional):**
ArgoCD can be optionally deployed as a continuous GitOps synchronization service. While recommended for production use, Konflux can operate without ArgoCD, though this results in reduced automation and requires manual synchronization of GitOps repositories.

**Impact of Optional Services:**
- **With both services**: Full automated GitOps experience with continuous deployment and streamlined onboarding
- **Without both services**: Konflux remains fully functional but requires manual GitOps repository setup and synchronization. This configuration provides:
  - Smaller deployment footprint suitable for lower-spec machines
  - Simplified setup for testing and development environments  
  - Reduced operational complexity for teams preferring manual control
  - Degraded user experience with manual setup steps
  - Reduced disaster recovery capabilities due to lack of automated drift detection

**Tenant Model:**
- **Tenant Definition**: A tenant is equivalent to a Kubernetes namespace
- **1:1 Mapping**: Each GitOps repository maps to exactly one Kubernetes namespace
- **Namespace Declaration**: The namespace name is a parameter to the registration service. Once the repo is registered, the namespace it is immutable.
- **Registration Immutability**: Re-registering the same repo is rejected to prevent namespace conflicts

**Resource Scope:**
- **Multi-Resource Support**: One GitOps repo can contain multiple applications, components, integrationTestScenarios, and releasePlans
- **Single Namespace Constraint**: All resources from a GitOps repo deploy to its designated namespace only
- **No Cross-Namespace Interaction**: Changes affecting N namespaces require changes in N separate GitOps repos

**Registration Process (when using optional services):**
1. Team registers GitOps repo via VS Code plugin, CLI (`konflux register`), or UI
2. at registration time the desired namespace name is provided to (UI | API)
3. GitOps Registration Service validates the repo and the requested namespace
4. Service provisions the new requested Kubernetes namespace
6. Service configures ArgoCD to monitor the repo for continuous deployment
7. ArgoCD continuously syncs changes from the repo to the namespace


**Manual Process (when not using optional services):**
1. Team manually creates Kubernetes namespace with desired name
2. Team manually configures cluster access and GitOps tooling
3. Team manually applies GitOps repository contents to namespace
4. Team manually monitors for changes and applies updates as needed

**Key Principles:**
- **Team Autonomy**: Each team owns their GitOps repo and corresponding namespace
- **Simplified Management**: Eliminates complex CODEOWNERS management in monorepos
- **Environment Agnostic**: Environments are not a concept in Konflux-CI; teams manage environment separation through their own repo organization

The following diagram illustrates the relationship between GitOps repositories, namespaces, and Konflux resources:

```mermaid
graph TD
    subgraph "Team"
        Repo["📁 GitOps Repo<br/>github.com/team/config"]
    end
    
    subgraph "Konflux"
        GRS["🏗️ GitOps Registration Service<br/>(Optional)<br/>• Validates repo<br/>• Provisions namespace<br/>• Configures ArgoCD"]
        
        NS["🎯 Namespace: team-prod<br/>(declared in repo)"]
        
        ArgoCD["🔄 ArgoCD Service<br/>(Optional)<br/>• Continuous sync<br/>• Propagates changes<br/>• Monitors repo"]
    end
    
    Repo -.->|"One-time registration<br/>(if using optional services)"| GRS
    GRS -.->|"Creates"| NS
    GRS -.->|"Configures (if available)"| ArgoCD
    
    Repo -->|"Continuous sync<br/>(if ArgoCD available)"| ArgoCD
    ArgoCD -->|"Deploys resources"| NS
    
    classDef repoStyle fill:#1976d2,stroke:#0d47a1,stroke-width:2px,color:#fff
    classDef nsStyle fill:#7b1fa2,stroke:#4a148c,stroke-width:2px,color:#fff
    classDef optionalServiceStyle fill:#f57c00,stroke:#e65100,stroke-width:2px,color:#fff,stroke-dasharray: 5 5
    
    class Repo repoStyle
    class NS nsStyle
    class GRS optionalServiceStyle
    class ArgoCD optionalServiceStyle
```

**Key Relationships:**
- **Optional Registration**: GitOps Registration Service (when available) is used once per repo to create namespace and configure ArgoCD
- **Optional Continuous Sync**: ArgoCD (when available) continuously propagates changes from repo to namespace
- **Manual Alternative**: Without optional services, teams manually manage namespace creation and GitOps synchronization
- **1:1 Mapping**: Each GitOps repo maps to exactly one namespace
- **Immutable Names**: Namespace names are declared in the repo and cannot change
- **Single Deployment Target**: All resources from one repo deploy to one namespace
- **No Cross-Namespace Resources**: Each team's resources are isolated within their own namespace


### CI/Validation Design

- Introduce a Konflux CLI validator (or GitHub Action) for local + CI use
- Validates schema, references, build logic statically
- Same validator embedded in VS Code plugin
- Optional: Plugin lints against live cluster (e.g., available build agents)

### UI Changes

**Preserve:**
- Dashboard
- Build and release logs
- Operational actions: triggering builds/tests, starting manual releases, pipeline management

**Remove/Demote:**
- UI forms for configuring components, applications, and other declarative resources

## Consequences

### Positive Consequences

1. **Unified Developer Experience**: Single Git-centric flow eliminates context switching between UI and GitOps
2. **Faster Onboarding**: Local validation reduces time-to-merge for onboarding PRs (enhanced with optional services)
3. **Clear Tenant Model**: 1:1 mapping between GitOps repos and namespaces provides clear ownership and boundaries
4. **Improved Team Autonomy**: Multi-repo model allows teams to own their GitOps repositories and corresponding namespaces
5. **Better IDE Integration**: Leverages familiar VS Code tooling and workflows
6. **Flexible Deployment Options**: Optional services allow deployment scaling from lightweight setups to full-featured production environments
7. **Resource Efficiency**: Minimal footprint option suitable for lower-spec machines and testing environments
8. **Optional GitOps Automation**: When ArgoCD is deployed, provides industry-standard continuous deployment with automatic drift detection and reconciliation
9. **Maintained GitOps Benefits**: Preserves disaster recovery, change history, and automation capabilities (enhanced with optional services)

### Negative Consequences

1. **Tool Dependency**: Requires VS Code and plugin installation for optimal experience
2. **Learning Curve**: Developers must adapt to new plugin-based workflow
3. **Development Overhead**: Requires building and maintaining VS Code plugin and optional services
4. **Manual Operations**: Without optional services, teams must manually manage GitOps operations, reducing automation benefits
5. **Migration Complexity**: Existing users must migrate from current UI/GitOps hybrid approach
6. **Configuration Complexity**: Teams must choose between manual setup (simple but limited) vs. optional services (full-featured but more complex)

### Risks and Mitigations

1. **Plugin Adoption**: Risk of low adoption if plugin is complex or unreliable
   - Mitigation: Provide CLI fallback and comprehensive documentation
2. **Schema Validation**: Local validation may diverge from server-side validation
   - Mitigation: Use same validation logic in plugin and CI
3. **No Rollback Option**: Once UI-based onboarding is deprecated, there is no fallback to the previous approach
   - Mitigation: Ensure thorough testing and gradual rollout with comprehensive user training and documentation

### Open Questions

No open questions at this time.

### Migration Path

1. **Phase 1**: Develop VS Code plugin with local validation
2. **Phase 2**: Implement optional GitOps Registration Service
3. **Phase 3**: Implement ArgoCD Service
4. **Phase 4**: Migration support for existing users
5. **Phase 5**: Remove deprecated UI configuration components

**Note**: Teams can choose to deploy Konflux without the optional services for simpler setups, accepting the trade-offs in automation and user experience.

**Note**: Once the GitOps approach is implemented, the UI-based onboarding will be completely deprecated with no fallback option. This decision prioritizes streamlining to a single onboarding flow to minimize maintenance overhead and deliver the best user outcomes.

### Migration from UI to GitOps

To support migration from the current UI-based approach to GitOps, a CLI tool will be provided that enables tenant administrators to export their existing namespace configurations to a local GitOps repository structure. The tool will accept a namespace as input and generate the required YAML objects (applications, components, integration test scenarios, release plans, and RBAC configurations) in the local folder structure expected by the GitOps workflow. This allows existing UI users to bootstrap their GitOps repositories with their current configurations and then transition to the new Git-centric workflow without recreating their entire setup from scratch.

## Security Implications

A critical security consideration in any GitOps implementation is ensuring that the GitOps sync process cannot create arbitrary resources beyond what a namespace administrator would normally be permitted to create. Without proper constraints, GitOps operators could potentially be exploited to escalate privileges or deploy unauthorized resources.

### Security Mitigation Approaches

**ArgoCD Application Sync Using Impersonation:**
ArgoCD impersonation allows GitOps sync operations to use dedicated, limited-privilege service accounts per namespace rather than the highly privileged control plane service account. This ensures that sync operations can only create resources that a namespace administrator would normally be allowed to create, providing strong tenant isolation through the principle of least privilege.

**ArgoCD AppProject Controls:**
ArgoCD AppProjects provide logical security boundaries that prevent cross-contamination by restricting which Git repositories can deploy to which namespaces. Each AppProject defines allowed source repositories, destination namespaces, and permitted resource types, with strict validation occurring before any sync operations begin. In Konflux's architecture, the GitOps Registration Service would automatically create and manage these AppProject definitions during tenant onboarding.


### References

- [ArgoCD Application Sync Using Impersonation](https://argo-cd.readthedocs.io/en/latest/operator-manual/app-sync-using-impersonation/) - Official ArgoCD documentation on impersonation features
- [Leveraging ArgoCD in Multi-tenanted Platforms](https://www.cecg.io/blog/multi-tenant-argocd/) - CECG guidance on using ArgoCD AppProjects for tenant autonomy and isolation





## References

No external references at this time. 
