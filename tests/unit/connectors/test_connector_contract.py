from __future__ import annotations

import pytest

from harnex_api.connectors.base import Connector
from harnex_api.connectors.registry import register_builtins, registry
from harnex_api.db.models import AuthFlow

register_builtins()
ALL_CONNECTOR_KEYS = [c.key for c in registry.all()]


@pytest.mark.parametrize("key", ALL_CONNECTOR_KEYS)
def test_key_is_nonempty_lowercase(key: str) -> None:
    connector = registry.get(key)
    assert isinstance(connector.key, str)
    assert connector.key, f"{key}: key must not be empty"
    assert connector.key == connector.key.lower(), f"{key}: key must be lowercase"


@pytest.mark.parametrize("key", ALL_CONNECTOR_KEYS)
def test_display_name_is_nonempty_string(key: str) -> None:
    connector = registry.get(key)
    assert isinstance(connector.display_name, str)
    assert connector.display_name, f"{key}: display_name must not be empty"


@pytest.mark.parametrize("key", ALL_CONNECTOR_KEYS)
def test_supported_auth_is_nonempty_list_of_authflow(key: str) -> None:
    connector = registry.get(key)
    assert isinstance(connector.supported_auth, list)
    assert connector.supported_auth, f"{key}: supported_auth must not be empty"
    for flow in connector.supported_auth:
        assert isinstance(flow, AuthFlow), f"{key}: {flow!r} is not an AuthFlow member"


@pytest.mark.parametrize("key", ALL_CONNECTOR_KEYS)
def test_default_base_url_is_str_or_none(key: str) -> None:
    connector = registry.get(key)
    val = connector.default_base_url
    assert val is None or isinstance(val, str), (
        f"{key}: default_base_url must be str or None, got {type(val)}"
    )


@pytest.mark.parametrize("key", ALL_CONNECTOR_KEYS)
def test_implements_connector_protocol(key: str) -> None:
    connector = registry.get(key)
    assert isinstance(connector, Connector), (
        f"{key}: does not satisfy the Connector Protocol — check for missing methods"
    )


@pytest.mark.parametrize("key", ALL_CONNECTOR_KEYS)
def test_key_matches_registry_entry(key: str) -> None:
    connector = registry.get(key)
    assert connector.key == key, (
        f"connector.key={connector.key!r} does not match registry key {key!r} — "
        "copy-paste error in ClassVar?"
    )


def test_all_expected_builtins_present() -> None:
    keys = {c.key for c in registry.all()}
    expected = {"generic", "github", "gitlab", "jenkins", "jira", "kubernetes", "linear", "slack"}
    missing = expected - keys
    assert not missing, f"Missing built-in connectors: {missing}"


def test_registry_has_no_duplicate_keys() -> None:
    keys = [c.key for c in registry.all()]
    assert len(keys) == len(set(keys)), "Duplicate keys found in registry"
