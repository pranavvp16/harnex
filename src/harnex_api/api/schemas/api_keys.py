from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from harnex_api.api.schemas.common import ApiModel


class ApiKeyScope(ApiModel):
    """Restricts which connections a key may execute against.

    `type="all"` is the default and grants access to every connection in the
    tenant. `type="connections"` restricts the key to the listed connection ids.
    """

    type: Literal["all", "connections"] = "all"
    connection_ids: list[UUID] = Field(default_factory=list)

    @field_validator("connection_ids", mode="after")
    @classmethod
    def _no_dupes(cls, v: list[UUID]) -> list[UUID]:
        # Order-preserving dedupe; FastAPI tolerates duplicates from forms.
        seen: set[UUID] = set()
        out: list[UUID] = []
        for item in v:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out


class ApiKeyCreate(ApiModel):
    name: str = Field(min_length=1, max_length=128)
    scope: ApiKeyScope = Field(default_factory=ApiKeyScope)
    # None = never expires. Capped at 10 years to discourage perma-keys.
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class ApiKeyOut(ApiModel):
    id: UUID
    tenant_id: UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    expires_at: datetime | None
    scope: ApiKeyScope


class ApiKeyIssued(ApiKeyOut):
    """Returned exactly once on creation. The plaintext is never recoverable later."""

    plaintext: str


__all__ = ["ApiKeyCreate", "ApiKeyIssued", "ApiKeyOut", "ApiKeyScope"]
