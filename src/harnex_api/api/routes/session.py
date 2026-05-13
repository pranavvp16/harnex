"""BFF cookie-session endpoints.

The web console authenticates via these routes; they own the OIDC code
exchange / password grant against Keycloak, set `HttpOnly` cookies, and
expose login / logout. The browser never sees an access or refresh token.

MCP (`/mcp`) is unaffected — it has its own bearer-API-key middleware in
`mcp/server.py` and does not touch any code in this module.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from typing import Literal
from urllib.parse import quote

from cryptography.fernet import InvalidToken, MultiFernet
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.session import (
    SessionMeOut,
    SessionPasswordIn,
    SessionPasswordOut,
    SessionUser,
)
from harnex_api.api.schemas.tenants import MembershipOut
from harnex_api.config import AppSettings, get_settings
from harnex_api.db.models import TenantMembership
from harnex_api.logging import get_logger
from harnex_api.services.web_session import (
    WebSessionAuthError,
    WebSessionConfigError,
    WebSessionService,
    build_authorize_url,
    get_shared_http,
)

router = APIRouter(prefix="/v1/session", tags=["session"])

_log = get_logger("harnex_api.session")

# Cookie carrying the OAuth state during the 5-minute /login -> /callback
# round-trip. Fernet-encrypted JSON; cleared once /callback consumes it.
_STATE_COOKIE_NAME = "harnex_oauth_state"
_STATE_TTL_SECONDS = 300


def _service(db: AsyncSession, settings: AppSettings) -> WebSessionService:
    return WebSessionService(db, settings, get_shared_http())


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip() or None
    return request.client.host if request.client else None


# ---------- Cookie helpers ----------


def _samesite(value: str) -> Literal["lax", "strict", "none"]:
    if value == "strict":
        return "strict"
    if value == "none":
        return "none"
    return "lax"


def _set_session_cookies(
    response: Response, *, sid: str, csrf: str, settings: AppSettings
) -> None:
    domain = settings.session_cookie_domain or None
    secure = settings.session_cookie_secure
    samesite = _samesite(settings.session_cookie_samesite)
    max_age = settings.session_absolute_ttl_seconds
    response.set_cookie(
        settings.session_cookie_name,
        sid,
        max_age=max_age,
        path="/",
        domain=domain,
        secure=secure,
        httponly=True,
        samesite=samesite,
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf,
        max_age=max_age,
        path="/",
        domain=domain,
        secure=secure,
        httponly=False,  # SPA reads this and echoes via X-CSRF-Token
        samesite=samesite,
    )


def _clear_session_cookies(response: Response, settings: AppSettings) -> None:
    # Browsers (Chrome ≥ 70's "schemeful same-site", recent Firefox) require
    # the deletion Set-Cookie's attributes to match the original — otherwise
    # the cookie silently survives logout. Mirror the same attrs we set in
    # _set_session_cookies, except `httponly` which differs per cookie.
    samesite = _samesite(settings.session_cookie_samesite)
    domain = settings.session_cookie_domain or None
    secure = settings.session_cookie_secure
    response.delete_cookie(
        settings.session_cookie_name,
        domain=domain,
        path="/",
        secure=secure,
        httponly=True,
        samesite=samesite,
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        domain=domain,
        path="/",
        secure=secure,
        httponly=False,
        samesite=samesite,
    )


# ---------- PKCE / state ----------


def _new_pkce() -> tuple[str, str]:
    """Returns (verifier, S256 challenge)."""
    verifier = secrets.token_urlsafe(64)[:96]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _state_fernet(settings: AppSettings) -> MultiFernet | None:
    return WebSessionService._build_fernet(settings)


def _encode_state(payload: dict[str, object], settings: AppSettings) -> str:
    f = _state_fernet(settings)
    if f is None:
        raise WebSessionConfigError(
            "HARNEX_SESSION_ENCRYPTION_KEYS not set — cannot sign OAuth state"
        )
    return f.encrypt(json.dumps(payload).encode("utf-8")).decode("ascii")


def _decode_state(value: str, settings: AppSettings) -> dict[str, object] | None:
    f = _state_fernet(settings)
    if f is None:
        return None
    try:
        raw = f.decrypt(value.encode("ascii"), ttl=_STATE_TTL_SECONDS)
    except InvalidToken:
        return None
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return decoded if isinstance(decoded, dict) else None


def _validate_return_to(value: str | None) -> str:
    """Block open-redirect attempts; only allow same-origin paths."""
    if not value:
        return "/"
    if not value.startswith("/"):
        return "/"
    if value.startswith("//") or value.startswith("/\\"):
        return "/"
    if any(ord(ch) < 0x20 for ch in value):
        return "/"
    return value


def _redirect_uri(settings: AppSettings) -> str:
    return f"{settings.api_base_url.rstrip('/')}/v1/session/callback"


# ---------- Routes ----------


@router.get("/login")
async def login(
    request: Request,
    idp_hint: str | None = None,
    return_to: str | None = None,
) -> RedirectResponse:
    """Start the auth-code (PKCE) flow against Keycloak.

    Generates a state + PKCE verifier, stores them in a 5-minute Fernet cookie,
    and 307s the browser to Keycloak's /auth endpoint.
    """
    settings = get_settings()
    if idp_hint is not None and idp_hint not in {"google", "github"}:
        raise HTTPException(status_code=400, detail="unsupported idp_hint")

    state = secrets.token_urlsafe(32)
    verifier, challenge = _new_pkce()
    try:
        encoded = _encode_state(
            {
                "state": state,
                "verifier": verifier,
                "return_to": _validate_return_to(return_to),
                "idp_hint": idp_hint,
            },
            settings,
        )
    except WebSessionConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    auth_url = build_authorize_url(
        settings=settings,
        state=state,
        code_challenge=challenge,
        redirect_uri=_redirect_uri(settings),
        idp_hint=idp_hint,
    )

    response = RedirectResponse(url=auth_url, status_code=307)
    response.set_cookie(
        _STATE_COOKIE_NAME,
        encoded,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=_STATE_TTL_SECONDS,
        # Scope to the callback path so the cookie isn't carried on every request.
        path="/v1/session/callback",
    )
    return response


@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle the Keycloak redirect; create a session row + cookies."""
    settings = get_settings()
    web_base = settings.web_base_url.rstrip("/")

    def _bounce_error(reason: str) -> RedirectResponse:
        resp = RedirectResponse(
            url=f"{web_base}/login?auth_error={quote(reason)}", status_code=303
        )
        resp.delete_cookie(_STATE_COOKIE_NAME, path="/v1/session/callback")
        return resp

    if error:
        _log.info("kc_callback_error", error=error, description=error_description)
        return _bounce_error(error)
    if not code or not state:
        return _bounce_error("invalid_callback")

    state_cookie = request.cookies.get(_STATE_COOKIE_NAME)
    if not state_cookie:
        return _bounce_error("state_missing")
    decoded = _decode_state(state_cookie, settings)
    if decoded is None:
        return _bounce_error("state_invalid")
    if decoded.get("state") != state:
        return _bounce_error("state_mismatch")
    verifier = decoded.get("verifier")
    raw_return_to = decoded.get("return_to")
    return_to = _validate_return_to(raw_return_to if isinstance(raw_return_to, str) else None)
    if not isinstance(verifier, str):
        return _bounce_error("state_invalid")

    svc = _service(db, settings)
    try:
        tokens = await svc.exchange_code(
            code=code, redirect_uri=_redirect_uri(settings), code_verifier=verifier
        )
        row, sid = await svc.create(
            tokens=tokens,
            ip=_client_ip(request),
            ua=request.headers.get("user-agent"),
        )
    except (WebSessionAuthError, WebSessionConfigError) as exc:
        _log.warning("session_create_failed", error=str(exc))
        return _bounce_error("login_failed")

    response = RedirectResponse(url=f"{web_base}{return_to}", status_code=303)
    _set_session_cookies(response, sid=sid, csrf=row.csrf_token, settings=settings)
    response.delete_cookie(_STATE_COOKIE_NAME, path="/v1/session/callback")
    await db.commit()
    return response


@router.post(
    "/password",
    response_model=SessionPasswordOut,
    status_code=status.HTTP_200_OK,
)
async def password_login(
    payload: SessionPasswordIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> SessionPasswordOut:
    """Direct password sign-in via the confidential client.

    Replaces the browser-side Direct Access Grants call. Rate-limiting is
    expected to live at the reverse-proxy or a future Redis token-bucket
    middleware; this route deliberately does not gate itself.
    """
    settings = get_settings()
    svc = _service(db, settings)
    try:
        tokens = await svc.password_grant(
            username=str(payload.email), password=payload.password
        )
        row, sid = await svc.create(
            tokens=tokens,
            ip=_client_ip(request),
            ua=request.headers.get("user-agent"),
        )
    except WebSessionAuthError as exc:
        # invalid_grant from Keycloak → bad creds. Anything else is upstream.
        if exc.kc_error == "invalid_grant":
            raise HTTPException(
                status_code=401,
                detail={"code": "invalid_credentials"},
            ) from exc
        raise HTTPException(
            status_code=502,
            detail={"code": "auth_provider_error", "kc_error": exc.kc_error},
        ) from exc
    except WebSessionConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _set_session_cookies(response, sid=sid, csrf=row.csrf_token, settings=settings)
    await db.commit()
    user = SessionUser(
        sub=row.keycloak_user_id,
        email=row.email,
        full_name=(
            row.claims_cache.get("name")
            or row.claims_cache.get("preferred_username")
            if isinstance(row.claims_cache, dict)
            else None
        ),
    )
    return SessionPasswordOut(ok=True, user=user, csrf_token=row.csrf_token)


@router.get("/me", response_model=SessionMeOut)
async def me(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SessionMeOut:
    """Cookie-authenticated identity + workspaces; used by the SPA on boot."""
    settings = get_settings()
    sid = request.cookies.get(settings.session_cookie_name)
    if not sid:
        raise HTTPException(status_code=401, detail="no_session")
    svc = _service(db, settings)
    row = await svc.lookup(sid)
    if row is None:
        raise HTTPException(status_code=401, detail="session_expired")
    try:
        row = await svc.silently_refresh_if_needed(row)
    except WebSessionAuthError as exc:
        raise HTTPException(status_code=401, detail="session_expired") from exc
    await svc.touch(row, ip=_client_ip(request), ua=request.headers.get("user-agent"))
    await db.commit()

    rows = await db.execute(
        select(TenantMembership)
        .where(TenantMembership.keycloak_user_id == row.keycloak_user_id)
        .options(selectinload(TenantMembership.tenant))
    )
    memberships = [MembershipOut.model_validate(m) for m in rows.scalars().all()]
    full_name = None
    if isinstance(row.claims_cache, dict):
        n = row.claims_cache.get("name") or row.claims_cache.get("preferred_username")
        full_name = n if isinstance(n, str) else None

    return SessionMeOut(
        sub=row.keycloak_user_id,
        email=row.email,
        full_name=full_name,
        memberships=memberships,
        csrf_token=row.csrf_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Idempotent logout — revoke the current session and clear cookies."""
    settings = get_settings()
    sid = request.cookies.get(settings.session_cookie_name)
    if sid:
        svc = _service(db, settings)
        row = await svc.lookup(sid)
        if row is not None:
            await svc.revoke(row, reason="logout")
            await db.commit()
    _clear_session_cookies(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Revoke every session for the current caller's Keycloak `sub`."""
    settings = get_settings()
    sid = request.cookies.get(settings.session_cookie_name)
    if not sid:
        raise HTTPException(status_code=401, detail="no_session")
    svc = _service(db, settings)
    row = await svc.lookup(sid)
    if row is None:
        _clear_session_cookies(response, settings)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response
    await svc.revoke_all_for_user(row.keycloak_user_id, reason="logout_all")
    await db.commit()
    _clear_session_cookies(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


__all__ = ["router"]
