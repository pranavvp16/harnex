from __future__ import annotations

from datetime import datetime
from uuid import UUID

from harnex_api.api.schemas.common import ApiModel


class FileItem(ApiModel):
    """One row in the files dashboard.

    ``download_url`` is freshly minted on every list call — the URL stored on
    the Execution row at upload time is almost always expired by the time the
    user opens the page.
    """

    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    skill_key: str
    download_url: str
    download_url_expires_at: datetime
    created_at: datetime


__all__ = ["FileItem"]
