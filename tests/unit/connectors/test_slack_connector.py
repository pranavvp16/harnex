from __future__ import annotations

import pytest

from harnex_api.connectors.base import LoadedSpec
from harnex_api.connectors.slack import SLACK_OPENAPI_URL, SlackConnector
from harnex_api.db.models import AuthFlow

from .conftest import make_connection, make_request


@pytest.fixture
def connector() -> SlackConnector:
    return SlackConnector()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_key() -> None:
    assert SlackConnector.key == "slack"


def test_display_name() -> None:
    assert SlackConnector.display_name == "Slack"


def test_supported_auth() -> None:
    assert AuthFlow.bearer in SlackConnector.supported_auth
    assert AuthFlow.oauth_authcode in SlackConnector.supported_auth


def test_default_base_url() -> None:
    assert SlackConnector.default_base_url == "https://slack.com/api"


def test_test_endpoint() -> None:
    ep = SlackConnector.test_endpoint
    assert ep.method == "GET"
    assert ep.path == "/auth.test"


def test_openapi_url_is_slackapi_github() -> None:
    assert "slackapi" in SLACK_OPENAPI_URL


# ---------------------------------------------------------------------------
# infer_base_url — inherits BaseConnector defaults (connection → spec → default)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_infer_base_url_returns_default_when_no_connection_url(
    connector: SlackConnector,
) -> None:
    conn = make_connection(connector_key="slack", base_url=None)
    result = await connector.infer_base_url(conn, spec=None)
    assert result == "https://slack.com/api"


@pytest.mark.asyncio
async def test_infer_base_url_respects_explicit_connection_base_url(
    connector: SlackConnector,
) -> None:
    conn = make_connection(
        connector_key="slack", base_url="https://slack-mirror.example.com"
    )
    result = await connector.infer_base_url(conn, spec=None)
    assert result == "https://slack-mirror.example.com"


@pytest.mark.asyncio
async def test_infer_base_url_falls_back_to_spec_server_before_default(
    connector: SlackConnector,
) -> None:
    conn = make_connection(connector_key="slack", base_url=None)
    spec = LoadedSpec(
        document={"servers": [{"url": "https://slack.com/api/v2"}]},
        source="url",
        raw_hash="abc",
        original_format="openapi-3",
    )
    result = await connector.infer_base_url(conn, spec=spec)
    assert result == "https://slack.com/api/v2"


@pytest.mark.asyncio
async def test_infer_base_url_connection_url_wins_over_spec(
    connector: SlackConnector,
) -> None:
    conn = make_connection(connector_key="slack", base_url="https://slack-mirror.example.com")
    spec = LoadedSpec(
        document={"servers": [{"url": "https://slack.com/api/v2"}]},
        source="url",
        raw_hash="abc",
        original_format="openapi-3",
    )
    result = await connector.infer_base_url(conn, spec=spec)
    assert result == "https://slack-mirror.example.com"


# ---------------------------------------------------------------------------
# before_execute — Slack does NOT override; BaseConnector returns same object
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_before_execute_is_identity(connector: SlackConnector) -> None:
    req = make_request(
        method="GET",
        path="/conversations.list",
        headers={"Authorization": "Bearer xoxb-xxx"},
        query={"limit": "50"},
    )
    result = await connector.before_execute(req)
    assert result is req


# ---------------------------------------------------------------------------
# load_spec — stubs the fetcher so no HTTP call is made
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_spec_uses_slack_openapi_url_by_default(
    connector: SlackConnector,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import harnex_api.services.ingestion.fetcher as fetcher_mod

    captured: list[str] = []

    async def _fake_fetch(url: str) -> LoadedSpec:
        captured.append(url)
        return LoadedSpec(document={}, source="url", raw_hash="fake", original_format="openapi-3")

    monkeypatch.setattr(fetcher_mod, "fetch_spec_from_url", _fake_fetch)
    conn = make_connection(connector_key="slack", spec_url=None)
    await connector.load_spec(conn)
    assert captured == [SLACK_OPENAPI_URL]


@pytest.mark.asyncio
async def test_load_spec_uses_connection_spec_url_when_set(
    connector: SlackConnector,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import harnex_api.services.ingestion.fetcher as fetcher_mod

    custom_url = "https://mirror.example.com/slack-openapi.json"
    captured: list[str] = []

    async def _fake_fetch(url: str) -> LoadedSpec:
        captured.append(url)
        return LoadedSpec(document={}, source="url", raw_hash="x", original_format="openapi-3")

    monkeypatch.setattr(fetcher_mod, "fetch_spec_from_url", _fake_fetch)
    conn = make_connection(connector_key="slack", spec_url=custom_url)
    await connector.load_spec(conn)
    assert captured == [custom_url]
