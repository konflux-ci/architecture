---
date: 2023-01-23T00:00:00Z
title: Namespace Name Format
number: 12
---
# Namespace Name Format

## Status

Accepted

## Context

The OSD-based control plane provisions one namespace in the target member cluster for every workspace (internally represented by a Space CR) which is created for a Konflux user. All the namespace names provisioned in this way should have a fixed suffix because of two reasons:
1. Visual separation of the namespaces provisioned for Konflux workspaces.
2. Limiting the risk of conflicting with the names used for other namespaces that are present in the cluster - either by default for every OCP/OSD/ROSA cluster or created via other SRE pipelines.

## Decision

Every namespace provisioned for an Konflux top-level workspace will have a name with the fixed suffix `-tenant`. The complete format will be `<workspace-name>-tenant`.
Every namespace provisioned for an Konflux environment sub-workspace (created from a `SpaceRequest` CR using `appstudio-env` tier) will have a name with the fixed suffix `-env`. The complete format will be `<sub-workspace-name>-env`.

## Consequences

Any changes in the format of the namespace names cause the deletion of all existing namespaces (provisioned for Konflux workspaces), followed by the creation of the namespaces which will use the new format. In other words, all data in the old namespaces will be deleted.
