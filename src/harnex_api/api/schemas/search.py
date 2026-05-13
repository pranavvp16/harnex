from __future__ import annotations

from pydantic import Field

from harnex_api.api.schemas.common import ApiModel


class SearchRequest(ApiModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(10, ge=1, le=50)
    connector_filter: str | None = None
    skills: bool = False


class SearchHitOut(ApiModel):
    operation_id: str
    connection_id: str
    connector_key: str | None
    method: str
    path: str
    summary: str
    score: float


class SkillHitOut(ApiModel):
    skill_key: str
    name: str
    runtime: str
    output_format: str
    instructions: str
    score: float


class SearchResponse(ApiModel):
    hits: list[SearchHitOut]
    clarification_needed: bool
    candidate_connectors: list[str]
    skills: list[SkillHitOut] = Field(default_factory=list)


__all__ = ["SearchHitOut", "SearchRequest", "SearchResponse", "SkillHitOut"]
