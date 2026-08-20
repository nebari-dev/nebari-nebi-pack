---
title: Helm values
description: Every value the nebari-nebi-pack chart accepts, and what each one derives when left empty.
---

`nebari-nebi-pack` is a single chart — no subcharts. To see the shipped defaults for the version
you are installing:

```bash
helm show values oci://quay.io/nebari/charts/nebari-nebi-pack --version <version>
```

Many values default to `""` and are *derived* rather than empty. The derivations all assume a
stock Nebari deployment, so overriding them is only necessary when your cluster differs.

## Required values

| Value | Purpose |
| --- | --- |
| `nebariapp.hostname` | Public hostname for Nebi. Required whenever `nebariapp.enabled` is `true` (the default) — the chart refuses to render without it. Also the base for the derived Keycloak hostname and the OIDC redirect URL. |

## Nebari integration

The `nebariapp.*` tree becomes a `NebariApp` resource (`reconcilers.nebari.dev/v1`) that the
nebari-operator turns into routing, TLS, Keycloak clients, and a landing-page tile.

| Value | Default | Purpose |
| --- | --- | --- |
| `nebariapp.enabled` | `true` | Set `false` to deploy outside Nebari. No `NebariApp` is rendered, and the OIDC environment variables are dropped with it — routing and auth become your responsibility. |
| `nebariapp.hostname` | — | Required. See above. |
| `nebariapp.service.name` | `""` | Service the `NebariApp` routes to. Empty derives the chart fullname. |
| `nebariapp.service.port` | `80` | Service port to route to. |
| `nebariapp.routing.routes` | `[{pathPrefix: /}]` | Paths routed to Nebi. |
| `nebariapp.routing.publicRoutes` | `/api/`, `/docs/` | Paths that **bypass the gateway OIDC filter**, so bearer-token API callers (such as the jhub-apps environment selector) reach Nebi directly. Nebi validates the token itself. |

### Auth

| Value | Default | Purpose |
| --- | --- | --- |
| `nebariapp.auth.enabled` | `true` | Whether the operator enforces authentication for this app. |
| `nebariapp.auth.provider` | `keycloak` | Identity provider. |
| `nebariapp.auth.provisionClient` | `true` | Have the operator create the Keycloak client and write its secret. |
| `nebariapp.auth.redirectURI` | `/oauth2/callback` | Must match the Envoy Gateway `SecurityPolicy` callback path. Nebi does not run its own SSO proxy — auth happens at the gateway, so this is oauth2-proxy's callback, not a Nebi route. |
| `nebariapp.auth.scopes` | `openid`, `profile`, `email`, `groups` | Scopes requested. `groups` is what makes `auth.proxyAdminGroups` work. |
| `nebariapp.auth.tokenExchange.enabled` | `true` | Let other `NebariApp` clients (for example JupyterHub) exchange a user token for a Nebi-audience token. Required by the jhub-apps environment selector and Nebi auto-auth. |

### Landing page

Controls whether and how Nebi appears on the Nebari landing page portal.

| Value | Default |
| --- | --- |
| `nebariapp.landingPage.enabled` | `true` |
| `nebariapp.landingPage.displayName` | `Nebi` |
| `nebariapp.landingPage.description` | `Manage and share Conda/Pip environments for your Nebari cluster` |
| `nebariapp.landingPage.icon` | the Nebi icon on GitHub |
| `nebariapp.landingPage.category` | `Platform` |
| `nebariapp.landingPage.priority` | `10` |
| `nebariapp.landingPage.externalUrl` | unset — defaults to the hostname |
| `nebariapp.landingPage.healthCheck.enabled` | `true` |
| `nebariapp.landingPage.healthCheck.path` | `/api/v1/health` |
| `nebariapp.landingPage.healthCheck.intervalSeconds` | `30` |
| `nebariapp.landingPage.healthCheck.timeoutSeconds` | `5` |

## Application

| Value | Default | Purpose |
| --- | --- | --- |
| `image.repository` | `quay.io/nebari/nebi` | Nebi image. |
| `image.tag` | pinned in `values.yaml` | Pinned to a specific `sha-` tag rather than tracking `appVersion`. |
| `image.pullPolicy` | `IfNotPresent` | |
| `replicaCount` | `1` | Keep at `1`. The queue is in-memory and the environments volume is `ReadWriteOnce`. |
| `strategy.type` | `Recreate` | Not a rolling update — a second pod cannot attach the `ReadWriteOnce` environments volume, so a rolling update would fail with a Multi-Attach error. |
| `server.port` | `8460` | Container port. |
| `server.mode` | `production` | Nebi server mode. |
| `log.format` | `json` | |
| `log.level` | `info` | |
| `queue.type` | `memory` | In-memory, which is why the deployment is single-pod. |
| `resources` | `{}` | Unset by default; the file shows a commented-out starting point. |

## Auth and OIDC

Nebi runs with `NEBI_AUTH_TYPE=basic` and validates the OIDC token the gateway forwards, using
the verifier configured here. These variables are only set when **both** `auth.oidc.enabled` and
`nebariapp.enabled` are true.

| Value | Default | Purpose |
| --- | --- | --- |
| `auth.proxyAdminGroups` | `admin,nebi-admin` | Keycloak groups granted Nebi's admin role. |
| `auth.oidc.enabled` | `true` | A stock Nebari install authenticates against Keycloak with no extra values. |
| `auth.oidc.issuerURL` | `""` | Derives `https://<keycloak.hostname>/realms/<keycloak.realm>`. |
| `auth.oidc.discoveryURL` | `""` | For split-horizon clusters where the public issuer is unreachable from in-cluster pods. Nebi fetches `.well-known/openid-configuration` here while still validating the token `iss` against `issuerURL`. |
| `auth.oidc.clientID` | `""` | Derives `<release namespace>-<fullname>`. |
| `auth.oidc.clientSecretName` | `""` | Derives `<fullname>-oidc-client`, the Secret the operator writes. Read from its `client-secret` key. |

### Keycloak

| Value | Default | Purpose |
| --- | --- | --- |
| `keycloak.hostname` | `""` | Public Keycloak hostname. Empty derives `keycloak.<base domain of nebariapp.hostname>`. |
| `keycloak.serviceHost` | `keycloak-keycloakx-http.keycloak.svc.cluster.local:8080` | In-cluster Keycloak service (`host:port`) used to derive `discoveryURL`. Matches the codecentric/keycloakx Service naming every Nebari deploy ships with. |
| `keycloak.realm` | `nebari` | Realm name. |

### What the derivations produce

Installing with `--namespace nebi`, release name `nebi`, and
`nebariapp.hostname: nebi.example.com` yields:

```
NEBI_AUTH_OIDC_ISSUER_URL     https://keycloak.example.com/realms/nebari
NEBI_AUTH_OIDC_DISCOVERY_URL  http://keycloak-keycloakx-http.keycloak.svc.cluster.local:8080/realms/nebari
NEBI_AUTH_OIDC_CLIENT_ID      nebi-nebi-nebari-nebi-pack
NEBI_AUTH_OIDC_REDIRECT_URL   https://nebi.example.com/api/v1/auth/oidc/callback
client secret                 Secret nebi-nebari-nebi-pack-oidc-client, key client-secret
```

`discoveryURL` has three levels of precedence: an explicit `auth.oidc.discoveryURL`; otherwise
`https://<keycloak.hostname>/realms/<realm>` if `keycloak.hostname` is set; otherwise the
in-cluster `keycloak.serviceHost` URL shown above.

## Storage

| Value | Default | Purpose |
| --- | --- | --- |
| `persistence.enabled` | `true` | PVC for built workspace environments. |
| `persistence.size` | `20Gi` | Built environments are large — size generously. |
| `persistence.accessMode` | `ReadWriteOnce` | The reason for `strategy.type: Recreate`. |
| `persistence.storageClassName` | `""` | Empty uses the cluster default. |
| `persistence.mountPath` | `/app/data/environments` | Also sets `NEBI_STORAGE_WORKSPACES_DIR`. |

## Branding

Rebrands the Nebi web UI at deploy time. When any field is set the chart renders a
`<fullname>-branding` ConfigMap, mounts it at `/etc/nebi/branding`, and sets
`NEBI_BRANDING_CONFIG_PATH`. All fields empty (the default) renders nothing.

| Value | Default | Purpose |
| --- | --- | --- |
| `branding.title` | `""` | Browser tab title. Empty uses `Nebi - Environment Management`. |
| `branding.logoUrl` | `""` | Header logo. Must be same-origin — a root-relative path or a base64 `data:` image URI. External URLs are rejected by the frontend. |
| `branding.logoUrlDark` | `""` | Optional dark-mode logo. Empty falls back to `logoUrl`. Needs a newer image than the pinned tag. |
| `branding.faviconUrl` | `""` | Favicon, same URL rules as `logoUrl`. |
| `branding.theme.light` | `{}` | camelCase CSS token overrides applied to `:root`. |
| `branding.theme.dark` | `{}` | camelCase CSS token overrides applied to `.dark`. |

Full reference — the token list, URL and value restrictions, and how to verify a deploy — in
[Branding](/branding/).

## TLS trust

| Value | Default | Purpose |
| --- | --- | --- |
| `orgCABundle.configMapName` | `""` | Mounts a ConfigMap of extra CA certificates into the pod and sets `SSL_CERT_FILE` to `/etc/ssl/certs/org-ca.crt`. |

Needed on clusters with a TLS-intercepting egress proxy whose CA is not in the image's trust
store — without it, pixi/rattler outbound HTTPS to conda-forge, PyPI, or GitHub fails with
`unknown CA`.

Both the mount and the environment variable are required: Rust's `rustls-native-certs`, which
pixi/rattler use, honors `SSL_CERT_FILE` but does not iterate `/etc/ssl/certs/`. Setting this
value does both.

The ConfigMap must already exist in the release namespace and must have a `ca-bundle.crt` key
holding one or more PEM-encoded CA certificates:

```bash
kubectl create configmap org-ca-bundle -n nebi \
  --from-file=ca-bundle.crt=/path/to/corporate-ca.pem
```

When empty, no mount is added and rendered output is byte-identical to chart versions from before
the feature existed.

## Embedded PostgreSQL

| Value | Default | Purpose |
| --- | --- | --- |
| `postgres.enabled` | `true` | Deploys a single-instance PostgreSQL StatefulSet. Set `false` to use your own database — the chart then stops setting `NEBI_DATABASE_DSN`, so you must configure the connection yourself. |
| `postgres.image.repository` | `postgres` | |
| `postgres.image.tag` | `16` | |
| `postgres.image.pullPolicy` | `IfNotPresent` | |
| `postgres.storage.size` | `10Gi` | |
| `postgres.storage.storageClassName` | `""` | Empty uses the cluster default. |
| `postgres.resources` | `{}` | |

The generated DSN points at the `<fullname>-postgres` Service with `sslmode=disable` (in-cluster
traffic) and interpolates the password from the generated Secret rather than embedding it.

## Service, service account, overrides

| Value | Default |
| --- | --- |
| `service.type` | `ClusterIP` |
| `service.port` | `80` |
| `service.targetPort` | `8460` |
| `serviceAccount.create` | `true` |
| `serviceAccount.name` | `""` — empty derives the fullname |
| `serviceAccount.annotations` | `{}` |
| `nameOverride` / `fullnameOverride` | `""` — standard Helm name overrides |

## Values you do not set

The JWT signing secret and the PostgreSQL password are generated by the chart's `secret-init`
Job on first install and reused on every upgrade. There are no values for them. See
[Getting started](/getting-started/#secrets-are-generated-for-you).
