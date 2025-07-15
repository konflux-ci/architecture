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

    style App fill:#f9f,stroke:#333,stroke-width:2px
    style Comp fill:#f9f,stroke:#333,stroke-width:2px
    style Snap fill:#ccf,stroke:#333,stroke-width:2px
    style ITS fill:#f9f,stroke:#333,stroke-width:2px
    style RP fill:#f9f,stroke:#333,stroke-width:2px
    style Release fill:#ccf,stroke:#333,stroke-width:2px
    style PR fill:#eee,stroke:#333,stroke-width:1px
    style PRM fill:#eee,stroke:#333,stroke-width:1px
    style BPR fill:#eee,stroke:#333,stroke-width:1px
    style TPR fill:#eee,stroke:#333,stroke-width:1px
    style RPA fill:#f9f,stroke:#333,stroke-width:2px
    style ECP fill:#f9f,stroke:#333,stroke-width:2px
    style IC fill:#ffb74d,stroke:#333,stroke-width:2px
    style QIO fill:#fff,stroke:#333,stroke-width:1px
    style MPC fill:#ffb74d,stroke:#333,stroke-width:2px
    style IR fill:#fff,stroke:#333,stroke-width:1px
    style IRR fill:#fff,stroke:#333,stroke-width:1px
    style ISC fill:#ffb74d,stroke:#333,stroke-width:2px
    style EXT fill:#fff,stroke:#333,stroke-width:1px

    classDef controlPlane fill:#f9f,stroke:#333,stroke-width:2px;
    class App,Comp,ITS,RP,RPA,ECP,IC,MPC,ISC controlPlane;

    classDef dataPlane fill:#ccf,stroke:#333,stroke-width:2px;
    class Snap,Release dataPlane;

    classDef tekton fill:#eee,stroke:#333,stroke-width:1px;
    class PR,PRM,BPR,TPR tekton;
```

## Service (Component) Context

```mermaid
graph TD
    subgraph Konflux Add-Ons
        IC[Image Controller]
        MPC[Multi-Platform Controller]
        ISC[Internal Services Controller]
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

    style IC fill:#ffb74d,stroke:#333,stroke-width:2px;
    style MPC fill:#ffb74d,stroke:#333,stroke-width:2px;
    style ISC fill:#ffb74d,stroke:#333,stroke-width:2px;
    style kubeapi fill:#f0e68c,stroke:#333,stroke-width:2px;
    style TW fill:#f0e68c,stroke:#333,stroke-width:2px;
    style MW fill:#f0e68c,stroke:#333,stroke-width:2px;
    style AWS fill:#fff,stroke:#333,stroke-width:1px;
    style IBM fill:#fff,stroke:#333,stroke-width:1px;
    style EXT fill:#fff,stroke:#333,stroke-width:1px;
    style OCI fill:#fff,stroke:#333,stroke-width:1px;
```

### Image Controller

The [Image Controller] manages the `ImageRepository` resource, which is a subsidiary of the `Component` resource. It induces the Image Controller to create and manage quay.io repositories for the build pipeline run. It injects push secrets into the tenant namespace for use by the build pipeline.

### Multi-Platform Controller

The [Multi-Platform Controller] has no explicit resources of its own, but it reacts when it sees the build pipeline run and provisions VMs in multiple public cloud APIs (AWS and IBM Cloud) to provide multi-architecture compute for builds, including linux/amd64 and linux/arm64 from AWS and linux/ppc64le and linux/s390x from IBM Cloud.

### Internal Services Controller

The [Internal Services Controller] has a single resource, the `InternalRequest`, that is created in the managed namespace by the managed release pipeline run. An Internal Services Controller running on a different cluster watches for those and reconciles them to perform actions in another network zone. 

[Image Controller]: ./image-controller.md
[Multi-Platform Controller]: ./multi-platform-controller.md
[Internal Services Controller]: ./internal-services.md
