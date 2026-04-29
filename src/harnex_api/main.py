from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
from harnex_api.config import get_settings
from harnex_api.logging import configure_logging, get_logger
from harnex_api.mcp.server import build_streamable_http_app


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    log = get_logger("harnex_api")
    log.info("startup", env=settings.env, version=__version__)
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
