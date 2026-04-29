from __future__ import annotations

import httpx
import pytest

from harnex_api.main import create_app


@pytest.fixture
def app():
    return create_app()


async def test_mcp_endpoint_rejects_missing_auth(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # MCP streamable HTTP listens at the mount root.
        resp = await client.post("/mcp/", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})
    assert resp.status_code == 401
