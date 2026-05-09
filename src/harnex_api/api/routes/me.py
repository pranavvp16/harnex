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
from harnex_api.config import get_settings
from harnex_api.db.models import Tenant, TenantMembership, TenantRole

router = APIRouter(prefix="/v1/me", tags=["me"])


@router.get("", response_model=MeOut)
async def get_me(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> MeOut:
    """Return the caller's identity + workspaces.

    Console uses this to (a) decide whether to send the user to onboarding
    and (b) populate the org switcher across every workspace the caller
    belongs to. Results are keyed by authenticated subject (JWT sub or dev
    subject), never by arbitrary tenant roster.
    """
    rows = await db.execute(
        select(TenantMembership)
        .where(TenantMembership.keycloak_user_id == ctx.subject)
        .options(selectinload(TenantMembership.tenant))
    )
    memberships = list(rows.scalars().all())

    if memberships:
        membership_dtos = [MembershipOut.model_validate(m) for m in memberships]
    elif get_settings().env in ("local", "dev") and ctx.subject == "dev":
        # Dev-only: seeded tenant sometimes has no membership row while the UI
        # still pins `X-Harnex-Dev-Tenant` — synthesize membership for parity.
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
    else:
        membership_dtos = []

    return MeOut(
        user=UserOut(id=ctx.subject, email=None, full_name=None),
        memberships=membership_dtos,
        current_tenant_id=ctx.tenant_id,
    )


__all__ = ["router"]
