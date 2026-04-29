from __future__ import annotations

from dataclasses import dataclass

from harnex_api.connectors.base import LoadedSpec
from harnex_api.services.ingestion.chunker import SpecChunk, operations_to_chunks
from harnex_api.services.ingestion.enricher import enrich_spec
from harnex_api.services.search.embeddings import EmbeddingProvider, get_embedding_provider
from harnex_api.services.search.vector_search import VectorSearch, get_vector_search


@dataclass(frozen=True)
class IndexResult:
    operation_count: int
    chunk_count: int
    spec_hash: str


async def index_spec(
    *,
    tenant_id: str,
    connection_id: str,
    connector_key: str | None,
    spec: LoadedSpec,
    embeddings: EmbeddingProvider | None = None,
    vector_search: VectorSearch | None = None,
) -> IndexResult:
    """Run a parsed spec through enrich -> chunk -> embed -> upsert."""
    emb = embeddings or get_embedding_provider()
    vs = vector_search or get_vector_search()

    operations = enrich_spec(spec.document)
    chunks: list[SpecChunk] = operations_to_chunks(
        tenant_id=tenant_id,
        connection_id=connection_id,
        connector_key=connector_key,
        operations=operations,
    )
    if not chunks:
        await vs.ensure_index(tenant_id, emb.dim)
        return IndexResult(operation_count=0, chunk_count=0, spec_hash=spec.raw_hash)

    await vs.ensure_index(tenant_id, emb.dim)
    vectors = await emb.embed_batch([c.embedding_text for c in chunks])
    await vs.upsert(tenant_id, chunks, vectors)
    return IndexResult(
        operation_count=len(operations),
        chunk_count=len(chunks),
        spec_hash=spec.raw_hash,
    )


__all__ = ["IndexResult", "index_spec"]
