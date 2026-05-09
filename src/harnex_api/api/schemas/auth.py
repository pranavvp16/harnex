from __future__ import annotations

from pydantic import EmailStr, Field

from harnex_api.api.schemas.common import ApiModel
from harnex_api.api.schemas.tenants import MembershipOut


class RegisterIn(ApiModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    full_name: str = Field(min_length=2, max_length=128)


class RegisterOut(ApiModel):
    ok: bool = True


class AuthMeOut(ApiModel):
    sub: str
    email: str | None
    full_name: str | None
    memberships: list[MembershipOut]


__all__ = ["AuthMeOut", "RegisterIn", "RegisterOut"]
