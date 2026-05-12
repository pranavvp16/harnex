"""ExecuteService — structured-fallback and code-mode execution paths.

Looks up a connection, finds the operation, builds the request, applies the
connector's auth context, then either sends via httpx (structured path) or
runs a generated Node.js fetch script in the Blaxel sandbox (code-mode path).

Code-mode is the layer on top — structured is the deterministic fallback when
no sandbox is configured or when code-mode is not explicitly requested.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
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
from harnex_api.db.session import session_scope
from harnex_api.logging import get_logger
from harnex_api.services.connections import get_connection
from harnex_api.services.execute.operation import (
    ExecuteParams,
    MissingRequiredParamError,
    OperationNotFoundError,
    build_request,
    find_operation,
)
from harnex_api.services.execute.sandbox import generate_fetch_script, get_sandbox_runner
from harnex_api.services.usage.monthly import bump_usage_monthly

_SENSITIVE_HEADER_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "www-authenticate",
        "proxy-authorization",
    }
)


def sanitize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Strip sensitive outbound / inbound headers before persisting execution summaries."""
    return {k: v for k, v in headers.items() if k.lower() not in _SENSITIVE_HEADER_KEYS}


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


@dataclass
class _PreparedExecute:
    conn: Any
    connector: Any
    spec: LoadedSpec
    base_url: str
    op: Any
    req: ExecuteRequest
    auth_ctx: AuthContext


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


async def _record_execution(
    *,
    session: AsyncSession,
    tenant_id: UUID,
    connection_id: UUID | None,
    request: ExecuteRequest | None,
    outcome: ExecuteOutcome,
    mode: ExecutionMode = ExecutionMode.structured,
    api_key_id: UUID | None = None,
) -> Execution:
    row = Execution(
        tenant_id=tenant_id,
        connection_id=connection_id,
        api_key_id=api_key_id,
        mode=mode,
        status=outcome.status,
        operation_id=outcome.operation_id or (request.operation_id if request else None),
        method=outcome.method or (request.method if request else None),
        path=outcome.path or (request.path if request else None),
        request_summary={
            "headers": sanitize_headers(dict(request.headers if request else {})),
            "query": dict(request.query if request else {}),
            "has_body": bool(request and request.body is not None),
        },
        response_summary={
            "http_status": outcome.http_status,
            "headers": sanitize_headers(dict(outcome.response_headers)),
            "body": outcome.response_body,
        },
        error_kind=outcome.error_kind,
        error_message=outcome.error_message,
        duration_ms=outcome.duration_ms,
    )
    session.add(row)
    log = get_logger(__name__)
    try:
        async with session_scope() as usage_session:
            await bump_usage_monthly(usage_session, tenant_id, executions=1)
    except Exception:
        log.exception("usage bump failed — ignoring", tenant_id=str(tenant_id))
    return row


async def _prepare_execute(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    connection_id: UUID,
    operation_id: str,
    params: ExecuteParams,
    api_key_id: UUID | None = None,
) -> _PreparedExecute | ExecuteOutcome:
    """Shared prep phase for both execute modes.

    Returns _PreparedExecute on success, or an ExecuteOutcome (already recorded)
    on early-exit errors (missing connection, not-ready, op-not-found, bad-params).
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
        await _record_execution(
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
        await _record_execution(
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

    return _PreparedExecute(
        conn=conn,
        connector=connector,
        spec=spec,
        base_url=base_url,
        op=op,
        req=req,
        auth_ctx=auth_ctx,
    )


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

    Builds the HTTP request from the OpenAPI spec + params, applies connector
    auth, sends via httpx, and records an Execution row.
    """
    prepared = await _prepare_execute(
        session,
        tenant_id=tenant_id,
        connection_id=connection_id,
        operation_id=operation_id,
        params=params,
        api_key_id=api_key_id,
    )
    if isinstance(prepared, ExecuteOutcome):
        return prepared

    req = prepared.req

    started = time.perf_counter()
    timestamp = datetime.now(UTC)
    try:
        client = http_client or httpx.AsyncClient(timeout=30.0)
        owns_client = http_client is None
        try:
            resp = await client.request(
                req.method,
                f"{prepared.base_url.rstrip('/')}{req.path}",
                params=req.query,
                headers=req.headers,
                json=req.body
                if req.body is not None and not isinstance(req.body, (str, bytes))
                else None,
                content=req.body if isinstance(req.body, (str, bytes)) else None,
                auth=prepared.auth_ctx.basic_auth,
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
        await _record_execution(
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
        await _record_execution(
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
        response_headers=sanitize_headers(dict(resp.headers.items())),
        response_body=body,
        error_kind=None if resp.is_success else f"http_{resp.status_code}",
        error_message=None if resp.is_success else f"upstream returned {resp.status_code}",
        duration_ms=duration_ms,
        operation_id=operation_id,
        method=req.method,
        path=req.path,
    )
    await _record_execution(
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


async def execute_code(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    connection_id: UUID,
    operation_id: str,
    params: ExecuteParams,
    api_key_id: UUID | None = None,
    timeout_seconds: int | None = None,
) -> ExecuteOutcome:
    """Code-mode execute path — runs a generated Node.js fetch script in the Blaxel sandbox.

    Shares the same prep phase as execute_structured (connection lookup, op resolution,
    auth context), then diverges: instead of httpx, it emits a JS script and runs it
    in the sandbox. The sandbox returns JSON on stdout; this function parses and
    records the result with mode=ExecutionMode.code.
    """
    prepared = await _prepare_execute(
        session,
        tenant_id=tenant_id,
        connection_id=connection_id,
        operation_id=operation_id,
        params=params,
        api_key_id=api_key_id,
    )
    if isinstance(prepared, ExecuteOutcome):
        return prepared

    req = prepared.req
    full_url = f"{prepared.base_url.rstrip('/')}{req.path}"
    script = generate_fetch_script(
        method=req.method,
        url=full_url,
        headers=req.headers,
        query=req.query,
        body=req.body,
    )

    started = time.perf_counter()
    runner = get_sandbox_runner()
    result = await runner.run_node_script(source=script, timeout_seconds=timeout_seconds)
    duration_ms = int((time.perf_counter() - started) * 1000)

    if result.exit_code != 0:
        outcome = ExecuteOutcome(
            status=ExecutionStatus.error,
            http_status=None,
            error_kind="sandbox_error",
            error_message=result.stderr[:2048] or "sandbox exited with non-zero code",
            duration_ms=duration_ms,
            operation_id=operation_id,
            method=req.method,
            path=req.path,
        )
        await _record_execution(
            session=session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            request=req,
            outcome=outcome,
            mode=ExecutionMode.code,
            api_key_id=api_key_id,
        )
        return outcome

    try:
        parsed: dict[str, Any] = json.loads(result.stdout)
        http_status: int = int(parsed["http_status"])
        resp_headers: dict[str, str] = sanitize_headers(dict(parsed.get("headers") or {}))
        resp_body: Any = parsed.get("body")
    except (ValueError, KeyError, TypeError):
        outcome = ExecuteOutcome(
            status=ExecutionStatus.error,
            http_status=None,
            error_kind="sandbox_output_invalid",
            error_message=result.stdout[:2048],
            duration_ms=duration_ms,
            operation_id=operation_id,
            method=req.method,
            path=req.path,
        )
        await _record_execution(
            session=session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            request=req,
            outcome=outcome,
            mode=ExecutionMode.code,
            api_key_id=api_key_id,
        )
        return outcome

    is_success = 200 <= http_status < 300
    outcome = ExecuteOutcome(
        status=ExecutionStatus.success if is_success else ExecutionStatus.error,
        http_status=http_status,
        response_headers=resp_headers,
        response_body=resp_body,
        error_kind=None if is_success else f"http_{http_status}",
        error_message=None if is_success else f"upstream returned {http_status}",
        duration_ms=duration_ms,
        operation_id=operation_id,
        method=req.method,
        path=req.path,
    )
    await _record_execution(
        session=session,
        tenant_id=tenant_id,
        connection_id=connection_id,
        request=req,
        outcome=outcome,
        mode=ExecutionMode.code,
        api_key_id=api_key_id,
    )
    return outcome


__all__ = [
    "ConnectionMissingError",
    "ConnectionNotReadyError",
    "ExecuteOutcome",
    "execute_code",
    "execute_structured",
    "sanitize_headers",
]
