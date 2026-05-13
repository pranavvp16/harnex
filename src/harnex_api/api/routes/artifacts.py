"""Signed download endpoint for the local-filesystem object storage backend.

Only active when the Azure backend is not configured. Reads bytes from the
``LocalFilesystemStorage`` root and streams them back. The signature in the
query string is HMAC-SHA256 over ``tenant_id|storage_key|expires``; expired or
mismatched signatures get a 404 (not a 401 — we don't want to leak which
artifacts exist).
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from harnex_api.services.object_storage.local_fs import (
    LocalFilesystemStorage,
    verify_signed_url,
)

router = APIRouter(prefix="/v1/artifacts", tags=["artifacts"], include_in_schema=False)


def _resolve_under_root(root: Path, storage_key: str) -> Path:
    """Resolve ``storage_key`` relative to ``root`` and assert containment.

    Belt-and-braces — the storage keys we mint are uuid-based so there is no
    user-controlled path component, but verifying here protects against future
    regressions.
    """
    target = (root / storage_key).resolve()
    if not str(target).startswith(str(root)):
        raise HTTPException(status_code=404, detail="not_found")
    return target


@router.get("/{tenant_id}/{storage_key:path}")
async def download_artifact(
    tenant_id: str,
    storage_key: str,
    expires: int = Query(...),
    signature: str = Query(...),
) -> FileResponse:
    if not verify_signed_url(
        tenant_id=tenant_id, storage_key=storage_key, expires=expires, signature=signature
    ):
        raise HTTPException(status_code=404, detail="not_found")
    storage = LocalFilesystemStorage()
    target = _resolve_under_root(storage.root, storage_key)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="not_found")
    media_type, _ = mimetypes.guess_type(target.name)
    return FileResponse(path=target, media_type=media_type or "application/octet-stream")


__all__ = ["router"]
