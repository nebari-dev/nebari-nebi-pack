"""Helpers for rendering this chart with `helm template` and asserting on the result.

These tests are pure render tests: no cluster, no network. They call the real
`helm` binary so the assertions cover the templates as Helm actually evaluates
them (including `include`, `toPrettyJson` and `sha256sum`), which is the part a
YAML-only lint pass cannot check.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

CHART_DIR = Path(__file__).resolve().parent.parent
RELEASE = "test"

# nebariapp.hostname is required whenever the NebariApp is enabled (the default),
# so every render supplies it unless a test overrides it.
DEFAULT_VALUES = {"nebariapp.hostname": "nebi.example.com"}


def _escape(value):
    """Escape a --set value: helm treats backslash as an escape and splits on commas."""
    return str(value).replace("\\", "\\\\").replace(",", "\\,")


class Manifests:
    """The documents rendered by one `helm template` invocation."""

    def __init__(self, raw):
        self.raw = raw
        self.docs = [doc for doc in yaml.safe_load_all(raw) if doc]

    def find(self, kind, name=None, name_suffix=None):
        """Every document of `kind`, optionally filtered by exact or suffix name."""
        out = []
        for doc in self.docs:
            if doc.get("kind") != kind:
                continue
            doc_name = doc.get("metadata", {}).get("name", "")
            if name is not None and doc_name != name:
                continue
            if name_suffix is not None and not doc_name.endswith(name_suffix):
                continue
            out.append(doc)
        return out

    def get(self, kind, name=None, name_suffix=None):
        """The single document matching, failing the test if it is not unique."""
        found = self.find(kind, name=name, name_suffix=name_suffix)
        assert len(found) == 1, (
            f"expected exactly 1 {kind} matching "
            f"name={name!r} name_suffix={name_suffix!r}, got {len(found)}: "
            f"{[d.get('metadata', {}).get('name') for d in found]}"
        )
        return found[0]

    @property
    def pod_spec(self):
        """The nebi Deployment's pod template."""
        return self.get("Deployment", name=f"{RELEASE}-nebari-nebi-pack")["spec"]["template"]

    @property
    def container(self):
        """The nebi container."""
        return self.pod_spec["spec"]["containers"][0]

    def env(self, name):
        """The value of an env var on the nebi container, or None if unset."""
        for var in self.container.get("env", []):
            if var["name"] == name:
                return var.get("value")
        return None

    def volume_mount(self, name):
        """The nebi container's volumeMount by name, or None if absent."""
        for mount in self.container.get("volumeMounts", []):
            if mount["name"] == name:
                return mount
        return None

    def volume(self, name):
        """The pod's volume by name, or None if absent."""
        for volume in self.pod_spec["spec"].get("volumes", []):
            if volume["name"] == name:
                return volume
        return None

    @property
    def branding_config(self):
        """The branding ConfigMap's config.json, parsed."""
        cm = self.get("ConfigMap", name_suffix="-branding")
        return json.loads(cm["data"]["config.json"])


@pytest.fixture(scope="session")
def helm():
    """Path to the helm binary, skipping the suite when it is not installed."""
    path = shutil.which("helm")
    if path is None:
        pytest.skip("helm is not installed")
    return path


@pytest.fixture(scope="session")
def render(helm):
    """Render the chart. `values` is a dict of --set paths to values."""

    def _render(values=None, defaults=True):
        merged = dict(DEFAULT_VALUES) if defaults else {}
        merged.update(values or {})
        args = [helm, "template", RELEASE, str(CHART_DIR)]
        for key, value in merged.items():
            args += ["--set", f"{key}={_escape(value)}"]
        result = subprocess.run(args, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"helm template failed ({result.returncode}):\n{result.stderr}"
        )
        return Manifests(result.stdout)

    return _render
