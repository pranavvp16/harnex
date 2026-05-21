"""Daily-executions endpoint — zero-fills missing days, scopes to tenant window."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from harnex_api.api.dependencies.auth import TenantContext
from harnex_api.api.routes.usage import get_daily_executions


def _mock_session_for_daily(buckets: list[tuple[datetime, int]]) -> Any:
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = buckets
    session.execute = AsyncMock(return_value=result)
    return session


async def test_daily_executions_empty_returns_zero_filled_window() -> None:
    ctx = TenantContext(tenant_id=uuid.uuid4(), subject="dev")
    session = _mock_session_for_daily([])

    out = await get_daily_executions(ctx=ctx, db=session, days=30)

    assert out.days == 30
    assert len(out.points) == 30
    assert all(p.count == 0 for p in out.points)
    # Last point is today (UTC); first is 29 days prior — series is contiguous.
    today = datetime.now(UTC).date()
    assert out.points[-1].date == today.isoformat()
    assert out.points[0].date == (today - timedelta(days=29)).isoformat()


async def test_daily_executions_buckets_into_correct_days() -> None:
    ctx = TenantContext(tenant_id=uuid.uuid4(), subject="dev")
    today = datetime.now(UTC).date()
    d_today = datetime.combine(today, datetime.min.time(), tzinfo=UTC)
    d_yest = d_today - timedelta(days=1)
    session = _mock_session_for_daily([(d_today, 3), (d_yest, 1)])

    out = await get_daily_executions(ctx=ctx, db=session, days=7)

    assert out.days == 7
    assert len(out.points) == 7
    by_date = {p.date: p.count for p in out.points}
    assert by_date[today.isoformat()] == 3
    assert by_date[(today - timedelta(days=1)).isoformat()] == 1
    # Days with no executions stay at zero rather than being omitted.
    assert by_date[(today - timedelta(days=5)).isoformat()] == 0
