"""Lightweight credential/connectivity probe used by the connection wizard.

The wizard's "Test connection" button hits this without persisting the
connection — we build the auth context from the form-supplied credentials
in memory, send a single low-cost request, and report status. The
connector-specific test path is declared on each builtin connector
(`ConnectorTestEndpoint`); `bare_url` and `openapi_*` modes fall back to a
GET against the resolved base URL.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

from harnex_api.auth.strategies import AuthContext, AuthCredentials, get_strategy
from harnex_api.connectors.base import ConnectorTestEndpoint
from harnex_api.connectors.registry import register_builtins, registry
from harnex_api.db.models import AuthFlow, ConnectionMode

TEST_TIMEOUT_SECONDS = 8.0


def _response_duration_ms(resp: httpx.Response) -> int:
    """Best-effort request duration (mock responses may not populate `.elapsed`)."""
    try:
        return max(0, int(resp.elapsed.total_seconds() * 1000))
    except RuntimeError:
        return 0


def _is_blocked_destination_ip(ip: str) -> bool:
    """True when the IP must not be reached by wizard connection tests (SSRF guard)."""
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return bool(
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_reserved
        or parsed.is_unspecified
    )


def _bracket_ip(ip: str) -> str:
    """Format IP for URL netloc (IPv6 must be bracketed)."""
    try:
        if ipaddress.ip_address(ip).version == 6:
            return f"[{ip}]"
    except ValueError:
        pass
    return ip


def _stable_public_ips_sync(hostname: str) -> tuple[list[str] | None, str | None]:
    """Resolve twice on the same thread; reject flaky DNS (mitigates rebinding races).

    Returns ``(ips, None)`` on success, or ``(None, error_message)``.
    """

    def lookup_once() -> list[str]:
        try:
            infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        except socket.gaierror:
            return []
        out: list[str] = []
        seen: set[str] = set()
        for info in infos:
            ip_s = str(info[4][0])
            if ip_s not in seen:
                seen.add(ip_s)
                out.append(ip_s)
        return out

    a = lookup_once()
    b = lookup_once()
    if not a:
        return None, "could not resolve hostname"
    if sorted(a) != sorted(b):
        return None, "dns resolution changed between checks — refusing to connect"
    pub = [ip for ip in a if not _is_blocked_destination_ip(ip)]
    if not pub:
        return None, "hostname resolves to a non-public IP address"
    return pub, None


async def _guard_public_http_url(url: str) -> tuple[bool, str, list[str] | None]:
    """Validate origin is HTTP(S) with a public destination.

    For hostname origins, returns the ordered list of resolved public IPs (two
    identical lookups) so plain-HTTP probes can connect by IP with a Host header,
    avoiding a separate DNS lookup inside httpx (DNS rebinding). HTTPS probes
    still use the hostname URL (certificate validation); redirects are disabled
    to avoid bypassing this check.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "only http and https URLs can be tested", None
    host = parsed.hostname
    if not host:
        return False, "missing host in URL", None

    try:
        literal = ipaddress.ip_address(host)
        if _is_blocked_destination_ip(str(literal)):
            return False, "target uses a non-public IP address", None
        return True, "", None
    except ValueError:
        pass

    ips, err = await asyncio.to_thread(_stable_public_ips_sync, host)
    if err:
        return False, err, None
    return True, "", ips


def _rewrite_http_base_with_ip(base_url: str, chosen_ip: str, original_hostname: str) -> tuple[str, dict[str, str]]:
    """Rewrite http origin to a literal IP netloc; preserve name-based vhosts via Host."""
    p = urlparse(base_url)
    port = p.port or 80
    bip = _bracket_ip(chosen_ip)
    netloc = f"{bip}:{port}" if port != 80 else bip
    rewritten = urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))
    return rewritten, {"Host": original_hostname}


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
    if payload.mode == ConnectionMode.builtin:
        if not payload.connector_key:
            return None
        register_builtins()
        if not registry.has(payload.connector_key):
            return None
        default = getattr(registry.get(payload.connector_key), "default_base_url", None)
        if default:
            return str(default).rstrip("/")
        return payload.base_url.rstrip("/") if payload.base_url else None
    if payload.base_url:
        return payload.base_url.rstrip("/")
    if payload.connector_key:
        register_builtins()
        if registry.has(payload.connector_key):
            connector_default = getattr(registry.get(payload.connector_key), "default_base_url", None)
            if connector_default:
                return str(connector_default).rstrip("/")
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

    ok_dest, dest_msg, pin_ips = await _guard_public_http_url(f"{base_url}/")
    if not ok_dest:
        target_preview = f"{base_url}{endpoint.path}"
        return ConnectionTestResult(
            ok=False,
            http_status=None,
            method=endpoint.method,
            url=target_preview,
            error_kind="ssrf_blocked",
            message=dest_msg,
            duration_ms=0,
        )

    parsed_base = urlparse(base_url)
    effective_base = base_url
    pin_headers: dict[str, str] = {}
    if (
        parsed_base.scheme == "http"
        and parsed_base.hostname
        and pin_ips
    ):
        try:
            ipaddress.ip_address(parsed_base.hostname)
        except ValueError:
            effective_base, pin_headers = _rewrite_http_base_with_ip(
                base_url, pin_ips[0], parsed_base.hostname
            )

    target = f"{effective_base.rstrip('/')}{endpoint.path}"

    headers = dict(auth.headers)
    headers.update(pin_headers)
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
        async with httpx.AsyncClient(
            timeout=TEST_TIMEOUT_SECONDS,
            follow_redirects=False,
        ) as client:
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

    if 300 <= resp.status_code < 400:
        loc = resp.headers.get("location") or resp.headers.get("Location")
        detail = f"HTTP {resp.status_code}"
        if loc:
            detail = f"{detail} — redirects are not followed ({loc[:200]})"
        else:
            detail = f"{detail} — redirects are not followed"
        return ConnectionTestResult(
            ok=False,
            http_status=resp.status_code,
            method=endpoint.method,
            url=target,
            error_kind="redirect_blocked",
            message=detail,
            duration_ms=_response_duration_ms(resp),
        )

    ok, kind, msg = _classify(resp.status_code)
    display_target = f"{base_url.rstrip('/')}{endpoint.path}"
    return ConnectionTestResult(
        ok=ok,
        http_status=resp.status_code,
        method=endpoint.method,
        url=display_target,
        error_kind=kind,
        message=msg,
        duration_ms=_response_duration_ms(resp),
    )


__all__ = [
    "ConnectionTestInput",
    "ConnectionTestResult",
    "test_connection_config",
]
