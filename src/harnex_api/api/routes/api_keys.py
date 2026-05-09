from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.api_keys import (
    ApiKeyCreate,
    ApiKeyIssued,
    ApiKeyOut,
    ApiKeyScope,
)
from harnex_api.db.models import ApiKey, Connection
from harnex_api.services.api_keys import issue_key

router = APIRouter(prefix="/v1/api-keys", tags=["api-keys"])


def _row_to_out(row: ApiKey) -> ApiKeyOut:
    return ApiKeyOut(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        key_prefix=row.key_prefix,
        is_active=row.is_active,
        last_used_at=row.last_used_at,
        created_at=row.created_at,
        expires_at=row.expires_at,
        scope=ApiKeyScope.model_validate(row.scope or {"type": "all"}),
    )


@router.get("", response_model=list[ApiKeyOut])
async def list_api_keys(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyOut]:
    rows = await db.execute(
        select(ApiKey)
        .where(ApiKey.tenant_id == ctx.tenant_id, ApiKey.is_active.is_(True))
        .order_by(ApiKey.created_at.desc())
    )
    return [_row_to_out(r) for r in rows.scalars().all()]


@router.post("", response_model=ApiKeyIssued, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyIssued:
    if payload.scope.type == "connections":
        if not payload.scope.connection_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scope.connection_ids must be non-empty when type='connections'",
            )
        # Verify every referenced connection actually belongs to this tenant.
        rows = await db.execute(
            select(Connection.id).where(
                Connection.tenant_id == ctx.tenant_id,
                Connection.id.in_(payload.scope.connection_ids),
            )
        )
        owned = {row for row in rows.scalars().all()}
        missing = [str(cid) for cid in payload.scope.connection_ids if cid not in owned]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"unknown connection ids: {', '.join(missing)}",
            )

    expires_at: datetime | None = None
    if payload.expires_in_days is not None:
        expires_at = datetime.now(UTC) + timedelta(days=payload.expires_in_days)

    issued = issue_key()
    row = ApiKey(
        tenant_id=ctx.tenant_id,
        name=payload.name,
        key_prefix=issued.prefix,
        key_hash=issued.hash_blob,
        is_active=True,
        created_by=ctx.subject,
        expires_at=expires_at,
        scope=payload.scope.model_dump(mode="json"),
    )
    db.add(row)
    await db.flush()
    out = _row_to_out(row)
    return ApiKeyIssued(**out.model_dump(), plaintext=issued.plaintext)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    row = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.tenant_id == ctx.tenant_id)
    )
    obj = row.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="api key not found")
    obj.is_active = False


__all__ = ["router"]
