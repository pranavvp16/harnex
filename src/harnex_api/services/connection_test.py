"""Lightweight credential/connectivity probe used by the connection wizard.

The wizard's "Test connection" button hits this without persisting the
connection — we build the auth context from the form-supplied credentials
in memory, send a single low-cost request, and report status. The
connector-specific test path is declared on each builtin connector
(`ConnectorTestEndpoint`); `bare_url` and `openapi_*` modes fall back to a
GET against the resolved base URL.
"""

from __future__ import annotations

import ipaddress
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

from harnex_api.auth.strategies import AuthContext, AuthCredentials, get_strategy
from harnex_api.connectors.base import ConnectorTestEndpoint
from harnex_api.connectors.registry import register_builtins, registry
from harnex_api.db.models import AuthFlow, ConnectionMode
from harnex_api.services.ssrf import (
    bracket_ip as _bracket_ip,
)
from harnex_api.services.ssrf import (
    guard_public_http_url as _guard_public_http_url,
)

TEST_TIMEOUT_SECONDS = 8.0
METADATA_BODY_MAX_BYTES = 256 * 1024
METADATA_VALUE_MAX = 200


def _response_duration_ms(resp: httpx.Response) -> int:
    """Best-effort request duration (mock responses may not populate `.elapsed`)."""
    try:
        return max(0, int(resp.elapsed.total_seconds() * 1000))
    except RuntimeError:
        return 0


def _rewrite_http_base_with_ip(
    base_url: str, chosen_ip: str, original_hostname: str
) -> tuple[str, dict[str, str]]:
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
    metadata: dict[str, str] = field(default_factory=dict)


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
            connector_default = getattr(
                registry.get(payload.connector_key), "default_base_url", None
            )
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


def _cap_text(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    return s[:METADATA_VALUE_MAX]


def _instance_label_from_base(display_base_url: str) -> str | None:
    """Human-facing host (with non-default port) from the wizard's canonical base URL."""
    url = display_base_url.strip()
    if not url:
        return None
    if "://" not in url:
        url = f"https://{url}"
    p = urlparse(url.rstrip("/"))
    if not p.hostname:
        return None
    host = str(p.hostname)
    port = p.port
    scheme = (p.scheme or "https").lower()
    default = 443 if scheme == "https" else 80 if scheme == "http" else None
    if port and default is not None and port != default:
        return f"{host}:{port}"
    return host


def _try_parse_json_object(raw_body: bytes) -> dict[str, Any] | None:
    chunk = raw_body[:METADATA_BODY_MAX_BYTES]
    if not chunk or not chunk.strip():
        return None
    try:
        text = chunk.decode("utf-8")
    except UnicodeDecodeError:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _metadata_github(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    if u := _cap_text(data.get("login")):
        out["Username"] = u
    if n := _cap_text(data.get("name")):
        out["Name"] = n
    return out


def _metadata_gitlab(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    if u := _cap_text(data.get("username")):
        out["Username"] = u
    if n := _cap_text(data.get("name")):
        out["Name"] = n
    return out


def _metadata_jira(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    if d := _cap_text(data.get("displayName")):
        out["Display name"] = d
    if e := _cap_text(data.get("emailAddress")):
        out["Email"] = e
    return out


def _metadata_jenkins(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    fn = _cap_text(data.get("fullName"))
    jid = _cap_text(data.get("id"))
    if fn:
        out["User"] = fn
    elif jid:
        out["User"] = jid
    return out


def _metadata_slack(data: dict[str, Any]) -> dict[str, str]:
    if data.get("ok") is not True:
        return {}
    out: dict[str, str] = {}
    if t := _cap_text(data.get("team")):
        out["Team"] = t
    if u := _cap_text(data.get("user")):
        out["User"] = u
    return out


def _metadata_linear(data: dict[str, Any]) -> dict[str, str]:
    viewer = data.get("data")
    if not isinstance(viewer, dict):
        return {}
    v = viewer.get("viewer")
    if not isinstance(v, dict):
        return {}
    out: dict[str, str] = {}
    if i := _cap_text(v.get("id")):
        out["Viewer ID"] = i
    if n := _cap_text(v.get("name")):
        out["Name"] = n
    return out


def _metadata_kubernetes(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    vers = data.get("versions")
    if isinstance(vers, list) and vers:
        parts = [p for x in vers[:15] if (p := _cap_text(x))]
        if parts:
            joined = ", ".join(parts)
            out["API versions"] = joined[:METADATA_VALUE_MAX]
    if not out and (k := _cap_text(data.get("kind"))):
        out["Kind"] = k
    return out


def _connector_body_metadata(connector_key: str, data: dict[str, Any]) -> dict[str, str]:
    if connector_key == "github":
        return _metadata_github(data)
    if connector_key == "gitlab":
        return _metadata_gitlab(data)
    if connector_key == "jira":
        return _metadata_jira(data)
    if connector_key == "jenkins":
        return _metadata_jenkins(data)
    if connector_key == "slack":
        return _metadata_slack(data)
    if connector_key == "linear":
        return _metadata_linear(data)
    if connector_key == "kubernetes":
        return _metadata_kubernetes(data)
    return {}


def extract_probe_metadata(
    *,
    probe_ok: bool,
    connector_key: str | None,
    display_base_url: str,
    response_headers: Mapping[str, str],
    raw_body: bytes,
) -> dict[str, str]:
    """Build non-secret key/value metadata for a successful probe (wizard display)."""
    if not probe_ok:
        return {}
    hdr = {str(k).lower(): str(v) for k, v in response_headers.items()}
    meta: dict[str, str] = {}
    if inst := _instance_label_from_base(display_base_url):
        meta["Instance"] = inst

    ctype: str | None = None
    raw_ct = hdr.get("content-type")
    if raw_ct:
        ctype = _cap_text(raw_ct.split(";")[0].strip())

    if connector_key is None:
        if ctype:
            meta["Content-Type"] = ctype
        return meta

    body = _try_parse_json_object(raw_body)
    if body is None:
        if ctype:
            meta["Content-Type"] = ctype
        return meta

    meta.update(_connector_body_metadata(connector_key, body))
    if ctype and "Content-Type" not in meta:
        meta["Content-Type"] = ctype
    return meta


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
    if parsed_base.scheme == "http" and parsed_base.hostname and pin_ips:
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
    headers_lc = {str(k).lower(): str(v) for k, v in resp.headers.items()}
    meta = extract_probe_metadata(
        probe_ok=ok,
        connector_key=payload.connector_key,
        display_base_url=base_url.rstrip("/"),
        response_headers=headers_lc,
        raw_body=resp.content,
    )
    return ConnectionTestResult(
        ok=ok,
        http_status=resp.status_code,
        method=endpoint.method,
        url=display_target,
        error_kind=kind,
        message=msg,
        duration_ms=_response_duration_ms(resp),
        metadata=meta,
    )


__all__ = [
    "ConnectionTestInput",
    "ConnectionTestResult",
    "extract_probe_metadata",
    "test_connection_config",
]
