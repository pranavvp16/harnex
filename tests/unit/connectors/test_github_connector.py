from __future__ import annotations

import pytest

from harnex_api.connectors.base import LoadedSpec
from harnex_api.connectors.github import GITHUB_OPENAPI_URL, GitHubConnector
from harnex_api.db.models import AuthFlow

from .conftest import make_connection


@pytest.fixture
def connector() -> GitHubConnector:
    return GitHubConnector()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_key() -> None:
    assert GitHubConnector.key == "github"


def test_display_name() -> None:
    assert GitHubConnector.display_name == "GitHub"


def test_supported_auth_includes_bearer_and_oauth() -> None:
    assert AuthFlow.bearer in GitHubConnector.supported_auth
    assert AuthFlow.oauth_authcode in GitHubConnector.supported_auth


def test_default_base_url() -> None:
    assert GitHubConnector.default_base_url == "https://api.github.com"


def test_test_endpoint() -> None:
    ep = GitHubConnector.test_endpoint
    assert ep.method == "GET"
    assert ep.path == "/user"


# ---------------------------------------------------------------------------
# infer_base_url — inherits BaseConnector logic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_infer_base_url_returns_default_when_no_connection_base_url(
    connector: GitHubConnector,
) -> None:
    conn = make_connection(connector_key="github", base_url=None)
    result = await connector.infer_base_url(conn, spec=None)
    assert result == "https://api.github.com"


@pytest.mark.asyncio
async def test_infer_base_url_connection_base_url_wins_over_default(
    connector: GitHubConnector,
) -> None:
    conn = make_connection(
        connector_key="github", base_url="https://github.enterprise.example.com"
    )
    result = await connector.infer_base_url(conn, spec=None)
    assert result == "https://github.enterprise.example.com"


@pytest.mark.asyncio
async def test_infer_base_url_falls_back_to_spec_server_when_no_explicit_url(
    connector: GitHubConnector,
) -> None:
    conn = make_connection(connector_key="github", base_url=None)
    spec = LoadedSpec(
        document={"servers": [{"url": "https://api.github.com/v3"}]},
        source="url",
        raw_hash="abc",
        original_format="openapi-3",
    )
    result = await connector.infer_base_url(conn, spec=spec)
    assert result == "https://api.github.com/v3"


@pytest.mark.asyncio
async def test_infer_base_url_connection_url_wins_over_spec_server(
    connector: GitHubConnector,
) -> None:
    conn = make_connection(
        connector_key="github", base_url="https://github.enterprise.example.com"
    )
    spec = LoadedSpec(
        document={"servers": [{"url": "https://api.github.com"}]},
        source="url",
        raw_hash="abc",
        original_format="openapi-3",
    )
    result = await connector.infer_base_url(conn, spec=spec)
    assert result == "https://github.enterprise.example.com"


# ---------------------------------------------------------------------------
# load_spec — stubs the fetcher so no HTTP call is made
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_spec_uses_github_openapi_url_by_default(
    connector: GitHubConnector,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import harnex_api.services.ingestion.fetcher as fetcher_mod

    captured: list[str] = []

    async def _fake_fetch(url: str) -> LoadedSpec:
        captured.append(url)
        return LoadedSpec(document={}, source="url", raw_hash="fake", original_format="openapi-3")

    monkeypatch.setattr(fetcher_mod, "fetch_spec_from_url", _fake_fetch)
    conn = make_connection(connector_key="github", spec_url=None)
    await connector.load_spec(conn)
    assert captured == [GITHUB_OPENAPI_URL]


@pytest.mark.asyncio
async def test_load_spec_uses_connection_spec_url_when_set(
    connector: GitHubConnector,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import harnex_api.services.ingestion.fetcher as fetcher_mod

    custom_url = "https://my-mirror.example.com/github-api.json"
    captured: list[str] = []

    async def _fake_fetch(url: str) -> LoadedSpec:
        captured.append(url)
        return LoadedSpec(document={}, source="url", raw_hash="x", original_format="openapi-3")

    monkeypatch.setattr(fetcher_mod, "fetch_spec_from_url", _fake_fetch)
    conn = make_connection(connector_key="github", spec_url=custom_url)
    await connector.load_spec(conn)
    assert captured == [custom_url]
