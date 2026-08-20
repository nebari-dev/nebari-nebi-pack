---
title: Local development
description: Run the chart on a local k3d cluster with Tilt, and work on the docs site.
---

## Prerequisites

- [ctlptl](https://github.com/tilt-dev/ctlptl) — creates the local cluster and registry
- [Tilt](https://tilt.dev/) — the deploy loop
- [k3d](https://k3d.io/) and Docker — the cluster itself
- Helm 3.8+

## Bring the cluster up

Two commands cover the whole lifecycle:

```bash
make up     # create the cluster (if needed) and start Tilt
make down   # stop Tilt and delete the cluster
```

`make up` runs `ctlptl apply`, which is idempotent — it creates the k3d cluster
`k3d-nebari-dev` and a local registry on port `5005` only if they do not already exist — then
starts `tilt up`. If Tilt is already running it says so instead of starting a second copy.

Tilt's UI is at **http://localhost:10350**, and Nebi is port-forwarded to
**http://localhost:8460**.

## What the local deploy changes

The Tiltfile installs this same chart with three overrides, because a laptop cluster is not a
Nebari cluster:

```python
'nebariapp.enabled=false',                     # no nebari-operator here, so no NebariApp
'persistence.storageClassName=local-path',     # k3d's built-in StorageClass
'postgres.storage.storageClassName=local-path',
```

`nebariapp.enabled=false` is the consequential one. With no `NebariApp` there is no gateway, no
Keycloak client, and no OIDC — the chart drops the `NEBI_AUTH_OIDC_*` environment variables
entirely. Locally you are talking to Nebi with authentication effectively out of the picture, so
**the auth path is the one thing this loop cannot exercise.** Test that on a real Nebari cluster.

The Tiltfile also pins `allow_k8s_contexts('k3d-nebari-dev')` as a guardrail, so a stray
`kubectl config use-context` cannot point Tilt at a production cluster. The apply timeout is
raised to 600s because first-run image pulls are slow.

## Rendering the chart without a cluster

For template-level work you do not need Tilt at all. `helm template` is much faster and is how
the derived values in these docs were checked:

```bash
# The chart requires a hostname whenever nebariapp is enabled
helm template nebi . --set nebariapp.hostname=nebi.example.com

# Confirm what the OIDC values derive to for a given namespace and release
helm template nebi . -n nebi --set nebariapp.hostname=nebi.example.com \
  | grep -A1 NEBI_AUTH_OIDC

# Lint before pushing
helm lint .
```

Rendering with `nebariapp.enabled=false` shows you what the local Tilt deploy actually applies.

## The docs site

The site is [Astro](https://astro.build) + [Starlight](https://starlight.astro.build), living in
`docs/`, with Makefile targets for each step:

```bash
make docs              # dev server with hot reload at http://localhost:4321
make docs-install      # npm ci from the lockfile
make docs-build        # build to docs/dist/
make docs-preview      # serve the production build
make docs-test         # vitest unit tests
make docs-check-links  # build, then verify every internal link resolves
```

### Adding a page

Add a `.md` or `.mdx` file under `docs/src/content/docs/` — each file becomes a page — then add it
to the sidebar in `docs/astro.config.mjs` under `starlight.sidebar`.

### Site and base URLs

The build reads two environment variables, set by `.github/workflows/docs.yml`:

| Deploy | `SITE` | `BASE` |
| --- | --- | --- |
| `main` | `https://packs.nebari.dev` | `/nebi-pack/` |
| PR preview | `https://<branch>.nebi-pack.pages.dev` | `/` |
| Local (defaults) | `https://packs.nebari.dev` | `/` |

`BASE` is why the `remark-base-links` plugin exists: it rewrites internal links at build time so
the same Markdown works whether the site is served from a subpath in production or from the root
in a preview. Write links as `/helm-values/` and let the plugin prefix them.

To check the production layout locally, build the way CI does:

```bash
cd docs && SITE=https://packs.nebari.dev BASE=/nebi-pack/ npm run build && npm run preview
```

### Branding

Nebari branding — colors, fonts, logo, favicon, footer, GitHub link — comes from the
[`@nebari/starlight`](https://github.com/nebari-dev/starlight) plugin rather than vendored files.
To pick up a theme update, bump the dependency:

```bash
cd docs && npm install @nebari/starlight@latest
```

## Deploys

Docs deploy to Cloudflare Pages from `.github/workflows/docs.yml`: pushes to `main` publish to
[packs.nebari.dev/nebi-pack/](https://packs.nebari.dev/nebi-pack/), and pull requests get a
preview URL posted as a PR comment. Preview deployments are deleted when the PR closes, by
`docs-preview-cleanup.yml`.

Deploys are skipped for pull requests from forks, since those cannot read the Cloudflare
credentials.
