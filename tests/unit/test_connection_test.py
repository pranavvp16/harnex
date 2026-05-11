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
    extract_probe_metadata,
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
    p = _input(mode=ConnectionMode.bare_url, base_url="https://example.com/api/")
    assert _resolve_base_url(p) == "https://example.com/api"


def test_resolve_base_url_falls_back_to_connector_default() -> None:
    p = _input(connector_key="github", base_url=None)
    assert _resolve_base_url(p) == "https://api.github.com"


def test_resolve_base_url_builtin_falls_back_when_no_default() -> None:
    p = _input(
        mode=ConnectionMode.builtin,
        connector_key="jenkins",
        base_url="https://jenkins.example/com/",
    )
    assert _resolve_base_url(p) == "https://jenkins.example/com"


def test_resolve_base_url_builtin_ignores_custom_base_url() -> None:
    p = _input(
        mode=ConnectionMode.builtin,
        connector_key="github",
        base_url="http://127.0.0.1:8080/evil",
    )
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


def test_extract_probe_metadata_empty_when_not_ok() -> None:
    meta = extract_probe_metadata(
        probe_ok=False,
        connector_key="github",
        display_base_url="https://api.github.com",
        response_headers={},
        raw_body=b'{"login":"octocat"}',
    )
    assert meta == {}


def test_extract_probe_metadata_instance_only_generic() -> None:
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key=None,
        display_base_url="https://ci.example.com:8080/",
        response_headers={"content-type": "text/html"},
        raw_body=b"<html></html>",
    )
    assert meta["Instance"] == "ci.example.com:8080"
    assert meta["Content-Type"] == "text/html"


def test_extract_github_metadata() -> None:
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key="github",
        display_base_url="https://api.github.com",
        response_headers={"Content-Type": "application/json"},
        raw_body=b'{"login":"octocat","name":"Octo Cat"}',
    )
    assert meta["Username"] == "octocat"
    assert meta["Name"] == "Octo Cat"
    assert meta["Instance"] == "api.github.com"


def test_extract_gitlab_metadata() -> None:
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key="gitlab",
        display_base_url="https://gitlab.com",
        response_headers={"content-type": "application/json"},
        raw_body=b'{"username":"dev","name":"Dev User"}',
    )
    assert meta["Username"] == "dev"
    assert meta["Name"] == "Dev User"


def test_extract_jira_metadata() -> None:
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key="jira",
        display_base_url="https://acme.atlassian.net",
        response_headers={},
        raw_body=(b'{"displayName":"Pat","emailAddress":"pat@example.com","accountId":"a1"}'),
    )
    assert meta["Display name"] == "Pat"
    assert meta["Email"] == "pat@example.com"


def test_extract_jenkins_metadata_prefers_fullname() -> None:
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key="jenkins",
        display_base_url="https://jenkins.example/",
        response_headers={},
        raw_body=b'{"fullName":"Pat Dev","id":"pat"}',
    )
    assert meta["User"] == "Pat Dev"


def test_extract_jenkins_metadata_falls_back_id() -> None:
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key="jenkins",
        display_base_url="https://jenkins.example/",
        response_headers={},
        raw_body=b'{"id":"pat_bot"}',
    )
    assert meta["User"] == "pat_bot"


def test_extract_slack_skips_when_ok_false() -> None:
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key="slack",
        display_base_url="https://slack.com/api",
        response_headers={},
        raw_body=b'{"ok":false,"error":"invalid_auth"}',
    )
    assert "Team" not in meta and "User" not in meta
    assert meta["Instance"] == "slack.com"


def test_extract_slack_metadata_when_ok_true() -> None:
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key="slack",
        display_base_url="https://slack.com/api",
        response_headers={"content-type": "application/json; charset=utf-8"},
        raw_body=(
            b'{"ok":true,"team":"acme","user":"alice","team_id":"T1",'
            b'"url":"https://acme.slack.com/"}'
        ),
    )
    assert meta["Team"] == "acme"
    assert meta["User"] == "alice"


def test_extract_linear_metadata() -> None:
    body = b'{"data":{"viewer":{"id":"lin_1","name":"Alice","email":"a@example.com"}}}'
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key="linear",
        display_base_url="https://api.linear.app",
        response_headers={"content-type": "application/json"},
        raw_body=body,
    )
    assert meta["Viewer ID"] == "lin_1"
    assert meta["Name"] == "Alice"


def test_extract_kubernetes_versions() -> None:
    meta = extract_probe_metadata(
        probe_ok=True,
        connector_key="kubernetes",
        display_base_url="https://kube.example:6443",
        response_headers={"content-type": "application/json"},
        raw_body=(
            b'{"kind":"APIVersions","versions":["v1","apps/v1"],'
            b'"serverAddressByClientCIDRs":[{"serverAddress":"1.2.3.4:6443"}]}'
        ),
    )
    assert meta["Instance"] == "kube.example:6443"
    assert "v1" in meta["API versions"]


@pytest.mark.asyncio
async def test_run_reports_missing_base_url() -> None:
    p = _input(mode=ConnectionMode.bare_url, connector_key=None, base_url=None)
    result: ConnectionTestResult = await run_test(p)
    assert result.ok is False
    assert result.error_kind == "missing_base_url"
    assert result.http_status is None


@pytest.mark.asyncio
async def test_run_blocks_ssrf_loopback() -> None:
    p = _input(mode=ConnectionMode.bare_url, connector_key=None, base_url="http://127.0.0.1:8080/")
    result = await run_test(p)
    assert result.ok is False
    assert result.error_kind == "ssrf_blocked"


@pytest.mark.asyncio
async def test_run_handles_network_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx

    async def _allow_public_url(url: str) -> tuple[bool, str, list[str] | None]:
        del url
        return True, "", None

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

    monkeypatch.setattr(ct, "_guard_public_http_url", _allow_public_url)
    monkeypatch.setattr(ct.httpx, "AsyncClient", _FailingClient)
    p = _input(mode=ConnectionMode.bare_url, connector_key=None, base_url="https://example.invalid")
    result = await run_test(p)
    assert result.ok is False
    assert result.error_kind == "network_error"


@pytest.mark.asyncio
async def test_run_redirect_not_followed(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    async def _allow(url: str) -> tuple[bool, str, list[str] | None]:
        del url
        return True, "", None

    class _RedirectClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs

        async def __aenter__(self) -> object:
            return self

        async def __aexit__(self, *exc: object) -> None:
            return None

        async def request(self, **kwargs: object) -> httpx.Response:
            return httpx.Response(302, headers={"Location": "http://127.0.0.1/private"})

    monkeypatch.setattr(ct, "_guard_public_http_url", _allow)
    monkeypatch.setattr(ct.httpx, "AsyncClient", _RedirectClient)
    p = _input(mode=ConnectionMode.bare_url, connector_key=None, base_url="https://example.com/")
    result = await run_test(p)
    assert result.ok is False
    assert result.error_kind == "redirect_blocked"
