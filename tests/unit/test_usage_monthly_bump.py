from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from harnex_api.services.usage.monthly import bump_usage_monthly


@pytest.mark.asyncio
async def test_bump_usage_monthly_noop_when_all_zero() -> None:
    session = AsyncMock()
    await bump_usage_monthly(session, uuid4(), executions=0, searches=0, embedding_tokens=0)
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_bump_usage_monthly_issues_postgres_upsert() -> None:
    session = AsyncMock()
    tenant_id = uuid4()
    await bump_usage_monthly(session, tenant_id, executions=2, searches=1, embedding_tokens=3)
    session.execute.assert_called_once()
    stmt = session.execute.call_args[0][0]
    sql = str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    ).lower()
    assert "on conflict" in sql
    assert "usage_monthly" in sql
