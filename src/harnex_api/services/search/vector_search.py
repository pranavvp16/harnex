"""Hybrid (semantic + keyword) search over the shared spec catalog.

Chunks live in `operation_chunks` keyed on `connector_specs.id`, not per
tenant. Tenant scoping happens at query time by joining through
`connections.spec_id` and filtering on `connections.tenant_id`. The
keyword half uses a STORED tsvector with weighted setweight() over
summary/path/description/tags; the semantic half uses pgvector HNSW with
cosine distance. Results are fused by Reciprocal Rank Fusion (k=60), which
needs no score normalization between the two ranks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from harnex_api.config import get_settings
from harnex_api.db.session import get_sessionmaker

# Reciprocal Rank Fusion constant. 60 is the canonical default from the
# original Cormack et al. paper — robust under skew, parameter-free.
_RRF_K = 60
# Per-channel cap before fusion. Keep larger than top_k so fusion has room
# to surface chunks that rank well in only one channel.
_PER_CHANNEL_LIMIT = 50


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    connection_id: str
    connector_key: str | None
    operation_id: str
    method: str
    path: str
    summary: str
    score: float
    document: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillHit:
    """A retrieval hit against the global skills catalog.

    Unlike :class:`SearchHit` this is not tenant-scoped — skills are global
    built-ins. The full ``instructions`` (the skill's ``SKILL.md``) is shipped
    inline so the agent can write code against it without a follow-up call.
    """

    skill_key: str
    name: str
    runtime: str
    output_format: str
    instructions: str
    score: float


class VectorSearch(Protocol):
    async def search(
        self,
        *,
        tenant_id: str,
        embedding: list[float],
        query_text: str,
        top_k: int = 10,
        connector_filter: str | None = None,
    ) -> list[SearchHit]: ...


class SkillVectorSearch(Protocol):
    async def search(
        self,
        *,
        embedding: list[float],
        query_text: str,
        top_k: int = 1,
    ) -> list[SkillHit]: ...


class PgVectorSearch:
    """Hybrid search over `operation_chunks` with tenant scoping via JOIN."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def search(
        self,
        *,
        tenant_id: str,
        embedding: list[float],
        query_text: str,
        top_k: int = 10,
        connector_filter: str | None = None,
    ) -> list[SearchHit]:
        async with self._session_factory() as session:
            return await self._search(
                session,
                tenant_id=tenant_id,
                embedding=embedding,
                query_text=query_text,
                top_k=top_k,
                connector_filter=connector_filter,
            )

    async def _search(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        embedding: list[float],
        query_text: str,
        top_k: int,
        connector_filter: str | None,
    ) -> list[SearchHit]:
        # When two of the tenant's connections share a spec_id (e.g. two
        # GitHub orgs on the same SaaS spec), a chunk would otherwise appear
        # twice. DISTINCT ON pins it to the most-recently-created connection
        # so each operation surfaces once with a stable connection_id.
        sql = text(
            """
            WITH chunk_connection AS (
                SELECT DISTINCT ON (oc.id)
                    oc.id AS chunk_id,
                    c.id AS connection_id,
                    c.connector_key,
                    oc.operation_id,
                    oc.method,
                    oc.path,
                    oc.summary,
                    oc.embedding,
                    oc.search_tsv
                FROM operation_chunks oc
                JOIN connections c ON c.spec_id = oc.spec_id
                WHERE c.tenant_id = CAST(:tenant_id AS uuid)
                    AND (CAST(:connector_filter AS text) IS NULL
                         OR c.connector_key = :connector_filter)
                ORDER BY oc.id, c.created_at DESC
            ),
            semantic AS (
                SELECT chunk_id,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> CAST(:emb AS vector))
                           AS rank
                FROM chunk_connection
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT :limit
            ),
            keyword AS (
                SELECT cc.chunk_id,
                       ROW_NUMBER() OVER (ORDER BY ts_rank_cd(cc.search_tsv, q) DESC)
                           AS rank
                FROM chunk_connection cc,
                     websearch_to_tsquery('english', :q) AS q
                WHERE cc.search_tsv @@ q
                ORDER BY ts_rank_cd(cc.search_tsv, q) DESC
                LIMIT :limit
            ),
            fused AS (
                SELECT chunk_id, SUM(score) AS score
                FROM (
                    SELECT chunk_id, 1.0 / (:rrf_k + rank) AS score FROM semantic
                    UNION ALL
                    SELECT chunk_id, 1.0 / (:rrf_k + rank) AS score FROM keyword
                ) t
                GROUP BY chunk_id
            )
            SELECT cc.chunk_id, cc.connection_id, cc.connector_key,
                   cc.operation_id, cc.method, cc.path, cc.summary,
                   f.score
            FROM fused f
            JOIN chunk_connection cc ON cc.chunk_id = f.chunk_id
            ORDER BY f.score DESC
            LIMIT :top_k
            """
        )
        # pgvector accepts a list literal in text-mode parameters via the
        # `[1.0,2.0,...]` representation; SQLAlchemy renders the list that way.
        emb_literal = "[" + ",".join(repr(float(x)) for x in embedding) + "]"
        result = await session.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "emb": emb_literal,
                "q": query_text or "",
                "connector_filter": connector_filter,
                "limit": _PER_CHANNEL_LIMIT,
                "top_k": top_k,
                "rrf_k": _RRF_K,
            },
        )
        hits: list[SearchHit] = []
        for row in result.mappings().all():
            hits.append(
                SearchHit(
                    chunk_id=str(row["chunk_id"]),
                    connection_id=str(row["connection_id"]),
                    connector_key=row["connector_key"],
                    operation_id=row["operation_id"],
                    method=row["method"],
                    path=row["path"],
                    summary=row["summary"] or "",
                    score=float(row["score"]),
                    document={},
                )
            )
        return hits


class FakeVectorSearch:
    """In-process search backend used by unit tests.

    Tests call `register(...)` to seed records (one per chunk + connection
    pairing). `search()` does a cosine over the registered embeddings; tenant
    filtering is exact-match. No keyword half — RRF degenerates to semantic
    only, which is fine for testing the orchestration layer.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: list[dict[str, Any]] = []

    def register(
        self,
        *,
        tenant_id: str,
        connection_id: str,
        connector_key: str | None,
        chunk_id: str,
        operation_id: str,
        method: str,
        path: str,
        summary: str,
        embedding: list[float],
    ) -> None:
        with self._lock:
            self._records.append(
                {
                    "tenant_id": tenant_id,
                    "connection_id": connection_id,
                    "connector_key": connector_key,
                    "chunk_id": chunk_id,
                    "operation_id": operation_id,
                    "method": method,
                    "path": path,
                    "summary": summary,
                    "embedding": list(embedding),
                }
            )

    def reset(self) -> None:
        with self._lock:
            self._records.clear()

    async def search(
        self,
        *,
        tenant_id: str,
        embedding: list[float],
        query_text: str,
        top_k: int = 10,
        connector_filter: str | None = None,
    ) -> list[SearchHit]:
        with self._lock:
            scored: list[tuple[float, dict[str, Any]]] = []
            for rec in self._records:
                if rec["tenant_id"] != tenant_id:
                    continue
                if connector_filter and rec["connector_key"] != connector_filter:
                    continue
                scored.append((_cosine(embedding, rec["embedding"]), rec))
            scored.sort(key=lambda p: p[0], reverse=True)
            return [
                SearchHit(
                    chunk_id=rec["chunk_id"],
                    connection_id=rec["connection_id"],
                    connector_key=rec["connector_key"],
                    operation_id=rec["operation_id"],
                    method=rec["method"],
                    path=rec["path"],
                    summary=rec["summary"],
                    score=score,
                    document={},
                )
                for score, rec in scored[:top_k]
            ]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class PgVectorSkillSearch:
    """Hybrid skill search over the global ``skills`` table — no tenant scoping.

    The skills catalog is small (a handful of rows for built-ins) so we don't
    bother with materialized CTEs; the query is plenty fast.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def search(
        self,
        *,
        embedding: list[float],
        query_text: str,
        top_k: int = 1,
    ) -> list[SkillHit]:
        async with self._session_factory() as session:
            return await self._search(
                session, embedding=embedding, query_text=query_text, top_k=top_k
            )

    async def _search(
        self,
        session: AsyncSession,
        *,
        embedding: list[float],
        query_text: str,
        top_k: int,
    ) -> list[SkillHit]:
        sql = text(
            """
            WITH semantic AS (
                SELECT id,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> CAST(:emb AS vector))
                           AS rank
                FROM skills
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT :limit
            ),
            keyword AS (
                SELECT s.id,
                       ROW_NUMBER() OVER (ORDER BY ts_rank_cd(s.search_tsv, q) DESC)
                           AS rank
                FROM skills s,
                     websearch_to_tsquery('english', :q) AS q
                WHERE s.search_tsv @@ q
                ORDER BY ts_rank_cd(s.search_tsv, q) DESC
                LIMIT :limit
            ),
            fused AS (
                SELECT id, SUM(score) AS score
                FROM (
                    SELECT id, 1.0 / (:rrf_k + rank) AS score FROM semantic
                    UNION ALL
                    SELECT id, 1.0 / (:rrf_k + rank) AS score FROM keyword
                ) t
                GROUP BY id
            )
            SELECT s.key, s.name, s.runtime, s.output_format, s.instructions, f.score
            FROM fused f
            JOIN skills s ON s.id = f.id
            ORDER BY f.score DESC
            LIMIT :top_k
            """
        )
        emb_literal = "[" + ",".join(repr(float(x)) for x in embedding) + "]"
        result = await session.execute(
            sql,
            {
                "emb": emb_literal,
                "q": query_text or "",
                "limit": _PER_CHANNEL_LIMIT,
                "top_k": top_k,
                "rrf_k": _RRF_K,
            },
        )
        return [
            SkillHit(
                skill_key=row["key"],
                name=row["name"],
                runtime=str(row["runtime"]),
                output_format=row["output_format"],
                instructions=row["instructions"] or "",
                score=float(row["score"]),
            )
            for row in result.mappings().all()
        ]


class FakeSkillVectorSearch:
    """In-process skill search for unit tests."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: list[dict[str, Any]] = []

    def register(
        self,
        *,
        skill_key: str,
        name: str,
        runtime: str,
        output_format: str,
        instructions: str,
        embedding: list[float],
    ) -> None:
        with self._lock:
            self._records.append(
                {
                    "skill_key": skill_key,
                    "name": name,
                    "runtime": runtime,
                    "output_format": output_format,
                    "instructions": instructions,
                    "embedding": list(embedding),
                }
            )

    def reset(self) -> None:
        with self._lock:
            self._records.clear()

    async def search(
        self,
        *,
        embedding: list[float],
        query_text: str,
        top_k: int = 1,
    ) -> list[SkillHit]:
        with self._lock:
            scored = [(_cosine(embedding, rec["embedding"]), rec) for rec in self._records]
            scored.sort(key=lambda p: p[0], reverse=True)
            return [
                SkillHit(
                    skill_key=rec["skill_key"],
                    name=rec["name"],
                    runtime=rec["runtime"],
                    output_format=rec["output_format"],
                    instructions=rec["instructions"],
                    score=score,
                )
                for score, rec in scored[:top_k]
            ]


_fake_singleton = FakeVectorSearch()
_fake_skill_singleton = FakeSkillVectorSearch()


def get_vector_search() -> VectorSearch:
    settings = get_settings()
    if settings.use_fake_vector_search:
        return _fake_singleton
    return PgVectorSearch(get_sessionmaker())


def get_skill_vector_search() -> SkillVectorSearch:
    settings = get_settings()
    if settings.use_fake_vector_search:
        return _fake_skill_singleton
    return PgVectorSkillSearch(get_sessionmaker())


def get_fake_vector_search() -> FakeVectorSearch:
    """Test helper — returns the process-wide fake instance."""
    return _fake_singleton


def get_fake_skill_vector_search() -> FakeSkillVectorSearch:
    """Test helper — returns the process-wide fake skills instance."""
    return _fake_skill_singleton


__all__ = [
    "FakeSkillVectorSearch",
    "FakeVectorSearch",
    "PgVectorSearch",
    "PgVectorSkillSearch",
    "SearchHit",
    "SkillHit",
    "SkillVectorSearch",
    "VectorSearch",
    "get_fake_skill_vector_search",
    "get_fake_vector_search",
    "get_skill_vector_search",
    "get_vector_search",
]
