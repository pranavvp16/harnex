"""Tenant-isolated object storage for skill-generated artifacts.

Skills produce files (PDF, docx, xlsx, pptx) that the agent should be able to
download. Files land in object storage under a tenant-scoped key prefix and the
runner mints a short-TTL signed URL the agent can hand to the user.

Production target: Azure Blob Storage. Local dev uses a filesystem-backed
fallback that serves bytes via a signed FastAPI route.
"""

from __future__ import annotations

from harnex_api.services.object_storage.base import ObjectStorage, UploadResult
from harnex_api.services.object_storage.local_fs import LocalFilesystemStorage
from harnex_api.services.object_storage.provider import get_object_storage

__all__ = [
    "LocalFilesystemStorage",
    "ObjectStorage",
    "UploadResult",
    "get_object_storage",
]
