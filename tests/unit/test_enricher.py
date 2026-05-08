from __future__ import annotations

from harnex_api.services.ingestion.enricher import enrich_spec


def _spec(paths: dict) -> dict:
    return {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}, "paths": paths}


def test_enrich_generates_operation_id_when_missing():
    ops = enrich_spec(
        _spec(
            {
                "/repos/{owner}/{repo}/issues": {
                    "post": {"summary": "Create an issue", "tags": ["issues"]}
                }
            }
        )
    )
    assert len(ops) == 1
    op = ops[0]
    assert op.method == "POST"
    assert op.operation_id == "post_repos_by_owner_by_repo_issues"
    assert "create" in op.semantic_tags
    assert "issues" in op.semantic_tags


def test_enrich_keeps_declared_operation_id():
    ops = enrich_spec(_spec({"/items": {"get": {"operationId": "items.list", "summary": "List"}}}))
    assert ops[0].operation_id == "items.list"


def test_enrich_collects_security_scheme_keys():
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "t", "version": "1"},
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"},
            }
        },
        "security": [{"bearerAuth": []}],
        "paths": {"/me": {"get": {"summary": "whoami"}}},
    }
    ops = enrich_spec(spec)
    assert ops[0].auth_scheme_keys == ["bearerAuth"]


def test_enrich_skips_non_operation_keys():
    ops = enrich_spec(
        _spec(
            {
                "/x": {
                    "parameters": [{"name": "shared", "in": "query"}],
                    "get": {"summary": "x"},
                }
            }
        )
    )
    assert len(ops) == 1
    assert ops[0].parameters[0]["name"] == "shared"
