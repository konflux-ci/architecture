# ADR 0071: Decentralize Tenant Build Configuration from konflux-release-data

## Status

Proposed

## Context

Today, all Konflux tenant configuration — Applications, Components, ImageRepositories, IntegrationTestScenarios, ReleasePlans, and RBAC — is managed through a single monorepo: `konflux-release-data`. This includes both **release configurations** (ReleasePlanAdmissions, EnterpriseContractPolicies) which require releng/ProdSec review, and **tenant build configurations** (Applications, Components, ITS) which are self-serviceable.

This creates several problems:

1. **Bottleneck for automation.** Teams wanting to dynamically create/delete Components (e.g., CNV's developer build environments, ephemeral test namespaces) must go through an MR → CI → merge → ArgoCD sync cycle that takes 30-45 minutes per change. Rebase conflicts with unrelated MRs in the same repo add further delays.

2. **Blocked self-service paths.** Users can create Applications and Components via the Konflux UI instantly, but the equivalent GitOps path requires an MR to a shared repo. RBAC policies (`deny-serviceaccount-token-secrets`, restricted bot-actions ClusterRoles) prevent teams from using their own automation (e.g., external ArgoCD) to manage resources in their own namespaces.

3. **Misaligned scope.** `konflux-release-data` is a *release* configuration repo. Tenant build configuration (what to build, where to build it) is operationally distinct from release configuration (how to release, what policies to enforce). Co-locating them creates unnecessary coupling.

4. **Scale limitations.** As tenant count grows, CI pipeline duration increases for all tenants. A change to one tenant's Components triggers validation across the entire repo.

## Decision

Separate tenant build configuration from release configuration:

- **Keep in `konflux-release-data`:** ReleasePlanAdmissions, EnterpriseContractPolicies, constraints, prodsec configs, CODEOWNERS for release approval — anything requiring releng or ProdSec review.

- **Move out of `konflux-release-data`:** Applications, Components, ImageRepositories, IntegrationTestScenarios, ReleasePlans, tenant RBAC (maintainers/contributors/admins), ServiceAccounts — anything that is self-serviceable by the tenant team.

### Options for where tenant config moves

**Option A: Per-tenant repos**
Each tenant team maintains their own GitOps repo (or directory in their existing repo) for Konflux resources. ArgoCD ApplicationSets discover and sync per-tenant sources.

- Pro: Full team autonomy, no shared repo bottleneck, natural RBAC via repo ownership
- Con: Loss of centralized cross-referencing (RP ↔ RPA validation), harder to audit globally, migration effort per tenant

**Option B: Centralized but separate repo**
A new `konflux-tenant-config` repo with faster CI (no release validation), relaxed merge requirements (auto-merge for tenant-scoped changes), and per-tenant ArgoCD Applications.

- Pro: Central auditability preserved, easier DR/migration, incremental change from current state
- Con: Still a shared repo (lighter bottleneck), still requires MR workflow

**Option C: Direct API / Operator-managed**
Tenants manage resources via Konflux API/CLI/UI directly. An operator reconciles desired state. No GitOps repo required for build config.

- Pro: Fastest self-service, matches UI behavior, no MR overhead
- Con: No git audit trail for build config, DR relies on operator backup, harder to reproduce state

## Consequences

### If accepted
- Teams can manage build resources at their own pace without MR bottleneck
- Release configuration review integrity preserved (stays in KRD)
- RBAC can be relaxed for tenant-scoped build resources without affecting release security
- DR/migration process needs to account for new config source(s)
- Cross-referencing between ReleasePlans and RPAs needs alternative validation mechanism

### If rejected
- Growing tension as more teams automate and hit the MR bottleneck
- Workarounds proliferate (teams requesting custom RBAC exceptions, shadow automation)
- KRD CI continues to slow as tenant count grows

## Related

- [KONFLUX-14725](https://redhat.atlassian.net/browse/KONFLUX-14725)
- [Slack thread](https://redhat-internal.slack.com/archives/C04PZ7H0VA8/p1782827507880419) — CNV team's request and discussion
- Existing ADR discussion on gitops-only workflow (referenced in #forum-konflux-developer)
