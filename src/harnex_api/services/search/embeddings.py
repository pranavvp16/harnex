from __future__ import annotations

import hashlib
import math
from typing import Protocol

from harnex_api.config import get_settings


class EmbeddingProvider(Protocol):
    dim: int

    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class FakeEmbeddingProvider:
    """Deterministic, dependency-free embeddings for unit tests + local smoke runs.

    Uses repeated SHA-256 hashing of the input to fill `dim` floats in [-1, 1],
    then L2-normalizes. Same text always yields the same vector, and two
    similar strings produce vectors with non-trivial cosine similarity because
    they share a hash prefix.
    """

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

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


class AzureOpenAIEmbeddings:
    """Uses Azure OpenAI deployments for embeddings. Lazy-imports the SDK so
    tests that pin to fakes don't need the network or credentials.
    """

    def __init__(
        self, *, endpoint: str, api_key: str, api_version: str, deployment: str, dim: int
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version
        self.deployment = deployment
        self.dim = dim
        self._client: object | None = None

    def _get_client(self) -> object:
        if self._client is None:
            from openai import AsyncAzureOpenAI  # lazy

            self._client = AsyncAzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version,
            )
        return self._client

    async def embed(self, text: str) -> list[float]:
        result = await self.embed_batch([text])
        return result[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        resp = await client.embeddings.create(  # type: ignore[attr-defined]
            model=self.deployment,
            input=texts,
        )
        return [item.embedding for item in resp.data]


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.use_fake_embeddings or not settings.azure_openai_endpoint:
        return FakeEmbeddingProvider(dim=settings.azure_openai_embedding_dim)
    return AzureOpenAIEmbeddings(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key.get_secret_value(),
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_embedding_deployment,
        dim=settings.azure_openai_embedding_dim,
    )


__all__ = [
    "AzureOpenAIEmbeddings",
    "EmbeddingProvider",
    "FakeEmbeddingProvider",
    "get_embedding_provider",
]
