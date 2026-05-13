"""LocalFilesystemStorage — round-trip upload → refresh_url → delete."""

from __future__ import annotations

import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from harnex_api.services.object_storage.local_fs import (
    LocalFilesystemStorage,
    verify_signed_url,
)


async def test_upload_then_refresh_url_signs_fresh(tmp_path: Path) -> None:
    storage = LocalFilesystemStorage(root=tmp_path)
    tenant_id = uuid.uuid4()
    upload = await storage.upload(
        tenant_id=tenant_id,
        filename="report.pdf",
        data=b"%PDF-fake\n",
        content_type="application/pdf",
        ttl_seconds=60,
    )
    assert (tmp_path / upload.storage_key).is_file()

    refreshed = await storage.refresh_url(
        tenant_id=tenant_id,
        storage_key=upload.storage_key,
        content_type="application/pdf",
        ttl_seconds=120,
    )
    parsed = urlparse(refreshed)
    params = parse_qs(parsed.query)
    assert "expires" in params and "signature" in params
    expires = int(params["expires"][0])
    signature = params["signature"][0]
    assert verify_signed_url(
        tenant_id=str(tenant_id),
        storage_key=upload.storage_key,
        expires=expires,
        signature=signature,
    )


async def test_delete_removes_file(tmp_path: Path) -> None:
    storage = LocalFilesystemStorage(root=tmp_path)
    tenant_id = uuid.uuid4()
    upload = await storage.upload(
        tenant_id=tenant_id,
        filename="x.xlsx",
        data=b"abc",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ttl_seconds=60,
    )
    target = tmp_path / upload.storage_key
    assert target.is_file()

    await storage.delete(tenant_id=tenant_id, storage_key=upload.storage_key)
    assert not target.exists()


async def test_delete_is_idempotent(tmp_path: Path) -> None:
    storage = LocalFilesystemStorage(root=tmp_path)
    tenant_id = uuid.uuid4()
    # Deleting a key that was never uploaded is a no-op, not an error.
    await storage.delete(
        tenant_id=tenant_id,
        storage_key=f"tenants/{tenant_id}/2026/05/missing/file.bin",
    )


async def test_delete_rejects_cross_tenant_key(tmp_path: Path) -> None:
    storage = LocalFilesystemStorage(root=tmp_path)
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    upload = await storage.upload(
        tenant_id=tenant_a,
        filename="secret.txt",
        data=b"shh",
        content_type="text/plain",
        ttl_seconds=60,
    )
    # Tenant B must not be able to delete tenant A's blob even with the right key.
    await storage.delete(tenant_id=tenant_b, storage_key=upload.storage_key)
    assert (tmp_path / upload.storage_key).is_file()
