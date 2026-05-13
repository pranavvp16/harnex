"""Files dashboard — list / refresh-download / delete skill-generated artifacts.

Backed by the `executions` table: skill runs already record `artifact_url`,
`artifact_bytes`, and the canonical `storage_key`/`filename`/`content_type`
in `response_summary`. This module surfaces those rows to the console UI and
re-mints the signed URL on every list call so click-through always works.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.common import Page
from harnex_api.api.schemas.files import FileItem
from harnex_api.config import get_settings
from harnex_api.db.models import Execution, ExecutionMode
from harnex_api.logging import get_logger
from harnex_api.services.object_storage import ObjectStorage, get_object_storage

router = APIRouter(prefix="/v1/files", tags=["files"])
_log = get_logger(__name__)


def _skill_key_from_operation_id(operation_id: str | None) -> str:
    # skill_runner stores it as f"skill:{skill.key}"; tolerate the raw key too.
    if not operation_id:
        return ""
    return operation_id.removeprefix("skill:") if operation_id.startswith("skill:") else operation_id


def _summary_str(summary: dict[str, Any], key: str) -> str:
    val = summary.get(key)
    return val if isinstance(val, str) else ""


def _summary_int(summary: dict[str, Any], key: str) -> int:
    val = summary.get(key)
    return val if isinstance(val, int) else 0


async def _build_file_item(
    row: Execution,
    *,
    storage: ObjectStorage,
    ttl_seconds: int,
) -> FileItem | None:
    """Return None when the Execution row is missing the bits we need to serve.

    Defensive — every skill execution that writes ``artifact_url`` should also
    write the storage_key/filename/content_type triple, but if a legacy row is
    incomplete we'd rather drop it than crash the list call.
    """
    summary = row.response_summary or {}
    storage_key = _summary_str(summary, "storage_key")
    filename = _summary_str(summary, "filename")
    content_type = _summary_str(summary, "content_type") or "application/octet-stream"
    if not storage_key or not filename:
        return None
    try:
        download_url = await storage.refresh_url(
            tenant_id=row.tenant_id,
            storage_key=storage_key,
            content_type=content_type,
            ttl_seconds=ttl_seconds,
        )
    except Exception as exc:
        # Azure raises PermissionError for cross-tenant storage_keys; either backend
        # can raise on transient network errors. Drop the row instead of 500ing the
        # whole listing — same defensive posture as the missing-metadata branch above.
        _log.warning(
            "file_refresh_url_failed",
            execution_id=str(row.id),
            storage_key=storage_key,
            error=str(exc),
        )
        return None
    return FileItem(
        id=row.id,
        filename=filename,
        content_type=content_type,
        size_bytes=row.artifact_bytes or _summary_int(summary, "size_bytes"),
        skill_key=_skill_key_from_operation_id(row.operation_id),
        download_url=download_url,
        download_url_expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        created_at=row.created_at,
    )


@router.get("", response_model=Page[FileItem])
async def list_files(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    skill_key: str | None = Query(None, description="Filter to one skill (e.g. 'pdf')."),
) -> Page[FileItem]:
    settings = get_settings()
    base = select(Execution).where(
        Execution.tenant_id == ctx.tenant_id,
        Execution.mode == ExecutionMode.skill,
        Execution.artifact_url.is_not(None),
    )
    if skill_key:
        base = base.where(Execution.operation_id == f"skill:{skill_key}")

    total_row = await db.execute(select(func.count()).select_from(base.subquery()))
    total = int(total_row.scalar_one())

    rows = await db.execute(
        base.order_by(Execution.created_at.desc()).limit(limit).offset(offset)
    )
    storage = get_object_storage()
    items: list[FileItem] = []
    dropped = 0
    for r in rows.scalars().all():
        item = await _build_file_item(
            r, storage=storage, ttl_seconds=settings.skill_download_url_ttl_seconds
        )
        if item is None:
            dropped += 1
            continue
        items.append(item)
    # Rows we just dropped (missing storage_key/filename or a backend refresh
    # error) shouldn't inflate the count the client uses to drive its "Next"
    # button — otherwise hasNext stays true on a page that would render empty.
    return Page(items=items, total=max(0, total - dropped), limit=limit, offset=offset)


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    execution_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    row = (
        await db.execute(
            select(Execution).where(
                Execution.id == execution_id,
                Execution.tenant_id == ctx.tenant_id,
                Execution.mode == ExecutionMode.skill,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file not found")
    if row.artifact_url is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="file already deleted"
        )

    summary = row.response_summary or {}
    storage_key = _summary_str(summary, "storage_key")
    if storage_key:
        storage = get_object_storage()
        try:
            await storage.delete(tenant_id=ctx.tenant_id, storage_key=storage_key)
        except Exception as exc:
            # Backend delete failed — don't null the row, so the operator can
            # retry once the underlying issue is fixed.
            _log.exception(
                "file_delete_storage_error",
                execution_id=str(execution_id),
                storage_key=storage_key,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="object storage delete failed",
            ) from exc

    row.artifact_url = None
    row.artifact_bytes = None
    new_summary = dict(summary)
    new_summary.pop("storage_key", None)
    new_summary.pop("download_url", None)
    row.response_summary = new_summary


__all__ = ["router"]
