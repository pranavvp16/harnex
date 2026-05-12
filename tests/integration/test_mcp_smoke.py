from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from harnex_api.main import create_app
from harnex_api.services.api_key_auth import ApiKeyAuth

pytestmark = pytest.mark.asyncio


@pytest.fixture
def app():
    return create_app()


async def test_mcp_bare_path_redirects_with_trailing_slash(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        resp = await client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        )
    assert resp.status_code == 307
    assert resp.headers["location"] in ("/mcp/", "http://test/mcp/")


async def test_mcp_endpoint_rejects_missing_auth(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/mcp/", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})
    assert resp.status_code == 401
    payload = resp.json()
    assert payload["jsonrpc"] == "2.0"
    assert payload["id"] == 1
    assert payload["error"]["code"] == -32001
    assert "Authentication required" in payload["error"]["message"]
    assert resp.headers.get("www-authenticate", "").lower().startswith("bearer")


async def test_mcp_endpoint_rejects_invalid_bearer(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/mcp/",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": "abc"},
            headers={"Authorization": "Bearer hnx_not_a_real_key"},
        )
    assert resp.status_code == 401
    payload = resp.json()
    assert payload["jsonrpc"] == "2.0"
    assert payload["id"] == "abc"
    assert payload["error"]["code"] == -32001


_DEV_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_DUMMY_API_KEY_ID = uuid.UUID("00000000-0000-0000-0000-0000000000AA")


async def test_mcp_initialize_returns_capabilities_and_tools(app) -> None:
    """Verify that an authenticated MCP initialize + tools/list round-trip works.

    This is a regression test for the bug where the auth middleware's
    body-drain-and-replay caused EventSourceResponse to see an
    ``http.disconnect`` on the second ``receive()`` call, killing the SSE
    stream before any data was written ("no tools visible").
    """
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    from harnex_api.mcp.server import get_mcp_app

    fake_auth = ApiKeyAuth(
        api_key_id=_DUMMY_API_KEY_ID,
        tenant_id=_DEV_TENANT_ID,
        scope_type="all",
        scope_connection_ids=(),
    )

    # Start the MCP session manager (mimics what lifespan() does in main.py).
    mcp = get_mcp_app()
    _ = mcp.streamable_http_app()  # ensure inner app is built
    async with mcp.session_manager.run():
        with (
            patch("harnex_api.mcp.server.authenticate_key", new_callable=AsyncMock, return_value=fake_auth),
            patch(
                "harnex_api.mcp.server.connection_summary_for_tools_list",
                new_callable=AsyncMock,
                return_value="",
            ),
        ):
            # Use localhost to pass the transport security Host header check.
            asgi_transport = httpx.ASGITransport(app=app)

            def _make_client(**kwargs: object) -> httpx.AsyncClient:  # type: ignore[misc]
                return httpx.AsyncClient(transport=asgi_transport, base_url="http://localhost", **kwargs)

            async with streamablehttp_client(
                url="http://localhost/mcp/",
                headers={"Authorization": "Bearer hnx.test.key"},
                httpx_client_factory=_make_client,
            ) as (read_stream, write_stream, _session_id_cb), ClientSession(
                read_stream, write_stream
            ) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result.tools]
                assert "search" in tool_names, f"Expected 'search' tool, got: {tool_names}"
                assert "execute" in tool_names, f"Expected 'execute' tool, got: {tool_names}"
