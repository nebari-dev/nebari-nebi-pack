---
title: Getting started
description: Install the Nebari Nebi Pack Helm chart on a Nebari cluster and open Nebi for the first time.
---

## Prerequisites

- A Kubernetes cluster running [Nebari](https://www.nebari.dev/) with the
  [nebari-operator](https://github.com/nebari-dev/nebari-operator) installed — it provides the
  `NebariApp` CRD (`reconcilers.nebari.dev/v1`) the chart emits, and turns it into routing, TLS,
  and Keycloak clients.
- A Keycloak realm the cluster's users log in to (`nebari` by default).
- Helm 3.8+ (OCI registry support).
- One DNS name pointing at the cluster gateway, for the Nebi UI.
- A default StorageClass, or a name to pass for `persistence.storageClassName` and
  `postgres.storage.storageClassName`. The environments volume is `ReadWriteOnce`.

## Install

The chart is published to the central Nebari Helm repository:

```bash
helm repo add nebari https://raw.githubusercontent.com/nebari-dev/helm-repository/gh-pages/
helm repo update
```

It is also available as an OCI artifact, which needs no `helm repo add`:

```bash
helm install nebi oci://quay.io/nebari/charts/nebari-nebi-pack --version <version>
```

On a stock Nebari cluster a hostname is the only value you need:

```yaml
# nebi-values.yaml
nebariapp:
  hostname: nebi.example.com
```

```bash
helm install nebi nebari/nebari-nebi-pack \
  --namespace nebi --create-namespace \
  -f nebi-values.yaml
```

Everything else is derived. With `nebariapp.hostname: nebi.example.com` the chart resolves:

| Setting | Derived value |
| --- | --- |
| Keycloak hostname | `keycloak.example.com` — `keycloak.` plus the base domain of the hostname |
| OIDC issuer | `https://keycloak.example.com/realms/nebari` |
| OIDC discovery | `http://keycloak-keycloakx-http.keycloak.svc.cluster.local:8080/realms/nebari` |
| OIDC client ID | `nebi-nebi-nebari-nebi-pack` — `<namespace>-<fullname>` |
| Client secret | from the `nebi-nebari-nebi-pack-oidc-client` Secret the operator writes |

If your cluster does not follow those conventions, override the pieces that differ — see
[Helm values](/helm-values/).

## Secrets are generated for you

Nebi needs a JWT signing secret and, when the embedded PostgreSQL is enabled, a database
password. You do not supply either. The chart ships a `secret-init` Job that creates them on
first install and skips if the Secret already exists, so re-installs and upgrades keep the same
values.

The Job is annotated as an ArgoCD `PreSync` hook. That is deliberate: ArgoCD renders Helm
templates client-side, so `lookup()` always returns nil and `randAlphaNum` would mint new
credentials on every sync. Generating them in a Job keeps the Secret outside the Helm-managed
resource set, where ArgoCD will not diff or overwrite it.

## Verify

```bash
kubectl -n nebi get pods
kubectl -n nebi get nebariapp
curl -fsS https://nebi.example.com/api/v1/health
```

The `NebariApp` is what tells the platform this service exists. Once the operator reconciles it,
Nebi is routed at your hostname, has a certificate, has a Keycloak client, and appears as a tile
on the Nebari landing page under the **Platform** category.

Browse to `https://nebi.example.com` and you will be sent through Keycloak. Members of the
`admin` or `nebi-admin` groups get Nebi's admin role; change that with `auth.proxyAdminGroups`.

## Common adjustments

**Use an external database.** Turn off the embedded PostgreSQL and supply your own DSN:

```yaml
postgres:
  enabled: false
```

With `postgres.enabled: false` the chart stops setting `NEBI_DATABASE_DSN`, so configure Nebi's
database connection yourself.

**Size the environments volume.** Built environments are large; 20Gi is the default:

```yaml
persistence:
  size: 100Gi
  storageClassName: fast-ssd
```

**Deploy outside Nebari.** Without the operator there is no `NebariApp` to emit:

```yaml
nebariapp:
  enabled: false
```

This also disables the OIDC environment variables, since the client the operator would have
provisioned does not exist. You are then responsible for routing and authentication.

**Trust a corporate CA.** On clusters with a TLS-intercepting egress proxy, pixi/rattler cannot
reach conda-forge or PyPI until its CA is trusted:

```yaml
orgCABundle:
  configMapName: org-ca-bundle
```

See [Helm values](/helm-values/#tls-trust) for the ConfigMap's required shape.

## Upgrading

```bash
helm upgrade nebi nebari/nebari-nebi-pack -f nebi-values.yaml
```

The Deployment uses the `Recreate` strategy rather than a rolling update. The environments volume
is `ReadWriteOnce`, so a new pod cannot attach it while the old one still holds it — a rolling
update would deadlock on a Multi-Attach error. Expect a short gap in availability during upgrades.
