from __future__ import annotations

from pydantic import EmailStr, Field

from harnex_api.api.schemas.common import ApiModel
from harnex_api.api.schemas.tenants import MembershipOut


class SessionPasswordIn(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class SessionUser(ApiModel):
    sub: str
    email: str | None
    full_name: str | None


class SessionPasswordOut(ApiModel):
    ok: bool = True
    user: SessionUser
    csrf_token: str


class SessionMeOut(ApiModel):
    sub: str
    email: str | None
    full_name: str | None
    memberships: list[MembershipOut]
    csrf_token: str


__all__ = [
    "SessionMeOut",
    "SessionPasswordIn",
    "SessionPasswordOut",
    "SessionUser",
]
