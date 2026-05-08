"""Verify a tenant-issued API key against the api_keys table.

Used by the MCP server and any future M2M REST endpoints. Keeps the verifier
in services/ (not api/dependencies/) because the MCP transport doesn't run
through FastAPI's Depends machinery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.db.models import ApiKey
from harnex_api.services.api_keys import parse_prefix, verify_key


@dataclass(frozen=True)
class ApiKeyAuth:
    api_key_id: UUID
    tenant_id: UUID
    scope_type: str = "all"
    scope_connection_ids: tuple[UUID, ...] = field(default_factory=tuple)

    def allows_connection(self, connection_id: UUID) -> bool:
        if self.scope_type == "all":
            return True
        return connection_id in self.scope_connection_ids


class ApiKeyAuthError(Exception):
    """Raised when the supplied plaintext key is unknown, revoked, or expired."""


def _scope_tuple(scope: dict[str, Any] | None) -> tuple[str, tuple[UUID, ...]]:
    if not scope:
        return ("all", ())
    stype = str(scope.get("type") or "all")
    if stype == "all":
        return ("all", ())
    raw_ids = scope.get("connection_ids") or []
    parsed: list[UUID] = []
    for raw in raw_ids:
        try:
            parsed.append(UUID(str(raw)))
        except (TypeError, ValueError):
            continue
    return (stype, tuple(parsed))


async def authenticate_key(session: AsyncSession, plaintext: str) -> ApiKeyAuth:
    prefix = parse_prefix(plaintext)
    if not prefix:
        raise ApiKeyAuthError("malformed api key")

    rows = await session.execute(
        select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True))
    )
    candidates = list(rows.scalars().all())
    now = datetime.now(UTC)
    for row in candidates:
        if not verify_key(plaintext, row.key_hash):
            continue
        if row.expires_at is not None and row.expires_at <= now:
            raise ApiKeyAuthError("api key expired")
        row.last_used_at = now
        scope_type, scope_ids = _scope_tuple(row.scope)
        return ApiKeyAuth(
            api_key_id=row.id,
            tenant_id=row.tenant_id,
            scope_type=scope_type,
            scope_connection_ids=scope_ids,
        )

    raise ApiKeyAuthError("invalid api key")


__all__ = ["ApiKeyAuth", "ApiKeyAuthError", "authenticate_key"]
