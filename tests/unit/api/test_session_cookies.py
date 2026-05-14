"""Cookie attribute regressions for the BFF session routes.

These tests lock in the fix for the Greptile P1: `delete_cookie` was being
called without the `secure` flag, so logout's Set-Cookie header could fail to
clear a cookie that was originally set with `Secure` (Chrome / Firefox compare
attributes on deletion).
"""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from harnex_api.api.routes.session import _clear_session_cookies, _set_session_cookies
from harnex_api.config import get_settings


@pytest.fixture()
def secure_settings():
    os.environ["HARNEX_SESSION_ENCRYPTION_KEYS"] = Fernet.generate_key().decode()
    os.environ["KEYCLOAK_WEB_CLIENT_SECRET"] = "test-secret"
    os.environ["HARNEX_SESSION_COOKIE_SECURE"] = "true"
    get_settings.cache_clear()  # type: ignore[attr-defined]
    try:
        yield get_settings()
    finally:
        for k in (
            "HARNEX_SESSION_ENCRYPTION_KEYS",
            "KEYCLOAK_WEB_CLIENT_SECRET",
            "HARNEX_SESSION_COOKIE_SECURE",
        ):
            os.environ.pop(k, None)
        get_settings.cache_clear()  # type: ignore[attr-defined]


def _client(handler) -> TestClient:
    app = FastAPI()
    app.get("/")(handler)
    return TestClient(app)


def test_set_session_cookies_include_secure_and_httponly(secure_settings) -> None:
    def handler() -> Response:
        resp = Response()
        _set_session_cookies(resp, sid="sid-x", csrf="csrf-x", settings=secure_settings)
        return resp

    cookies = _client(handler).get("/").headers.get_list("set-cookie")
    sid_cookie = next(c for c in cookies if c.startswith(secure_settings.session_cookie_name + "="))
    csrf_cookie = next(c for c in cookies if c.startswith(secure_settings.csrf_cookie_name + "="))
    assert "Secure" in sid_cookie and "HttpOnly" in sid_cookie
    # SPA needs to read the CSRF cookie, so HttpOnly must NOT be set on it.
    assert "Secure" in csrf_cookie and "HttpOnly" not in csrf_cookie


def test_clear_session_cookies_carry_secure_flag(secure_settings) -> None:
    """Greptile P1 regression — deletion must echo the Secure attr."""

    def handler() -> Response:
        resp = Response()
        _clear_session_cookies(resp, secure_settings)
        return resp

    cookies = _client(handler).get("/").headers.get_list("set-cookie")
    assert any(
        c.startswith(secure_settings.session_cookie_name + "=") and "Secure" in c
        for c in cookies
    ), cookies
    assert any(
        c.startswith(secure_settings.csrf_cookie_name + "=") and "Secure" in c
        for c in cookies
    ), cookies
