"""Verify a tenant-issued API key against the api_keys table.

Used by the MCP server and any future M2M REST endpoints. Keeps the verifier
in services/ (not api/dependencies/) because the MCP transport doesn't run
through FastAPI's Depends machinery.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.db.models import ApiKey
from harnex_api.services.api_keys import parse_prefix, verify_key


@dataclass(frozen=True)
class ApiKeyAuth:
    api_key_id: UUID
    tenant_id: UUID


class ApiKeyAuthError(Exception):
    """Raised when the supplied plaintext key is unknown or revoked."""


async def authenticate_key(session: AsyncSession, plaintext: str) -> ApiKeyAuth:
    prefix = parse_prefix(plaintext)
    if not prefix:
        raise ApiKeyAuthError("malformed api key")

    rows = await session.execute(
        select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True))
    )
    candidates = list(rows.scalars().all())
    for row in candidates:
        if verify_key(plaintext, row.key_hash):
            row.last_used_at = datetime.now(UTC)
            return ApiKeyAuth(api_key_id=row.id, tenant_id=row.tenant_id)

    raise ApiKeyAuthError("invalid api key")


__all__ = ["ApiKeyAuth", "ApiKeyAuthError", "authenticate_key"]
