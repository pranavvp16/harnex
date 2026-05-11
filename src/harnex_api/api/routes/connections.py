from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.connections import (
    ConnectionCreate,
    ConnectionOut,
    ConnectionTestRequest,
    ConnectionTestResponse,
    ReindexResult,
)
from harnex_api.db.models import ConnectionMode
from harnex_api.logging import get_logger
from harnex_api.services import connections as svc
from harnex_api.services.connection_test import (
    ConnectionTestInput,
    test_connection_config,
)

router = APIRouter(prefix="/v1/connections", tags=["connections"])


@router.get("", response_model=list[ConnectionOut])
async def list_connections(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> list[ConnectionOut]:
    rows = await svc.list_connections(db, tenant_id=ctx.tenant_id)
    return [ConnectionOut.model_validate(r) for r in rows]


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(
    payload: ConnectionTestRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> ConnectionTestResponse:
    """Dry-run auth/connectivity probe.

    Builds an auth context from the supplied credentials in memory (never
    persisted) and sends one request to the connector's known test endpoint.
    Used by the connection wizard before the connection is created.
    """
    _ = ctx  # tenant scoping handled by tenant context; nothing reads it here.
    result = await test_connection_config(
        ConnectionTestInput(
            mode=payload.mode,
            connector_key=payload.connector_key,
            base_url=payload.base_url,
            auth_flow=payload.auth_flow,
            auth_config=payload.auth_config,
            credentials=payload.credentials,
        )
    )
    return ConnectionTestResponse(
        ok=result.ok,
        http_status=result.http_status,
        method=result.method,
        url=result.url,
        error_kind=result.error_kind,
        message=result.message,
        duration_ms=result.duration_ms,
        metadata=result.metadata,
    )


@router.post("", response_model=ConnectionOut, status_code=status.HTTP_201_CREATED)
async def create_connection(
    payload: ConnectionCreate,
    background: BackgroundTasks,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> ConnectionOut:
    try:
        row = await svc.create_connection(
            db,
            tenant_id=ctx.tenant_id,
            data=svc.ConnectionCreateInput(
                name=payload.name,
                mode=payload.mode,
                connector_key=payload.connector_key,
                base_url=payload.base_url,
                spec_url=payload.spec_url,
                auth_flow=payload.auth_flow,
                auth_config=payload.auth_config,
                credentials=payload.credentials,
            ),
        )
    except svc.ConnectionInputError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    # openapi_upload runs its own indexing once the file is POSTed to /spec.
    if payload.mode != ConnectionMode.openapi_upload:
        # Commit before scheduling so the bg task's fresh session can see the
        # new row — dependency-level commit otherwise races BackgroundTasks.
        await db.commit()
        get_logger("harnex_api.connections").info(
            "reindex_bg_scheduled",
            tenant_id=str(ctx.tenant_id),
            connection_id=str(row.id),
            mode=payload.mode.value,
        )
        background.add_task(
            svc.reindex_in_new_session, tenant_id=ctx.tenant_id, connection_id=row.id
        )
    return ConnectionOut.model_validate(row)


@router.get("/{connection_id}", response_model=ConnectionOut)
async def get_connection(
    connection_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> ConnectionOut:
    row = await svc.get_connection(db, tenant_id=ctx.tenant_id, connection_id=connection_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connection not found")
    return ConnectionOut.model_validate(row)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await svc.delete_connection(db, tenant_id=ctx.tenant_id, connection_id=connection_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connection not found")


@router.post("/{connection_id}/reindex", response_model=ReindexResult)
async def reindex_connection(
    connection_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> ReindexResult:
    result = await svc.reindex_connection(db, tenant_id=ctx.tenant_id, connection_id=connection_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connection not found")
    return ReindexResult(
        connection_id=connection_id,
        operation_count=result.operation_count,
        chunk_count=result.chunk_count,
        spec_hash=result.spec_hash or None,
    )


@router.post("/{connection_id}/spec", response_model=ReindexResult)
async def upload_spec(
    connection_id: UUID,
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> ReindexResult:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty upload")
    result = await svc.ingest_uploaded_spec(
        db, tenant_id=ctx.tenant_id, connection_id=connection_id, raw_bytes=raw
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connection not found")
    return ReindexResult(
        connection_id=connection_id,
        operation_count=result.operation_count,
        chunk_count=result.chunk_count,
        spec_hash=result.spec_hash or None,
    )


__all__ = ["router"]
