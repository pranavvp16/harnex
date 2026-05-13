"""Object-storage provider — fail fast when Azure isn't configured in staging/prod.

LocalFilesystemStorage writes to one pod's ephemeral disk, so a multi-replica
staging/prod deployment that silently falls back to it would serve 404s for
any download minted from a different pod. The provider raises at first call
in those environments rather than booting half-broken.
"""

from __future__ import annotations

import pytest

from harnex_api.config import get_settings
from harnex_api.services.object_storage import provider


@pytest.fixture(autouse=True)
def _reset_singleton_and_settings() -> None:
    provider._singleton = None
    get_settings.cache_clear()
    yield
    provider._singleton = None
    get_settings.cache_clear()


def _force_env(monkeypatch: pytest.MonkeyPatch, env: str) -> None:
    """Force HARNEX_ENV without touching the rest of the env."""
    monkeypatch.setenv("HARNEX_ENV", env)
    monkeypatch.setenv("HARNEX_AZURE_STORAGE_ACCOUNT", "")
    monkeypatch.setenv("HARNEX_AZURE_STORAGE_KEY", "")
    get_settings.cache_clear()


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_provider_raises_in_persistent_env_without_azure(
    monkeypatch: pytest.MonkeyPatch, env: str
) -> None:
    _force_env(monkeypatch, env)
    with pytest.raises(RuntimeError, match="Azure Blob Storage is required"):
        provider.get_object_storage()


@pytest.mark.parametrize("env", ["local", "dev"])
def test_provider_falls_back_to_local_in_dev(
    monkeypatch: pytest.MonkeyPatch, env: str
) -> None:
    _force_env(monkeypatch, env)
    storage = provider.get_object_storage()
    from harnex_api.services.object_storage.local_fs import LocalFilesystemStorage

    assert isinstance(storage, LocalFilesystemStorage)
