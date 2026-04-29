from __future__ import annotations

import pytest

from harnex_api.services.execute.operation import (
    ExecuteParams,
    MissingRequiredParamError,
    OperationNotFoundError,
    build_request,
    find_operation,
)

SPEC = {
    "openapi": "3.0.3",
    "info": {"title": "demo", "version": "0"},
    "paths": {
        "/repos/{owner}/{repo}/issues": {
            "get": {
                "operationId": "list_issues",
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                    {
                        "name": "state",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "per_page",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "integer"},
                    },
                ],
                "responses": {"200": {"description": "ok"}},
            },
            "post": {
                "operationId": "create_issue",
                "parameters": [
                    {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object"}}},
                },
                "responses": {"201": {"description": "created"}},
            },
        }
    },
}


def test_find_operation_returns_match() -> None:
    op = find_operation(SPEC, "list_issues")
    assert op.method == "GET"
    assert op.path == "/repos/{owner}/{repo}/issues"


def test_find_operation_missing_raises() -> None:
    with pytest.raises(OperationNotFoundError):
        find_operation(SPEC, "no_such_op")


def test_build_request_substitutes_path_params() -> None:
    op = find_operation(SPEC, "list_issues")
    req = build_request(
        op,
        ExecuteParams(
            path={"owner": "anthropics", "repo": "claude"},
            query={"per_page": 25, "state": "open"},
            headers={},
            body=None,
        ),
    )
    assert req.method == "GET"
    assert req.path == "/repos/anthropics/claude/issues"
    assert req.query == {"per_page": "25", "state": "open"}
    assert req.operation_id == "list_issues"


def test_build_request_missing_path_param_raises() -> None:
    op = find_operation(SPEC, "list_issues")
    with pytest.raises(MissingRequiredParamError):
        build_request(
            op,
            ExecuteParams(path={"owner": "x"}, query={"per_page": 1}, headers={}, body=None),
        )


def test_build_request_missing_required_query_raises() -> None:
    op = find_operation(SPEC, "list_issues")
    with pytest.raises(MissingRequiredParamError):
        build_request(
            op,
            ExecuteParams(
                path={"owner": "x", "repo": "y"}, query={}, headers={}, body=None
            ),
        )


def test_build_request_missing_required_body_raises() -> None:
    op = find_operation(SPEC, "create_issue")
    with pytest.raises(MissingRequiredParamError):
        build_request(
            op,
            ExecuteParams(path={"owner": "x", "repo": "y"}, query={}, headers={}, body=None),
        )


def test_build_request_includes_body_when_present() -> None:
    op = find_operation(SPEC, "create_issue")
    req = build_request(
        op,
        ExecuteParams(
            path={"owner": "x", "repo": "y"},
            query={},
            headers={},
            body={"title": "hello"},
        ),
    )
    assert req.body == {"title": "hello"}
    assert req.path == "/repos/x/y/issues"
    assert req.method == "POST"


def test_build_request_stringifies_query_values() -> None:
    op = find_operation(SPEC, "list_issues")
    req = build_request(
        op,
        ExecuteParams(
            path={"owner": "x", "repo": "y"},
            query={"per_page": 1, "state": True},
            headers={},
            body=None,
        ),
    )
    assert req.query == {"per_page": "1", "state": "true"}
