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

## Branding

The Nebi UI can be rebranded at deploy time — no image rebuild:

```yaml
branding:
  title: "Acme Environments"
  logoUrl: "/assets/acme-logo.svg"     # same-origin path or base64 data: URI
  logoUrlDark: "/assets/acme-logo-dark.svg"  # optional dark-mode variant
  faviconUrl: "/assets/acme-favicon.ico"
  theme:
    light:
      primary: "#0f62fe"
      primaryHover: "#0043ce"
    dark:
      primary: "#78a9ff"
```

When any field is set, the chart renders a `<release>-branding` ConfigMap
containing `config.json`, mounts it at `/etc/nebi/branding`, and sets
`NEBI_BRANDING_CONFIG_PATH`. Nebi serves that file at `/public/config.json` and
the UI applies it before it mounts. The Deployment carries a `checksum/config`
annotation over the ConfigMap, so editing branding rolls the pods instead of
appearing to sync with no visible effect.

`logoUrlDark` is optional: dark mode falls back to `logoUrl` when it is unset,
so a single-logo install behaves exactly as before.

With every field empty (the default) nothing is rendered and `helm template`
output is unchanged. See the `branding` block in `values.yaml` for the full list
of overridable theme tokens and the value restrictions.
