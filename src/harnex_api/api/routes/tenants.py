from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.tenants import SlugCheck, TenantCreate, TenantOut
from harnex_api.services.tenant import create as svc

router = APIRouter(prefix="/v1/tenants", tags=["tenants"])


@router.get("/check-slug", response_model=SlugCheck)
async def check_slug(
    slug: str = Query(min_length=2, max_length=64, pattern=r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"),
    db: AsyncSession = Depends(get_db),
) -> SlugCheck:
    available = await svc.slug_available(db, slug)
    return SlugCheck(slug=slug, available=available)


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    db: AsyncSession = Depends(get_db),
) -> TenantOut:
    """Create a workspace + owner membership.

    Anonymous: this is the onboarding entry point — the caller has no tenant
    yet, so there's nothing for `get_tenant_context` to resolve. The owner
    identity is taken from the supplied `profile` block. Once Keycloak is
    enforced, we'll switch to JWT-derived identity here.
    """
    owner_email = str(payload.profile.email) if payload.profile.email else None
    owner_user_id = owner_email or f"anon:{payload.profile.full_name.lower()}"

    tenant = await svc.create_tenant_with_owner(
        db,
        display_name=payload.display_name,
        requested_slug=payload.slug,
        owner_user_id=owner_user_id,
        owner_email=owner_email,
    )
    return TenantOut.model_validate(tenant)


__all__ = ["router"]
