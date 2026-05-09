from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from harnex_api.api.schemas.common import ApiModel
from harnex_api.db.models import TenantPlan, TenantRole

ALLOWED_TEAM_SIZES = ("Just me", "2-10", "11-50", "51+")


class ProfileInput(ApiModel):
    """Identity captured during onboarding before a workspace exists."""

    full_name: str = Field(min_length=2, max_length=128)
    handle: str | None = Field(default=None, max_length=64)
    email: EmailStr | None = None


class TenantCreate(ApiModel):
    display_name: str = Field(min_length=2, max_length=200)
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
    )
    team_size: str | None = None
    profile: ProfileInput


class TenantOut(ApiModel):
    id: UUID
    slug: str
    display_name: str
    plan: TenantPlan
    created_at: datetime


class MembershipOut(ApiModel):
    id: UUID
    tenant_id: UUID
    email: str | None
    role: TenantRole
    tenant: TenantOut


class UserOut(ApiModel):
    """The caller as identified by the request — JWT in prod, dev header in local."""

    id: str
    email: str | None
    full_name: str | None


class MeOut(ApiModel):
    user: UserOut
    memberships: list[MembershipOut]
    current_tenant_id: UUID | None


class SlugCheck(ApiModel):
    slug: str
    available: bool


__all__ = [
    "ALLOWED_TEAM_SIZES",
    "MeOut",
    "MembershipOut",
    "ProfileInput",
    "SlugCheck",
    "TenantCreate",
    "TenantOut",
    "UserOut",
]
