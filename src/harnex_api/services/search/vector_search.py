from __future__ import annotations

import math
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Protocol

from harnex_api.config import get_settings
from harnex_api.services.ingestion.chunker import SpecChunk, chunk_to_search_document


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


class VectorSearch(Protocol):
    async def ensure_index(self, tenant_id: str, dim: int) -> None: ...
    async def upsert(
        self, tenant_id: str, chunks: list[SpecChunk], embeddings: list[list[float]]
    ) -> None: ...
    async def delete_by_connection(self, tenant_id: str, connection_id: str) -> None: ...
    async def delete_chunks(self, tenant_id: str, chunk_ids: list[str]) -> None: ...
    async def search(
        self,
        tenant_id: str,
        embedding: list[float],
        *,
        top_k: int = 10,
        connector_filter: str | None = None,
    ) -> list[SearchHit]: ...


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class InMemoryVectorSearch:
    """In-process tenant-segmented index used by tests + local smoke runs."""

    def __init__(self) -> None:
        self._lock = RLock()
        # tenant_id -> chunk_id -> (document_dict, embedding)
        self._indexes: dict[str, dict[str, tuple[dict[str, Any], list[float]]]] = {}

    async def ensure_index(self, tenant_id: str, dim: int) -> None:
        with self._lock:
            self._indexes.setdefault(tenant_id, {})

    async def upsert(
        self, tenant_id: str, chunks: list[SpecChunk], embeddings: list[list[float]]
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must align")
        with self._lock:
            idx = self._indexes.setdefault(tenant_id, {})
            for chunk, emb in zip(chunks, embeddings, strict=True):
                idx[chunk.id] = (chunk_to_search_document(chunk, emb), list(emb))

    async def delete_by_connection(self, tenant_id: str, connection_id: str) -> None:
        with self._lock:
            idx = self._indexes.get(tenant_id)
            if not idx:
                return
            to_drop = [
                cid for cid, (doc, _) in idx.items() if doc.get("connection_id") == connection_id
            ]
            for cid in to_drop:
                idx.pop(cid, None)

    async def delete_chunks(self, tenant_id: str, chunk_ids: list[str]) -> None:
        with self._lock:
            idx = self._indexes.get(tenant_id)
            if not idx:
                return
            for cid in chunk_ids:
                idx.pop(cid, None)

    async def search(
        self,
        tenant_id: str,
        embedding: list[float],
        *,
        top_k: int = 10,
        connector_filter: str | None = None,
    ) -> list[SearchHit]:
        with self._lock:
            idx = self._indexes.get(tenant_id) or {}
            scored: list[tuple[float, dict[str, Any]]] = []
            for doc, emb in idx.values():
                if connector_filter and doc.get("connector_key") != connector_filter:
                    continue
                scored.append((_cosine(embedding, emb), doc))
            scored.sort(key=lambda p: p[0], reverse=True)
            top = scored[:top_k]
            return [
                SearchHit(
                    chunk_id=doc["id"],
                    connection_id=doc["connection_id"],
                    connector_key=doc.get("connector_key"),
                    operation_id=doc["operation_id"],
                    method=doc["method"],
                    path=doc["path"],
                    summary=doc["summary"],
                    score=score,
                    document=doc,
                )
                for score, doc in top
            ]


class AzureAISearch:
    """Adapter over `azure-search-documents`. Lazy-imported; only constructed
    when Azure env vars are set so tests can run without the package on the
    network path.
    """

    def __init__(self, *, endpoint: str, api_key: str, index_prefix: str) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.index_prefix = index_prefix

    def _index_name(self, tenant_id: str) -> str:
        return f"{self.index_prefix}-{tenant_id}"

    async def ensure_index(self, tenant_id: str, dim: int) -> None:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.indexes import SearchIndexClient
        from azure.search.documents.indexes.models import (
            HnswAlgorithmConfiguration,
            SearchableField,
            SearchField,
            SearchFieldDataType,
            SearchIndex,
            SimpleField,
            VectorSearchProfile,
        )
        from azure.search.documents.indexes.models import (
            VectorSearch as AzureVectorSearch,
        )

        client = SearchIndexClient(self.endpoint, AzureKeyCredential(self.api_key))
        try:
            client.get_index(self._index_name(tenant_id))
            return
        except Exception:
            pass

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SimpleField(name="tenant_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="connection_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="connector_key", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="operation_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="method", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="path", type=SearchFieldDataType.String),
            SearchableField(name="summary", type=SearchFieldDataType.String),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchField(
                name="tags",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True,
                facetable=True,
            ),
            SearchField(
                name="semantic_tags",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                filterable=True,
                facetable=True,
            ),
            SimpleField(name="schema_hash", type=SearchFieldDataType.String, filterable=True),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=dim,
                vector_search_profile_name="default",
            ),
        ]
        vector_search = AzureVectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
            profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="hnsw")],
        )
        index = SearchIndex(
            name=self._index_name(tenant_id), fields=fields, vector_search=vector_search
        )
        client.create_index(index)

    async def upsert(
        self, tenant_id: str, chunks: list[SpecChunk], embeddings: list[list[float]]
    ) -> None:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.aio import SearchClient

        async with SearchClient(
            self.endpoint, self._index_name(tenant_id), AzureKeyCredential(self.api_key)
        ) as client:
            docs = [
                chunk_to_search_document(chunk, emb)
                for chunk, emb in zip(chunks, embeddings, strict=True)
            ]
            await client.merge_or_upload_documents(documents=docs)

    async def delete_by_connection(self, tenant_id: str, connection_id: str) -> None:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.aio import SearchClient

        async with SearchClient(
            self.endpoint, self._index_name(tenant_id), AzureKeyCredential(self.api_key)
        ) as client:
            results = await client.search(
                search_text="*", filter=f"connection_id eq '{connection_id}'", select=["id"]
            )
            ids: list[dict[str, str]] = []
            async for item in results:
                ids.append({"id": item["id"]})
            if ids:
                await client.delete_documents(documents=ids)

    async def delete_chunks(self, tenant_id: str, chunk_ids: list[str]) -> None:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.aio import SearchClient

        async with SearchClient(
            self.endpoint, self._index_name(tenant_id), AzureKeyCredential(self.api_key)
        ) as client:
            await client.delete_documents(documents=[{"id": cid} for cid in chunk_ids])

    async def search(
        self,
        tenant_id: str,
        embedding: list[float],
        *,
        top_k: int = 10,
        connector_filter: str | None = None,
    ) -> list[SearchHit]:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.aio import SearchClient
        from azure.search.documents.models import VectorizedQuery

        vec = VectorizedQuery(vector=embedding, k_nearest_neighbors=top_k, fields="embedding")
        flt = f"connector_key eq '{connector_filter}'" if connector_filter else None
        async with SearchClient(
            self.endpoint, self._index_name(tenant_id), AzureKeyCredential(self.api_key)
        ) as client:
            results = await client.search(
                search_text=None, vector_queries=[vec], filter=flt, top=top_k
            )
            hits: list[SearchHit] = []
            async for doc in results:
                hits.append(
                    SearchHit(
                        chunk_id=doc["id"],
                        connection_id=doc["connection_id"],
                        connector_key=doc.get("connector_key"),
                        operation_id=doc["operation_id"],
                        method=doc["method"],
                        path=doc["path"],
                        summary=doc.get("summary", ""),
                        score=doc.get("@search.score", 0.0),
                        document=dict(doc),
                    )
                )
            return hits


_in_memory_singleton = InMemoryVectorSearch()


def get_vector_search() -> VectorSearch:
    settings = get_settings()
    if settings.use_fake_vector_search or not settings.azure_search_endpoint:
        return _in_memory_singleton
    return AzureAISearch(
        endpoint=settings.azure_search_endpoint,
        api_key=settings.azure_search_api_key.get_secret_value(),
        index_prefix=settings.azure_search_index_prefix,
    )


__all__ = [
    "AzureAISearch",
    "InMemoryVectorSearch",
    "SearchHit",
    "VectorSearch",
    "get_vector_search",
]
