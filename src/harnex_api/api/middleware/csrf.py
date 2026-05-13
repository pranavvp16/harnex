"""Double-submit CSRF middleware for cookie-authenticated requests.

Active only when a session cookie is present. Bypasses everything that
doesn't share the cookie attack surface:

- `/mcp` (Starlette sub-app, hnx... API keys — must remain untouched)
- `Authorization: Bearer hnx...` machine clients
- Safe methods (GET/HEAD/OPTIONS)
- Login / register endpoints (no session yet)
- Cookie-less Bearer-JWT requests during the rollout window
"""

from __future__ import annotations

import hmac

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from harnex_api.config import get_settings
from harnex_api.logging import get_logger

_log = get_logger("harnex_api.csrf")

# /mcp is checked FIRST so the sub-app is never touched by CSRF logic.
_EXEMPT_PATH_PREFIXES: tuple[str, ...] = (
    "/mcp",
    "/v1/session/login",
    "/v1/session/callback",
    "/v1/session/password",
    "/v1/auth/register",
    "/healthz",
)
_SAFE_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS"})


class CsrfMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # MCP is a mounted Starlette sub-app authenticated by tenant API keys.
        # Must short-circuit before any cookie/header inspection.
        if any(path.startswith(prefix) for prefix in _EXEMPT_PATH_PREFIXES):
            return await call_next(request)
        if request.method in _SAFE_METHODS:
            return await call_next(request)

        # M2M REST clients carry an `hnx...` API key, no cookie. Bypass.
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer hnx"):
            return await call_next(request)

        settings = get_settings()
        cookie = request.cookies.get(settings.session_cookie_name)
        if cookie is None:
            # No cookie → either legacy Bearer JWT (rollout) or anonymous. CSRF
            # protection is meaningless without an ambient credential.
            return await call_next(request)

        header = request.headers.get("X-CSRF-Token", "")
        csrf_cookie = request.cookies.get(settings.csrf_cookie_name, "")
        if not header or not csrf_cookie or not hmac.compare_digest(header, csrf_cookie):
            _log.warning(
                "csrf_rejected",
                path=path,
                method=request.method,
                has_header=bool(header),
                has_cookie=bool(csrf_cookie),
            )
            return JSONResponse(status_code=403, content={"detail": "csrf_failed"})

        return await call_next(request)


__all__ = ["CsrfMiddleware"]
