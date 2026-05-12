"""Monthly usage counters (`usage_monthly`) — atomic bumps for dashboard / quota."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.db.models import UsageMonthly


def current_year_month_utc() -> str:
    """Billing month key aligned with ``GET /v1/usage/current`` (UTC ``YYYY-MM``)."""
    return datetime.now(UTC).strftime("%Y-%m")


async def bump_usage_monthly(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    executions: int = 0,
    searches: int = 0,
    embedding_tokens: int = 0,
) -> None:
    """Atomically increment monthly counters for ``tenant_id`` (PostgreSQL upsert).

    Uses ``INSERT ... ON CONFLICT`` on ``uq_usage_tenant_month`` so concurrent
    MCP/REST calls do not lose increments.
    """
    if executions == 0 and searches == 0 and embedding_tokens == 0:
        return

    ym = current_year_month_utc()
    insert_stmt = insert(UsageMonthly).values(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        year_month=ym,
        executions=executions,
        searches=searches,
        embedding_tokens=embedding_tokens,
    )
    upsert = insert_stmt.on_conflict_do_update(
        constraint="uq_usage_tenant_month",
        set_={
            "executions": UsageMonthly.executions + insert_stmt.excluded.executions,
            "searches": UsageMonthly.searches + insert_stmt.excluded.searches,
            "embedding_tokens": UsageMonthly.embedding_tokens
            + insert_stmt.excluded.embedding_tokens,
            "updated_at": func.now(),
        },
    )
    await session.execute(upsert)


__all__ = ["bump_usage_monthly", "current_year_month_utc"]
