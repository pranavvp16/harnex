from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.db import get_db
from harnex_api.api.dependencies.rate_limit import enforce_tenant_create_budget
from harnex_api.api.schemas.tenants import SlugCheck, TenantCreate, TenantOut
from harnex_api.services.tenant import create as svc

router = APIRouter(prefix="/v1/tenants", tags=["tenants"])

_MAX_KEYCLOAK_USER_ID_LEN = 128
_ANON_PREFIX = "anon:"


def _owner_subject_key(owner_email: str | None, full_name: str) -> str:
    """Derive `TenantMembership.keycloak_user_id` bounded to DB column width."""
    if owner_email:
        return owner_email[:_MAX_KEYCLOAK_USER_ID_LEN]
    raw = f"{_ANON_PREFIX}{full_name.lower()}"
    if len(raw) <= _MAX_KEYCLOAK_USER_ID_LEN:
        return raw
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"{_ANON_PREFIX}{digest}"


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
    _rate: None = Depends(enforce_tenant_create_budget),
    db: AsyncSession = Depends(get_db),
) -> TenantOut:
    """Create a workspace + owner membership.

    Anonymous: this is the onboarding entry point — the caller has no tenant
    yet, so there's nothing for `get_tenant_context` to resolve. The owner
    identity is taken from the supplied `profile` block. Once Keycloak is
    enforced, we'll switch to JWT-derived identity here.
    """
    owner_email = str(payload.profile.email) if payload.profile.email else None
    owner_user_id = _owner_subject_key(owner_email, payload.profile.full_name)

    tenant = await svc.create_tenant_with_owner(
        db,
        display_name=payload.display_name,
        requested_slug=payload.slug,
        owner_user_id=owner_user_id,
        owner_email=owner_email,
    )
    return TenantOut.model_validate(tenant)


__all__ = ["router"]
