"""Unit-level coverage for WebSessionService helpers that need no DB.

The DB-touching paths (`create`, `lookup`, `silently_refresh_if_needed`) are
covered by integration tests that run against a real Postgres + a respx-mocked
Keycloak — they live under `tests/integration/`.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from cryptography.fernet import Fernet

from harnex_api.config import AppSettings, get_settings
from harnex_api.db.models import WebSession
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


def _make_row(*, at_expires_in_seconds: int) -> WebSession:
    now = datetime.now(UTC)
    return WebSession(
        sid_hash=b"\x00" * 32,
        keycloak_user_id="user-x",
        email=None,
        access_token_ct=b"x",
        refresh_token_ct=b"x",
        id_token_ct=None,
        claims_cache={},
        csrf_token="csrf",
        access_token_expires_at=now + timedelta(seconds=at_expires_in_seconds),
        refresh_token_expires_at=now + timedelta(seconds=3600),
        absolute_expires_at=now + timedelta(days=30),
        idle_expires_at=now + timedelta(hours=24),
    )


async def test_revoke_commits_inline(settings_with_key: AppSettings) -> None:
    """Greptile P1 regression — `_revoke` must commit before returning.

    Without an in-place commit, when `silently_refresh_if_needed` re-raises
    `WebSessionAuthError`, FastAPI's `get_db` teardown calls
    `session.rollback()` and the revocation is silently lost — letting the
    same compromised cookie keep loop-refreshing against Keycloak.
    """
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    svc = WebSessionService(db=db, settings=settings_with_key, http=None)  # type: ignore[arg-type]
    row = _make_row(at_expires_in_seconds=300)
    await svc._revoke(row, reason="refresh_reuse")
    db.commit.assert_awaited_once()
    assert row.revoked_at is not None
    assert row.revoked_reason == "refresh_reuse"


async def test_silent_refresh_commits_rotated_tokens(
    settings_with_key: AppSettings,
) -> None:
    """Greptile P1 regression — rotated tokens must persist across rollback.

    Keycloak invalidates the old RT the moment it issues new ones (refresh
    rotation). If `silently_refresh_if_needed` only `flush()`s and the route
    body later raises, `get_db` rolls back the new ciphertexts and the next
    request retries with the stale (now-invalid) RT → `invalid_grant` →
    reuse-detection fires → user permanently logged out for an unrelated
    server error.
    """
    row = _make_row(at_expires_in_seconds=10)  # near expiry → triggers refresh

    # Mock the FOR UPDATE re-read: same row, still un-revoked, still near-expiry.
    locked_result = MagicMock()
    locked_result.scalar_one.return_value = row
    db = MagicMock()
    db.execute = AsyncMock(return_value=locked_result)
    db.commit = AsyncMock()

    svc = WebSessionService(db=db, settings=settings_with_key, http=None)  # type: ignore[arg-type]
    # Seed a valid encrypted RT so `decrypt(latest.refresh_token_ct)` succeeds.
    row.refresh_token_ct = svc.encrypt("the-old-refresh-token")

    new_claims = {"sub": "user-x", "name": "User"}
    new_tokens = MagicMock()
    new_tokens.access_token = "new-access"
    new_tokens.refresh_token = "new-refresh"
    new_tokens.id_token = None
    new_tokens.access_token_expires_at = datetime.now(UTC) + timedelta(seconds=300)
    new_tokens.refresh_token_expires_at = datetime.now(UTC) + timedelta(seconds=3600)
    new_tokens.claims = new_claims
    svc.refresh = AsyncMock(return_value=new_tokens)  # type: ignore[method-assign]

    out = await svc.silently_refresh_if_needed(row)
    assert out is row
    db.commit.assert_awaited_once()
    # Ciphertexts must be the freshly-encrypted new values.
    assert svc.decrypt(row.access_token_ct) == "new-access"
    assert svc.decrypt(row.refresh_token_ct) == "new-refresh"
