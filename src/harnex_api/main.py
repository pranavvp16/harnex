from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from harnex_api import __version__
from harnex_api.api.routes import (
    api_keys,
    connections,
    connectors,
    execute,
    executions,
    search,
    usage,
)
from harnex_api.config import AppSettings, get_settings
from harnex_api.logging import configure_logging, get_logger
from harnex_api.mcp.server import build_streamable_http_app


async def _provision_sandbox(settings: AppSettings) -> None:
    """Idempotent sandbox warm-up — mirrors scripts/blaxel_provision.py."""
    os.environ.setdefault("BL_API_KEY", settings.blaxel_api_key.get_secret_value())
    os.environ.setdefault("BL_WORKSPACE", settings.blaxel_workspace)
    from blaxel.core import SandboxInstance  # local import — keep SDK out of cold path

    config: dict[str, Any] = {
        "name": settings.blaxel_sandbox_name,
        "image": settings.blaxel_sandbox_image,
        "memory": settings.blaxel_sandbox_memory_mb,
        "region": settings.blaxel_sandbox_region,
    }
    await SandboxInstance.create_if_not_exists(config)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    log = get_logger("harnex_api")
    log.info("startup", env=settings.env, version=__version__)
    if settings.blaxel_api_key.get_secret_value():
        try:
            await _provision_sandbox(settings)
            log.info("blaxel_sandbox_ready", name=settings.blaxel_sandbox_name)
        except Exception as exc:
            # Non-fatal — code-mode execute calls will fail gracefully at request time.
            log.warning("blaxel_sandbox_unavailable", error=str(exc))
    try:
        yield
    finally:
        log.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Harnex API",
        version=__version__,
        lifespan=lifespan,
    )

    if settings.env in ("local", "dev"):
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "env": settings.env, "version": __version__}

    app.include_router(connectors.router)
    app.include_router(connections.router)
    app.include_router(api_keys.router)
    app.include_router(executions.router)
    app.include_router(usage.router)
    app.include_router(search.router)
    app.include_router(execute.router)

    # MCP shipped surface — exactly two tools (search, execute), bearer auth via tenant API keys.
    app.mount("/mcp", build_streamable_http_app())

    return app


app = create_app()
