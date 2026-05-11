from __future__ import annotations

import pytest

from harnex_api.services.search.embeddings import FakeEmbeddingProvider
from harnex_api.services.search.service import SearchService
from harnex_api.services.search.vector_search import FakeVectorSearch


@pytest.mark.asyncio
async def test_search_service_returns_relevant_chunk():
    emb = FakeEmbeddingProvider(dim=64)
    vs = FakeVectorSearch()

    issues_create_emb = await emb.embed("POST /repos/{owner}/{repo}/issues create issue")
    issues_list_emb = await emb.embed("GET /repos/{owner}/{repo}/issues list issues")
    pulls_create_emb = await emb.embed("POST /repos/{owner}/{repo}/pulls create pull request")

    for op_id, method, path, summary, vec in [
        ("issues/create", "POST", "/repos/{owner}/{repo}/issues", "Create an issue", issues_create_emb),
        ("issues/list", "GET", "/repos/{owner}/{repo}/issues", "List issues", issues_list_emb),
        ("pulls/create", "POST", "/repos/{owner}/{repo}/pulls", "Create a pull request", pulls_create_emb),
    ]:
        vs.register(
            tenant_id="t-test",
            connection_id="c-test",
            connector_key="github",
            chunk_id=op_id,
            operation_id=op_id,
            method=method,
            path=path,
            summary=summary,
            embedding=vec,
        )

    service = SearchService(embeddings=emb, vector_search=vs)
    response = await service.search(tenant_id="t-test", query="create issue", top_k=3)
    assert response.hits, "expected search to return at least one hit"
    top = response.hits[0]
    assert top.path == "/repos/{owner}/{repo}/issues"
    assert top.method == "POST"
    assert top.connector_key == "github"
    vs.reset()


@pytest.mark.asyncio
async def test_search_clarification_when_multiple_connectors_match():
    emb = FakeEmbeddingProvider(dim=64)
    vs = FakeVectorSearch()

    gh_emb = await emb.embed("POST /repos/{owner}/{repo}/issues create issue")
    jenkins_emb = await emb.embed("POST /job/{name}/build create build")

    vs.register(
        tenant_id="t-multi",
        connection_id="c-gh",
        connector_key="github",
        chunk_id="gh-1",
        operation_id="issues/create",
        method="POST",
        path="/repos/{owner}/{repo}/issues",
        summary="Create an issue",
        embedding=gh_emb,
    )
    vs.register(
        tenant_id="t-multi",
        connection_id="c-jk",
        connector_key="jenkins",
        chunk_id="jk-1",
        operation_id="build_job",
        method="POST",
        path="/job/{name}/build",
        summary="Trigger a job build",
        embedding=jenkins_emb,
    )

    service = SearchService(embeddings=emb, vector_search=vs)
    response = await service.search(tenant_id="t-multi", query="create build", top_k=5)
    assert len(response.candidate_connectors) >= 1

    filtered = await service.search(
        tenant_id="t-multi", query="create build", top_k=5, connector_filter="github"
    )
    assert filtered.clarification_needed is False
    assert all(h.connector_key == "github" for h in filtered.hits)
    vs.reset()
