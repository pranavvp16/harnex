from __future__ import annotations

import pytest

from harnex_api.connectors.base import LoadedSpec
from harnex_api.services.ingestion.pipeline import index_spec
from harnex_api.services.search.service import SearchService

SPEC = {
    "openapi": "3.0.3",
    "info": {"title": "demo", "version": "1"},
    "paths": {
        "/repos/{owner}/{repo}/issues": {
            "post": {
                "operationId": "issues/create",
                "summary": "Create an issue",
                "tags": ["issues"],
            },
            "get": {
                "operationId": "issues/list",
                "summary": "List issues",
                "tags": ["issues"],
            },
        },
        "/repos/{owner}/{repo}/pulls": {
            "post": {
                "operationId": "pulls/create",
                "summary": "Create a pull request",
                "tags": ["pulls"],
            }
        },
    },
}


@pytest.mark.asyncio
async def test_indexing_then_searching_returns_relevant_chunk():
    loaded = LoadedSpec(document=SPEC, source="inline", raw_hash="h", original_format="openapi-3")
    result = await index_spec(
        tenant_id="t-test",
        connection_id="c-test",
        connector_key="github",
        spec=loaded,
    )
    assert result.operation_count == 3
    assert result.chunk_count == 3

    service = SearchService()
    response = await service.search(tenant_id="t-test", query="create issue", top_k=3)
    assert response.hits, "expected search to return at least one hit"
    top = response.hits[0]
    assert top.path == "/repos/{owner}/{repo}/issues"
    assert top.method == "POST"
    assert top.connector_key == "github"


@pytest.mark.asyncio
async def test_search_clarification_when_multiple_connectors_match():
    spec_jenkins = {
        "openapi": "3.0.3",
        "info": {"title": "j", "version": "1"},
        "paths": {
            "/job/{name}/build": {
                "post": {"operationId": "build_job", "summary": "Trigger a job build"}
            }
        },
    }
    await index_spec(
        tenant_id="t-multi",
        connection_id="c-gh",
        connector_key="github",
        spec=LoadedSpec(document=SPEC, source="inline", raw_hash="h1", original_format="openapi-3"),
    )
    await index_spec(
        tenant_id="t-multi",
        connection_id="c-jk",
        connector_key="jenkins",
        spec=LoadedSpec(
            document=spec_jenkins, source="inline", raw_hash="h2", original_format="openapi-3"
        ),
    )

    service = SearchService()
    response = await service.search(tenant_id="t-multi", query="create build", top_k=5)
    assert len(response.candidate_connectors) >= 1
    # When connector_filter is supplied, clarification is suppressed.
    filtered = await service.search(
        tenant_id="t-multi", query="create build", top_k=5, connector_filter="github"
    )
    assert filtered.clarification_needed is False
    assert all(h.connector_key == "github" for h in filtered.hits)
