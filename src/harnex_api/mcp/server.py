"""Harnex MCP server — the shipped product surface.

Exactly two tools per the product contract:
  - search:  semantic search over a tenant's indexed APIs
  - execute: invoke a single OpenAPI operation by id

REST routes (under /v1/...) are internal/admin only and are not exposed via MCP.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

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


# Per-call auth state. Set by the auth middleware before the tool body runs.
_caller_context: ContextVar[_CallerContext | None] = ContextVar(
    "harnex_mcp_caller", default=None
)


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
    mcp = FastMCP("harnex")

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
                    connection_id=UUID(connection_id),
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


def build_streamable_http_app() -> Any:
    """Return an ASGI app that serves the MCP streamable-HTTP transport.

    Wraps FastMCP's app with a tiny middleware that:
      - extracts the Bearer token
      - looks up the api key in the DB
      - sets the per-call caller context

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
            await JSONResponse(
                {"error": "missing or invalid Authorization header"}, status_code=401
            )(scope, receive, send)
            return
        try:
            async with session_scope() as session:
                auth = await authenticate_key(session, token)
        except ApiKeyAuthError as exc:
            await JSONResponse({"error": str(exc)}, status_code=401)(scope, receive, send)
            return

        ctx_token = _caller_context.set(
            _CallerContext(api_key_id=auth.api_key_id, tenant_id=auth.tenant_id)
        )
        try:
            await inner(scope, receive, send)
        finally:
            _caller_context.reset(ctx_token)

    return app


__all__ = ["build_streamable_http_app", "create_mcp_app"]
