from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import (
    AuthenticatedUser,
    get_authenticated_user,
)
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.dependencies.rate_limit import enforce_tenant_create_budget
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
    user: AuthenticatedUser = Depends(get_authenticated_user),
    _rate: None = Depends(enforce_tenant_create_budget),
    db: AsyncSession = Depends(get_db),
) -> TenantOut:
    """Create a workspace + owner membership for the JWT-authenticated caller.

    Owner identity comes from the verified token: `sub` populates
    `TenantMembership.keycloak_user_id` and the token's `email` claim is the
    canonical address. The onboarding payload's `profile.email` is used only
    as a fallback when the IDP didn't include an email claim.
    """
    owner_email = user.email or (str(payload.profile.email) if payload.profile.email else None)
    tenant = await svc.create_tenant_with_owner(
        db,
        display_name=payload.display_name,
        requested_slug=payload.slug,
        owner_user_id=user.sub,
        owner_email=owner_email,
    )
    return TenantOut.model_validate(tenant)


__all__ = ["router"]
