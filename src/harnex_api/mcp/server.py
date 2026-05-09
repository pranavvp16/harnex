"""Harnex MCP server — the shipped product surface.

Exactly two tools per the product contract:
  - search:  semantic search over a tenant's indexed APIs
  - execute: invoke a single OpenAPI operation by id

REST routes (under /v1/...) are internal/admin only and are not exposed via MCP.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from harnex_api.db.session import session_scope
from harnex_api.services.api_key_auth import ApiKeyAuthError, authenticate_key
from harnex_api.services.execute.operation import ExecuteParams
from harnex_api.services.execute.runner import (
    ConnectionMissingError,
    ConnectionNotReadyError,
    execute_structured,
)
from harnex_api.services.search.service import SearchService


@dataclass(frozen=True)
class _CallerContext:
    api_key_id: UUID
    tenant_id: UUID
    scope_type: str = "all"
    scope_connection_ids: tuple[UUID, ...] = ()

    def allows_connection(self, connection_id: UUID) -> bool:
        if self.scope_type == "all":
            return True
        return connection_id in self.scope_connection_ids


# Per-call auth state. Set by the auth middleware before the tool body runs.
_caller_context: ContextVar[_CallerContext | None] = ContextVar("harnex_mcp_caller", default=None)


def _require_caller() -> _CallerContext:
    caller = _caller_context.get()
    if caller is None:
        raise PermissionError("missing api key — set Authorization: Bearer hnx....")
    return caller


def create_mcp_app() -> FastMCP:
    """Build and return the FastMCP instance.

    Tool docstrings are part of the wire contract — agents read them to decide
    when to call. Keep them concise and behaviorally specific.
    """
    # Mounted at `/mcp` in `main.py`; Starlette strips that prefix so the inner path is `/`.
    mcp = FastMCP("harnex", streamable_http_path="/")

    @mcp.tool()
    async def search(
        query: str, top_k: int = 10, connector_filter: str | None = None
    ) -> dict[str, Any]:
        """Semantic search across the connected APIs for this tenant.

        Returns operation candidates (`operation_id`, `connection_id`, summary,
        score). When the top hits span multiple connectors, sets
        `clarification_needed=true` and lists `candidate_connectors` so the
        caller can ask the user which platform they meant.

        Pass `connector_filter` (e.g. "github", "jenkins") to narrow scope.
        """
        caller = _require_caller()
        svc = SearchService()
        result = await svc.search(
            tenant_id=str(caller.tenant_id),
            query=query,
            top_k=top_k,
            connector_filter=connector_filter,
        )
        return {
            "hits": [
                {
                    "operation_id": h.operation_id,
                    "connection_id": h.connection_id,
                    "connector_key": h.connector_key,
                    "method": h.method,
                    "path": h.path,
                    "summary": h.summary,
                    "score": h.score,
                }
                for h in result.hits
            ],
            "clarification_needed": result.clarification_needed,
            "candidate_connectors": result.candidate_connectors,
        }

    @mcp.tool()
    async def execute(
        connection_id: str,
        operation_id: str,
        path_params: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        body: Any = None,
    ) -> dict[str, Any]:
        """Invoke a single API operation on a tenant connection.

        `operation_id` and `connection_id` come from a prior `search` call.
        Path params, query params, headers, and body are keyed by parameter
        name as defined in the operation's OpenAPI spec.

        Returns `{status, http_status, body, error_kind?, error_message?,
        duration_ms}`. Status is one of `success`, `error`, or `timeout`.
        """
        caller = _require_caller()
        try:
            conn_uuid = UUID(connection_id)
        except ValueError:
            return {
                "status": "error",
                "error_kind": "invalid_connection_id",
                "error_message": connection_id,
            }
        if not caller.allows_connection(conn_uuid):
            return {
                "status": "error",
                "error_kind": "scope_forbidden",
                "error_message": "this api key is scoped to a subset of connections",
            }
        params = ExecuteParams(
            path=path_params or {},
            query=query or {},
            headers=headers or {},
            body=body,
        )
        try:
            async with session_scope() as session:
                outcome = await execute_structured(
                    session,
                    tenant_id=caller.tenant_id,
                    connection_id=conn_uuid,
                    operation_id=operation_id,
                    params=params,
                    api_key_id=caller.api_key_id,
                )
        except ConnectionMissingError:
            return {
                "status": "error",
                "error_kind": "connection_not_found",
                "error_message": connection_id,
            }
        except ConnectionNotReadyError as exc:
            return {
                "status": "error",
                "error_kind": "connection_not_ready",
                "error_message": str(exc),
            }
        return {
            "status": outcome.status.value,
            "http_status": outcome.http_status,
            "body": outcome.response_body,
            "headers": outcome.response_headers,
            "error_kind": outcome.error_kind,
            "error_message": outcome.error_message,
            "duration_ms": outcome.duration_ms,
            "operation_id": outcome.operation_id,
            "method": outcome.method,
            "path": outcome.path,
        }

    return mcp


def _extract_bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        return None
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


_AUTH_HINT = (
    "Authentication required. Create an API key at http://localhost:5173/api-keys "
    "and pass Authorization: Bearer hnx..."
)
# JSON-RPC application error code reserved for auth failures on this surface.
_JSONRPC_AUTH_ERROR_CODE = -32001


async def _drain_body(receive: Any) -> bytes:
    """Read the full ASGI request body. Caller must not need to replay it."""
    chunks: list[bytes] = []
    while True:
        message = await receive()
        if message["type"] == "http.request":
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        else:
            break
    return b"".join(chunks)


def _extract_jsonrpc_id(body: bytes) -> Any:
    if not body:
        return None
    try:
        payload = json.loads(body)
    except (ValueError, TypeError):
        return None
    if isinstance(payload, dict):
        return payload.get("id")
    return None


def _jsonrpc_auth_error(request_id: Any, message: str) -> Response:
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "error": {"code": _JSONRPC_AUTH_ERROR_CODE, "message": message},
            "id": request_id,
        },
        status_code=401,
        headers={"WWW-Authenticate": 'Bearer realm="harnex-mcp"'},
    )


def build_streamable_http_app() -> Any:
    """Return an ASGI app that serves the MCP streamable-HTTP transport.

    Wraps FastMCP's app with a tiny middleware that:
      - extracts the Bearer token
      - looks up the api key in the DB
      - sets the per-call caller context

    On auth failure returns a JSON-RPC 2.0 error envelope (status 401) so MCP
    clients see a structured, self-documenting error instead of an empty body.

    Mounted under `/mcp` by `harnex_api.main`.
    """
    mcp = create_mcp_app()
    inner = mcp.streamable_http_app()

    async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await inner(scope, receive, send)
            return
        request = Request(scope, receive=receive)
        token = _extract_bearer(request)
        if not token:
            body = await _drain_body(receive)
            await _jsonrpc_auth_error(_extract_jsonrpc_id(body), _AUTH_HINT)(
                scope, receive, send
            )
            return
        try:
            async with session_scope() as session:
                auth = await authenticate_key(session, token)
        except ApiKeyAuthError as exc:
            body = await _drain_body(receive)
            await _jsonrpc_auth_error(
                _extract_jsonrpc_id(body), f"{exc}. {_AUTH_HINT}"
            )(scope, receive, send)
            return

        ctx_token = _caller_context.set(
            _CallerContext(
                api_key_id=auth.api_key_id,
                tenant_id=auth.tenant_id,
                scope_type=auth.scope_type,
                scope_connection_ids=auth.scope_connection_ids,
            )
        )
        try:
            await inner(scope, receive, send)
        finally:
            _caller_context.reset(ctx_token)

    return app


__all__ = ["build_streamable_http_app", "create_mcp_app"]
