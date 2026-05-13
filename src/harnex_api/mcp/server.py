"""Harnex MCP server — the shipped product surface.

Exactly two tools per the product contract:
  - search:  semantic search over a tenant's indexed APIs
  - execute: invoke a single OpenAPI operation by id

REST routes (under /v1/...) are internal/admin only and are not exposed via MCP.
"""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import Tool as MCPTool
from sqlalchemy import func, select
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from harnex_api.config import get_settings
from harnex_api.db.models import Connection
from harnex_api.db.session import session_scope
from harnex_api.logging import get_logger
from harnex_api.services.api_key_auth import ApiKeyAuthError, authenticate_key
from harnex_api.services.execute.operation import ExecuteParams
from harnex_api.services.execute.runner import (
    ConnectionMissingError,
    ConnectionNotReadyError,
    execute_code,
    execute_structured,
)
from harnex_api.services.execute.skill_runner import (
    SkillNotFoundError,
    _ensure_outcome_envelope,
    execute_skill,
)
from harnex_api.services.search.service import SearchService
from harnex_api.services.usage.monthly import bump_usage_monthly

# Singleton FastMCP instance — must match the app mounted at `/mcp` so lifespan can run
# `session_manager.run()` on the same StreamableHTTPSessionManager FastMCP creates.
_fast_mcp: FastMCP | None = None


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


def _caller_cache_key(caller: _CallerContext) -> tuple[Any, ...]:
    return (
        caller.tenant_id,
        caller.scope_type,
        caller.scope_connection_ids,
    )


_SUMMARY_CACHE_TTL_SEC = 30.0
_SUMMARY_CACHE_MAX_KEYS = 256
# Bounded LRU-ish cache for tools/list connection blurbs (tenant + key scope).
_connection_summary_cache: OrderedDict[tuple[Any, ...], tuple[float, str]] = OrderedDict()


def _connection_summary_cache_get(key: tuple[Any, ...]) -> str | None:
    now = time.monotonic()
    item = _connection_summary_cache.get(key)
    if item is None:
        return None
    inserted, text = item
    if now - inserted > _SUMMARY_CACHE_TTL_SEC:
        del _connection_summary_cache[key]
        return None
    _connection_summary_cache.move_to_end(key)
    return text


def _connection_summary_cache_set(key: tuple[Any, ...], text: str) -> None:
    now = time.monotonic()
    _connection_summary_cache[key] = (now, text)
    _connection_summary_cache.move_to_end(key)
    while len(_connection_summary_cache) > _SUMMARY_CACHE_MAX_KEYS:
        _connection_summary_cache.popitem(last=False)


async def _load_connection_summary_block(caller: _CallerContext) -> str:
    lines: list[str] = []
    connector_keys: set[str] = set()
    async with session_scope() as session:
        where_clause: list[Any] = [Connection.tenant_id == caller.tenant_id]
        if caller.scope_type != "all":
            if not caller.scope_connection_ids:
                return "\n\n".join(
                    [
                        "Connections for this API key:",
                        "This API key is scoped to specific connections, but the allow-list "
                        "is empty — no connections are visible.",
                    ]
                )
            where_clause.append(Connection.id.in_(caller.scope_connection_ids))

        total = int(
            (
                await session.execute(
                    select(func.count()).select_from(Connection).where(*where_clause)
                )
            ).scalar_one()
        )
        stmt = (
            select(Connection.name, Connection.connector_key, Connection.status)
            .where(*where_clause)
            .order_by(Connection.name)
            .limit(40)
        )
        rows = (await session.execute(stmt)).all()
        if not rows:
            lines.append(
                "No connections in scope yet. Add and index a connection in the Harnex "
                "console; search only returns operations from connections in `ready` state."
            )
        else:
            for name, connector_key, status in rows:
                key = connector_key or "generic"
                if connector_key:
                    connector_keys.add(connector_key)
                lines.append(f"- {name} ({key}): {status.value}")
            if len(rows) == 40 and total > 40:
                lines.append(
                    f"(and {total - 40} more — use `connector_filter` to narrow scope.)"
                )

    parts: list[str] = ["Connections for this API key:", "\n".join(lines)]
    if len(connector_keys) > 1:
        keys = ", ".join(sorted(connector_keys))
        parts.append(f"Use connector_filter when disambiguating: {keys}.")
    return "\n\n".join(parts)


async def connection_summary_for_tools_list(caller: _CallerContext) -> str:
    """Build (cached) text appended to the MCP `search` tool description."""
    cache_key = _caller_cache_key(caller)
    cached = _connection_summary_cache_get(cache_key)
    if cached is not None:
        return cached
    text = await _load_connection_summary_block(caller)
    _connection_summary_cache_set(cache_key, text)
    return text


class HarnexFastMCP(FastMCP):
    """FastMCP with request-scoped `search` tool descriptions."""

    async def list_tools(self) -> list[MCPTool]:
        tools = await super().list_tools()
        caller = _caller_context.get()
        if caller is None:
            return tools
        suffix = await connection_summary_for_tools_list(caller)
        patched: list[MCPTool] = []
        for t in tools:
            if t.name == "search":
                base = (t.description or "").rstrip()
                patched.append(
                    t.model_copy(update={"description": f"{base}\n\n{suffix}"})
                )
            else:
                patched.append(t)
        return patched


def create_mcp_app() -> FastMCP:
    """Build (once) and return the FastMCP instance.

    Tool docstrings are part of the wire contract — agents read them to decide
    when to call. Keep them concise and behaviorally specific.
    """
    global _fast_mcp
    if _fast_mcp is not None:
        return _fast_mcp

    # DNS-rebinding allowlist: localhost defaults + the configured public host.
    # Without populating allowed_hosts, FastMCP rejects every non-localhost Host
    # header with "Invalid Host header" — so prod / Cursor / Claude Desktop all
    # break until the public hostname is in this list.
    settings = get_settings()
    allowed_hosts: list[str] = [
        "127.0.0.1",
        "localhost",
        "127.0.0.1:*",
        "localhost:*",
    ]
    if settings.public_host:
        allowed_hosts += [settings.public_host, f"{settings.public_host}:*"]
    transport_security = TransportSecuritySettings(allowed_hosts=allowed_hosts)

    # Mounted at `/mcp` in `main.py`; Starlette strips that prefix so the inner path is `/`.
    mcp = HarnexFastMCP("harnex", streamable_http_path="/", transport_security=transport_security)

    @mcp.tool()
    async def search(
        query: str,
        top_k: int = 10,
        connector_filter: str | None = None,
        skills: bool = False,
    ) -> dict[str, Any]:
        """Semantic search across the connected APIs for this tenant.

        Returns operation candidates (`operation_id`, `connection_id`, summary,
        score). When the top hits span multiple connectors, sets
        `clarification_needed=true` and lists `candidate_connectors` so the
        caller can ask the user which platform they meant.

        Pass `connector_filter` (e.g. "github", "jenkins") to narrow scope.

        **Skills.** Harnex also ships document-building skills for PDF, Word
        (.docx), Excel (.xlsx), and PowerPoint (.pptx). Pass `skills=true` when
        the user wants to *produce a file* — e.g. "build a PDF report",
        "export users as xlsx", "make a slide deck", "draft a Word memo". The
        response then includes a top-matching skill under `skills[]` with the
        full instructions inline; use those instructions to write code, then
        call `execute` with `skill_key="<key>"` and `code="<your code>"`. The
        generated file is uploaded to tenant-isolated storage and `execute`
        returns a short-lived download URL.
        """
        caller = _require_caller()
        svc = SearchService()
        result = await svc.search(
            tenant_id=str(caller.tenant_id),
            query=query,
            top_k=top_k,
            connector_filter=connector_filter,
            include_skills=skills,
        )
        log = get_logger(__name__)
        try:
            async with session_scope() as usage_session:
                await bump_usage_monthly(
                    usage_session,
                    caller.tenant_id,
                    searches=1,
                    embedding_tokens=result.embedding_tokens,
                )
        except Exception:
            log.exception("usage bump failed — ignoring", tenant_id=str(caller.tenant_id))
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
            "skills": [
                {
                    "skill_key": s.skill_key,
                    "name": s.name,
                    "runtime": s.runtime,
                    "output_format": s.output_format,
                    "instructions": s.instructions,
                    "score": s.score,
                }
                for s in result.skills
            ],
        }

    @mcp.tool()
    async def execute(
        connection_id: str | None = None,
        operation_id: str | None = None,
        path_params: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        body: Any = None,
        mode: str = "structured",
        skill_key: str | None = None,
        code: str | None = None,
    ) -> dict[str, Any]:
        """Invoke any operation on a connected API — or run a document-building skill.

        Two modes, picked by which arguments you pass:

        **API mode** (default): pass `connection_id` + `operation_id` from a
        prior `search` hit; the call is dispatched against the connected API.

        **Skill mode**: pass `skill_key` (e.g. "pdf", "docx", "xlsx", "pptx")
        + `code`. The code runs in an isolated Blaxel sandbox using the skill's
        runtime (Node.js for docx, Python for pdf/xlsx/pptx). Write your file
        to `$HARNEX_OUTPUT_DIR/<name>.<ext>`; the runner uploads it to
        tenant-isolated storage and returns a short-TTL `download_url` you can
        hand to the user. The full SKILL.md (returned by `search(skills=true)`)
        explains the contract — follow it.

        Inputs (API mode):
          - `connection_id`, `operation_id`: from a prior `search` hit.
          - `path_params`: values for `{...}` placeholders in the operation path
            (e.g. `{"owner": "octocat", "repo": "hello-world"}`).
          - `query`: query-string parameters.
          - `headers`: extra request headers (auth headers are injected
            automatically — do not duplicate).
          - `body`: JSON request body for POST/PUT/PATCH operations.
          - `mode`: `"structured"` (default httpx) or `"code"` (Node `fetch`
            inside the sandbox).

        Inputs (skill mode):
          - `skill_key`: one of the skills returned by `search(skills=true)`.
          - `code`: the script you want executed. Must write its output file
            under `$HARNEX_OUTPUT_DIR`.

        Returns (API mode): `{status, http_status, body, headers, error_kind?,
        error_message?, duration_ms, operation_id, method, path}`.

        Returns (skill mode): `{status, skill_key, runtime, output_format,
        download_url, filename, content_type, size_bytes, duration_ms,
        error_kind?, error_message?, execution_id}`.

        All paths write to the audit log (`executions`).
        """
        caller = _require_caller()
        if skill_key is not None:
            if not code:
                return {
                    "status": "error",
                    "error_kind": "missing_code",
                    "error_message": "skill execution requires `code`",
                }
            try:
                async with session_scope() as session:
                    skill_outcome = await execute_skill(
                        session,
                        tenant_id=caller.tenant_id,
                        skill_key=skill_key,
                        code=code,
                        api_key_id=caller.api_key_id,
                    )
            except SkillNotFoundError:
                return {
                    "status": "error",
                    "error_kind": "skill_not_found",
                    "error_message": skill_key,
                }
            return _ensure_outcome_envelope(skill_outcome)
        if connection_id is None or operation_id is None:
            return {
                "status": "error",
                "error_kind": "missing_args",
                "error_message": (
                    "execute requires either (connection_id + operation_id) or "
                    "(skill_key + code)"
                ),
            }
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
        if mode not in ("structured", "code"):
            return {
                "status": "error",
                "error_kind": "invalid_mode",
                "error_message": f"mode must be 'structured' or 'code', got {mode!r}",
            }
        params = ExecuteParams(
            path=path_params or {},
            query=query or {},
            headers=headers or {},
            body=body,
        )
        try:
            async with session_scope() as session:
                if mode == "code":
                    outcome = await execute_code(
                        session,
                        tenant_id=caller.tenant_id,
                        connection_id=conn_uuid,
                        operation_id=operation_id,
                        params=params,
                        api_key_id=caller.api_key_id,
                    )
                else:
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

    _fast_mcp = mcp
    return mcp


def get_mcp_app() -> FastMCP:
    """Return the same FastMCP instance used by `build_streamable_http_app`."""
    return create_mcp_app()


def _extract_bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        return None
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def _auth_hint() -> str:
    """Human-oriented URL where users can issue MCP API keys.

    Uses `HARNEX_PUBLIC_HOST` when set (production / staging); otherwise the
    local Vite dev default so local MCP runs stay actionable.
    """
    settings = get_settings()
    host = settings.public_host.strip()
    base_url = f"https://{host}" if host else "http://localhost:5173"
    return (
        f"Authentication required. Create an API key at {base_url}/api-keys "
        "and pass Authorization: Bearer hnx..."
    )


# JSON-RPC application error code reserved for auth failures on this surface.
_JSONRPC_AUTH_ERROR_CODE = -32001


async def _drain_body(receive: Any) -> bytes:
    """Read the full ASGI request body."""
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


def _receive_replay(body: bytes) -> Any:
    """ASGI receive that replays a captured body once, then disconnects.

    Only suitable for short-circuit error responses where we need the
    body to extract the JSON-RPC ID but then immediately close the
    connection.  Must NOT be used for streaming responses (SSE) because
    the second call returns ``http.disconnect`` which tells the server
    the client has gone away — killing any in-flight SSE stream.
    """

    sent = False

    async def receive() -> dict[str, Any]:
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    return receive


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

    **Important**: on the happy path the original ASGI ``receive`` is forwarded
    to the inner app untouched.  We only drain-and-replay the body for short-
    circuit error responses where we need it to extract the JSON-RPC request ID.
    Draining-and-replaying on the success path would cause ``receive_replay`` to
    emit ``http.disconnect`` on its second call, which tells
    ``EventSourceResponse`` (the SSE transport) that the client has gone away
    — killing the stream before any events are written.  Passing the real
    ``receive`` through preserves proper disconnect detection.

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
            receive_replay = _receive_replay(body)
            await _jsonrpc_auth_error(_extract_jsonrpc_id(body), _auth_hint())(
                scope, receive_replay, send
            )
            return
        try:
            async with session_scope() as session:
                auth = await authenticate_key(session, token)
        except ApiKeyAuthError as exc:
            body = await _drain_body(receive)
            receive_replay = _receive_replay(body)
            await _jsonrpc_auth_error(
                _extract_jsonrpc_id(body), f"{exc}. {_auth_hint()}"
            )(scope, receive_replay, send)
            return

        # -- Happy path: forward the original receive to the inner app. --------
        # We deliberately do NOT drain-and-replay the body here. The MCP
        # streamable-HTTP transport uses EventSourceResponse (SSE), which calls
        # receive() after reading the request body to detect client disconnects.
        # Our _receive_replay returns http.disconnect on its second call, which
        # tells the SSE writer the client has gone away and kills the stream
        # before any events are written (empty body → "no tools visible").
        # Passing the real receive preserves proper disconnect detection.
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


__all__ = ["build_streamable_http_app", "create_mcp_app", "get_mcp_app"]
