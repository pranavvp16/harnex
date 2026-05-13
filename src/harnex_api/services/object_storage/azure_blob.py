"""Azure Blob Storage backend for skill-generated artifacts.

Container layout::

    <container>/tenants/<tenant_id>/<yyyy>/<mm>/<uuid>/<filename>

Tenant isolation is enforced via the key prefix and the fact that the only path
that mints a SAS URL is the skill runner, which always runs under a tenant
context. SAS URLs are scoped to the single uploaded blob, read-only, and
expire after ``ttl_seconds``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import quote
from uuid import UUID

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobSasPermissions, ContentSettings, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient

from harnex_api.services.object_storage.base import UploadResult


def _safe_filename(name: str) -> str:
    cleaned = name.replace("/", "_").replace("\\", "_").strip()
    return cleaned or "artifact"


class AzureBlobStorage:
    """Azure Blob Storage backend — short-TTL SAS URLs per upload.

    Constructor takes the resolved credential material (account name + key).
    The provider factory in :mod:`harnex_api.services.object_storage.provider`
    resolves these from settings (filled at startup, ideally via Infisical).
    """

    def __init__(
        self,
        *,
        account_name: str,
        account_key: str,
        container: str,
    ) -> None:
        self._account_name = account_name
        self._account_key = account_key
        self._container = container
        self._endpoint = f"https://{account_name}.blob.core.windows.net"

    async def upload(
        self,
        *,
        tenant_id: UUID,
        filename: str,
        data: bytes,
        content_type: str,
        ttl_seconds: int,
    ) -> UploadResult:
        now = datetime.now(UTC)
        safe_name = _safe_filename(filename)
        artifact_id = uuid.uuid4().hex
        storage_key = (
            f"tenants/{tenant_id}/{now:%Y}/{now:%m}/{artifact_id}/{safe_name}"
        )

        async with BlobServiceClient(
            account_url=self._endpoint, credential=self._account_key
        ) as service:
            blob = service.get_blob_client(container=self._container, blob=storage_key)
            await blob.upload_blob(
                data,
                overwrite=False,
                content_settings=ContentSettings(content_type=content_type),
            )

        url = self._sas_url(storage_key, ttl_seconds=ttl_seconds, now=now)
        return UploadResult(
            download_url=url,
            storage_key=storage_key,
            size_bytes=len(data),
            content_type=content_type,
        )

    def _sas_url(
        self,
        storage_key: str,
        *,
        ttl_seconds: int,
        now: datetime | None = None,
    ) -> str:
        anchor = now or datetime.now(UTC)
        sas = generate_blob_sas(
            account_name=self._account_name,
            account_key=self._account_key,
            container_name=self._container,
            blob_name=storage_key,
            permission=BlobSasPermissions(read=True),
            expiry=anchor + timedelta(seconds=max(1, ttl_seconds)),
        )
        # Re-quote the blob path so any path-segment-delimiters survive concat
        # with the SAS query string. account/container/key chars are URL-safe
        # apart from slashes, which we want to keep.
        return f"{self._endpoint}/{self._container}/{quote(storage_key, safe='/')}?{sas}"

    async def refresh_url(
        self,
        *,
        tenant_id: UUID,
        storage_key: str,
        content_type: str,
        ttl_seconds: int,
    ) -> str:
        if not storage_key.startswith(f"tenants/{tenant_id}/"):
            raise PermissionError("storage_key does not belong to this tenant")
        return self._sas_url(storage_key, ttl_seconds=ttl_seconds)

    async def delete(self, *, tenant_id: UUID, storage_key: str) -> None:
        if not storage_key.startswith(f"tenants/{tenant_id}/"):
            return
        async with BlobServiceClient(
            account_url=self._endpoint, credential=self._account_key
        ) as service:
            blob = service.get_blob_client(container=self._container, blob=storage_key)
            try:
                await blob.delete_blob()
            except ResourceNotFoundError:
                # Idempotent — match the local backend's behavior.
                return


__all__ = ["AzureBlobStorage"]
