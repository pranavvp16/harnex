"""Find an OpenAPI operation by id and build a concrete HTTP request from user params.

Pure functions — no DB, no network, no LLM. The executor calls these to turn a
`(spec, operation_id, params)` triple into an `ExecuteRequest` ready for the
sandbox/connector pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from harnex_api.connectors.base import ExecuteRequest
from harnex_api.services.ingestion.enricher import Operation, enrich_spec

_PATH_PARAM = re.compile(r"\{([^{}]+)\}")


class OperationNotFoundError(LookupError):
    """No operation with that id exists in the spec."""


class MissingRequiredParamError(ValueError):
    """A required parameter (path/query/body) was not supplied."""


@dataclass(frozen=True)
class ExecuteParams:
    """The shape callers (MCP tool / REST route) supply per execution."""

    path: dict[str, Any]
    query: dict[str, Any]
    headers: dict[str, str]
    body: Any | None


def find_operation(spec: dict[str, Any], operation_id: str) -> Operation:
    for op in enrich_spec(spec):
        if op.operation_id == operation_id:
            return op
    raise OperationNotFoundError(operation_id)


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _substitute_path(path: str, path_params: dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in path_params:
            raise MissingRequiredParamError(f"path parameter '{name}' missing")
        return _stringify(path_params[name])

    return _PATH_PARAM.sub(repl, path)


def _split_params_by_location(op: Operation) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {"path": [], "query": [], "header": [], "cookie": []}
    for p in op.parameters:
        loc = p.get("in")
        if loc in out:
            out[loc].append(p)
    return out


def _required_names(params: list[dict[str, Any]]) -> set[str]:
    return {p.get("name") for p in params if p.get("required")} - {None}  # type: ignore[arg-type]


def build_request(
    op: Operation, params: ExecuteParams
) -> ExecuteRequest:
    """Compose a concrete request from an operation + supplied params.

    Validates required params (path, query, body presence). Header/cookie params
    are accepted but not enforced — connector auth fills in the rest.
    """
    by_loc = _split_params_by_location(op)

    missing_query = _required_names(by_loc["query"]) - set(params.query.keys())
    if missing_query:
        raise MissingRequiredParamError(
            f"missing required query params: {sorted(missing_query)}"
        )

    if op.request_body and op.request_body.get("required") and params.body is None:
        raise MissingRequiredParamError("request body required")

    rendered_path = _substitute_path(op.path, params.path)

    return ExecuteRequest(
        method=op.method,
        path=rendered_path,
        headers=dict(params.headers or {}),
        query={k: _stringify(v) for k, v in (params.query or {}).items()},
        body=params.body,
        operation_id=op.operation_id,
    )


__all__ = [
    "ExecuteParams",
    "MissingRequiredParamError",
    "OperationNotFoundError",
    "build_request",
    "find_operation",
]
