from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.common import Page
from harnex_api.api.schemas.executions import ExecutionOut
from harnex_api.db.models import Execution

router = APIRouter(prefix="/v1/executions", tags=["executions"])


@router.get("", response_model=Page[ExecutionOut])
async def list_executions(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[ExecutionOut]:
    base = select(Execution).where(Execution.tenant_id == ctx.tenant_id)
    total_row = await db.execute(select(func.count()).select_from(base.subquery()))
    total = int(total_row.scalar_one())
    rows = await db.execute(base.order_by(Execution.created_at.desc()).limit(limit).offset(offset))
    return Page(
        items=[ExecutionOut.model_validate(r) for r in rows.scalars().all()],
        total=total,
        limit=limit,
        offset=offset,
    )


__all__ = ["router"]
