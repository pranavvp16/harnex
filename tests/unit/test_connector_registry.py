from __future__ import annotations

from harnex_api.connectors.registry import register_builtins, registry


def test_builtins_register_and_have_metadata():
    register_builtins()
    keys = {c.key for c in registry.all()}
    assert {"generic", "github", "jenkins"}.issubset(keys)
    github = registry.get("github")
    assert github.default_base_url == "https://api.github.com"
