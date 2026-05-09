from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from harnex_api.api.dependencies.auth import (
    AuthenticatedUser,
    get_authenticated_user,
)
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.auth import AuthMeOut, RegisterIn, RegisterOut
from harnex_api.api.schemas.tenants import MembershipOut
from harnex_api.db.models import TenantMembership
from harnex_api.services.keycloak_admin import (
    EmailAlreadyExistsError,
    KeycloakAdminClient,
    KeycloakAdminError,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", response_model=RegisterOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn) -> RegisterOut:
    """Create a Keycloak user from the SPA's email/password sign-up form.

    The SPA follows up with the Direct Access Grants (`grant_type=password`)
    flow against Keycloak directly to obtain tokens; we don't return a JWT
    here. Tenant creation happens later via `POST /v1/tenants` once the
    caller is authenticated.
    """
    client = KeycloakAdminClient()
    try:
        await client.create_user(
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name,
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "email_taken", "message": "An account with that email already exists."},
        ) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"identity provider error: {exc}",
        ) from exc
    return RegisterOut(ok=True)


@router.get("/me", response_model=AuthMeOut)
async def auth_me(
    user: AuthenticatedUser = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> AuthMeOut:
    """Return the JWT-authenticated caller's identity + workspaces.

    Used by the SPA right after sign-in to decide whether to land on the
    dashboard (existing memberships) or onboarding (none yet).
    """
    rows = await db.execute(
        select(TenantMembership)
        .where(TenantMembership.keycloak_user_id == user.sub)
        .options(selectinload(TenantMembership.tenant))
    )
    memberships = [MembershipOut.model_validate(m) for m in rows.scalars().all()]
    return AuthMeOut(
        sub=user.sub,
        email=user.email,
        full_name=user.full_name,
        memberships=memberships,
    )


__all__ = ["router"]
