from __future__ import annotations

from dataclasses import dataclass

from harnex_api.services.search.embeddings import EmbeddingProvider, get_embedding_provider
from harnex_api.services.search.vector_search import SearchHit, VectorSearch, get_vector_search

# When the top hits span multiple connectors and no connector_filter was supplied,
# the agent is told to clarify which platform it meant. Tunable.
CLARIFICATION_TOP_N = 3


@dataclass(frozen=True)
class SearchResponse:
    hits: list[SearchHit]
    clarification_needed: bool
    candidate_connectors: list[str]
    embedding_tokens: int


class SearchService:
    def __init__(
        self,
        *,
        embeddings: EmbeddingProvider | None = None,
        vector_search: VectorSearch | None = None,
    ) -> None:
        self._embeddings = embeddings or get_embedding_provider()
        self._search = vector_search or get_vector_search()

    async def search(
        self,
        *,
        tenant_id: str,
        query: str,
        top_k: int = 10,
        connector_filter: str | None = None,
    ) -> SearchResponse:
        embedding = await self._embeddings.embed(query)
        hits = await self._search.search(
            tenant_id=tenant_id,
            embedding=embedding.vector,
            query_text=query,
            top_k=top_k,
            connector_filter=connector_filter,
        )
        connectors_in_top = {h.connector_key for h in hits[:CLARIFICATION_TOP_N] if h.connector_key}
        clarification = connector_filter is None and len(connectors_in_top) > 1 and len(hits) > 1
        return SearchResponse(
            hits=hits,
            clarification_needed=clarification,
            candidate_connectors=sorted(connectors_in_top),
            embedding_tokens=embedding.prompt_tokens,
        )


__all__ = ["CLARIFICATION_TOP_N", "SearchResponse", "SearchService"]
