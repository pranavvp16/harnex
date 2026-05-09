"""Create a tenant + owner membership during onboarding.

In dev/local, the caller is anonymous (no JWT) — the owner identity comes
from the onboarding payload. In prod, the API route should resolve the
Keycloak user id from the bearer JWT and pass it to `create_tenant_with_owner`.
"""

from __future__ import annotations

import re
import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.db.models import Tenant, TenantMembership, TenantPlan, TenantRole

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_MIN_SLUG_LEN = 2
_MAX_SLUG_LEN = 48
_SLUG_RETRIES = 6


def slugify(text: str) -> str:
    """Produce a URL-safe slug from a display name. Empty → 'workspace'."""
    cleaned = _SLUG_RE.sub("-", text.strip().lower()).strip("-")
    if len(cleaned) < _MIN_SLUG_LEN:
        return "workspace"
    return cleaned[:_MAX_SLUG_LEN]


async def slug_available(session: AsyncSession, slug: str) -> bool:
    existing = await session.execute(select(Tenant.id).where(Tenant.slug == slug))
    return existing.first() is None


async def _next_slug_candidate(session: AsyncSession, base: str) -> str:
    if await slug_available(session, base):
        return base
    for _ in range(_SLUG_RETRIES):
        suffix = secrets.token_hex(2)
        candidate = f"{base[: _MAX_SLUG_LEN - len(suffix) - 1]}-{suffix}"
        if await slug_available(session, candidate):
            return candidate
    # Last resort — random tail. Almost certainly unique.
    return f"ws-{secrets.token_hex(6)}"


async def create_tenant_with_owner(
    session: AsyncSession,
    *,
    display_name: str,
    requested_slug: str | None,
    owner_user_id: str,
    owner_email: str | None,
) -> Tenant:
    """Create a tenant and an owner membership in one transaction.

    Slug resolution: requested_slug wins if available; otherwise we slugify
    the display name and add a short suffix on collision.
    """
    base = (requested_slug or slugify(display_name)).lower()
    slug = await _next_slug_candidate(session, base)

    tenant = Tenant(
        slug=slug,
        display_name=display_name,
        plan=TenantPlan.free,
        is_active=True,
    )
    session.add(tenant)
    try:
        await session.flush()
    except IntegrityError:
        # Race on slug uniqueness — retry once with a fresh suffix.
        await session.rollback()
        slug = await _next_slug_candidate(session, base)
        tenant = Tenant(
            slug=slug,
            display_name=display_name,
            plan=TenantPlan.free,
            is_active=True,
        )
        session.add(tenant)
        await session.flush()

    membership = TenantMembership(
        tenant_id=tenant.id,
        keycloak_user_id=owner_user_id,
        email=owner_email,
        role=TenantRole.owner,
    )
    session.add(membership)
    await session.flush()
    return tenant


__all__ = ["create_tenant_with_owner", "slug_available", "slugify"]
