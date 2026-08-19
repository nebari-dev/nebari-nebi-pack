"""Runtime branding (values.yaml `branding`) render tests.

Branding is off by default, so the plain `helm lint` / `helm template` smoke
checks never exercise the ConfigMap, volume, env var or checksum path. These
tests render it explicitly and assert the config.json the SPA fetches
(frontend/src/lib/brandingConfig.ts) comes out in the shape it expects.
"""

import pytest

MOUNT_PATH = "/etc/nebi/branding"
CONFIG_PATH = f"{MOUNT_PATH}/config.json"
VOLUME = "branding-config"

FULL_BRANDING = {
    "branding.title": "Acme Environments",
    "branding.logoUrl": "/assets/acme-logo.svg",
    "branding.logoUrlDark": "/assets/acme-logo-dark.svg",
    "branding.faviconUrl": "/assets/acme-favicon.ico",
    "branding.theme.light.primary": "#0f62fe",
    "branding.theme.light.primaryHover": "#0043ce",
    "branding.theme.dark.primary": "#78a9ff",
}


class TestDisabledByDefault:
    """An unset branding block must not change the rendered output at all."""

    def test_no_branding_configmap(self, render):
        assert render().find("ConfigMap", name_suffix="-branding") == []

    def test_branding_is_absent_from_the_whole_render(self, render):
        assert "branding" not in render().raw

    def test_no_config_path_env_var(self, render):
        assert render().env("NEBI_BRANDING_CONFIG_PATH") is None

    def test_no_volume_or_mount(self, render):
        manifests = render()
        assert manifests.volume(VOLUME) is None
        assert manifests.volume_mount(VOLUME) is None

    def test_no_checksum_annotation(self, render):
        annotations = render().pod_spec["metadata"].get("annotations", {})
        assert "checksum/config" not in annotations


class TestConfigJson:
    """The document mounted into the pod."""

    def test_all_fields_round_trip(self, render):
        branding = render(FULL_BRANDING).branding_config["branding"]
        assert branding == {
            "title": "Acme Environments",
            "logoUrl": "/assets/acme-logo.svg",
            "logoUrlDark": "/assets/acme-logo-dark.svg",
            "faviconUrl": "/assets/acme-favicon.ico",
            "theme": {
                "light": {"primary": "#0f62fe", "primaryHover": "#0043ce"},
                "dark": {"primary": "#78a9ff"},
            },
        }

    def test_unset_fields_are_omitted_not_emitted_empty(self, render):
        """The frontend falls back per *missing* key, so empty values must not ship."""
        branding = render({"branding.title": "Acme"}).branding_config["branding"]
        assert branding == {"title": "Acme"}

    def test_theme_scheme_with_no_tokens_is_omitted(self, render):
        branding = render(
            {"branding.theme.light.primary": "#0f62fe"}
        ).branding_config["branding"]
        assert branding["theme"] == {"light": {"primary": "#0f62fe"}}

    def test_numeric_token_values_are_coerced_to_strings(self, render):
        """An unquoted YAML number would otherwise be dropped by the frontend."""
        tokens = render({"branding.theme.light.radius": 0.25}).branding_config[
            "branding"
        ]["theme"]["light"]
        assert tokens == {"radius": "0.25"}

    def test_values_needing_json_escaping_stay_parseable(self, render):
        """config.json is built with toPrettyJson, not hand-written JSON."""
        title = 'Acme "Data" \\ Platform'
        branding = render({"branding.title": title}).branding_config["branding"]
        assert branding["title"] == title


@pytest.mark.parametrize(
    "field",
    [
        "branding.title",
        "branding.logoUrl",
        # A dark-only logo is real branding to the SPA, so the chart must treat
        # it as real branding too.
        "branding.logoUrlDark",
        "branding.faviconUrl",
        "branding.theme.light.primary",
        "branding.theme.dark.primary",
    ],
)
def test_any_single_field_enables_branding(render, field):
    manifests = render({field: "x"})
    assert manifests.find("ConfigMap", name_suffix="-branding") != []
    assert manifests.env("NEBI_BRANDING_CONFIG_PATH") == CONFIG_PATH


class TestPodWiring:
    """How the ConfigMap reaches the container."""

    def test_env_var_points_at_the_mounted_file(self, render):
        assert render(FULL_BRANDING).env("NEBI_BRANDING_CONFIG_PATH") == CONFIG_PATH

    def test_volume_references_the_branding_configmap(self, render):
        manifests = render(FULL_BRANDING)
        cm_name = manifests.get("ConfigMap", name_suffix="-branding")["metadata"]["name"]
        assert manifests.volume(VOLUME)["configMap"]["name"] == cm_name

    def test_mounted_read_only_at_the_expected_path(self, render):
        mount = render(FULL_BRANDING).volume_mount(VOLUME)
        assert mount["mountPath"] == MOUNT_PATH
        assert mount["readOnly"] is True

    def test_mounted_as_a_directory(self, render):
        """A subPath mount is a one-time copy kubelet never refreshes."""
        assert "subPath" not in render(FULL_BRANDING).volume_mount(VOLUME)

    def test_pod_carries_a_checksum_annotation(self, render):
        annotations = render(FULL_BRANDING).pod_spec["metadata"]["annotations"]
        assert "checksum/config" in annotations

    def test_checksum_changes_when_branding_changes(self, render):
        """Otherwise a branding edit is an apparently no-op sync, not a rollout."""

        def checksum(values):
            return render(values).pod_spec["metadata"]["annotations"]["checksum/config"]

        assert checksum({"branding.title": "Acme"}) != checksum(
            {"branding.title": "Globex"}
        )

    def test_persistence_mount_survives_alongside_branding(self, render):
        """Branding shares the volumeMounts/volumes guards with the other mounts."""
        manifests = render(FULL_BRANDING)
        assert manifests.volume_mount("environments") is not None
        assert manifests.volume("environments") is not None
