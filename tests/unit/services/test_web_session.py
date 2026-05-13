"""Unit-level coverage for WebSessionService helpers that need no DB.

The DB-touching paths (`create`, `lookup`, `silently_refresh_if_needed`) are
covered by integration tests that run against a real Postgres + a respx-mocked
Keycloak — they live under `tests/integration/`.
"""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet

from harnex_api.config import AppSettings, get_settings
from harnex_api.services.web_session import (
    WebSessionConfigError,
    WebSessionService,
    build_authorize_url,
)


@pytest.fixture()
def settings_with_key() -> AppSettings:
    os.environ["HARNEX_SESSION_ENCRYPTION_KEYS"] = Fernet.generate_key().decode()
    os.environ["KEYCLOAK_WEB_CLIENT_SECRET"] = "test-secret"
    get_settings.cache_clear()  # type: ignore[attr-defined]
    try:
        yield get_settings()
    finally:
        os.environ.pop("HARNEX_SESSION_ENCRYPTION_KEYS", None)
        os.environ.pop("KEYCLOAK_WEB_CLIENT_SECRET", None)
        get_settings.cache_clear()  # type: ignore[attr-defined]


def test_new_sid_is_url_safe_and_hashes(settings_with_key: AppSettings) -> None:
    cookie, sid_hash = WebSessionService.new_sid()
    assert isinstance(cookie, str) and len(cookie) > 32
    assert isinstance(sid_hash, bytes) and len(sid_hash) == 32
    # Hashing the cookie back must match what we stored.
    assert WebSessionService.hash_sid(cookie) == sid_hash


def test_new_sid_is_unique(settings_with_key: AppSettings) -> None:
    seen = {WebSessionService.new_sid()[0] for _ in range(50)}
    assert len(seen) == 50


def test_fernet_roundtrip(settings_with_key: AppSettings) -> None:
    svc = WebSessionService(db=None, settings=settings_with_key, http=None)  # type: ignore[arg-type]
    ct = svc.encrypt("super-secret-token")
    assert ct != b"super-secret-token"
    assert svc.decrypt(ct) == "super-secret-token"


def test_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARNEX_SESSION_ENCRYPTION_KEYS", "")
    get_settings.cache_clear()  # type: ignore[attr-defined]
    settings = get_settings()
    svc = WebSessionService(db=None, settings=settings, http=None)  # type: ignore[arg-type]
    with pytest.raises(WebSessionConfigError):
        svc.encrypt("anything")
    get_settings.cache_clear()  # type: ignore[attr-defined]


def test_authorize_url_with_idp_hint(settings_with_key: AppSettings) -> None:
    url = build_authorize_url(
        settings=settings_with_key,
        state="STATE",
        code_challenge="CHALLENGE",
        redirect_uri="https://api.example.com/v1/session/callback",
        idp_hint="google",
    )
    assert "response_type=code" in url
    assert "code_challenge=CHALLENGE" in url
    assert "code_challenge_method=S256" in url
    assert "kc_idp_hint=google" in url
    assert "scope=openid+profile+email" in url


def test_authorize_url_no_idp_hint(settings_with_key: AppSettings) -> None:
    url = build_authorize_url(
        settings=settings_with_key,
        state="S",
        code_challenge="C",
        redirect_uri="https://api.example.com/v1/session/callback",
        idp_hint=None,
    )
    assert "kc_idp_hint" not in url
