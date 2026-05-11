"""Spec-catalog-aware indexing pipeline.

`index_spec` keys storage on
`(source_type, source_key, spec_hash, embedding_model, embedding_dim)`. When a
spec already exists in the catalog for the same embedding space (because a
sibling tenant's connection indexed it earlier, or because this connection's
spec is unchanged since last reindex), we reuse the row and skip embedding
entirely. Otherwise chunks are embedded once and inserted in a single
transaction.

Tenant scoping happens at *search* time via JOIN through `connections.spec_id`
— catalog rows themselves are global and contain only public OpenAPI text.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse, urlunparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.connectors.base import LoadedSpec
from harnex_api.db.models import (
    Connection,
    ConnectionMode,
    ConnectorSpec,
    OperationChunk,
    SpecSourceType,
)
from harnex_api.logging import get_logger
from harnex_api.services.ingestion.chunker import SpecChunk, operations_to_chunks
from harnex_api.services.ingestion.enricher import enrich_spec
from harnex_api.services.search.embeddings import EmbeddingProvider, get_embedding_provider


@dataclass(frozen=True)
class IndexResult:
    operation_count: int
    chunk_count: int
    spec_hash: str
    reused: bool = False


def _normalize_url(url: str) -> str:
    """Lower-case scheme/host and strip trailing slashes so trivially-different
    spec URLs hash to the same `source_key` (e.g. trailing slash, casing).
    """
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))


def _resolve_source(connection: Connection, spec_hash: str) -> tuple[SpecSourceType, str]:
    """Map the connection mode to a `(source_type, source_key)` pair.

    The source_key is what makes catalog rows shareable across tenants — for
    builtins it's the connector key (everyone on github.com SaaS hits the
    same spec); for openapi_url it's the normalized URL; for upload we key
    on the hash itself (anyone uploading identical bytes shares).
    """
    mode = connection.mode
    if mode == ConnectionMode.builtin and connection.connector_key:
        return SpecSourceType.builtin, connection.connector_key
    if mode == ConnectionMode.openapi_url and connection.spec_url:
        return SpecSourceType.openapi_url, _normalize_url(connection.spec_url)
    if mode == ConnectionMode.openapi_upload:
        return SpecSourceType.openapi_upload, spec_hash
    # bare_url should never reach the index path (callers gate that earlier),
    # but keep a sane fallback so we don't crash if it slips through.
    return SpecSourceType.bare_url, connection.connector_key or "bare"


async def index_spec(
    *,
    session: AsyncSession,
    connection: Connection,
    spec: LoadedSpec,
    embeddings: EmbeddingProvider | None = None,
) -> IndexResult:
    """Idempotent indexing keyed on spec identity and embedding space.

    Updates `connection.spec_id` in-place (caller is responsible for the
    surrounding transaction commit). Reuse fast-path skips embedding and
    chunk inserts entirely.
    """
    log = get_logger("harnex_api.ingestion")
    emb = embeddings or get_embedding_provider()
    source_type, source_key = _resolve_source(connection, spec.raw_hash)

    existing = await session.execute(
        select(ConnectorSpec).where(
            ConnectorSpec.source_type == source_type,
            ConnectorSpec.source_key == source_key,
            ConnectorSpec.spec_hash == spec.raw_hash,
            ConnectorSpec.embedding_model == emb.model_name,
            ConnectorSpec.embedding_dim == emb.dim,
        )
    )
    existing_spec = existing.scalar_one_or_none()
    previous_spec_id = connection.spec_id

    if existing_spec is not None:
        connection.spec_id = existing_spec.id
        log.info(
            "spec_reused",
            connection_id=str(connection.id),
            spec_id=str(existing_spec.id),
            source_type=source_type.value,
            source_key=source_key,
            spec_hash=spec.raw_hash,
            operation_count=existing_spec.operation_count,
        )
        await _gc_orphan(session, previous_spec_id, exclude_connection_id=connection.id)
        return IndexResult(
            operation_count=existing_spec.operation_count,
            chunk_count=existing_spec.operation_count,
            spec_hash=spec.raw_hash,
            reused=True,
        )

    operations = enrich_spec(spec.document)
    chunks: list[SpecChunk] = operations_to_chunks(
        spec_hash=spec.raw_hash,
        connector_key=connection.connector_key,
        operations=operations,
    )

    spec_row = ConnectorSpec(
        id=uuid.uuid4(),
        source_type=source_type,
        source_key=source_key,
        spec_hash=spec.raw_hash,
        embedding_model=emb.model_name,
        embedding_dim=emb.dim,
        operation_count=len(operations),
        raw_spec=spec.document,
        indexed_at=datetime.now(UTC),
    )
    session.add(spec_row)
    await session.flush()

    if chunks:
        vectors = await emb.embed_batch([c.embedding_text for c in chunks])
        if len(vectors) != len(chunks):
            raise RuntimeError("embedding count does not match chunk count")
        for chunk, vec in zip(chunks, vectors, strict=True):
            session.add(
                OperationChunk(
                    id=uuid.uuid4(),
                    spec_id=spec_row.id,
                    operation_id=chunk.operation_id,
                    method=chunk.method,
                    path=chunk.path,
                    summary=chunk.summary,
                    description=chunk.description,
                    tags=chunk.tags,
                    semantic_tags=chunk.semantic_tags,
                    auth_scheme_keys=chunk.auth_scheme_keys,
                    parameters=chunk.parameters,
                    request_body=chunk.request_body,
                    responses=chunk.responses,
                    embedding_text=chunk.embedding_text,
                    schema_hash=chunk.schema_hash,
                    embedding=vec,
                )
            )

    connection.spec_id = spec_row.id
    log.info(
        "spec_indexed",
        connection_id=str(connection.id),
        spec_id=str(spec_row.id),
        source_type=source_type.value,
        source_key=source_key,
        spec_hash=spec.raw_hash,
        embedding_model=emb.model_name,
        embedding_dim=emb.dim,
        operation_count=len(operations),
        chunk_count=len(chunks),
    )
    await _gc_orphan(session, previous_spec_id, exclude_connection_id=connection.id)
    return IndexResult(
        operation_count=len(operations),
        chunk_count=len(chunks),
        spec_hash=spec.raw_hash,
        reused=False,
    )


async def _gc_orphan(
    session: AsyncSession,
    spec_id: uuid.UUID | None,
    *,
    exclude_connection_id: uuid.UUID,
) -> None:
    """Drop a previously-referenced spec row if no connection still points at it.

    Uses CASCADE on `operation_chunks.spec_id` so chunks vanish too. The
    `exclude_connection_id` is the row we just rebound; it's already pointed
    at the new spec, but we filter explicitly so the check stays correct
    even before the caller commits.
    """
    if spec_id is None:
        return
    still_referenced = await session.execute(
        select(Connection.id)
        .where(Connection.spec_id == spec_id, Connection.id != exclude_connection_id)
        .limit(1)
    )
    if still_referenced.scalar_one_or_none() is not None:
        return
    orphan = await session.get(ConnectorSpec, spec_id)
    if orphan is not None:
        await session.delete(orphan)
        get_logger("harnex_api.ingestion").info(
            "spec_gc",
            spec_id=str(spec_id),
        )


__all__ = ["IndexResult", "index_spec"]
