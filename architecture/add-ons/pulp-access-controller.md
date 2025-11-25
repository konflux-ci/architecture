---
title: Pulp Access Controller
eleventyNavigation:
  key: Pulp Access Controller
  parent: Add-ons
  order: 2
toc: true
---

# Pulp Access Controller

# Overview
The Pulp Access Controller is a Kubernetes operator that makes working with Red Hat Pulp services less painful. Instead of manually creating secrets and configuring authentication for every team or project, you just create a `PulpAccessRequest` CR and the controller handles the rest.

It's built on [Kopf](https://github.com/nolar/kopf) (a Python framework for Kubernetes operators) and watches for `PulpAccessRequest` resources. When it sees one, it:
- Creates Kubernetes secrets with pre-configured `pulp-cli` settings
- Sets up mTLS authentication using your certificates
- Automatically creates Pulp domains (named `konflux-<namespace>`)
- Optionally wires up Quay.io as an OCI storage backend

Think of it as the glue between your namespace and Pulp - you provide the credentials, it does the boring setup work.

# Dependencies

The controller needs:
- Access to a Red Hat Pulp instance with API endpoints
- Valid TLS certificates for mTLS authentication (for domain creation and API access)
- Optionally, Quay.io credentials if you want OCI backend storage

It doesn't depend on other Konflux services, but teams typically use it alongside the Image Controller when they need to push container images to Pulp-backed registries.

## Controllers

There's just one controller that does everything:
- **PulpAccessRequest controller**
  - Watches for PulpAccessRequest CRs
  - Validates the credentials secret you reference
  - Creates the `pulp-access` secret with CLI config and certificates
  - Creates Pulp domains via the mTLS API
  - Optionally creates ImageRepository resources for Quay backend integration
  - Updates status to let you know what happened

# Interface

## PulpAccessRequest CR

This is how you tell the controller "hey, I need access to Pulp."

### Basic setup

First, create a secret with your TLS certificate and key:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-pulp-creds
  namespace: my-team
type: Opaque
stringData:
  cert: |
    -----BEGIN CERTIFICATE-----
    MIIDXTCCAkWgAwIBAgIJAKJ...
    -----END CERTIFICATE-----
  key: |
    -----BEGIN PRIVATE KEY-----
    MIIEvgIBADANBgkqhkiG9w0BA...
    -----END PRIVATE KEY-----
```

Then create a PulpAccessRequest that points to it:

```yaml
apiVersion: pulp.konflux-ci.dev/v1alpha1
kind: PulpAccessRequest
metadata:
  name: my-pulp-access
  namespace: my-team
spec:
  credentialsSecretName: my-pulp-creds
```

That's it. The controller will:
1. Read your credentials from `my-pulp-creds`
2. Create a domain called `konflux-my-team` in Pulp
3. Generate a `pulp-access` secret with everything configured

### With Quay backend

If you want Pulp to use Quay.io as the OCI storage backend (useful for container image workflows), add one line:

```yaml
apiVersion: pulp.konflux-ci.dev/v1alpha1
kind: PulpAccessRequest
metadata:
  name: pulp-with-quay
  namespace: my-team
spec:
  credentialsSecretName: my-pulp-creds
  use_quay_backend: true
```

The controller will create an ImageRepository resource and configure the Pulp domain to use Quay for storage.

### Alternative certificate naming

The controller is flexible about certificate naming. You can use either:
- `cert` and `key` (as shown above)
- `tls.crt` and `tls.key` (if you're copying from TLS secrets)

Both work fine.

## Generated Secret

The controller creates a secret called `pulp-access` in your namespace with these keys:

| Key | What's in it | Always there? |
|-----|-------------|---------------|
| `cli.toml` | Pre-configured pulp-cli config with mTLS settings | Yes |
| `tls.crt` | Your TLS certificate (base64 encoded) | If you provided a custom cert |
| `tls.key` | Your TLS private key (base64 encoded) | If you provided a custom key |
| `domain` | The Pulp domain name (`konflux-<namespace>`) | Yes |

You can mount this secret in your pods and use `pulp-cli` right away - no extra configuration needed.

## Status

After you create a PulpAccessRequest, check the status to see if everything worked:

```bash
kubectl get pulpaccessrequest my-pulp-access -o yaml
```

### What's in the status

The controller updates these fields:

| Field | Type | What it means |
|-------|------|---------------|
| `secretName` | string | Always `pulp-access` |
| `domain` | string | The domain it created (e.g., `konflux-my-team`) |
| `domainCreated` | boolean | Did the domain get created in Pulp? |
| `imageRepositoryCreated` | boolean | Was the ImageRepository created? (only when `use_quay_backend: true`) |
| `quayBackendConfigured` | boolean | Is Quay wired up as storage? (only when `use_quay_backend: true`) |
| `conditions` | array | Detailed status with reasons for success/failure |

### Status conditions

The `Ready` condition tells you what happened:

| Status | Reason | What it means |
|--------|--------|---------------|
| `True` | `SecretCreated` | Everything worked, secret is ready |
| `True` | `SecretExists` | Secret was already there (probably from a previous request) |
| `False` | `MissingCredentials` | You forgot to set `credentialsSecretName` |
| `False` | `SecretNotFound` | The credentials secret doesn't exist |
| `False` | `SecretReadError` | Controller couldn't read your credentials secret |
| `False` | `ApiError` | Kubernetes API error (permissions issue?) |
| `False` | `UnexpectedError` | Something went wrong (check controller logs) |

### Example status

When everything works, you'll see something like this:

```yaml
status:
  conditions:
  - lastTransitionTime: "2025-11-24T10:30:00Z"
    message: Successfully created secret 'pulp-access'
    reason: SecretCreated
    status: "True"
    type: Ready
  domain: konflux-my-team
  domainCreated: true
  imageRepositoryCreated: true
  quayBackendConfigured: true
  secretName: pulp-access
```

### Quick check

Want to know if it's ready without scrolling through YAML?

```bash
kubectl get pulpaccessrequest my-pulp-access -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

If it prints `True`, you're good to go.

## Common issues

**"Secret not found" error**: Make sure your credentials secret exists in the same namespace as the PulpAccessRequest.

**Domain creation fails**: Check that your TLS certificate is valid and has the right permissions for the Pulp API.

**Can't access the generated secret**: The secret is created in the same namespace as your PulpAccessRequest. If you're looking in a different namespace, you won't find it.

**Status shows Ready=False**: Check the `reason` and `message` in the conditions. The controller tries to be helpful with error messages.
