from __future__ import annotations

import asyncio
import logging
import secrets
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import HTTPException, Request, status

from harnex_api.config import get_settings

# Anonymous onboarding spam guard — tweak window/count if needed.

_WINDOW_SECONDS = 60.0
_MAX_POST_TENANTS_PER_WINDOW = 20

_LOG = logging.getLogger(__name__)

# Dev-only fallback when HARNEX_REDIS_URL is unset: per-process deque (no coordination
# across workers; resets on restart).
_recent: defaultdict[str, deque[float]] = defaultdict(deque)

_redis_lock = asyncio.Lock()
_redis_client: Any | None = None

_RLUA = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[2])
local n = redis.call('ZCARD', KEYS[1])
if n >= tonumber(ARGV[4]) then
  return 0
end
redis.call('ZADD', KEYS[1], ARGV[1], ARGV[3])
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[5]))
return 1
"""


def reset_redis_client() -> None:
    """Clear cached Redis connection (tests / settings reload)."""
    global _redis_client
    _redis_client = None


def _prune(now: float, host: str) -> deque[float]:
    q = _recent[host]
    while q and now - q[0] > _WINDOW_SECONDS:
        q.popleft()
    return q


async def _redis_backend() -> Any | None:
    global _redis_client
    url = (get_settings().redis_url or "").strip()
    if not url:
        return None
    async with _redis_lock:
        if _redis_client is None:
            import redis.asyncio as redis  # lazy — optional dependency surface

            _redis_client = redis.from_url(url, encoding="utf-8", decode_responses=True)
        return _redis_client


async def enforce_tenant_create_budget(request: Request) -> None:
    """Per-IP sliding-window limiter for unauthenticated POST /v1/tenants."""
    host = request.client.host if request.client else "unknown"
    redis_client = await _redis_backend()
    if redis_client is None:
        now = time.monotonic()
        q = _prune(now, host)
        if len(q) >= _MAX_POST_TENANTS_PER_WINDOW:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail="too many tenant signups — try again in a minute",
            )
        q.append(now)
        _LOG.debug(
            "tenant_create_rate_limit_memory",
            extra={"host": host, "note": "set HARNEX_REDIS_URL for Redis-backed limiting"},
        )
        return

    key = f"harnex:rl:tenant_create:{host}"
    now_ts = time.time()
    member = secrets.token_hex(16)
    allowed_raw = await redis_client.eval(
        _RLUA,
        1,
        key,
        str(now_ts),
        str(now_ts - _WINDOW_SECONDS),
        member,
        str(_MAX_POST_TENANTS_PER_WINDOW),
        str(int(_WINDOW_SECONDS) + 5),
    )
    allowed = int(allowed_raw) if allowed_raw is not None else 0
    if allowed != 1:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many tenant signups — try again in a minute",
        )


__all__ = ["enforce_tenant_create_budget", "reset_redis_client"]
