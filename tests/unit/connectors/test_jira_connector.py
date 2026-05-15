from __future__ import annotations

import pytest

from harnex_api.connectors.base import LoadedSpec
from harnex_api.connectors.jira import JIRA_OPENAPI_URL, JiraConnector
from harnex_api.db.models import AuthFlow

from .conftest import make_connection


@pytest.fixture
def connector() -> JiraConnector:
    return JiraConnector()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_key() -> None:
    assert JiraConnector.key == "jira"


def test_display_name() -> None:
    assert JiraConnector.display_name == "Jira"


def test_default_base_url_is_none() -> None:
    # Jira is always tenant-specific: <org>.atlassian.net
    assert JiraConnector.default_base_url is None


def test_supported_auth() -> None:
    assert AuthFlow.oauth_authcode in JiraConnector.supported_auth
    assert AuthFlow.basic in JiraConnector.supported_auth
    assert AuthFlow.bearer in JiraConnector.supported_auth


def test_test_endpoint() -> None:
    ep = JiraConnector.test_endpoint
    assert ep.method == "GET"
    assert ep.path == "/rest/api/3/myself"


def test_openapi_url_is_atlassian() -> None:
    assert "atlassian.com" in JIRA_OPENAPI_URL


# ---------------------------------------------------------------------------
# infer_base_url — ONLY returns connection.base_url, never spec servers
#
# The official Jira OpenAPI spec lists "https://your-domain.atlassian.net" in
# servers[] — a placeholder that would break routing if used as-is. Jira always
# requires an explicit tenant URL.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_infer_base_url_returns_connection_base_url(connector: JiraConnector) -> None:
    conn = make_connection(connector_key="jira", base_url="https://acme.atlassian.net")
    result = await connector.infer_base_url(conn, spec=None)
    assert result == "https://acme.atlassian.net"


@pytest.mark.asyncio
async def test_infer_base_url_returns_none_when_not_provided(connector: JiraConnector) -> None:
    conn = make_connection(connector_key="jira", base_url=None)
    result = await connector.infer_base_url(conn, spec=None)
    assert result is None


@pytest.mark.asyncio
async def test_infer_base_url_ignores_spec_servers(connector: JiraConnector) -> None:
    conn = make_connection(connector_key="jira", base_url=None)
    spec = LoadedSpec(
        document={"servers": [{"url": "https://your-domain.atlassian.net"}]},
        source="url",
        raw_hash="abc",
        original_format="openapi-3",
    )
    result = await connector.infer_base_url(conn, spec=spec)
    assert result is None


@pytest.mark.asyncio
async def test_infer_base_url_connection_url_wins_over_spec_servers(
    connector: JiraConnector,
) -> None:
    conn = make_connection(connector_key="jira", base_url="https://acme.atlassian.net")
    spec = LoadedSpec(
        document={"servers": [{"url": "https://your-domain.atlassian.net"}]},
        source="url",
        raw_hash="abc",
        original_format="openapi-3",
    )
    result = await connector.infer_base_url(conn, spec=spec)
    assert result == "https://acme.atlassian.net"


# ---------------------------------------------------------------------------
# load_spec — stubs the fetcher so no HTTP call is made
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_spec_uses_atlassian_url_by_default(
    connector: JiraConnector,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import harnex_api.services.ingestion.fetcher as fetcher_mod

    captured: list[str] = []

    async def _fake_fetch(url: str) -> LoadedSpec:
        captured.append(url)
        return LoadedSpec(document={}, source="url", raw_hash="fake", original_format="openapi-3")

    monkeypatch.setattr(fetcher_mod, "fetch_spec_from_url", _fake_fetch)
    conn = make_connection(connector_key="jira", spec_url=None)
    await connector.load_spec(conn)
    assert captured == [JIRA_OPENAPI_URL]


@pytest.mark.asyncio
async def test_load_spec_uses_connection_spec_url_when_set(
    connector: JiraConnector,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import harnex_api.services.ingestion.fetcher as fetcher_mod

    custom_url = "https://my-mirror.example.com/jira-openapi.json"
    captured: list[str] = []

    async def _fake_fetch(url: str) -> LoadedSpec:
        captured.append(url)
        return LoadedSpec(document={}, source="url", raw_hash="x", original_format="openapi-3")

    monkeypatch.setattr(fetcher_mod, "fetch_spec_from_url", _fake_fetch)
    conn = make_connection(connector_key="jira", spec_url=custom_url)
    await connector.load_spec(conn)
    assert captured == [custom_url]
