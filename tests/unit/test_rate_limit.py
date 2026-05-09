from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from harnex_api.api.dependencies import rate_limit as rl
from harnex_api.config import get_settings


@pytest.fixture(autouse=True)
def _isolate_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARNEX_REDIS_URL", "")
    get_settings.cache_clear()
    rl.reset_redis_client()
    rl._recent.clear()
    yield
    monkeypatch.setenv("HARNEX_REDIS_URL", "")
    get_settings.cache_clear()
    rl.reset_redis_client()
    rl._recent.clear()


@pytest.mark.asyncio
async def test_redis_eval_failure_falls_back_without_raising(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARNEX_REDIS_URL", "redis://localhost:6379/0")
    get_settings.cache_clear()
    rl.reset_redis_client()

    import redis.exceptions

    class BoomRedis:
        async def eval(self, *_args: object, **_kwargs: object) -> None:
            raise redis.exceptions.ConnectionError("simulated")

    async def fake_backend() -> BoomRedis:
        return BoomRedis()

    monkeypatch.setattr(rl, "_redis_backend", fake_backend)

    req = MagicMock()
    req.client.host = "192.0.2.1"

    await rl.enforce_tenant_create_budget(req)


@pytest.mark.asyncio
async def test_redis_failure_then_in_memory_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARNEX_REDIS_URL", "redis://localhost:6379/0")
    get_settings.cache_clear()
    rl.reset_redis_client()

    import redis.exceptions

    class BoomRedis:
        async def eval(self, *_args: object, **_kwargs: object) -> None:
            raise redis.exceptions.TimeoutError("simulated")

    boom = BoomRedis()

    async def fake_backend() -> BoomRedis:
        return boom

    monkeypatch.setattr(rl, "_redis_backend", fake_backend)

    req = MagicMock()
    req.client.host = "192.0.2.99"

    limit = rl._MAX_POST_TENANTS_PER_WINDOW
    for _ in range(limit):
        await rl.enforce_tenant_create_budget(req)

    with pytest.raises(HTTPException) as ei:
        await rl.enforce_tenant_create_budget(req)
    assert ei.value.status_code == 429
