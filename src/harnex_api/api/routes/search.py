from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.api.dependencies.auth import TenantContext, get_tenant_context
from harnex_api.api.dependencies.db import get_db
from harnex_api.api.schemas.search import (
    SearchHitOut,
    SearchRequest,
    SearchResponse,
    SkillHitOut,
)
from harnex_api.logging import get_logger
from harnex_api.services.search.service import SearchService
from harnex_api.services.usage.monthly import bump_usage_monthly

router = APIRouter(prefix="/v1/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    payload: SearchRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    svc = SearchService()
    result = await svc.search(
        tenant_id=str(ctx.tenant_id),
        query=payload.query,
        top_k=payload.top_k,
        connector_filter=payload.connector_filter,
        include_skills=payload.skills,
    )
    log = get_logger(__name__)
    try:
        await bump_usage_monthly(
            db,
            ctx.tenant_id,
            searches=1,
            embedding_tokens=result.embedding_tokens,
        )
    except Exception:
        log.exception("usage bump failed — ignoring", tenant_id=str(ctx.tenant_id))
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
        skills=[
            SkillHitOut(
                skill_key=s.skill_key,
                name=s.name,
                runtime=s.runtime,
                output_format=s.output_format,
                instructions=s.instructions,
                score=s.score,
            )
            for s in result.skills
        ],
    )


__all__ = ["router"]
