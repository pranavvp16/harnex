"""Files dashboard routes — list filters/refreshes URLs, delete cleans the row.

The DB session is mocked because the unit suite doesn't hit Postgres; the
ObjectStorage seam uses the real Protocol-backed fake so the wire-up the
handlers exercise is the same one production uses.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from fastapi import HTTPException

from harnex_api.api.dependencies.auth import TenantContext
from harnex_api.api.routes.files import delete_file, list_files
from harnex_api.db.models import (
    Execution,
    ExecutionMode,
    ExecutionStatus,
)
from harnex_api.services.object_storage.provider import set_object_storage


class _RecordingStorage:
    """ObjectStorage stub that records refresh + delete calls."""

    def __init__(self) -> None:
        self.refresh_calls: list[dict[str, Any]] = []
        self.delete_calls: list[dict[str, Any]] = []

    async def upload(self, **kwargs: Any) -> Any:
        raise AssertionError("upload should not be called from the files routes")

    async def refresh_url(
        self,
        *,
        tenant_id: UUID,
        storage_key: str,
        content_type: str,
        ttl_seconds: int,
    ) -> str:
        self.refresh_calls.append(
            {
                "tenant_id": str(tenant_id),
                "storage_key": storage_key,
                "content_type": content_type,
                "ttl_seconds": ttl_seconds,
            }
        )
        return f"https://signed.invalid/{storage_key}?expires={ttl_seconds}"

    async def delete(self, *, tenant_id: UUID, storage_key: str) -> None:
        self.delete_calls.append({"tenant_id": str(tenant_id), "storage_key": storage_key})


def _fake_execution(
    *,
    tenant_id: UUID,
    skill_key: str = "pdf",
    artifact_url: str | None = "https://stale.invalid/old",
    storage_key: str = "tenants/X/2026/05/abc/output.pdf",
    filename: str = "output.pdf",
    content_type: str = "application/pdf",
    size_bytes: int = 2755,
) -> Execution:
    row = Execution()
    row.id = uuid.uuid4()
    row.tenant_id = tenant_id
    row.connection_id = None
    row.api_key_id = None
    row.mode = ExecutionMode.skill
    row.status = ExecutionStatus.success
    row.operation_id = f"skill:{skill_key}"
    row.method = None
    row.path = None
    row.request_summary = {"skill_key": skill_key, "runtime": "python"}
    row.response_summary = {
        "download_url": "https://stale.invalid/old",
        "storage_key": storage_key,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": size_bytes,
    }
    row.error_kind = None
    row.error_message = None
    row.duration_ms = 1234
    row.artifact_url = artifact_url
    row.artifact_bytes = size_bytes
    row.created_at = datetime.now(UTC)
    row.updated_at = row.created_at
    return row


def _mock_session_for_list(rows: list[Execution]) -> Any:
    """Mock AsyncSession.execute to return the rows for the listing query."""
    session = MagicMock()
    count_result = MagicMock()
    count_result.scalar_one.return_value = len(rows)
    list_result = MagicMock()
    scalars_obj = MagicMock()
    scalars_obj.all.return_value = rows
    list_result.scalars.return_value = scalars_obj
    # `execute` is called twice: first for COUNT, then for the SELECT.
    session.execute = AsyncMock(side_effect=[count_result, list_result])
    return session


def _mock_session_for_lookup(row: Execution | None) -> Any:
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.fixture()
def storage_fake() -> _RecordingStorage:
    fake = _RecordingStorage()
    set_object_storage(fake)
    yield fake
    set_object_storage(None)  # type: ignore[arg-type]


async def test_list_files_refreshes_url_per_row(storage_fake: _RecordingStorage) -> None:
    tenant_id = uuid.uuid4()
    ctx = TenantContext(tenant_id=tenant_id, subject="dev")
    row = _fake_execution(tenant_id=tenant_id)
    session = _mock_session_for_list([row])

    page = await list_files(ctx=ctx, db=session, limit=50, offset=0, skill_key=None)

    assert page.total == 1
    assert len(page.items) == 1
    item = page.items[0]
    assert item.filename == "output.pdf"
    assert item.skill_key == "pdf"
    assert item.content_type == "application/pdf"
    assert item.size_bytes == 2755
    # The freshly-minted URL — never the stale one on the DB row.
    assert item.download_url.startswith("https://signed.invalid/")
    assert "stale.invalid" not in item.download_url
    assert len(storage_fake.refresh_calls) == 1
    assert storage_fake.refresh_calls[0]["storage_key"] == row.response_summary["storage_key"]


async def test_list_files_drops_rows_missing_storage_metadata(
    storage_fake: _RecordingStorage,
) -> None:
    tenant_id = uuid.uuid4()
    ctx = TenantContext(tenant_id=tenant_id, subject="dev")
    broken = _fake_execution(tenant_id=tenant_id)
    # Mimic a legacy row with no storage_key in response_summary.
    broken.response_summary = {"filename": "x.pdf"}
    session = _mock_session_for_list([broken])

    page = await list_files(ctx=ctx, db=session, limit=50, offset=0, skill_key=None)

    assert page.items == []
    assert storage_fake.refresh_calls == []


async def test_delete_file_removes_blob_and_nulls_pointers(
    storage_fake: _RecordingStorage,
) -> None:
    tenant_id = uuid.uuid4()
    ctx = TenantContext(tenant_id=tenant_id, subject="dev")
    row = _fake_execution(tenant_id=tenant_id)
    session = _mock_session_for_lookup(row)

    await delete_file(execution_id=row.id, ctx=ctx, db=session)

    assert storage_fake.delete_calls == [
        {
            "tenant_id": str(tenant_id),
            "storage_key": "tenants/X/2026/05/abc/output.pdf",
        }
    ]
    assert row.artifact_url is None
    assert row.artifact_bytes is None
    assert "storage_key" not in row.response_summary
    assert "download_url" not in row.response_summary
    # Other history fields stay so quota/usage stays correct.
    assert row.response_summary.get("filename") == "output.pdf"


async def test_delete_file_404_when_not_found(storage_fake: _RecordingStorage) -> None:
    tenant_id = uuid.uuid4()
    ctx = TenantContext(tenant_id=tenant_id, subject="dev")
    session = _mock_session_for_lookup(None)

    with pytest.raises(HTTPException) as exc_info:
        await delete_file(execution_id=uuid.uuid4(), ctx=ctx, db=session)
    assert exc_info.value.status_code == 404
    assert storage_fake.delete_calls == []


async def test_delete_file_409_when_already_deleted(
    storage_fake: _RecordingStorage,
) -> None:
    tenant_id = uuid.uuid4()
    ctx = TenantContext(tenant_id=tenant_id, subject="dev")
    row = _fake_execution(tenant_id=tenant_id, artifact_url=None)
    session = _mock_session_for_lookup(row)

    with pytest.raises(HTTPException) as exc_info:
        await delete_file(execution_id=row.id, ctx=ctx, db=session)
    assert exc_info.value.status_code == 409
    assert storage_fake.delete_calls == []
