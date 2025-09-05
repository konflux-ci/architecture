# NN. Exclude Kubernetes Events API from User RBAC Roles

Date: 2025-09-05

## Status

Proposed

Relates to [ADR 11. Roles and Permissions](0011-roles-and-permissions.md)

## Context

Konflux users require RBAC permissions to interact with various Kubernetes resources through our defined roles (Viewer, Contributor, Maintainer, Admin). The Kubernetes `events` API provides access to cluster events, which can contain information about resource changes and system activities. Users may find that API useful, but it raises other problems.

## Decision

We will exclude the Kubernetes `events` API from all Konflux user RBAC roles.

## Consequences

**Positive:**
- Prevents users from programmatically depending on the loosely structured events API that can change over time
- Eliminates security risk where users might access event information about resources they don't have direct permissions to view
- Reduces the attack surface by limiting overly broad access

**Negative:**
- Users cannot view cluster events through the standard Kubernetes API
- Some debugging and monitoring capabilities are reduced for end users
- Users may need to rely on other observability tools for event-based troubleshooting

**Neutral:**
- This aligns with the principle of least privilege for user-facing roles
- System administrators and operators can still access events through their elevated permissions
