---
title: "64. Adopt KubeArchive for resource lifecycle management"
status: Implemented
applies_to:
  - pipeline-service
  - kubearchive
topics:
  - archival
  - scalability
  - resource-lifecycle
---

# 64. Adopt KubeArchive for resource lifecycle management

Date: 2026-03-16

## Status

Implemented

## Context

Konflux generates a large amount of one-shot Kubernetes resources such as `PipelineRun`s, `TaskRun`s, `Snapshot`s, `Release`s... Some of these remain on the cluster, worsening the performance on Etcd and thus on the performance on the cluster. Konflux used (and still uses at the time of writing) Tekton Results to handle the cleanup and storage of Tekton related resources (`PipelineRun`s, `TaskRun`s ...). While useful, Tekton Results does not handle non-Tekton resources, leaving Konflux with a large number of `Snapshot`s and `Release`s without cleaning. Konflux developed custom scripts to address the cleanup of these resources, but they were not persisted for future reference.

## Decision

With this context in mind, Konflux decided to adopt [KubeArchive](https://github.com/kubearchive/kubearchive), a tool that archives and is able to delete resources for the cluster, born from the idea of Tekton Results but generalized to arbitrary Kubernetes resources. KubeArchive covered the archival and deletion of `Snapshot`s and `Release`s. KubeArchive could handle `PipelineRun`s, `TaskRun`s, `Pod`s and their logs as well, so Konflux decided to gradually adopt KubeArchive for these resources and remove Tekton Results from Konflux.

The decision was based on the following points:

* KubeArchive has a Kubernetes API compatible REST API, so Kubernetes clients are mostly usable with KubeArchive
* KubeArchive handles Tekton resources, so Konflux just needs to maintain one archival solution
* KubeArchive is managed at Red Hat, so steeering of its features is easier

## Consequences

- KubeArchive is deployed as an add-on (is not required to function)
- Tekton Results is gradually removed
- A PostgreSQL-compatible database is required for KubeArchive's storage backend
