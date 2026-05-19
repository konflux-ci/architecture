index.md 424L — Full system overview (read when 3+ services involved)

core/build-service.md 284L — Build pipelines, Tekton PipelineRun definitions, Component builds
core/enterprise-contract.md 198L — Policy enforcement, attestation validation, release gating
core/hybrid-application-service.md 371L — Validation webhooks for Application and Component CRs
core/index.md 175L — Core Services
core/integration-service.md 224L — Test orchestration, snapshot creation/validation, promotion logic
core/konflux-ui.md 20L — Web UI for Konflux platform (minimal architecture docs in this repo)
core/release-service.md 146L — Release orchestration, privileged pipelines, cross-namespace releases
add-ons/image-controller.md 215L — Image repository setup, robot account management, secret linking to ServiceAccounts
add-ons/index.md 239L — Add-ons
add-ons/internal-services.md 140L — Remote cluster polling for executing internal jobs across network boundaries
add-ons/kubearchive.md 98L — Archival and lifecycle management of ephemeral Kubernetes resources
add-ons/mintmaker.md 160L — Automated dependency updates using Renovate for Konflux components
add-ons/multi-platform-controller.md 274L — Dynamic VM provisioning for multi-architecture builds (arm64, ppc64le, s390x)
add-ons/project-controller.md 190L — Project and development stream management via templating system
add-ons/pulp-access-controller.md 217L — Automated Pulp domain and secret provisioning for artifact storage
