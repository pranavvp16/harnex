from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from harnex_api.api.schemas.common import ApiModel
from harnex_api.db.models import AuthFlow, ConnectionMode, ConnectionStatus


class ConnectionCreate(ApiModel):
    name: str = Field(min_length=1, max_length=128)
    mode: ConnectionMode
    connector_key: str | None = None
    base_url: str | None = Field(default=None, max_length=512)
    spec_url: str | None = Field(default=None, max_length=2048)
    auth_flow: AuthFlow = AuthFlow.none
    auth_config: dict[str, Any] = Field(default_factory=dict)
    # Plaintext secrets routed to Infisical, never persisted in the DB row.
    credentials: dict[str, str] = Field(default_factory=dict)


class ConnectionOut(ApiModel):
    id: UUID
    tenant_id: UUID
    connector_key: str | None
    name: str
    mode: ConnectionMode
    status: ConnectionStatus
    base_url: str | None
    spec_url: str | None
    auth_flow: AuthFlow
    auth_config: dict[str, Any]
    endpoint_count: int
    last_indexed_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class ReindexResult(ApiModel):
    connection_id: UUID
    operation_count: int
    chunk_count: int
    spec_hash: str | None


__all__ = ["ConnectionCreate", "ConnectionOut", "ReindexResult"]
