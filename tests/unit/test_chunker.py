from __future__ import annotations

from harnex_api.services.ingestion.chunker import operations_to_chunks
from harnex_api.services.ingestion.enricher import enrich_spec


def test_chunks_have_stable_ids_and_embedding_text():
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/issues": {"post": {"summary": "Create an issue", "tags": ["issues"]}},
            "/issues/{id}": {"get": {"summary": "Get issue"}},
        },
    }
    ops = enrich_spec(spec)
    chunks_a = operations_to_chunks(
        tenant_id="t1", connection_id="c1", connector_key="github", operations=ops
    )
    chunks_b = operations_to_chunks(
        tenant_id="t1", connection_id="c1", connector_key="github", operations=ops
    )
    assert [c.id for c in chunks_a] == [c.id for c in chunks_b]
    assert all("connector: github" in c.embedding_text for c in chunks_a)
    assert {(c.method, c.path) for c in chunks_a} == {("POST", "/issues"), ("GET", "/issues/{id}")}
