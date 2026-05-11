from __future__ import annotations

import asyncio
import hashlib
import math
from typing import Protocol

from harnex_api.config import get_settings

# OpenAI text-embedding-3 accepts up to 2048 inputs / ~8k tokens per request;
# 64 stays well under both limits and keeps latency predictable for large
# specs (e.g. GitHub's ~1k operations).
_EMBED_BATCH_SIZE = 64
_EMBED_MAX_ATTEMPTS = 3


class EmbeddingProvider(Protocol):
    dim: int

    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
    @property
    def model_name(self) -> str: ...


class FakeEmbeddingProvider:
    """Deterministic, dependency-free embeddings for unit tests + local smoke runs.

    Uses repeated SHA-256 hashing of the input to fill `dim` floats in [-1, 1],
    then L2-normalizes. Same text always yields the same vector, and two
    similar strings produce vectors with non-trivial cosine similarity because
    they share a hash prefix.
    """

    def __init__(self, dim: int = 1536) -> None:
        self.dim = dim

    @property
    def model_name(self) -> str:
        return f"fake-{self.dim}"

    async def embed(self, text: str) -> list[float]:
        return self._embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def _embed(self, text: str) -> list[float]:
        # Word-level bag of hashes — simple but gives reasonable similarity
        # behavior for tests where inputs share words.
        words = [w for w in text.lower().split() if w]
        vec = [0.0] * self.dim
        for word in words:
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            for i in range(self.dim):
                byte = digest[i % len(digest)]
                vec[i] += (byte / 255.0) * 2.0 - 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


class OpenAIEmbeddings:
    """OpenAI embeddings client (direct, not Azure).

    text-embedding-3-large supports MRL truncation via the `dimensions`
    parameter, so we can request 1536-d vectors from a 3072-d model and get
    near-best-quality results at half the storage / faster pgvector HNSW.
    """

    def __init__(self, *, api_key: str, model: str, dim: int) -> None:
        self.api_key = api_key
        self.model = model
        self.dim = dim
        self._client: object | None = None

    @property
    def model_name(self) -> str:
        return self.model

    def _get_client(self) -> object:
        if self._client is None:
            from openai import AsyncOpenAI  # lazy

            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def embed(self, text: str) -> list[float]:
        result = await self.embed_batch([text])
        return result[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._get_client()
        out: list[list[float]] = []
        for start in range(0, len(texts), _EMBED_BATCH_SIZE):
            chunk = texts[start : start + _EMBED_BATCH_SIZE]
            resp = await self._embed_chunk_with_retry(client, chunk)
            out.extend(item.embedding for item in resp.data)
        return out

    async def _embed_chunk_with_retry(self, client: object, chunk: list[str]):  # type: ignore[no-untyped-def]
        last_exc: Exception | None = None
        for attempt in range(_EMBED_MAX_ATTEMPTS):
            try:
                return await client.embeddings.create(  # type: ignore[attr-defined]
                    model=self.model,
                    input=chunk,
                    dimensions=self.dim,
                )
            except Exception as exc:
                last_exc = exc
                if attempt == _EMBED_MAX_ATTEMPTS - 1 or not _is_retryable(exc):
                    raise
                await asyncio.sleep(0.5 * (2**attempt))
        # Unreachable — the loop either returns or raises — but mypy needs it.
        raise last_exc  # type: ignore[misc]


def _is_retryable(exc: Exception) -> bool:
    """Heuristic: rate limits and 5xx-class transient errors are worth retrying."""
    name = type(exc).__name__
    if name in {"RateLimitError", "APITimeoutError", "APIConnectionError"}:
        return True
    status_code = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    return isinstance(status_code, int) and status_code >= 500


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    api_key = settings.openai_api_key.get_secret_value()
    if settings.use_fake_embeddings or not api_key:
        return FakeEmbeddingProvider(dim=settings.openai_embedding_dim)
    return OpenAIEmbeddings(
        api_key=api_key,
        model=settings.openai_embedding_model,
        dim=settings.openai_embedding_dim,
    )


__all__ = [
    "EmbeddingProvider",
    "FakeEmbeddingProvider",
    "OpenAIEmbeddings",
    "get_embedding_provider",
]
