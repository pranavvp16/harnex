from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.db import get_db
from harnex_api.config import AppSettings, get_settings
from harnex_api.db.models import TenantMembership
from harnex_api.logging import get_logger


@dataclass(frozen=True)
class TenantContext:
    """Resolved caller identity for tenant-scoped routes.

    `subject` is the Keycloak `sub` (user id) on JWT-authed requests, or the
    literal "dev" when the local-mode `X-Harnex-Dev-Tenant` fallback is used.
    """

    tenant_id: UUID
    subject: str


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identity resolved purely from a verified Keycloak JWT.

    Used by routes that need the caller's identity but do not yet have a
    tenant context — onboarding (`POST /v1/tenants`) and `/v1/auth/me`.
    """

    sub: str
    email: str | None
    full_name: str | None


class _JwksCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._keys: list[dict[str, Any]] | None = None
        self._fetched_at: float = 0.0

    async def get(self, jwks_url: str) -> list[dict[str, Any]]:
        now = time.monotonic()
        if self._keys is not None and (now - self._fetched_at) < self._ttl:
            return self._keys
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(jwks_url)
            resp.raise_for_status()
            payload = resp.json()
        self._keys = list(payload.get("keys", []))
        self._fetched_at = now
        return self._keys

    def invalidate(self) -> None:
        self._keys = None
        self._fetched_at = 0.0


_jwks_cache: _JwksCache | None = None


def _get_jwks_cache(settings: AppSettings) -> _JwksCache:
    global _jwks_cache
    if _jwks_cache is None:
        _jwks_cache = _JwksCache(settings.keycloak_jwks_cache_seconds)
    return _jwks_cache


def _jwks_url(settings: AppSettings) -> str:
    return (
        f"{settings.keycloak_base_url.rstrip('/')}"
        f"/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
    )


def _issuer(settings: AppSettings) -> str:
    base = settings.keycloak_issuer_base_url or settings.keycloak_base_url
    return f"{base.rstrip('/')}/realms/{settings.keycloak_realm}"


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        return None
    return parts[1].strip()


async def _verify_jwt(token: str, settings: AppSettings) -> dict[str, Any]:
    cache = _get_jwks_cache(settings)
    try:
        keys = await cache.get(_jwks_url(settings))
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="auth provider unreachable",
        ) from exc

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="malformed token",
        ) from exc

    kid = unverified_header.get("kid")
    matching = next((k for k in keys if k.get("kid") == kid), None)
    if matching is None:
        # Key rotation — invalidate cache and refetch once before giving up.
        cache.invalidate()
        try:
            keys = await cache.get(_jwks_url(settings))
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="auth provider unreachable",
            ) from exc
        matching = next((k for k in keys if k.get("kid") == kid), None)
    if matching is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="signing key not found",
        )

    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            matching,
            algorithms=[matching.get("alg", "RS256")],
            audience=settings.keycloak_audience,
            issuer=_issuer(settings),
            options={"verify_at_hash": False},
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token expired",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token: {exc}",
        ) from exc
    return claims


def _user_from_claims(claims: dict[str, Any]) -> AuthenticatedUser:
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token missing sub claim",
        )
    email = claims.get("email")
    name = claims.get("name") or claims.get("preferred_username")
    return AuthenticatedUser(
        sub=sub,
        email=email if isinstance(email, str) else None,
        full_name=name if isinstance(name, str) else None,
    )


async def get_authenticated_user(
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser:
    """Require a valid Keycloak JWT; return the user identity."""
    settings = get_settings()
    token = _bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )
    claims = await _verify_jwt(token, settings)
    return _user_from_claims(claims)


def _parse_uuid(raw: str, *, header_name: str) -> UUID:
    try:
        return UUID(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid uuid in {header_name}",
        ) from exc


async def _resolve_tenant_for_user(
    db: AsyncSession,
    *,
    sub: str,
    requested_tenant_id: UUID | None,
) -> UUID:
    rows = await db.execute(
        select(TenantMembership).where(TenantMembership.keycloak_user_id == sub)
    )
    memberships = list(rows.scalars().all())
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "no_tenant", "needs_onboarding": True},
        )
    if requested_tenant_id is not None:
        for m in memberships:
            if m.tenant_id == requested_tenant_id:
                return requested_tenant_id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not a member of the requested tenant",
        )
    return memberships[0].tenant_id


async def get_tenant_context(
    authorization: str | None = Header(default=None),
    x_harnex_tenant: str | None = Header(default=None),
    x_harnex_dev_tenant: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
    """Resolve the caller's tenant for a tenant-scoped route.

    Order:
    1. `Authorization: Bearer <jwt>` → verify against Keycloak JWKS, look up
       a `TenantMembership` for the `sub`. `X-Harnex-Tenant: <uuid>` picks
       a workspace when the user belongs to several.
    2. (local / compose dev only, no Authorization header)
       `X-Harnex-Dev-Tenant: <uuid>` → tenant id taken verbatim, subject="dev".
       Keeps integration tests, the local SPA, and `docker compose` (default
       `HARNEX_ENV=dev`) working without a real Keycloak. The gate is
       `HARNEX_ENV` ∈ {`local`, `dev`}; staging/production ignore the header.
    3. Otherwise → 401.
    """
    settings = get_settings()
    log = get_logger("harnex_api.auth")
    token = _bearer_token(authorization)
    if token:
        claims = await _verify_jwt(token, settings)
        user = _user_from_claims(claims)
        requested = (
            _parse_uuid(x_harnex_tenant, header_name="X-Harnex-Tenant")
            if x_harnex_tenant
            else None
        )
        tenant_id = await _resolve_tenant_for_user(
            db, sub=user.sub, requested_tenant_id=requested
        )
        return TenantContext(tenant_id=tenant_id, subject=user.sub)

    if settings.env in ("local", "dev") and x_harnex_dev_tenant:
        return TenantContext(
            tenant_id=_parse_uuid(x_harnex_dev_tenant, header_name="X-Harnex-Dev-Tenant"),
            subject="dev",
        )
    if x_harnex_dev_tenant and settings.env not in ("local", "dev"):
        # Make the failure mode explicit so a confused deploy notices fast.
        log.warning(
            "dev_tenant_header_rejected",
            env=settings.env,
            reason="X-Harnex-Dev-Tenant only honored when HARNEX_ENV is local or dev",
        )

    log.warning(
        "auth_missing",
        env=settings.env,
        has_authorization=authorization is not None,
        has_dev_tenant=x_harnex_dev_tenant is not None,
        has_tenant_header=x_harnex_tenant is not None,
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="missing bearer token",
    )


__all__ = [
    "AuthenticatedUser",
    "TenantContext",
    "get_authenticated_user",
    "get_tenant_context",
]
