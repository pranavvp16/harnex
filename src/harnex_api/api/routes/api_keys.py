from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.api_keys import ApiKeyCreate, ApiKeyIssued, ApiKeyOut
from harnex_api.db.models import ApiKey
from harnex_api.services.api_keys import issue_key

router = APIRouter(prefix="/v1/api-keys", tags=["api-keys"])


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
    return [ApiKeyOut.model_validate(r) for r in rows.scalars().all()]


@router.post("", response_model=ApiKeyIssued, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyIssued:
    issued = issue_key()
    row = ApiKey(
        tenant_id=ctx.tenant_id,
        name=payload.name,
        key_prefix=issued.prefix,
        key_hash=issued.hash_blob,
        is_active=True,
        created_by=ctx.subject,
    )
    db.add(row)
    await db.flush()
    return ApiKeyIssued(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        key_prefix=row.key_prefix,
        is_active=row.is_active,
        last_used_at=row.last_used_at,
        created_at=row.created_at,
        plaintext=issued.plaintext,
    )


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
