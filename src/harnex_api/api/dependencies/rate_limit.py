from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

# Anonymous onboarding spam guard — tweak window/count if needed.

_WINDOW_SECONDS = 60.0
_MAX_POST_TENANTS_PER_WINDOW = 20

_recent: defaultdict[str, deque[float]] = defaultdict(deque)


def _prune(now: float, host: str) -> deque[float]:
    q = _recent[host]
    while q and now - q[0] > _WINDOW_SECONDS:
        q.popleft()
    return q


def enforce_tenant_create_budget(request: Request) -> None:
    """Cheap per-IP limiter for unauthenticated POST /v1/tenants."""
    host = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _prune(now, host)
    if len(q) >= _MAX_POST_TENANTS_PER_WINDOW:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many tenant signups — try again in a minute",
        )
    q.append(now)


__all__ = ["enforce_tenant_create_budget"]
