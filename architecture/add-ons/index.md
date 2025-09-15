# Konflux Add-Ons

Konflux subsystems are divided into two categories: **core** and **add-ons**. The [core subsystems](../index.md) are required for a working system, while add-ons are optional services that provide additional capabilities.

This document describes the add-on subsystems and how they integrate with the rest of the Konflux platform.

## Application Context

```mermaid
graph TD
    QIO["quay.io tenant repositories"]
    subgraph clouds[Public Clouds]
        AWS["AWS Public Cloud"]
        IBM["IBM Public Cloud"]
    end
    BPR -- pushes images to --> QIO
    IC -- manages --> QIO
    MPC -- manages VMs --> clouds
    BPR -- SSHes to --> clouds

    subgraph tenant[Tenant Namespace]
        App[Application] --> Comp["Component(s)"]
        App --> ITS["IntegrationTestScenario(s)"]
        App --> RP["ReleasePlan(s)"]

        Comp -- defines --> BPR["Build PipelineRun(s)"]
        BPR -- produces --> Snap["Snapshot"]
        ITS -- defines --> TPR["Test PipelineRun(s)"]
        Snap -- triggers --> TPR
        RP -- defines release for --> Release["Release(s)"]
        TPR -- triggers --> Release

        Release -- initiates --> PR["Release PipelineRun(s) (Tenant)"]
        Comp -- defines --> IR["ImageRepository"]
    end

    subgraph addons[Add-on Namespaces]
        IC["Image Controller"]
        MPC["Multi-Platform Controller"]
        MM["MintMaker"]
    end

    IR -- managed by --> IC
    IC -- injects push secrets --> BPR
    BPR -- triggers multi-arch provisioning --> MPC
    MPC -- provisions VMs for --> BPR

    subgraph managed[Managed Namespace]
        RPA["ReleasePlanAdmission(s)"]
        ECP["EnterpriseContractPolicy(s)"]

        Release -- initiates --> PRM["Release PipelineRun(s) (Managed)"]
        RP -- matched to --> RPA
        RPA -- parameterizes --> PRM
        PRM -- enforces policy via --> ECP
        PRM -- creates --> IRR["InternalRequest"]
    end

    subgraph external[External Network Cluster]
        ISC["Internal Services Controller"]
        IRR -- watched by --> ISC
        ISC -- performs actions on --> EXT["External Network Resources"]
    end

    style App fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000000
    style Comp fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000000
    style Snap fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000000
    style ITS fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000000
    style RP fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000000
    style Release fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000000
    style PR fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000
    style PRM fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000
    style BPR fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000
    style TPR fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000
    style RPA fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000000
    style ECP fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000000
    style IC fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    style QIO fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000
    style MPC fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    style IR fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000
    style IRR fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000
    style ISC fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    style EXT fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000
    style AWS fill:#e8f5e8,stroke:#2e7d32,stroke-width:1px,color:#000000
    style IBM fill:#e8f5e8,stroke:#2e7d32,stroke-width:1px,color:#000000

    classDef controlPlane fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000000;
    class App,Comp,ITS,RP,RPA,ECP,IC,MPC,ISC,MM controlPlane;

    classDef dataPlane fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000000;
    class Snap,Release dataPlane;

    classDef tekton fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000;
    class PR,PRM,BPR,TPR tekton;

    click App "Application API Reference" "https://konflux-ci.dev/docs/reference/kube-apis/application-api/#k8s-api-github-com-konflux-ci-application-api-api-v1alpha1-application"
    click Comp "Component API Reference" "https://konflux-ci.dev/docs/reference/kube-apis/application-api/#k8s-api-github-com-konflux-ci-application-api-api-v1alpha1-component"
    click Snap "Snapshot API Reference" "https://konflux-ci.dev/docs/reference/kube-apis/application-api/#k8s-api-github-com-konflux-ci-application-api-api-v1alpha1-snapshot"
    click ITS "IntegrationTestScenario API Reference" "https://konflux-ci.dev/docs/reference/kube-apis/integration-service/#k8s-api-github-com-konflux-ci-integration-service-api-v1alpha1-integrationtestscenario"
    click Release "Release API Reference" "https://konflux-ci.dev/docs/reference/kube-apis/release-service/#k8s-api-github-com-konflux-ci-release-service-api-v1alpha1-release"
    click RP "ReleasePlan API Reference" "https://konflux-ci.dev/docs/reference/kube-apis/release-service/#k8s-api-github-com-konflux-ci-release-service-api-v1alpha1-releaseplan"
    click RPA "ReleasePlanAdmission API Reference" "https://konflux-ci.dev/docs/reference/kube-apis/release-service/#k8s-api-github-com-konflux-ci-release-service-api-v1alpha1-releaseplanadmission"
    click IR "ImageRepository API Reference" "https://konflux-ci.dev/docs/reference/kube-apis/image-controller/#k8s-api-github-com-konflux-ci-image-controller-api-v1alpha1-imagerepository"
```

## Service (Component) Context

```mermaid
graph TD
    subgraph Konflux Add-Ons
        IC[Image Controller]
        MPC[Multi-Platform Controller]
        ISC[Internal Services Controller]
        MM[MintMaker]
    end

    subgraph quayio[quay.io]
        OCI[OCI Repositories]
    end

    subgraph cloudapis[Public Cloud APIs]
        AWS[AWS]
        IBM[IBM Cloud]
    end

    subgraph kubeapi[Kubernetes API Server]
        TW[Tenant Workspace]
        MW[Managed Workspace]
    end

    IC -- Manages repositories --> OCI
    IC -- Watches ImageRepository --> TW
    IC -- Injects push secrets --> TW
    MPC -- Provisions multi-arch VMs for builds --> cloudapis
    MPC -- Watches Build PipelineRuns --> TW
    ISC -- Watches InternalRequest in Managed Namespace --> MW
    ISC -- Performs actions in --> EXT[External Network Zone]

    style IC fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000;
    style MPC fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000;
    style ISC fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000;
    style MM fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000;
    style kubeapi fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#000000;
    style TW fill:#ffffff,stroke:#1565c0,stroke-width:3px,color:#000000;
    style MW fill:#ffffff,stroke:#1565c0,stroke-width:3px,color:#000000;
    style AWS fill:#e8f5e8,stroke:#2e7d32,stroke-width:1px,color:#000000;
    style IBM fill:#e8f5e8,stroke:#2e7d32,stroke-width:1px,color:#000000;
    style EXT fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000;
    style OCI fill:#f5f5f5,stroke:#424242,stroke-width:1px,color:#000000;
```

### Image Controller

The [Image Controller] manages the `ImageRepository` resource, which is a subsidiary of the `Component` resource. It induces the Image Controller to create and manage quay.io repositories for the build pipeline run. It injects push secrets into the tenant namespace for use by the build pipeline.

### Multi-Platform Controller

The [Multi-Platform Controller] has no explicit resources of its own, but it reacts when it sees the build pipeline run and provisions VMs in multiple public cloud APIs (AWS and IBM Cloud) to provide multi-architecture compute for builds, including linux/amd64 and linux/arm64 from AWS and linux/ppc64le and linux/s390x from IBM Cloud.

### Internal Services Controller

The [Internal Services Controller] has a single resource, the `InternalRequest`, that is created in the managed namespace by the managed release pipeline run. An Internal Services Controller running on a different cluster watches for those and reconciles them to perform actions in another network zone.

### MintMaker

The [MintMaker] automates dependency updates for Konflux components using Renovate. It introduces the `DependencyUpdateCheck` custom resource that triggers dependency scanning across Components, creating Tekton PipelineRuns to execute Renovate scans and generate pull requests with dependency updates. The Tekton PipelineRuns execute in a system mintmaker namespace, not in Component namespace.

[Image Controller]: ./image-controller.md
[Multi-Platform Controller]: ./multi-platform-controller.md
[Internal Services Controller]: ./internal-services.md
[MintMaker]: ./mintmaker.md
