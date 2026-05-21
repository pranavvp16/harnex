from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.usage import DailyExecutionPoint, DailyExecutions, UsageCurrent
from harnex_api.db.models import Execution, Tenant, UsageMonthly
from harnex_api.services.usage.monthly import current_year_month_utc

router = APIRouter(prefix="/v1/usage", tags=["usage"])


@router.get("/current", response_model=UsageCurrent)
async def get_current_usage(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> UsageCurrent:
    tenant_row = await db.execute(select(Tenant).where(Tenant.id == ctx.tenant_id))
    tenant = tenant_row.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tenant not found")

    ym = current_year_month_utc()
    usage_row = await db.execute(
        select(UsageMonthly).where(
            UsageMonthly.tenant_id == ctx.tenant_id, UsageMonthly.year_month == ym
        )
    )
    usage = usage_row.scalar_one_or_none()
    return UsageCurrent(
        year_month=ym,
        executions=usage.executions if usage else 0,
        searches=usage.searches if usage else 0,
        embedding_tokens=usage.embedding_tokens if usage else 0,
        monthly_execution_quota=tenant.monthly_execution_quota,
    )


@router.get("/daily", response_model=DailyExecutions)
async def get_daily_executions(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=90),
) -> DailyExecutions:
    today_utc = datetime.now(UTC).date()
    start_date = today_utc - timedelta(days=days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)

    day_col = func.date_trunc("day", func.timezone("UTC", Execution.created_at)).label("day")
    rows = await db.execute(
        select(day_col, func.count().label("count"))
        .where(Execution.tenant_id == ctx.tenant_id, Execution.created_at >= start_dt)
        .group_by(day_col)
    )
    counts: dict[str, int] = {}
    for day, count in rows.all():
        # `day` is a datetime at midnight UTC from date_trunc
        counts[day.date().isoformat()] = int(count)

    points = [
        DailyExecutionPoint(
            date=(start_date + timedelta(days=i)).isoformat(),
            count=counts.get((start_date + timedelta(days=i)).isoformat(), 0),
        )
        for i in range(days)
    ]
    return DailyExecutions(days=days, points=points)


__all__ = ["router"]
