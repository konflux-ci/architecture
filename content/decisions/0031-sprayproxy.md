---
date: 2023-10-24T00:00:00Z
title: Sprayproxy
number: 31
---
# Sprayproxy

## Status

Accepted

## Context

Konflux has multiple member (backend) clusters. Each member cluster is running a Pipelines-As-Code (PaC) service, accepting webhook requests. A GitHub App can only specify a single destination for webhook requests. We need to forward those requests to multiple clusters.

## Decision

Deploy a service (`Sprayproxy`) on the Konflux host (frontend) clusters. The service route is configured in the GitHub App as a `Webhook URL`, so all webhook requests are directed to it. The service has a list of backends configured. The service does not distinguish between the type of requests the way PaC does (pull-request/push/comment etc), it treats them all equally. For each incoming request, a new outgoing request is constructed with the original payload and destination of each of the member clusters.

The service performs the following checks on incoming requests:

- Validating the request is from GitHub using a shared secret. The process is officially documented [here](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries).
- [Payloads are capped at 25 MB](https://docs.github.com/en/webhooks/webhook-events-and-payloads#payload-cap), but that's configurable.

The QE team requires the ability to dynamically add/remove backends. That functionality is disabled by default as it represents a security risk (bad actor could access private content if they get the forwarded content or cause denial of service). To enable that functionality, the service should be started with a special flag. The actual registration/unregistration happens through additionally exposed backends endpoint using the respective GET/POST/DELETE HTTP requests. The authentication happens through kube-rbac-proxy.

The service exports metrics visible only on the dashboards on the host clusters where the service is deployed. The authentication happens through kube-rbac-proxy.

## Consequences

- Each Konflux customer is onboarded to one cluster which means a pipeline on that particular cluster will be triggered as a result of the request. By "blindly" forwarding the request to all clusters, requests are also sent to clusters where they won't have effect and are discarded.
- Sprayproxy performs the same type of request verification as does PaC. The reason for doing that is we do not forward invalid requests to multiple clusters, but it also means extra workload. Operationally both services use the same shared secret, so when rotating the secret it only has to be done in a single place.
