"""ExecuteService — structured-fallback execution path.

Looks up a connection, finds the operation, builds the request, applies the
connector's auth context, sends via httpx, and records an Execution row.

Code-mode (LLM-generated JS validation in the sandbox) is the next layer —
this module owns the deterministic fallback that the structured path falls
through to when no validator is configured.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.auth.strategies import AuthContext
from harnex_api.connectors.base import ConnectionConfig, ExecuteRequest, LoadedSpec
from harnex_api.connectors.registry import register_builtins, registry
from harnex_api.db.models import (
    Execution,
    ExecutionMode,
    ExecutionStatus,
)
from harnex_api.services.connections import get_connection
from harnex_api.services.execute.operation import (
    ExecuteParams,
    MissingRequiredParamError,
    OperationNotFoundError,
    build_request,
    find_operation,
)


class ConnectionNotReadyError(RuntimeError):
    """Raised when the chosen connection has no spec/base_url to execute against."""


class ConnectionMissingError(LookupError):
    """The connection_id does not belong to this tenant."""


@dataclass
class ExecuteOutcome:
    status: ExecutionStatus
    http_status: int | None
    response_headers: dict[str, str] = field(default_factory=dict)
    response_body: Any | None = None
    error_kind: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    operation_id: str | None = None
    method: str | None = None
    path: str | None = None


def _merge_auth(req: ExecuteRequest, auth: AuthContext) -> ExecuteRequest:
    headers = dict(req.headers)
    headers.update(auth.headers)
    query = dict(req.query)
    query.update(auth.query)
    return ExecuteRequest(
        method=req.method,
        path=req.path,
        headers=headers,
        query=query,
        body=req.body,
        operation_id=req.operation_id,
    )


def _connection_to_config(conn: Any) -> ConnectionConfig:
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


async def _resolve_connector_and_spec(conn: Any) -> tuple[Any, LoadedSpec | None]:
    register_builtins()
    if conn.connector_key and registry.has(conn.connector_key):
        connector = registry.get(conn.connector_key)
    else:
        connector = registry.get("generic")
    cfg = _connection_to_config(conn)
    spec = await connector.load_spec(cfg)
    return connector, spec


def _record_execution(
    *,
    session: AsyncSession,
    tenant_id: UUID,
    connection_id: UUID | None,
    request: ExecuteRequest | None,
    outcome: ExecuteOutcome,
    api_key_id: UUID | None = None,
) -> Execution:
    row = Execution(
        tenant_id=tenant_id,
        connection_id=connection_id,
        api_key_id=api_key_id,
        mode=ExecutionMode.structured,
        status=outcome.status,
        operation_id=outcome.operation_id or (request.operation_id if request else None),
        method=outcome.method or (request.method if request else None),
        path=outcome.path or (request.path if request else None),
        request_summary={
            "headers": dict(request.headers if request else {}),
            "query": dict(request.query if request else {}),
            "has_body": bool(request and request.body is not None),
        },
        response_summary={
            "http_status": outcome.http_status,
            "headers": outcome.response_headers,
            "body": outcome.response_body,
        },
        error_kind=outcome.error_kind,
        error_message=outcome.error_message,
        duration_ms=outcome.duration_ms,
    )
    session.add(row)
    return row


async def execute_structured(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    connection_id: UUID,
    operation_id: str,
    params: ExecuteParams,
    api_key_id: UUID | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> ExecuteOutcome:
    """Deterministic execute path — no LLM, no sandbox.

    The MCP `execute` tool calls this with the agent-supplied params. Code-mode
    will branch off here once the JS validator is implemented; for now this is
    the authoritative path.
    """
    conn = await get_connection(session, tenant_id=tenant_id, connection_id=connection_id)
    if conn is None:
        raise ConnectionMissingError(str(connection_id))

    connector, spec = await _resolve_connector_and_spec(conn)
    base_url = await connector.infer_base_url(_connection_to_config(conn), spec)
    if not base_url or spec is None:
        raise ConnectionNotReadyError(
            f"connection {connection_id} has no base_url or spec to execute against"
        )

    try:
        op = find_operation(spec.document, operation_id)
    except OperationNotFoundError:
        outcome = ExecuteOutcome(
            status=ExecutionStatus.error,
            http_status=None,
            error_kind="operation_not_found",
            error_message=operation_id,
            operation_id=operation_id,
        )
        _record_execution(
            session=session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            request=None,
            outcome=outcome,
            api_key_id=api_key_id,
        )
        return outcome

    try:
        req = build_request(op, params)
    except MissingRequiredParamError as exc:
        outcome = ExecuteOutcome(
            status=ExecutionStatus.error,
            http_status=None,
            error_kind="invalid_params",
            error_message=str(exc),
            operation_id=operation_id,
            method=op.method,
            path=op.path,
        )
        _record_execution(
            session=session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            request=None,
            outcome=outcome,
            api_key_id=api_key_id,
        )
        return outcome

    auth_ctx: AuthContext = await connector.build_auth_context(
        tenant_id=str(tenant_id),
        connection_id=str(conn.id),
        auth_flow=conn.auth_flow,
        auth_config=conn.auth_config or {},
    )
    req = await connector.before_execute(req)
    req = _merge_auth(req, auth_ctx)

    started = time.perf_counter()
    timestamp = datetime.now(UTC)
    try:
        client = http_client or httpx.AsyncClient(timeout=30.0)
        owns_client = http_client is None
        try:
            resp = await client.request(
                req.method,
                f"{base_url.rstrip('/')}{req.path}",
                params=req.query,
                headers=req.headers,
                json=req.body if req.body is not None and not isinstance(req.body, (str, bytes)) else None,
                content=req.body if isinstance(req.body, (str, bytes)) else None,
                auth=auth_ctx.basic_auth,
            )
        finally:
            if owns_client:
                await client.aclose()
    except httpx.TimeoutException as exc:
        outcome = ExecuteOutcome(
            status=ExecutionStatus.timeout,
            http_status=None,
            error_kind="timeout",
            error_message=str(exc),
            duration_ms=int((time.perf_counter() - started) * 1000),
            operation_id=operation_id,
            method=req.method,
            path=req.path,
        )
        _record_execution(
            session=session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            request=req,
            outcome=outcome,
            api_key_id=api_key_id,
        )
        return outcome
    except httpx.HTTPError as exc:
        outcome = ExecuteOutcome(
            status=ExecutionStatus.error,
            http_status=None,
            error_kind="transport_error",
            error_message=str(exc),
            duration_ms=int((time.perf_counter() - started) * 1000),
            operation_id=operation_id,
            method=req.method,
            path=req.path,
        )
        _record_execution(
            session=session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            request=req,
            outcome=outcome,
            api_key_id=api_key_id,
        )
        return outcome

    duration_ms = int((time.perf_counter() - started) * 1000)
    body: Any
    try:
        body = resp.json()
    except ValueError:
        body = resp.text[:8192]  # cap stored body size

    status_kind = ExecutionStatus.success if resp.is_success else ExecutionStatus.error
    outcome = ExecuteOutcome(
        status=status_kind,
        http_status=resp.status_code,
        response_headers={k: v for k, v in resp.headers.items() if k.lower() != "set-cookie"},
        response_body=body,
        error_kind=None if resp.is_success else f"http_{resp.status_code}",
        error_message=None if resp.is_success else f"upstream returned {resp.status_code}",
        duration_ms=duration_ms,
        operation_id=operation_id,
        method=req.method,
        path=req.path,
    )
    _record_execution(
        session=session,
        tenant_id=tenant_id,
        connection_id=connection_id,
        request=req,
        outcome=outcome,
        api_key_id=api_key_id,
    )
    # Tag for observability — the tenant timestamp helps debug clock skew.
    _ = timestamp
    return outcome


__all__ = [
    "ConnectionMissingError",
    "ConnectionNotReadyError",
    "ExecuteOutcome",
    "execute_structured",
]
