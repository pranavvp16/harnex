from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

import harnex_api.mcp.server as mcp_server


@pytest.fixture(autouse=True)
def _clear_summary_cache() -> None:
    mcp_server._connection_summary_cache.clear()
    yield
    mcp_server._connection_summary_cache.clear()


def test_caller_cache_key_stable() -> None:
    tid = uuid4()
    kid = uuid4()
    a = mcp_server._caller_cache_key(
        mcp_server._CallerContext(api_key_id=kid, tenant_id=tid, scope_type="all")
    )
    b = mcp_server._caller_cache_key(
        mcp_server._CallerContext(api_key_id=kid, tenant_id=tid, scope_type="all")
    )
    assert a == b


def test_caller_cache_key_differs_on_scope() -> None:
    tid = uuid4()
    kid = uuid4()
    cid = uuid4()
    all_key = mcp_server._caller_cache_key(
        mcp_server._CallerContext(api_key_id=kid, tenant_id=tid, scope_type="all")
    )
    scoped = mcp_server._caller_cache_key(
        mcp_server._CallerContext(
            api_key_id=kid,
            tenant_id=tid,
            scope_type="connections",
            scope_connection_ids=(cid,),
        )
    )
    assert all_key != scoped


@pytest.mark.asyncio
async def test_connection_summary_uses_loader_once_per_cache_key() -> None:
    caller = mcp_server._CallerContext(api_key_id=uuid4(), tenant_id=uuid4())
    with patch.object(
        mcp_server,
        "_load_connection_summary_block",
        new_callable=AsyncMock,
        return_value="SUMMARY",
    ) as loader:
        first = await mcp_server.connection_summary_for_tools_list(caller)
        second = await mcp_server.connection_summary_for_tools_list(caller)
    assert first == "SUMMARY"
    assert second == "SUMMARY"
    assert loader.await_count == 1


@pytest.mark.asyncio
async def test_list_tools_appends_connection_block_to_search() -> None:
    app = mcp_server.HarnexFastMCP("test-mcp", streamable_http_path="/")

    @app.tool()
    async def search(query: str) -> str:
        """Static base for search."""
        return query

    caller = mcp_server._CallerContext(api_key_id=uuid4(), tenant_id=uuid4())
    token = mcp_server._caller_context.set(caller)
    try:
        with patch.object(
            mcp_server,
            "connection_summary_for_tools_list",
            new_callable=AsyncMock,
            return_value="CONN_CONTEXT",
        ) as summ:
            tools = await app.list_tools()
    finally:
        mcp_server._caller_context.reset(token)

    search_tool = next(t for t in tools if t.name == "search")
    assert "Static base for search." in (search_tool.description or "")
    assert "CONN_CONTEXT" in (search_tool.description or "")
    summ.assert_awaited_once()
