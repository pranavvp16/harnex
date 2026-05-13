from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class UploadResult:
    """Outcome of a successful object upload.

    ``download_url`` is a short-TTL signed URL the caller can hand to a user;
    ``storage_key`` is the canonical, tenant-prefixed key inside the bucket
    (useful for audit / re-download).
    """

    download_url: str
    storage_key: str
    size_bytes: int
    content_type: str


class ObjectStorage(Protocol):
    async def upload(
        self,
        *,
        tenant_id: UUID,
        filename: str,
        data: bytes,
        content_type: str,
        ttl_seconds: int,
    ) -> UploadResult: ...

    async def refresh_url(
        self,
        *,
        tenant_id: UUID,
        storage_key: str,
        content_type: str,
        ttl_seconds: int,
    ) -> str:
        """Mint a fresh short-TTL signed download URL for an existing object.

        Used by the files dashboard — the URL on the Execution row was minted
        at upload time and almost always expired by the time the user opens
        the page. Re-signing avoids storing long-lived URLs in the DB.
        """
        ...

    async def delete(self, *, tenant_id: UUID, storage_key: str) -> None:
        """Remove the object at ``storage_key``.

        Idempotent: deleting an already-deleted key returns successfully so
        the caller's row-update path doesn't need to special-case the gap
        between blob deletion and DB update.
        """
        ...
