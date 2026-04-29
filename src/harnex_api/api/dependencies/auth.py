from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Header, HTTPException, status

from harnex_api.config import get_settings


@dataclass(frozen=True)
class TenantContext:
    """Resolved caller identity. Populated by `get_tenant_context`.

    `subject` is whatever Phase 2 fills in from the JWT (Keycloak user id) or
    api-key id; for now in dev mode it's the literal "dev".
    """

    tenant_id: UUID
    subject: str


def _parse_uuid(raw: str | None, *, header_name: str) -> UUID:
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"missing {header_name} header",
        )
    try:
        return UUID(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid uuid in {header_name}",
        ) from exc


async def get_tenant_context(
    x_harnex_dev_tenant: str | None = Header(default=None),
) -> TenantContext:
    """Resolve the caller's tenant.

    Phase 2 will:
    - validate `Authorization: Bearer <jwt>` against Keycloak JWKS
    - extract the active tenant id from a custom claim (org/group)
    - support `X-Harnex-API-Key` for M2M

    For now, in `local`/`dev` env we accept `X-Harnex-Dev-Tenant: <uuid>` so
    the console + integration tests can drive admin routes end-to-end.
    """
    settings = get_settings()
    if settings.env in ("local", "dev"):
        return TenantContext(
            tenant_id=_parse_uuid(x_harnex_dev_tenant, header_name="X-Harnex-Dev-Tenant"),
            subject="dev",
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="auth not configured for this environment",
    )


__all__ = ["TenantContext", "get_tenant_context"]
