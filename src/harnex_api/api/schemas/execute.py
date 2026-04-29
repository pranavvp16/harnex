from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from harnex_api.api.schemas.common import ApiModel
from harnex_api.db.models import ExecutionStatus


class ExecuteRequestIn(ApiModel):
    connection_id: UUID
    operation_id: str = Field(min_length=1, max_length=256)
    path_params: dict[str, Any] = Field(default_factory=dict)
    query: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None


class ExecuteResponse(ApiModel):
    status: ExecutionStatus
    http_status: int | None
    body: Any | None
    headers: dict[str, str]
    error_kind: str | None
    error_message: str | None
    duration_ms: int | None
    operation_id: str | None
    method: str | None
    path: str | None


__all__ = ["ExecuteRequestIn", "ExecuteResponse"]
