"""Idempotent dev-tenant seeding.

Used at app startup in `local`/`dev` environments so the console (which
authenticates with a hardcoded UUID via `X-Harnex-Dev-Tenant`) can hit
POST/PUT/DELETE endpoints without a foreign-key violation.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.db.models import Tenant, TenantPlan

DEV_TENANT_ID: UUID = UUID("11111111-1111-1111-1111-111111111111")
DEV_TENANT_SLUG = "dev"
DEV_TENANT_DISPLAY_NAME = "Local Dev Tenant"


async def ensure_dev_tenant(session: AsyncSession) -> Tenant:
    existing = await session.execute(select(Tenant).where(Tenant.id == DEV_TENANT_ID))
    row = existing.scalar_one_or_none()
    if row is not None:
        return row

    tenant = Tenant(
        id=DEV_TENANT_ID,
        slug=DEV_TENANT_SLUG,
        display_name=DEV_TENANT_DISPLAY_NAME,
        plan=TenantPlan.free,
        is_active=True,
    )
    session.add(tenant)
    await session.flush()
    return tenant


__all__ = ["DEV_TENANT_ID", "DEV_TENANT_SLUG", "ensure_dev_tenant"]
