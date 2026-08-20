---
title: Nebi Pack
description: Conda/Pip environment management for Nebari — Nebi plus an embedded PostgreSQL, wired into Keycloak SSO by one Helm chart.
---

The Nebari Nebi Pack deploys **[Nebi](https://github.com/nebari-dev/nebi)**, an environment
management platform, onto a [Nebari](https://www.nebari.dev/) cluster. Users get a browser UI for
building and sharing Conda/Pip environments behind Keycloak SSO; operators get one Helm chart that
deploys Nebi and its database and hands routing, TLS, and authentication to the
[nebari-operator](https://github.com/nebari-dev/nebari-operator).

Environments built in Nebi are available to the rest of the cluster — the
[jhub-apps](https://github.com/nebari-dev/jhub-apps) environment selector reads them over Nebi's
API using a token exchanged in Keycloak.

## What ships today

| Component | What it is | Image / chart |
| --- | --- | --- |
| Nebi | The environment management server and UI. Builds environments with [pixi](https://pixi.sh/)/rattler and stores them on a PersistentVolume. Listens on `:8460`. | `quay.io/nebari/nebi` |
| PostgreSQL | An embedded single-instance database for Nebi's metadata, deployed as a StatefulSet. Optional — point Nebi at your own with `postgres.enabled=false`. | `postgres:16` |
| This chart | Renders both, plus a `NebariApp` that gets the service routed, certificated, and put on the Nebari landing page. | `oci://quay.io/nebari/charts/nebari-nebi-pack` |

The service is exposed at a single hostname you choose:

```
https://nebi.example.com          # the Nebi UI (SSO at the gateway)
https://nebi.example.com/api/     # the REST API (bearer token, bypasses the gateway filter)
https://nebi.example.com/docs/    # the OpenAPI browser
```

## In this guide

- **[Getting started](/getting-started/)** — install the chart on a Nebari cluster and open Nebi
  for the first time
- **[Local development](/local-development/)** — run the chart on a local k3d cluster with Tilt

## Reference pages

- **[Helm values](/helm-values/)** — every value the chart accepts, and what each one derives when
  left empty
- **[Architecture & auth](/architecture/)** — how Nebi, PostgreSQL, Keycloak, and the
  nebari-operator fit together, and why authentication happens at the gateway

## Convention over configuration

A stock Nebari install needs almost nothing beyond a hostname. `nebariapp.hostname` is the only
required value: from it the chart derives the Keycloak hostname, the OIDC issuer, the client ID,
and the client secret name, all matching the client the nebari-operator provisions for this
`NebariApp`. Every derived value has an explicit override if your cluster does not follow the
convention — see [Helm values](/helm-values/).
