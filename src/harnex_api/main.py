from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.responses import RedirectResponse

from harnex_api import __version__
from harnex_api.api.middleware.csrf import CsrfMiddleware
from harnex_api.api.routes import (
    api_keys,
    artifacts,
    connections,
    connectors,
    execute,
    executions,
    files,
    me,
    search,
    tenants,
    usage,
)
from harnex_api.api.routes import auth as auth_routes
from harnex_api.api.routes import (
    session as session_routes,
)
from harnex_api.auth.vault import InfisicalVault, InMemoryVault, set_vault
from harnex_api.config import AppSettings, get_settings
from harnex_api.connectors.seed import ensure_connector_catalog
from harnex_api.db.session import session_scope
from harnex_api.logging import configure_logging, get_logger
from harnex_api.mcp.server import build_streamable_http_app
from harnex_api.services.tenant.seed import DEV_TENANT_ID, ensure_dev_tenant


async def _seed_dev_tenant() -> None:
    """Idempotent dev-tenant seed for local/dev startup."""
    async with session_scope() as session:
        await ensure_dev_tenant(session)


async def _seed_connector_catalog() -> None:
    """Idempotent connector-catalog seed; required so the connector_key FK resolves."""
    async with session_scope() as session:
        await ensure_connector_catalog(session)


async def _seed_builtin_skills() -> int:
    """Idempotent built-in skill seed (docx/pdf/xlsx/pptx)."""
    from harnex_api.services.skills.registry import seed_builtin_skills

    async with session_scope() as session:
        return await seed_builtin_skills(session)


async def _provision_sandbox(settings: AppSettings) -> None:
    """Idempotent sandbox warm-up — mirrors scripts/blaxel_provision.py.

    Provisions both the Node (default code-mode + docx skill) and Python
    (pdf/xlsx/pptx skill) sandboxes. Package installs happen out-of-band via
    ``scripts/blaxel_provision.py`` — startup just ensures the sandbox exists.
    """
    os.environ.setdefault("BL_API_KEY", settings.blaxel_api_key.get_secret_value())
    os.environ.setdefault("BL_WORKSPACE", settings.blaxel_workspace)
    from blaxel.core import SandboxInstance  # local import — keep SDK out of cold path

    for cfg in (
        {
            "name": settings.blaxel_sandbox_name,
            "image": settings.blaxel_sandbox_image,
            "memory": settings.blaxel_sandbox_memory_mb,
            "region": settings.blaxel_sandbox_region,
        },
        {
            "name": settings.blaxel_python_sandbox_name,
            "image": settings.blaxel_python_sandbox_image,
            "memory": settings.blaxel_sandbox_memory_mb,
            "region": settings.blaxel_sandbox_region,
        },
    ):
        await SandboxInstance.create_if_not_exists(cfg)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from harnex_api.mcp.server import get_mcp_app

    mcp = get_mcp_app()
    _ = mcp.streamable_http_app()
    async with mcp.session_manager.run():
        settings = get_settings()
        configure_logging(settings.log_level)
        log = get_logger("harnex_api")
        log.info("startup", env=settings.env, version=__version__)

        # Vault selection: Infisical when fully configured; otherwise fail-fast in
        # staging/prod, warn-and-fallback in local/dev. The InMemoryVault is wiped on
        # restart, so silently using it in any persistent environment is the source
        # of "my connection's credentials disappeared" bug reports — make it loud.
        _cid = settings.infisical_client_id.get_secret_value()
        _csec = settings.infisical_client_secret.get_secret_value()
        infisical_configured = bool(_cid and _csec and settings.infisical_project_id)
        if infisical_configured:
            set_vault(
                InfisicalVault(
                    base_url=settings.infisical_base_url,
                    project_id=settings.infisical_project_id,
                    environment=settings.infisical_environment,
                    client_id=_cid,
                    client_secret=_csec,
                )
            )
            log.info("vault", backend="infisical", base_url=settings.infisical_base_url)
        elif settings.env in ("staging", "prod"):
            raise RuntimeError(
                "Infisical is required in staging/prod. Set INFISICAL_PROJECT_ID, "
                "INFISICAL_CLIENT_ID, and INFISICAL_CLIENT_SECRET in the environment."
            )
        else:
            set_vault(InMemoryVault())
            log.warning(
                "vault_not_persistent",
                backend="in_memory",
                env=settings.env,
                hint=(
                    "Connection credentials will NOT survive a process restart. "
                    "Fill INFISICAL_* in .env and run scripts/infisical_smoke.py "
                    "to enable persistence."
                ),
            )

        try:
            await _seed_connector_catalog()
            log.info("connector_catalog_seeded")
        except Exception as exc:
            # Non-fatal — DB may be unreachable at boot in some local setups.
            log.warning("connector_catalog_seed_failed", error=str(exc))
        try:
            changed = await _seed_builtin_skills()
            log.info("builtin_skills_seeded", changed=changed)
        except Exception as exc:
            # Non-fatal — embedding provider or DB may be unreachable at boot.
            log.warning("builtin_skills_seed_failed", error=str(exc))
        if settings.env in ("local", "dev"):
            try:
                await _seed_dev_tenant()
                log.info("dev_tenant_seeded", tenant_id=str(DEV_TENANT_ID))
            except Exception as exc:
                # Non-fatal — DB may be unreachable at boot in some local setups.
                log.warning("dev_tenant_seed_failed", error=str(exc))
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

    # Double-submit CSRF for cookie-authenticated requests. /mcp and Bearer
    # hnx... clients are exempt — see CsrfMiddleware._EXEMPT_PATH_PREFIXES.
    app.add_middleware(CsrfMiddleware)

    if settings.env in ("local", "dev"):
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        """Convert DB constraint violations into 400s with a structured payload.

        Production responses redact the raw driver message to avoid leaking
        schema details (table/column names). Local/dev keeps the full text so
        developers can self-diagnose.
        """
        # SQLAlchemy/asyncpg surfaces the constraint name on `orig.constraint_name`.
        constraint = getattr(getattr(exc, "orig", None), "constraint_name", None)
        leaky = settings.env in ("local", "dev")
        detail: dict[str, Any] = {
            "error": "constraint_violation",
            "message": (
                "Request violates a database constraint."
                if not leaky
                else f"Request violates a database constraint: {exc.orig}"
            ),
        }
        if constraint:
            detail["constraint"] = constraint
        get_logger("harnex_api").warning(
            "integrity_error",
            path=request.url.path,
            method=request.method,
            constraint=constraint,
            error=str(exc.orig) if exc.orig else str(exc),
        )
        return JSONResponse(status_code=400, content=detail)

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
    app.include_router(tenants.router)
    app.include_router(me.router)
    app.include_router(auth_routes.router)
    app.include_router(session_routes.router)
    app.include_router(artifacts.router)
    app.include_router(files.router)

    @app.api_route(
        "/mcp",
        methods=["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        include_in_schema=False,
    )
    async def _mcp_redirect_slash(request: Request) -> RedirectResponse:
        """Starlette's Mount matches `/mcp/...` but not bare `/mcp`; normalize for clients."""
        suffix = f"?{request.url.query}" if request.url.query else ""
        return RedirectResponse(url=f"/mcp/{suffix}", status_code=307)

    # MCP shipped surface — exactly two tools (search, execute), bearer auth via tenant API keys.
    app.mount("/mcp", build_streamable_http_app())

    return app


app = create_app()
