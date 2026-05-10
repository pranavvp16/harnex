"""Live Infisical round-trip + cross-tenant isolation test.

Skipped when INFISICAL_* envs are empty (the common local-dev case). When the
envs are populated, this test asserts the *behavioral* property the
path-namespacing scheme is supposed to give us: a read scoped to tenant A's
path must never surface tenant B's secret.

Mark: `integration` (excluded from unit runs, opt-in via `pytest tests/integration`).
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from harnex_api.auth.vault import InfisicalVault, connection_secret_path
from harnex_api.config import get_settings

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (
            os.environ.get("INFISICAL_PROJECT_ID")
            and os.environ.get("INFISICAL_CLIENT_ID")
            and os.environ.get("INFISICAL_CLIENT_SECRET")
        ),
        reason="INFISICAL_* envs unset — skipping live vault test",
    ),
]


@pytest.fixture
async def vault() -> AsyncIterator[InfisicalVault]:
    settings = get_settings()
    yield InfisicalVault(
        base_url=settings.infisical_base_url,
        project_id=settings.infisical_project_id,
        environment=settings.infisical_environment,
        client_id=settings.infisical_client_id.get_secret_value(),
        client_secret=settings.infisical_client_secret.get_secret_value(),
    )


async def test_round_trip(vault: InfisicalVault) -> None:
    """Sanity: write -> read -> delete -> read returns None."""
    path = f"smoke/round-trip/{uuid4()}"
    try:
        await vault.set_secret(path, {"k": "v1"})
        assert await vault.get_secret(path) == {"k": "v1"}
        await vault.delete_secret(path)
        assert await vault.get_secret(path) is None
    finally:
        await vault.delete_secret(path)


async def test_cross_tenant_isolation(vault: InfisicalVault) -> None:
    """The path scheme must keep tenant A and tenant B's secrets separate.

    Two writes under distinct `tenants/{id}/connections/{id}` paths must
    produce distinct, non-overlapping reads. A read against tenant A's path
    must never surface tenant B's value.
    """
    tenant_a = str(uuid4())
    tenant_b = str(uuid4())
    conn = str(uuid4())
    path_a = connection_secret_path(tenant_a, conn)
    path_b = connection_secret_path(tenant_b, conn)
    try:
        await vault.set_secret(path_a, {"token": "tokA"})
        await vault.set_secret(path_b, {"token": "tokB"})

        got_a = await vault.get_secret(path_a)
        got_b = await vault.get_secret(path_b)
        assert got_a == {"token": "tokA"}
        assert got_b == {"token": "tokB"}

        # Deleting one tenant's secret must not affect the other's.
        await vault.delete_secret(path_a)
        assert await vault.get_secret(path_a) is None
        assert await vault.get_secret(path_b) == {"token": "tokB"}
    finally:
        await vault.delete_secret(path_a)
        await vault.delete_secret(path_b)
