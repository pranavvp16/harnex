from __future__ import annotations

from fastapi import APIRouter, Depends

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.schemas.search import SearchHitOut, SearchRequest, SearchResponse
from harnex_api.services.search.service import SearchService

router = APIRouter(prefix="/v1/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    payload: SearchRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> SearchResponse:
    svc = SearchService()
    result = await svc.search(
        tenant_id=str(ctx.tenant_id),
        query=payload.query,
        top_k=payload.top_k,
        connector_filter=payload.connector_filter,
    )
    return SearchResponse(
        hits=[
            SearchHitOut(
                operation_id=h.operation_id,
                connection_id=h.connection_id,
                connector_key=h.connector_key,
                method=h.method,
                path=h.path,
                summary=h.summary,
                score=h.score,
            )
            for h in result.hits
        ],
        clarification_needed=result.clarification_needed,
        candidate_connectors=result.candidate_connectors,
    )


__all__ = ["router"]
