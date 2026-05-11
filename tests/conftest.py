from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

# Force fakes for tests so we don't need Azure / Infisical / Postgres / Keycloak.
os.environ.setdefault("HARNEX_ENV", "local")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/harnex_test")
os.environ.setdefault("HARNEX_USE_FAKE_EMBEDDINGS", "1")
os.environ.setdefault("HARNEX_USE_FAKE_VECTOR_SEARCH", "1")
os.environ.setdefault("AZURE_OPENAI_EMBEDDING_DIM", "64")
os.environ.setdefault("HARNEX_REDIS_URL", "")

from harnex_api.api.dependencies.rate_limit import reset_redis_client
from harnex_api.auth.vault import InMemoryVault, set_vault
from harnex_api.config import get_settings

# Reset cached settings to pick up the fake env above on first access.
get_settings.cache_clear()  # type: ignore[attr-defined]
reset_redis_client()


@pytest.fixture(autouse=True)
def _isolated_vault() -> Iterator[None]:
    """Force a fresh InMemoryVault for every test.

    Without this, tests inherit whatever vault was last installed at module
    import time — and a populated `.env` would silently route writes to the real
    Infisical instance. Per-test reset also prevents cross-test leakage.
    """
    set_vault(InMemoryVault())
    yield
