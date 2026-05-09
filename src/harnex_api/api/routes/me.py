from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.tenants import (
    MembershipOut,
    MeOut,
    TenantOut,
    UserOut,
)
from harnex_api.db.models import Tenant, TenantMembership, TenantRole

router = APIRouter(prefix="/v1/me", tags=["me"])


@router.get("", response_model=MeOut)
async def get_me(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> MeOut:
    """Return the caller's identity + workspaces.

    Console uses this to (a) decide whether to send the user to onboarding
    and (b) populate the org switcher. In dev mode the "user" is the
    X-Harnex-Dev-Tenant header value; in prod it'll be JWT-derived.
    """
    rows = await db.execute(
        select(TenantMembership)
        .where(TenantMembership.tenant_id == ctx.tenant_id)
        .options(selectinload(TenantMembership.tenant))
    )
    memberships = list(rows.scalars().all())

    if memberships:
        membership_dtos = [MembershipOut.model_validate(m) for m in memberships]
    else:
        # Dev path: tenant exists (e.g. seeded dev tenant) but no membership row.
        # Synthesize one so the console can still render the workspace.
        tenant_row = await db.execute(select(Tenant).where(Tenant.id == ctx.tenant_id))
        tenant = tenant_row.scalar_one_or_none()
        membership_dtos = (
            [
                MembershipOut(
                    id=ctx.tenant_id,
                    tenant_id=tenant.id,
                    email=None,
                    role=TenantRole.owner,
                    tenant=TenantOut.model_validate(tenant),
                )
            ]
            if tenant is not None
            else []
        )

    return MeOut(
        user=UserOut(id=ctx.subject, email=None, full_name=None),
        memberships=membership_dtos,
        current_tenant_id=ctx.tenant_id,
    )


__all__ = ["router"]
