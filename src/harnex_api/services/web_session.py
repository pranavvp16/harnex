"""Backing service for the BFF cookie-session auth.

Owns:
- Opaque session id generation + SHA-256 hashing for at-rest storage.
- Fernet (MultiFernet) symmetric encryption of Keycloak tokens.
- Keycloak HTTP exchanges: auth-code, password grant, refresh, RP-initiated logout.
- Session row lifecycle: create / lookup / touch / silent-refresh / revoke.

No FastAPI imports — pure service so it can be unit-tested without the app.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from harnex_api.config import AppSettings
from harnex_api.db.models import WebSession
from harnex_api.logging import get_logger

_log = get_logger("harnex_api.web_session")

# Shared httpx client for Keycloak calls — kept module-level so connection
# pooling works across both `routes/session.py` and `dependencies/auth.py`.
_shared_http: httpx.AsyncClient | None = None


def get_shared_http() -> httpx.AsyncClient:
    global _shared_http
    if _shared_http is None:
        _shared_http = httpx.AsyncClient(timeout=10.0)
    return _shared_http


class WebSessionError(Exception):
    """Base error raised by the service. The route layer maps to HTTP codes."""


class WebSessionConfigError(WebSessionError):
    """Service was constructed without a usable encryption key or client secret."""


class WebSessionAuthError(WebSessionError):
    """Keycloak rejected the credentials / code / refresh token."""

    def __init__(self, message: str, *, kc_error: str | None = None) -> None:
        super().__init__(message)
        self.kc_error = kc_error


@dataclass(frozen=True)
class TokenSet:
    """Normalized output of any Keycloak token exchange."""

    access_token: str
    refresh_token: str
    id_token: str | None
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    claims: dict[str, Any]


def _now() -> datetime:
    return datetime.now(UTC)


def _decode_segment(seg: str) -> dict[str, Any]:
    padded = seg.replace("-", "+").replace("_", "/")
    pad_len = (4 - (len(padded) % 4)) % 4
    raw = base64.b64decode(padded + "=" * pad_len)
    decoded: dict[str, Any] = json.loads(raw)
    return decoded


def _decode_jwt_claims(token: str) -> dict[str, Any]:
    """Best-effort claim extraction (no signature check) for cache only.

    Tokens are obtained from a TLS connection to our confidential Keycloak
    client, so re-verifying the signature here would be belt-and-braces.
    """
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    try:
        return _decode_segment(parts[1])
    except (ValueError, json.JSONDecodeError):
        return {}


def _safe_user_fields(claims: dict[str, Any]) -> tuple[str, str | None, str | None]:
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise WebSessionAuthError("token missing sub")
    email = claims.get("email") if isinstance(claims.get("email"), str) else None
    name = claims.get("name") or claims.get("preferred_username")
    full_name = name if isinstance(name, str) else None
    return sub, email, full_name


def build_authorize_url(
    *,
    settings: AppSettings,
    state: str,
    code_challenge: str,
    redirect_uri: str,
    idp_hint: str | None,
) -> str:
    """Build Keycloak's authorization endpoint URL for the auth-code (PKCE) flow.

    Module-level helper so callers don't need a DB session to construct it
    (the login route runs before any session exists).
    """
    base = (settings.keycloak_issuer_base_url or settings.keycloak_base_url).rstrip("/")
    params: list[tuple[str, str]] = [
        ("response_type", "code"),
        ("client_id", settings.keycloak_web_client_id),
        ("redirect_uri", redirect_uri),
        ("scope", "openid profile email"),
        ("state", state),
        ("code_challenge", code_challenge),
        ("code_challenge_method", "S256"),
    ]
    if idp_hint:
        params.append(("kc_idp_hint", idp_hint))
    return (
        f"{base}/realms/{settings.keycloak_realm}/protocol/openid-connect/auth"
        f"?{urlencode(params)}"
    )


class WebSessionService:
    def __init__(
        self,
        db: AsyncSession,
        settings: AppSettings,
        http: httpx.AsyncClient,
    ) -> None:
        self._db = db
        self._settings = settings
        self._http = http
        self._fernet = self._build_fernet(settings)

    # ---------- crypto ----------

    @staticmethod
    def _build_fernet(settings: AppSettings) -> MultiFernet | None:
        raw = settings.session_encryption_keys.get_secret_value().strip()
        if not raw:
            return None
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        if not keys:
            return None
        return MultiFernet([Fernet(k.encode("ascii")) for k in keys])

    def _require_fernet(self) -> MultiFernet:
        if self._fernet is None:
            raise WebSessionConfigError(
                "HARNEX_SESSION_ENCRYPTION_KEYS not set — cookie sessions disabled."
            )
        return self._fernet

    def encrypt(self, plaintext: str) -> bytes:
        return self._require_fernet().encrypt(plaintext.encode("utf-8"))

    def decrypt(self, ciphertext: bytes) -> str:
        return self._require_fernet().decrypt(ciphertext).decode("utf-8")

    # ---------- session id ----------

    @staticmethod
    def new_sid() -> tuple[str, bytes]:
        """Returns (cookie_value, sha256_hash_for_db)."""
        cookie = secrets.token_urlsafe(32)
        return cookie, hashlib.sha256(cookie.encode("ascii")).digest()

    @staticmethod
    def hash_sid(cookie_value: str) -> bytes:
        return hashlib.sha256(cookie_value.encode("ascii")).digest()

    @staticmethod
    def new_csrf() -> str:
        return secrets.token_urlsafe(32)

    # ---------- Keycloak HTTP ----------

    def _token_url(self) -> str:
        base = (self._settings.keycloak_issuer_base_url or self._settings.keycloak_base_url).rstrip("/")
        return f"{base}/realms/{self._settings.keycloak_realm}/protocol/openid-connect/token"

    def _logout_url(self) -> str:
        base = (self._settings.keycloak_issuer_base_url or self._settings.keycloak_base_url).rstrip("/")
        return f"{base}/realms/{self._settings.keycloak_realm}/protocol/openid-connect/logout"

    async def _post_token(self, body: dict[str, str]) -> TokenSet:
        secret = self._settings.keycloak_web_client_secret.get_secret_value()
        if not secret:
            raise WebSessionConfigError("KEYCLOAK_WEB_CLIENT_SECRET is not configured")
        payload = {**body, "client_id": self._settings.keycloak_web_client_id, "client_secret": secret}
        resp = await self._http.post(
            self._token_url(),
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            try:
                data = resp.json()
            except ValueError:
                data = {}
            kc_err = data.get("error") if isinstance(data, dict) else None
            raise WebSessionAuthError(
                f"keycloak token endpoint returned {resp.status_code}",
                kc_error=kc_err,
            )
        data = resp.json()
        access_token = data["access_token"]
        refresh_token = data.get("refresh_token") or ""
        if not refresh_token:
            raise WebSessionAuthError("keycloak response missing refresh_token")
        id_token = data.get("id_token")
        expires_in = int(data.get("expires_in", 0))
        refresh_expires_in = int(data.get("refresh_expires_in", 0))
        # 60s skew buffer — never trust the bare expires_in.
        now = _now()
        at_exp = now + timedelta(seconds=max(expires_in - 60, 30))
        rt_exp = now + timedelta(seconds=max(refresh_expires_in - 60, 60))
        claims = _decode_jwt_claims(id_token or access_token)
        return TokenSet(
            access_token=access_token,
            refresh_token=refresh_token,
            id_token=id_token,
            access_token_expires_at=at_exp,
            refresh_token_expires_at=rt_exp,
            claims=claims,
        )

    async def exchange_code(
        self, *, code: str, redirect_uri: str, code_verifier: str
    ) -> TokenSet:
        return await self._post_token(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            }
        )

    async def password_grant(self, *, username: str, password: str) -> TokenSet:
        return await self._post_token(
            {
                "grant_type": "password",
                "username": username,
                "password": password,
                "scope": "openid profile email",
            }
        )

    async def refresh(self, refresh_token: str) -> TokenSet:
        return await self._post_token(
            {"grant_type": "refresh_token", "refresh_token": refresh_token}
        )

    async def kc_logout(self, refresh_token: str) -> None:
        secret = self._settings.keycloak_web_client_secret.get_secret_value()
        if not secret:
            return
        try:
            await self._http.post(
                self._logout_url(),
                data={
                    "client_id": self._settings.keycloak_web_client_id,
                    "client_secret": secret,
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as exc:
            # Best-effort — local session is already gone.
            _log.warning("kc_logout_failed", error=str(exc))

    # ---------- session lifecycle ----------

    async def create(
        self,
        *,
        tokens: TokenSet,
        ip: str | None,
        ua: str | None,
    ) -> tuple[WebSession, str]:
        """Create a new session row; returns (row, plaintext_sid_for_cookie)."""
        sub, email, _full_name = _safe_user_fields(tokens.claims)
        sid_plain, sid_hash = self.new_sid()
        now = _now()
        row = WebSession(
            sid_hash=sid_hash,
            keycloak_user_id=sub,
            email=email,
            access_token_ct=self.encrypt(tokens.access_token),
            refresh_token_ct=self.encrypt(tokens.refresh_token),
            id_token_ct=self.encrypt(tokens.id_token) if tokens.id_token else None,
            claims_cache=tokens.claims,
            csrf_token=self.new_csrf(),
            access_token_expires_at=tokens.access_token_expires_at,
            refresh_token_expires_at=tokens.refresh_token_expires_at,
            absolute_expires_at=now
            + timedelta(seconds=self._settings.session_absolute_ttl_seconds),
            idle_expires_at=now
            + timedelta(seconds=self._settings.session_idle_ttl_seconds),
            last_seen_at=now,
            last_seen_ip=ip,
            last_seen_ua=(ua or "")[:256] or None,
        )
        self._db.add(row)
        await self._db.flush()
        return row, sid_plain

    async def lookup(self, sid_plaintext: str) -> WebSession | None:
        """Return a live session row for the given cookie value, else None.

        "Live" = not revoked, idle TTL not exceeded, absolute TTL not exceeded.
        """
        if not sid_plaintext:
            return None
        sid_hash = self.hash_sid(sid_plaintext)
        result = await self._db.execute(
            select(WebSession).where(WebSession.sid_hash == sid_hash)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        now = _now()
        if row.revoked_at is not None:
            return None
        if row.idle_expires_at <= now or row.absolute_expires_at <= now:
            return None
        return row

    async def touch(
        self,
        row: WebSession,
        *,
        ip: str | None,
        ua: str | None,
    ) -> None:
        now = _now()
        new_idle = min(
            now + timedelta(seconds=self._settings.session_idle_ttl_seconds),
            row.absolute_expires_at,
        )
        # `func.now()` for updated_at because raw `execute(update(...))` skips
        # the SQLAlchemy ORM unit-of-work and so TimestampMixin's `onupdate`
        # hook doesn't fire on its own.
        await self._db.execute(
            update(WebSession)
            .where(WebSession.id == row.id)
            .values(
                last_seen_at=now,
                last_seen_ip=ip,
                last_seen_ua=(ua or "")[:256] or None,
                idle_expires_at=new_idle,
                updated_at=func.now(),
            )
        )
        row.last_seen_at = now
        row.last_seen_ip = ip
        row.last_seen_ua = (ua or "")[:256] or None
        row.idle_expires_at = new_idle

    async def silently_refresh_if_needed(self, row: WebSession) -> WebSession:
        """Refresh the access token if it's within 60s of expiry.

        Uses ``SELECT ... FOR UPDATE`` on the session row to serialize multi-tab
        refreshes — a parallel refresh would invalidate the family under
        Keycloak's refresh-token rotation. Losers re-read the row after the
        winner commits and use the freshly-rotated tokens.
        """
        if row.access_token_expires_at > _now() + timedelta(seconds=60):
            return row

        # Lock and re-read the row; another worker may have just rotated tokens.
        locked = await self._db.execute(
            select(WebSession).where(WebSession.id == row.id).with_for_update()
        )
        latest = locked.scalar_one()
        if latest.revoked_at is not None:
            raise WebSessionAuthError("session revoked during refresh")
        if latest.access_token_expires_at > _now() + timedelta(seconds=60):
            # Another worker won the race; use its fresh tokens.
            return latest

        try:
            refresh_plain = self.decrypt(latest.refresh_token_ct)
        except InvalidToken as exc:
            await self._revoke(latest, reason="decrypt_failed")
            raise WebSessionAuthError("session ciphertext invalid") from exc

        try:
            tokens = await self.refresh(refresh_plain)
        except WebSessionAuthError as exc:
            # Refresh-token reuse / invalid_grant → kill the session.
            if exc.kc_error in {"invalid_grant", "unauthorized_client"}:
                await self._revoke(latest, reason="refresh_reuse")
                # Best-effort: tell Keycloak the now-revoked RT is dead.
                with contextlib.suppress(Exception):
                    await self.kc_logout(refresh_plain)
            raise

        latest.access_token_ct = self.encrypt(tokens.access_token)
        latest.refresh_token_ct = self.encrypt(tokens.refresh_token)
        if tokens.id_token:
            latest.id_token_ct = self.encrypt(tokens.id_token)
        latest.claims_cache = tokens.claims
        latest.access_token_expires_at = tokens.access_token_expires_at
        latest.refresh_token_expires_at = tokens.refresh_token_expires_at
        await self._db.flush()
        return latest

    async def _revoke(self, row: WebSession, *, reason: str) -> None:
        """Mark a session revoked and **commit immediately**.

        Revocations must survive the caller's exception path. The reuse-
        detection flow in `silently_refresh_if_needed` revokes and then
        re-raises `WebSessionAuthError`; the route layer maps that to an
        `HTTPException`, which triggers `get_db`'s `session.rollback()`.
        Without the commit here, the revocation row never lands on disk,
        every subsequent request finds the session un-revoked, locks it,
        retries the refresh, and hits Keycloak again — turning a
        compromised session into a per-request token-storm against
        Keycloak's `/token` endpoint. Committing in-place breaks that loop.
        """
        now = _now()
        await self._db.execute(
            update(WebSession)
            .where(WebSession.id == row.id)
            .values(revoked_at=now, revoked_reason=reason, updated_at=func.now())
        )
        await self._db.commit()
        row.revoked_at = now
        row.revoked_reason = reason

    async def revoke(self, row: WebSession, *, reason: str = "logout") -> None:
        if row.revoked_at is not None:
            return
        try:
            refresh_plain = self.decrypt(row.refresh_token_ct)
        except InvalidToken:
            refresh_plain = None
        await self._revoke(row, reason=reason)
        if refresh_plain:
            await self.kc_logout(refresh_plain)

    async def revoke_all_for_user(self, sub: str, *, reason: str = "logout_all") -> int:
        """Revoke every live session for `sub` AND tell Keycloak.

        DB-only revocation isn't enough — an exfiltrated refresh token would
        still be exchangeable at Keycloak's /token endpoint. So we decrypt
        each session's RT and POST it to /protocol/openid-connect/logout
        before marking the row revoked. Best-effort per session — a single
        Keycloak hiccup must not block the rest from being killed.
        """
        rows_result = await self._db.execute(
            select(WebSession).where(
                WebSession.keycloak_user_id == sub,
                WebSession.revoked_at.is_(None),
            )
        )
        rows = list(rows_result.scalars().all())
        for row in rows:
            try:
                refresh_plain = self.decrypt(row.refresh_token_ct)
            except InvalidToken:
                refresh_plain = None
            if refresh_plain:
                with contextlib.suppress(Exception):
                    await self.kc_logout(refresh_plain)

        if not rows:
            return 0
        now = _now()
        result = await self._db.execute(
            update(WebSession)
            .where(
                WebSession.keycloak_user_id == sub,
                WebSession.revoked_at.is_(None),
            )
            .values(revoked_at=now, revoked_reason=reason, updated_at=func.now())
        )
        # CursorResult.rowcount exists on UPDATE; SQLAlchemy's Result base type
        # doesn't expose it. The fallback handles the dialect-shaped Result.
        return int(getattr(result, "rowcount", 0) or len(rows))

    async def delete_expired(self, *, grace_seconds: int = 7 * 86400) -> int:
        """Purge sessions whose absolute TTL passed or whose revocation aged out.

        The grace window keeps recently-revoked rows around long enough for
        audit / forensics. Intended to be invoked by a cron job — see
        `scripts/cleanup_web_sessions.py`.
        """
        now = _now()
        cutoff = now - timedelta(seconds=grace_seconds)
        result = await self._db.execute(
            delete(WebSession).where(
                or_(
                    WebSession.absolute_expires_at < cutoff,
                    WebSession.revoked_at < cutoff,
                )
            )
        )
        return int(getattr(result, "rowcount", 0) or 0)


__all__ = [
    "TokenSet",
    "WebSessionAuthError",
    "WebSessionConfigError",
    "WebSessionError",
    "WebSessionService",
    "build_authorize_url",
    "get_shared_http",
]
