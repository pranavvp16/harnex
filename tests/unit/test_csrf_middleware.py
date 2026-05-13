"""CSRF middleware invariants.

The most important test here is `test_mcp_path_is_exempt` — it proves that
the cookie/CSRF auth path cannot reach into the mounted MCP sub-app, even
when a session cookie happens to be present in the same browser.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from harnex_api.api.middleware.csrf import CsrfMiddleware
from harnex_api.config import get_settings


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.add_middleware(CsrfMiddleware)

    @app.get("/v1/safe")
    def _safe() -> dict[str, str]:
        return {"ok": "true"}

    @app.post("/v1/state")
    def _state() -> dict[str, str]:
        return {"ok": "true"}

    # Simulate the MCP mount — different ASGI app, but same URL prefix.
    @app.post("/mcp/anything")
    def _mcp() -> dict[str, str]:
        return {"mcp": "true"}

    @app.post("/v1/session/password")
    def _password_login() -> dict[str, str]:
        return {"ok": "true"}

    return TestClient(app)


def _cookies(settings_session: str = "abc", settings_csrf: str = "xyz") -> dict[str, str]:
    settings = get_settings()
    return {
        settings.session_cookie_name: settings_session,
        settings.csrf_cookie_name: settings_csrf,
    }


def test_get_bypasses_csrf(client: TestClient) -> None:
    resp = client.get("/v1/safe")
    assert resp.status_code == 200


def test_post_without_cookie_bypasses_csrf(client: TestClient) -> None:
    # During rollout, Bearer-JWT clients have no session cookie; they must
    # not be 403'd by this middleware.
    resp = client.post("/v1/state")
    assert resp.status_code == 200


def test_post_with_cookie_but_no_csrf_header_is_rejected(client: TestClient) -> None:
    resp = client.post("/v1/state", cookies=_cookies())
    assert resp.status_code == 403
    assert resp.json() == {"detail": "csrf_failed"}


def test_post_with_matching_cookie_and_header_passes(client: TestClient) -> None:
    cookies = _cookies(settings_csrf="match-me")
    resp = client.post(
        "/v1/state", cookies=cookies, headers={"X-CSRF-Token": "match-me"}
    )
    assert resp.status_code == 200


def test_post_with_mismatched_csrf_is_rejected(client: TestClient) -> None:
    cookies = _cookies(settings_csrf="cookie-value")
    resp = client.post(
        "/v1/state", cookies=cookies, headers={"X-CSRF-Token": "header-value"}
    )
    assert resp.status_code == 403


def test_bearer_hnx_bypasses_csrf(client: TestClient) -> None:
    # M2M REST clients with a tenant API key never carry a cookie and must
    # never be challenged by CSRF.
    resp = client.post(
        "/v1/state",
        headers={"Authorization": "Bearer hnx_test_abcdef"},
    )
    assert resp.status_code == 200


def test_bearer_hnx_with_cookie_still_bypasses(client: TestClient) -> None:
    # An hnx... bearer must dominate even when a stray cookie is present.
    resp = client.post(
        "/v1/state",
        cookies=_cookies(),
        headers={"Authorization": "Bearer hnx_test_abcdef"},
    )
    assert resp.status_code == 200


def test_mcp_path_is_exempt(client: TestClient) -> None:
    # The non-negotiable: /mcp must not be touched by CSRF even when a
    # cookie is present and no X-CSRF-Token header is sent.
    resp = client.post("/mcp/anything", cookies=_cookies())
    assert resp.status_code == 200
    assert resp.json() == {"mcp": "true"}


def test_session_login_endpoints_are_exempt(client: TestClient) -> None:
    # /v1/session/password runs before any session exists; CSRF protection
    # is impossible (no cookie yet) and would brick login.
    resp = client.post("/v1/session/password")
    assert resp.status_code == 200
