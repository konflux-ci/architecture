---
title: KubeArchive
eleventyNavigation:
  key: KubeArchive
  parent: Add-ons
  order: 6
toc: true
overview:
  scope: "Archival and lifecycle management of ephemeral Kubernetes resources"
  key_crds:
    - KubeArchiveConfig
    - ClusterKubeArchiveConfig
  related_services:
    - pipeline-service
    - integration-service
    - release-service
  related_adrs:
    - "0064"
  key_concepts:
    - Resource archival to external database
    - CEL-based archival and deletion policies
    - Kubernetes RBAC-delegated REST API server
---

# KubeArchive

## Overview

[KubeArchive](https://github.com/kubearchive/kubearchive) is a tool that archives Kubernetes resources outside of the cluster and is able to delete these resources from the cluster. And it exposes a REST API protected by the Kubernetes RBAC (it uses SubjectAccessReview and TokenReview to delegate auth).

KubeArchive is essential for operating Konflux at scale. Without it, completed `Snapshot`s, `Release`s other resources accumulate in Etcd, impacting cluster performance. See [ADR 63](../../ADR/0063-kubearchive.md) for the decision to adopt KubeArchive.

## Architecture

KubeArchive consists of four components:

- **Operator**: A Kubernetes controller that reconciles `KubeArchiveConfig` and `ClusterKubeArchiveConfig` custom resources. It manages RBAC resources and other intermediate resources used for KubeArchive internal coordination. It also watches resources, filters them and sends the ones that need action to the KubeArchive Sink.

- **Sink**: Receives resources from the Operator's watches and persists the resources to its database. The Sink processes add, update, and delete events and ensures the DB reflects the latest state of each resource.

- **API Server**: A REST API that exposes archived resources. It delegates authentication and authorization to the Kubernetes RBAC service — clients authenticate with the same bearer tokens used for Kubernetes API requests. The API follows the pattern `https://<host>/api/v1/namespaces/{namespace}/{resource-type}` so it is compatible with most Kubernetes clients.

- **Vacuum**: A CronJob that process that scans the cluster for resources when delayed deletes or counted deletes are required (`keepLastWhen` rules).

## Configuration

KubeArchive is configured through two custom resources:

### KubeArchiveConfig

Defines archival and deletion rules for resources within a single namespace. Just one `KubeArchiveConfig` named `kubearchive` is allowed per namespace.
See an example of `KubeArchiveConfig` below:

```yaml
apiVersion: kubearchive.org/v1
kind: KubeArchiveConfig
metadata:
  name: kubearchive
  namespace: <tenant-ns>
spec:
  resources:
    - selector:
        apiVersion: tekton.dev/v1
        kind: PipelineRun
      archiveWhen: "has(status.completionTime)"
      deleteWhen: "timestamp(status.completionTime) < now() - duration('72h')"
    - selector:
        apiVersion: appstudio.redhat.com/v1alpha1
        kind: Snapshot
      archiveWhen: "true"
      keepLastWhen:
        - name: daily-backups
          when: "metadata.name.startsWith('daily-backup-')"
          count: 7
```

### ClusterKubeArchiveConfig (cluster-scoped)

Follows a very similar syntax like the `KubeArchiveConfig` custom resource but applies to all the namespaces
that contain `KubeArchiveConfig`.

### Rule Types

All rules use [CEL (Common Expression Language)](https://github.com/google/cel-spec) expressions:

- **archiveWhen**: Archives matching resources to the database. Evaluated by both the controller (on change) and the vacuum (on schedule).
- **deleteWhen**: Deletes resources from the cluster after archiving them. Evaluated by the controller (on change).
- **keepLastWhen**: Retains only the N most recent matching resources, deleting and archiving older ones. Evaluated by the vacuum (on schedule).
- **archiveOnDelete**: Archives resources when they are deleted by an external process (a delete event is sent to the watch), if they match the specified condition.

## Dependencies

KubeArchive depends on:
- A PostgreSQL-compatible database for storing archived resources
- Kubernetes itself

## Repositories

- [kubearchive/kubearchive](https://github.com/kubearchive/kubearchive)
