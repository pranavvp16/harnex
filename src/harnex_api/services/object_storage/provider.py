from __future__ import annotations

from harnex_api.config import get_settings
from harnex_api.logging import get_logger
from harnex_api.services.object_storage.azure_blob import AzureBlobStorage
from harnex_api.services.object_storage.base import ObjectStorage
from harnex_api.services.object_storage.local_fs import LocalFilesystemStorage

_log = get_logger(__name__)
_singleton: ObjectStorage | None = None


def get_object_storage() -> ObjectStorage:
    """Return the configured object storage backend.

    Resolves once per process. Uses Azure Blob when ``HARNEX_AZURE_STORAGE_ACCOUNT``
    + ``HARNEX_AZURE_STORAGE_KEY`` are populated; otherwise falls back to the
    local filesystem backend (suitable for dev/tests only).
    """
    global _singleton
    if _singleton is not None:
        return _singleton

    settings = get_settings()
    account = getattr(settings, "azure_storage_account", "")
    key_secret = getattr(settings, "azure_storage_key", None)
    container = getattr(settings, "azure_storage_container", "harnex-artifacts")
    key = key_secret.get_secret_value() if key_secret is not None else ""

    if account and key:
        _log.info("object_storage", backend="azure_blob", container=container)
        _singleton = AzureBlobStorage(
            account_name=account, account_key=key, container=container
        )
    else:
        _log.warning(
            "object_storage_local_fallback",
            hint="set HARNEX_AZURE_STORAGE_ACCOUNT + HARNEX_AZURE_STORAGE_KEY for production",
        )
        _singleton = LocalFilesystemStorage()
    return _singleton


def set_object_storage(storage: ObjectStorage) -> None:
    """Test seam — install a deterministic in-memory backend."""
    global _singleton
    _singleton = storage


__all__ = ["get_object_storage", "set_object_storage"]
