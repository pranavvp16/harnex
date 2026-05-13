from __future__ import annotations

from dataclasses import dataclass, field

from harnex_api.services.search.embeddings import EmbeddingProvider, get_embedding_provider
from harnex_api.services.search.vector_search import (
    SearchHit,
    SkillHit,
    SkillVectorSearch,
    VectorSearch,
    get_skill_vector_search,
    get_vector_search,
)

# When the top hits span multiple connectors and no connector_filter was supplied,
# the agent is told to clarify which platform it meant. Tunable.
CLARIFICATION_TOP_N = 3
# Skill retrieval is coarse-grained — we only ever surface the top match because
# there are exactly four built-ins and they're orthogonal. The agent then writes
# code against that skill's instructions.
SKILL_TOP_K = 1


@dataclass(frozen=True)
class SearchResponse:
    hits: list[SearchHit]
    clarification_needed: bool
    candidate_connectors: list[str]
    embedding_tokens: int
    skills: list[SkillHit] = field(default_factory=list)


class SearchService:
    def __init__(
        self,
        *,
        embeddings: EmbeddingProvider | None = None,
        vector_search: VectorSearch | None = None,
        skill_search: SkillVectorSearch | None = None,
    ) -> None:
        self._embeddings = embeddings or get_embedding_provider()
        self._search = vector_search or get_vector_search()
        self._skill_search = skill_search or get_skill_vector_search()

    async def search(
        self,
        *,
        tenant_id: str,
        query: str,
        top_k: int = 10,
        connector_filter: str | None = None,
        include_skills: bool = False,
    ) -> SearchResponse:
        embedding = await self._embeddings.embed(query)
        hits = await self._search.search(
            tenant_id=tenant_id,
            embedding=embedding.vector,
            query_text=query,
            top_k=top_k,
            connector_filter=connector_filter,
        )
        skills: list[SkillHit] = []
        if include_skills:
            # The agent opted in. We don't second-guess with thresholds — return
            # the closest skill so it has something to work with.
            skills = await self._skill_search.search(
                embedding=embedding.vector,
                query_text=query,
                top_k=SKILL_TOP_K,
            )
        connectors_in_top = {h.connector_key for h in hits[:CLARIFICATION_TOP_N] if h.connector_key}
        clarification = connector_filter is None and len(connectors_in_top) > 1 and len(hits) > 1
        return SearchResponse(
            hits=hits,
            clarification_needed=clarification,
            candidate_connectors=sorted(connectors_in_top),
            embedding_tokens=embedding.prompt_tokens,
            skills=skills,
        )


__all__ = ["CLARIFICATION_TOP_N", "SKILL_TOP_K", "SearchResponse", "SearchService"]
