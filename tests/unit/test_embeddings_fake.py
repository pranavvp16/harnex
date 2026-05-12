from __future__ import annotations

import math

import pytest

from harnex_api.services.search.embeddings import FakeEmbeddingProvider


@pytest.mark.asyncio
async def test_fake_embedding_is_deterministic_and_normalized():
    provider = FakeEmbeddingProvider(dim=64)
    a = (await provider.embed("create issue github repo")).vector
    b = (await provider.embed("create issue github repo")).vector
    assert a == b
    norm = math.sqrt(sum(x * x for x in a))
    assert pytest.approx(norm, abs=1e-6) == 1.0


@pytest.mark.asyncio
async def test_similar_texts_have_higher_similarity_than_unrelated():
    provider = FakeEmbeddingProvider(dim=64)
    q = (await provider.embed("create issue")).vector
    similar = (await provider.embed("create new issue")).vector
    unrelated = (await provider.embed("delete pipeline build")).vector
    sim_close = sum(a * b for a, b in zip(q, similar, strict=False))
    sim_far = sum(a * b for a, b in zip(q, unrelated, strict=False))
    assert sim_close > sim_far
