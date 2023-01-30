# 12. Namespace Name Format

Date: 2023-01-23

## Status

Accepted

## Context

The OSD-based control plane provisions one namespace in the target member cluster for every workspace (internally represented by a Space CR) which is created for a StoneSoup user. All the namespace names provisioned in this way should have a fixed suffix because of two reasons:
1. Visual separation of the namespaces provisioned for StoneSoup workspaces.
2. Limiting the risk of conflicting with the names used for other namespaces that are present in the cluster - either by default for every OCP/OSD/ROSA cluster or created via other SRE pipelines.

## Decision

Every namespace provisioned for a StoneSoup top-level workspace will have a name with the fixed suffix `-tenant`. The complete format will be `<workspace-name>-tenant`.

This applies only to the top-level workspaces that support StoneSoup API. This doesn't apply to the environment sub-workspaces since their template(s) and their suffix(es) haven't been decided yet.

## Consequences

Any changes in the format of the namespace names cause the deletion of all existing namespaces (provisioned for StoneSoup workspaces), followed by the creation of the namespaces which will use the new format. In other words, all data in the old namespaces will be deleted.
