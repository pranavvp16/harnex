from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.usage import UsageCurrent
from harnex_api.db.models import Tenant, UsageMonthly
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


__all__ = ["router"]
