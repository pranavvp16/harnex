from __future__ import annotations

import httpx
import pytest

from harnex_api.main import create_app


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
        # MCP streamable HTTP listens at the mount root.
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
