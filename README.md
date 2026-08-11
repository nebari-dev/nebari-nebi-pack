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

## Network Policy Notes

The chart enables `networkPolicy.enabled` by default. On upgrade, this may block
deployments that rely on private egress, such as private package mirrors,
externally managed databases, or Keycloak behind a private ingress load balancer.
Add explicit `networkPolicy.app.extraEgress` rules for those destinations, or
temporarily set `networkPolicy.enabled=false` while migrating.

By default, in-cluster HTTP egress is limited to the `keycloak` namespace on
port `8080`, matching the default `keycloak.serviceHost`. If
`keycloak.hostname` is set and resolves to a private ingress address, that
address falls inside the default blocked private CIDR ranges; add an
`extraEgress` entry for that address or prefer the in-cluster discovery URL.
