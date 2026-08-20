# nebari-nebi-pack
Nebi deployment pack for Nebari

## Install from Helm Repository

The chart is published to the central Nebari Helm repository:

```bash
helm repo add nebari https://raw.githubusercontent.com/nebari-dev/helm-repository/gh-pages/
helm repo update
helm install nebi nebari/nebari-nebi-pack
```

It is also available as an OCI artifact on quay.io (no `helm repo add` needed):

```bash
helm install nebi oci://quay.io/nebari/charts/nebari-nebi-pack --version <version>
```

> **Cutover note:** releases from `0.1.0-alpha.7` onward publish to the central
> repository above. The previous per-repo index at
> `https://nebari-dev.github.io/nebari-nebi-pack` is frozen; releases packaged
> there before the cutover remain installable from it, but new versions land
> only in the central repository.

## Documentation

The docs site lives in `docs/` and is built with [Astro](https://astro.build) + [Starlight](https://starlight.astro.build). It deploys automatically to [packs.nebari.dev/nebi-pack/](https://packs.nebari.dev/nebi-pack/) on every merge to `main`. Pull requests get a preview URL posted as a PR comment.

### Running locally

```bash
make docs           # start dev server at http://localhost:4321
make docs-build     # build to docs/dist/
make docs-preview   # serve the production build locally
make docs-test      # run unit tests
```

### Adding or editing content

Content lives in `docs/src/content/docs/`. Each `.md` or `.mdx` file becomes a page. The sidebar is configured in `docs/astro.config.mjs` under `starlight.sidebar`.

### Updating the shared theme

Nebari branding (colors, fonts, logo, favicon, footer) comes from the [`@nebari/starlight`](https://github.com/nebari-dev/starlight) plugin, not vendored files. To pick up a theme update, bump the version in `docs/package.json`:

```bash
cd docs && nix-shell --run "npm install @nebari/starlight@latest"
```
