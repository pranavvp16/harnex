from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.execute import ExecuteRequestIn, ExecuteResponse
from harnex_api.db.models import ExecutionMode
from harnex_api.services.execute.operation import ExecuteParams
from harnex_api.services.execute.runner import (
    ConnectionMissingError,
    ConnectionNotReadyError,
    execute_code,
    execute_structured,
)

router = APIRouter(prefix="/v1/execute", tags=["execute"])


@router.post("", response_model=ExecuteResponse)
async def execute(
    payload: ExecuteRequestIn,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> ExecuteResponse:
    """Internal/admin execute endpoint — same orchestrator as the MCP `execute` tool.

    Used by the console for connection-test runs. Production agents should call
    the MCP tool, not this route.
    """
    params = ExecuteParams(
        path=payload.path_params,
        query=payload.query,
        headers=payload.headers,
        body=payload.body,
    )
    try:
        if payload.mode == ExecutionMode.code:
            outcome = await execute_code(
                db,
                tenant_id=ctx.tenant_id,
                connection_id=payload.connection_id,
                operation_id=payload.operation_id,
                params=params,
            )
        else:
            outcome = await execute_structured(
                db,
                tenant_id=ctx.tenant_id,
                connection_id=payload.connection_id,
                operation_id=payload.operation_id,
                params=params,
            )
    except ConnectionMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="connection not found"
        ) from exc
    except ConnectionNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ExecuteResponse(
        status=outcome.status,
        http_status=outcome.http_status,
        body=outcome.response_body,
        headers=outcome.response_headers,
        error_kind=outcome.error_kind,
        error_message=outcome.error_message,
        duration_ms=outcome.duration_ms,
        operation_id=outcome.operation_id,
        method=outcome.method,
        path=outcome.path,
    )


__all__ = ["router"]
