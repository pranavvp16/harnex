from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from harnex_api.api.schemas.common import ApiModel


class ApiKeyCreate(ApiModel):
    name: str = Field(min_length=1, max_length=128)


class ApiKeyOut(ApiModel):
    id: UUID
    tenant_id: UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime


class ApiKeyIssued(ApiKeyOut):
    """Returned exactly once on creation. The plaintext is never recoverable later."""

    plaintext: str


__all__ = ["ApiKeyCreate", "ApiKeyIssued", "ApiKeyOut"]
