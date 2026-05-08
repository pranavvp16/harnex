from __future__ import annotations

import pytest

from harnex_api.db.models import AuthFlow, ConnectionMode
from harnex_api.services import connection_test as ct
from harnex_api.services.connection_test import (
    ConnectionTestInput,
    ConnectionTestResult,
    _classify,
    _resolve_base_url,
    _resolve_test_endpoint,
)
from harnex_api.services.connection_test import (
    test_connection_config as run_test,
)


def _input(**overrides: object) -> ConnectionTestInput:
    base = dict(
        mode=ConnectionMode.builtin,
        connector_key="github",
        base_url=None,
        auth_flow=AuthFlow.bearer,
        auth_config={},
        credentials={"token": "ghp_example"},
    )
    base.update(overrides)
    return ConnectionTestInput(**base)  # type: ignore[arg-type]


def test_resolve_test_endpoint_uses_connector_default() -> None:
    ep = _resolve_test_endpoint("github")
    assert ep.method == "GET"
    assert ep.path == "/user"


def test_resolve_test_endpoint_falls_back_for_unknown() -> None:
    ep = _resolve_test_endpoint(None)
    assert ep.method == "GET"
    assert ep.path == "/"


def test_resolve_base_url_prefers_explicit() -> None:
    p = _input(base_url="https://example.com/api/")
    assert _resolve_base_url(p) == "https://example.com/api"


def test_resolve_base_url_falls_back_to_connector_default() -> None:
    p = _input(connector_key="github", base_url=None)
    assert _resolve_base_url(p) == "https://api.github.com"


def test_resolve_base_url_returns_none_when_unknown() -> None:
    p = _input(mode=ConnectionMode.bare_url, connector_key=None, base_url=None)
    assert _resolve_base_url(p) is None


def test_classify_status_codes() -> None:
    ok, kind, _ = _classify(200)
    assert ok is True and kind is None
    ok, kind, _ = _classify(401)
    assert ok is False and kind == "auth_failed"
    ok, kind, _ = _classify(404)
    assert ok is False and kind == "not_found"
    ok, kind, _ = _classify(503)
    assert ok is False and kind == "upstream_error"


@pytest.mark.asyncio
async def test_run_reports_missing_base_url() -> None:
    p = _input(mode=ConnectionMode.bare_url, connector_key=None, base_url=None)
    result: ConnectionTestResult = await run_test(p)
    assert result.ok is False
    assert result.error_kind == "missing_base_url"
    assert result.http_status is None


@pytest.mark.asyncio
async def test_run_handles_network_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx

    class _FailingClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs

        async def __aenter__(self) -> _FailingClient:
            return self

        async def __aexit__(self, *exc: object) -> None:
            return None

        async def request(self, **kwargs: object) -> httpx.Response:
            del kwargs
            raise httpx.ConnectError("dns failed")

    monkeypatch.setattr(ct.httpx, "AsyncClient", _FailingClient)
    p = _input(base_url="https://example.invalid")
    result = await run_test(p)
    assert result.ok is False
    assert result.error_kind == "network_error"
