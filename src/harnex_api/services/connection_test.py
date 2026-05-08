"""Lightweight credential/connectivity probe used by the connection wizard.

The wizard's "Test connection" button hits this without persisting the
connection — we build the auth context from the form-supplied credentials
in memory, send a single low-cost request, and report status. The
connector-specific test path is declared on each builtin connector
(`ConnectorTestEndpoint`); `bare_url` and `openapi_*` modes fall back to a
GET against the resolved base URL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from harnex_api.auth.strategies import AuthContext, AuthCredentials, get_strategy
from harnex_api.connectors.base import ConnectorTestEndpoint
from harnex_api.connectors.registry import register_builtins, registry
from harnex_api.db.models import AuthFlow, ConnectionMode

TEST_TIMEOUT_SECONDS = 8.0


@dataclass(frozen=True)
class ConnectionTestInput:
    mode: ConnectionMode
    connector_key: str | None
    base_url: str | None
    auth_flow: AuthFlow
    auth_config: dict[str, Any] = field(default_factory=dict)
    credentials: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ConnectionTestResult:
    ok: bool
    http_status: int | None
    method: str
    url: str
    error_kind: str | None
    message: str
    duration_ms: int


def _resolve_test_endpoint(connector_key: str | None) -> ConnectorTestEndpoint:
    if not connector_key:
        return ConnectorTestEndpoint()
    register_builtins()
    if not registry.has(connector_key):
        return ConnectorTestEndpoint()
    return getattr(registry.get(connector_key), "test_endpoint", ConnectorTestEndpoint())


def _resolve_base_url(payload: ConnectionTestInput) -> str | None:
    if payload.base_url:
        return payload.base_url.rstrip("/")
    if payload.connector_key:
        register_builtins()
        if registry.has(payload.connector_key):
            default = getattr(registry.get(payload.connector_key), "default_base_url", None)
            if default:
                return str(default).rstrip("/")
    return None


def _build_auth_context(payload: ConnectionTestInput) -> AuthContext:
    strategy = get_strategy(payload.auth_flow)
    creds = AuthCredentials(flow=payload.auth_flow, values=payload.credentials)
    return strategy.build(payload.auth_config, creds)


def _classify(status_code: int) -> tuple[bool, str | None, str]:
    if status_code in (401, 403):
        return False, "auth_failed", f"HTTP {status_code} — credentials rejected"
    if status_code == 404:
        # 404 is ambiguous — base URL may be wrong but auth could still be fine.
        return False, "not_found", f"HTTP {status_code} — endpoint not found"
    if 200 <= status_code < 400:
        return True, None, f"HTTP {status_code} — connection ok"
    if 500 <= status_code < 600:
        return False, "upstream_error", f"HTTP {status_code} — upstream error"
    return False, "http_error", f"HTTP {status_code}"


async def test_connection_config(payload: ConnectionTestInput) -> ConnectionTestResult:
    base_url = _resolve_base_url(payload)
    if not base_url:
        return ConnectionTestResult(
            ok=False,
            http_status=None,
            method="GET",
            url="",
            error_kind="missing_base_url",
            message="A base URL is required to test this connection",
            duration_ms=0,
        )

    endpoint = _resolve_test_endpoint(payload.connector_key)
    auth = _build_auth_context(payload)

    target = f"{base_url}{endpoint.path}"
    headers = dict(auth.headers)
    if endpoint.body is not None:
        headers.setdefault("Content-Type", "application/json")

    request_kwargs: dict[str, Any] = {
        "method": endpoint.method,
        "url": target,
        "params": auth.query or None,
        "headers": headers,
    }
    if auth.basic_auth:
        request_kwargs["auth"] = auth.basic_auth
    if endpoint.body is not None:
        request_kwargs["json"] = endpoint.body

    try:
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = await client.request(**request_kwargs)
    except httpx.TimeoutException:
        return ConnectionTestResult(
            ok=False,
            http_status=None,
            method=endpoint.method,
            url=target,
            error_kind="timeout",
            message=f"Request timed out after {int(TEST_TIMEOUT_SECONDS)}s",
            duration_ms=int(TEST_TIMEOUT_SECONDS * 1000),
        )
    except httpx.RequestError as exc:
        return ConnectionTestResult(
            ok=False,
            http_status=None,
            method=endpoint.method,
            url=target,
            error_kind="network_error",
            message=str(exc) or exc.__class__.__name__,
            duration_ms=0,
        )

    ok, kind, msg = _classify(resp.status_code)
    return ConnectionTestResult(
        ok=ok,
        http_status=resp.status_code,
        method=endpoint.method,
        url=target,
        error_kind=kind,
        message=msg,
        duration_ms=int(resp.elapsed.total_seconds() * 1000),
    )


__all__ = [
    "ConnectionTestInput",
    "ConnectionTestResult",
    "test_connection_config",
]
