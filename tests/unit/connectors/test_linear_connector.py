from __future__ import annotations

import pytest

from harnex_api.connectors.linear import LinearConnector
from harnex_api.db.models import AuthFlow

from .conftest import make_request


@pytest.fixture
def connector() -> LinearConnector:
    return LinearConnector()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_key() -> None:
    assert LinearConnector.key == "linear"


def test_display_name() -> None:
    assert LinearConnector.display_name == "Linear"


def test_supported_auth() -> None:
    assert AuthFlow.bearer in LinearConnector.supported_auth
    assert AuthFlow.oauth_authcode in LinearConnector.supported_auth


def test_default_base_url() -> None:
    assert LinearConnector.default_base_url == "https://api.linear.app"


def test_test_endpoint_is_post_to_graphql() -> None:
    ep = LinearConnector.test_endpoint
    assert ep.method == "POST"
    assert ep.path == "/graphql"
    assert ep.body is not None


# ---------------------------------------------------------------------------
# before_execute — the core Linear behavior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_before_execute_rewrites_method_to_post(connector: LinearConnector) -> None:
    req = make_request(method="GET", path="/issues")
    result = await connector.before_execute(req)
    assert result.method == "POST"


@pytest.mark.asyncio
async def test_before_execute_rewrites_path_to_graphql(connector: LinearConnector) -> None:
    req = make_request(method="GET", path="/issues")
    result = await connector.before_execute(req)
    assert result.path == "/graphql"


@pytest.mark.asyncio
async def test_before_execute_sets_content_type_json(connector: LinearConnector) -> None:
    req = make_request(method="GET", path="/issues", headers={})
    result = await connector.before_execute(req)
    assert result.headers.get("Content-Type") == "application/json"


@pytest.mark.asyncio
async def test_before_execute_content_type_overrides_caller_value(
    connector: LinearConnector,
) -> None:
    # {**request.headers, "Content-Type": "application/json"} — literal wins
    req = make_request(method="POST", path="/graphql", headers={"Content-Type": "text/plain"})
    result = await connector.before_execute(req)
    assert result.headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_before_execute_preserves_authorization_header(
    connector: LinearConnector,
) -> None:
    req = make_request(
        method="POST",
        path="/anything",
        headers={"Authorization": "Bearer lin_api_xxx"},
    )
    result = await connector.before_execute(req)
    assert result.headers["Authorization"] == "Bearer lin_api_xxx"
    assert result.headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_before_execute_preserves_body(connector: LinearConnector) -> None:
    body = {"query": "query { viewer { id } }"}
    req = make_request(method="POST", path="/graphql", body=body)
    result = await connector.before_execute(req)
    assert result.body == body


@pytest.mark.asyncio
async def test_before_execute_preserves_query_params(connector: LinearConnector) -> None:
    req = make_request(method="GET", path="/issues", query={"foo": "bar"})
    result = await connector.before_execute(req)
    assert result.query == {"foo": "bar"}


@pytest.mark.asyncio
async def test_before_execute_preserves_operation_id(connector: LinearConnector) -> None:
    req = make_request(method="GET", path="/issues", operation_id="listIssues")
    result = await connector.before_execute(req)
    assert result.operation_id == "listIssues"


@pytest.mark.asyncio
async def test_before_execute_returns_new_object(connector: LinearConnector) -> None:
    req = make_request(method="GET", path="/issues")
    result = await connector.before_execute(req)
    assert result is not req
    assert req.method == "GET"
    assert req.path == "/issues"
