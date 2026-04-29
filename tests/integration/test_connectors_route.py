from __future__ import annotations

import httpx
import pytest

from harnex_api.main import create_app


@pytest.fixture
def app():
    return create_app()


async def test_list_connectors_returns_builtins(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/connectors")
    assert resp.status_code == 200
    payload = resp.json()
    keys = {c["key"] for c in payload}
    assert {"generic", "github", "jenkins"}.issubset(keys)
    github = next(c for c in payload if c["key"] == "github")
    assert "bearer" in github["supported_auth"] or "oauth_authcode" in github["supported_auth"]


async def test_healthz(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_connections_requires_dev_tenant_header(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/connections")
    assert resp.status_code == 401
