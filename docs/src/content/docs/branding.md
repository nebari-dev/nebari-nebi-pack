---
title: Branding
description: Rebrand the Nebi web UI — title, logo, favicon, and theme tokens — at deploy time, with no image rebuild.
---

The Nebi UI reads its branding from a `config.json` that the SPA fetches **before React mounts**.
The chart renders that file from Helm values, so the title, logo, favicon, and color tokens are
deploy-time settings rather than build-time ones — no image rebuild, no fork of the frontend.

Every field is optional and every field falls back independently. With the whole `branding` block
left at its defaults nothing is rendered at all: no ConfigMap, no volume, no environment variable,
and `helm template` output is byte-identical to chart versions from before the feature existed.

## Quick start

```yaml
# nebi-values.yaml
nebariapp:
  hostname: nebi.example.com

branding:
  title: "Acme Environments"
  logoUrl: "data:image/svg+xml;base64,PHN2ZyB4bWxucz0..."
  faviconUrl: "data:image/x-icon;base64,AAABAAEAEBAA..."
  theme:
    light:
      primary: "#0f62fe"
      primaryHover: "#0043ce"
    dark:
      primary: "#78a9ff"
```

```bash
helm upgrade --install nebi nebari/nebari-nebi-pack \
  --namespace nebi -f nebi-values.yaml
```

The pods roll on apply — see [Changes roll the pods](#changes-roll-the-pods).

## Values

| Value | Purpose |
| --- | --- |
| `branding.title` | Browser tab title. Empty uses `Nebi - Environment Management`. |
| `branding.logoUrl` | Logo in the UI header. Empty uses the built-in Nebi logo, which already switches between light and dark variants. |
| `branding.logoUrlDark` | Optional dark-mode logo. Empty falls back to `logoUrl`, then to the built-in dark logo. Light mode always uses `logoUrl`. |
| `branding.faviconUrl` | Favicon. Applied to every existing `icon` / `shortcut icon` / `apple-touch-icon` link, or added if the page has none. Empty uses the built-in favicon. |
| `branding.theme.light` | CSS custom-property overrides written to `:root`. |
| `branding.theme.dark` | CSS custom-property overrides written to `.dark`. |

## Logo and favicon URLs

Asset URLs must be **same-origin**. The frontend accepts:

- a root-relative path — `/assets/acme-logo.svg`
- an absolute `http(s)` URL whose origin matches the page's own
- a base64 `data:` URI of an allowed image type — `image/png`, `image/jpeg`, `image/svg+xml`,
  `image/webp`, `image/gif`, `image/x-icon`, `image/vnd.microsoft.icon`

and rejects everything else, silently falling back to the built-in asset. External CDN URLs,
protocol-relative `//host/logo.svg`, `javascript:`, non-base64 `data:` URIs, and
`data:text/html` are all rejected.

In practice a **base64 `data:` URI is the option that works without extra infrastructure**. Nebi
serves static assets only from the frontend embedded in its image, so a root-relative path like
`/assets/acme-logo.svg` resolves only if something on the Nebi hostname actually serves it — it is
not a path you can drop a file into. Encode the asset instead:

```bash
# Prints a data: URI ready to paste into values (macOS/Linux)
printf 'data:image/svg+xml;base64,%s\n' "$(base64 < acme-logo.svg | tr -d '\n')"
```

Keep an eye on size — the URI travels in the ConfigMap, and a ConfigMap caps out at ~1 MiB. An
optimized SVG or a small PNG is well within that; a multi-megabyte raster is not.

Root-relative URLs are resolved against the app's base path, so they keep working if Nebi is
served under a sub-path.

## Theme tokens

Token names are camelCase and are converted to CSS custom properties at runtime:

| Token key | CSS variable |
| --- | --- |
| `primary` | `--color-primary` |
| `primaryHover` | `--color-primary-hover` |
| `radius` | `--radius` |
| `--my-own-var` | `--my-own-var` — a key already starting with `--` is passed through verbatim |

`light` tokens are emitted into a `:root` block and `dark` tokens into a `.dark` block, in a single
`<style>` element appended to the head before the app mounts.

The overridable tokens come from the frontend's `index.css`:

`background`, `foreground`, `card`, `cardForeground`, `popover`, `popoverForeground`, `primary`,
`primaryForeground`, `primaryHover`, `navHover`, `secondary`, `secondaryForeground`, `muted`,
`mutedForeground`, `accent`, `accentForeground`, `destructive`, `destructiveForeground`, `border`,
`input`, `ring`, `radius`.

### Value restrictions

Values are sanitized in the browser. A value is **dropped** if it contains any of `;` `<` `>` `{`
`}` `"` `'` `\` or `url(`, `expression(`, or `javascript:`. Any CSS color notation without those
characters works — `#0f62fe`, `rgb(15 98 254)`, `hsl(217 98% 53%)`, `oklch(0.55 0.22 260)`.

Note that the quote restriction means font-family stacks containing quoted names cannot be set
this way.

Numbers are safe to write unquoted in values — the chart coerces token values to strings, because
the frontend ignores non-string values and an unquoted `radius: 0.5` would otherwise be dropped.

## How it works

When **any** branding field is non-empty, the chart renders three extra things:

1. A ConfigMap named `<fullname>-branding` holding a `config.json` with only the fields you set.
2. A read-only volume mounting that ConfigMap at `/etc/nebi/branding` — mounted as a **directory**,
   not with `subPath`, so kubelet keeps the file up to date in place.
3. `NEBI_BRANDING_CONFIG_PATH=/etc/nebi/branding/config.json` on the Nebi container.

Nebi serves that file at `/public/config.json` in place of the copy baked into the image, and the
SPA fetches it at startup, applying the title, favicon, logo, and theme tokens before it mounts. If
the fetch or parse fails, the app logs a warning and renders with its built-in defaults.

The rendered `config.json` for the quick-start values above:

```json
{
  "branding": {
    "faviconUrl": "data:image/x-icon;base64,AAABAAEAEBAA...",
    "logoUrl": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0...",
    "theme": {
      "dark": {
        "primary": "#78a9ff"
      },
      "light": {
        "primary": "#0f62fe",
        "primaryHover": "#0043ce"
      }
    },
    "title": "Acme Environments"
  }
}
```

Only the fields you set are emitted. An unset field is omitted rather than written as `""`, and a
color scheme with no tokens is dropped entirely — so each missing field falls back to the
frontend's built-in default.

### Changes roll the pods

The Deployment carries a `checksum/config` annotation over the branding ConfigMap. Editing branding
values therefore changes the pod template and triggers a rollout, instead of appearing to apply
cleanly while the running pod keeps serving the old file.

Note that `strategy.type` is `Recreate` — the environments volume is `ReadWriteOnce`, so the old
pod terminates before the new one starts and there is a brief gap in availability.

## Image requirements

Runtime branding needs a Nebi image that supports it:

| Feature | Requires |
| --- | --- |
| `title`, `logoUrl`, `faviconUrl`, `theme` | Nebi with runtime theming support — the tag pinned in `values.yaml` has it. |
| `logoUrlDark` | A newer Nebi than the pinned tag ([nebi#516](https://github.com/nebari-dev/nebi/pull/516)). On an older image the key is ignored and dark mode keeps using `logoUrl`, so setting it early is harmless but has no effect until you bump `image.tag`. |

## Verifying a deploy

```bash
# The file the chart rendered
kubectl get configmap nebi-nebari-nebi-pack-branding -n nebi \
  -o jsonpath='{.data.config\.json}'

# The file the pod is actually serving
kubectl exec deploy/nebi-nebari-nebi-pack -n nebi -- cat /etc/nebi/branding/config.json

# What the browser fetches
curl -s https://nebi.example.com/public/config.json
```

If the UI still looks unbranded, check that the pod restarted after your last `helm upgrade`, then
open the browser console — a rejected logo URL or dropped theme value is a validation failure in
the SPA, not a chart problem.

## Testing chart changes

The branding render path has its own test suite, since branding is off by default and the standard
`helm template` smoke checks never exercise it:

```bash
make test        # or: uv run pytest tests/test_branding.py
```

It asserts the default render is unchanged, that any single field switches branding on, and that
the `config.json` comes out in the shape the SPA expects.
