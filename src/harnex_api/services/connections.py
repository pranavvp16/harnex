from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.auth.vault import connection_secret_path, get_vault
from harnex_api.connectors.base import ConnectionConfig, LoadedSpec
from harnex_api.connectors.registry import register_builtins, registry
from harnex_api.db.models import (
    AuthFlow,
    Connection,
    ConnectionMode,
    ConnectionStatus,
)
from harnex_api.services.ingestion.fetcher import (
    SpecFetchError,
    SpecValidationError,
    fetch_spec_from_url,
    parse_uploaded_spec,
)
from harnex_api.services.ingestion.pipeline import IndexResult, index_spec


class ConnectionInputError(ValueError):
    """User-facing 400-class validation error."""


@dataclass(frozen=True)
class ConnectionCreateInput:
    name: str
    mode: ConnectionMode
    connector_key: str | None
    base_url: str | None
    spec_url: str | None
    auth_flow: AuthFlow
    auth_config: dict[str, Any]
    credentials: dict[str, str]


def _validate_input(data: ConnectionCreateInput) -> None:
    if data.mode == ConnectionMode.builtin and not data.connector_key:
        raise ConnectionInputError("builtin mode requires connector_key")
    if data.mode == ConnectionMode.openapi_url and not data.spec_url:
        raise ConnectionInputError("openapi_url mode requires spec_url")
    if data.mode == ConnectionMode.bare_url and not data.base_url:
        raise ConnectionInputError("bare_url mode requires base_url")
    if data.connector_key:
        register_builtins()
        if not registry.has(data.connector_key) and data.mode == ConnectionMode.builtin:
            raise ConnectionInputError(f"unknown connector_key: {data.connector_key}")


async def create_connection(
    session: AsyncSession, *, tenant_id: UUID, data: ConnectionCreateInput
) -> Connection:
    _validate_input(data)
    conn = Connection(
        tenant_id=tenant_id,
        connector_key=data.connector_key,
        name=data.name,
        mode=data.mode,
        status=ConnectionStatus.pending,
        base_url=data.base_url,
        spec_url=data.spec_url,
        auth_flow=data.auth_flow,
        auth_config=data.auth_config,
    )
    session.add(conn)
    await session.flush()  # populate conn.id

    if data.credentials:
        await get_vault().set_secret(
            connection_secret_path(str(tenant_id), str(conn.id)),
            data.credentials,
        )
    return conn


async def list_connections(session: AsyncSession, *, tenant_id: UUID) -> list[Connection]:
    rows = await session.execute(
        select(Connection)
        .where(Connection.tenant_id == tenant_id)
        .order_by(Connection.created_at.desc())
    )
    return list(rows.scalars().all())


async def get_connection(
    session: AsyncSession, *, tenant_id: UUID, connection_id: UUID
) -> Connection | None:
    row = await session.execute(
        select(Connection).where(
            Connection.id == connection_id, Connection.tenant_id == tenant_id
        )
    )
    return row.scalar_one_or_none()


async def delete_connection(
    session: AsyncSession, *, tenant_id: UUID, connection_id: UUID
) -> bool:
    conn = await get_connection(session, tenant_id=tenant_id, connection_id=connection_id)
    if conn is None:
        return False
    # Vault delete is best-effort — DB row deletion is the source of truth.
    with contextlib.suppress(Exception):
        await get_vault().delete_secret(connection_secret_path(str(tenant_id), str(connection_id)))
    await session.delete(conn)
    return True


def _to_config(conn: Connection) -> ConnectionConfig:
    return ConnectionConfig(
        id=str(conn.id),
        tenant_id=str(conn.tenant_id),
        connector_key=conn.connector_key,
        mode=conn.mode,
        name=conn.name,
        base_url=conn.base_url,
        spec_url=conn.spec_url,
        spec_blob_path=conn.spec_blob_path,
        auth_flow=conn.auth_flow,
        auth_config=conn.auth_config or {},
    )


async def reindex_connection(
    session: AsyncSession, *, tenant_id: UUID, connection_id: UUID
) -> IndexResult | None:
    conn = await get_connection(session, tenant_id=tenant_id, connection_id=connection_id)
    if conn is None:
        return None
    register_builtins()
    spec: LoadedSpec | None = None
    try:
        if conn.connector_key and registry.has(conn.connector_key):
            connector = registry.get(conn.connector_key)
            spec = await connector.load_spec(_to_config(conn))
        elif conn.spec_url:
            spec = await fetch_spec_from_url(conn.spec_url)
    except (SpecFetchError, SpecValidationError) as exc:
        conn.status = ConnectionStatus.error
        conn.last_error = str(exc)
        return IndexResult(operation_count=0, chunk_count=0, spec_hash="")

    if spec is None:
        conn.status = ConnectionStatus.ready
        conn.last_indexed_at = datetime.now(UTC)
        conn.last_error = None
        return IndexResult(operation_count=0, chunk_count=0, spec_hash="")

    conn.status = ConnectionStatus.indexing
    result = await index_spec(
        tenant_id=str(tenant_id),
        connection_id=str(conn.id),
        connector_key=conn.connector_key,
        spec=spec,
    )
    conn.endpoint_count = result.operation_count
    conn.spec_hash = result.spec_hash
    conn.status = ConnectionStatus.ready
    conn.last_indexed_at = datetime.now(UTC)
    conn.last_error = None
    return result


async def ingest_uploaded_spec(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    connection_id: UUID,
    raw_bytes: bytes,
) -> IndexResult | None:
    """Used by the upload route — parses the uploaded bytes then indexes them."""
    conn = await get_connection(session, tenant_id=tenant_id, connection_id=connection_id)
    if conn is None:
        return None
    try:
        spec = parse_uploaded_spec(raw_bytes)
    except SpecValidationError as exc:
        conn.status = ConnectionStatus.error
        conn.last_error = str(exc)
        return IndexResult(operation_count=0, chunk_count=0, spec_hash="")

    conn.status = ConnectionStatus.indexing
    result = await index_spec(
        tenant_id=str(tenant_id),
        connection_id=str(conn.id),
        connector_key=conn.connector_key,
        spec=spec,
    )
    conn.endpoint_count = result.operation_count
    conn.spec_hash = result.spec_hash
    conn.status = ConnectionStatus.ready
    conn.last_indexed_at = datetime.now(UTC)
    conn.last_error = None
    return result


__all__ = [
    "ConnectionCreateInput",
    "ConnectionInputError",
    "create_connection",
    "delete_connection",
    "get_connection",
    "ingest_uploaded_spec",
    "list_connections",
    "reindex_connection",
]
