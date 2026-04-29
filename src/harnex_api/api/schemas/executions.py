from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from harnex_api.api.schemas.common import ApiModel
from harnex_api.db.models import ExecutionMode, ExecutionStatus


class ExecutionOut(ApiModel):
    id: UUID
    tenant_id: UUID
    connection_id: UUID | None
    mode: ExecutionMode
    status: ExecutionStatus
    operation_id: str | None
    method: str | None
    path: str | None
    request_summary: dict[str, Any]
    response_summary: dict[str, Any]
    error_kind: str | None
    error_message: str | None
    duration_ms: int | None
    created_at: datetime


__all__ = ["ExecutionOut"]
