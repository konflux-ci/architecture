# 2. Interacting with Internal Services

Date: 2022-10-20

## Status

---

New

## Context

---

Many organizations, including Red Hat, possess numerous internal services that help productize their software.
In many cases, these internal services will continue to play a role in the release workflows used in AppStudio/HACBS.

It is extremely important to design the interaction with internal services in such as way as to avoid any potential
attack vectors towards an organization's internal networks.

**Problem**: AppStudio/Release pipelines need to **initiate** processes with an organization's internal services which
are **not publicly addressable** in a secure fashion and be able to obtain process status and completion results.

## Decision

---

Use a "controller" running in a private cluster that can watch and reconcile **Request** custom resources in
one or more workspaces. This will be referred to as the **Internal Service Controller**.

**Request** is used here as a general type meaning that real use cases might involve custom resources
such as **ServiceABCRequest**.

This strategy will make use of [KCP]'s VirtualWorkspace model allowing a controller to watch a group of
workspace via a single KUBECONFIG.

This internal service controller is expected to trigger a specific job that encapsulates the Internal Service's unit of work
that HACBS wants to initiate.

It is expected that the controller should update the **status** of the **Request** CR to denote the progress of the
triggered unit of work.

The controller should also be able to update the **Request** CR to provide a **result** back to the process that
originally created the custom resource.

**Example:**

During the course of an attempt to release content, artifacts may need to be signed. The service that
performs the signing process is an internal service within an organization with no publicly addressable API.
The [release-service] may execute a release strategy that has a step that wants to access that signing service's
API and obtain a result payload to be used in downstream steps in the release strategy.

## Architecture Overview

---

![Interacting with Internal Services](../diagrams/interacting-with-internal-services.jpg)

## Open Questions

---

* How can internal services controllers control who they accept requests from?

## Consequences

---

* If the managed workspace for a customer is a cluster that they control, that teams will have to install their own
Custom Resource Definitions on that cluster.
 * Then custom release pipelines can create CRs for that CRD to make a request to the Internal Service.
* Skill gap. Not all engineers are experienced with writing controllers. Nonetheless, this pattern will enable
developers to gain the experience.

## References

---

[KCP]: ../ref/kcp.md
[release-service]: ../book/release-service.md

