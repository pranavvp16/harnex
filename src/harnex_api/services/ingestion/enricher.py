from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head")

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_PATH_PARAM = re.compile(r"\{([^{}]+)\}")


@dataclass(frozen=True)
class Operation:
    operation_id: str
    method: str
    path: str
    summary: str
    description: str
    tags: list[str]
    parameters: list[dict[str, Any]] = field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[str, Any] = field(default_factory=dict)
    security: list[dict[str, Any]] = field(default_factory=list)
    auth_scheme_keys: list[str] = field(default_factory=list)
    semantic_tags: list[str] = field(default_factory=list)


def _slug(value: str) -> str:
    return _NON_ALNUM.sub("_", value.lower()).strip("_")


def _generate_operation_id(method: str, path: str) -> str:
    parts = [_slug(method)]
    for segment in path.strip("/").split("/"):
        if not segment:
            continue
        m = _PATH_PARAM.match(segment)
        if m:
            parts.append("by_" + _slug(m.group(1)))
        else:
            parts.append(_slug(segment))
    return "_".join(p for p in parts if p) or _slug(f"{method}_root")


def _collect_security_schemes(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return (spec.get("components") or {}).get("securitySchemes") or {}


_VERB_TAGS: dict[str, list[str]] = {
    "get": ["read", "list"],
    "post": ["create", "write"],
    "put": ["update", "write"],
    "patch": ["update", "write"],
    "delete": ["delete", "write"],
}


def _semantic_tags(method: str, path: str, summary: str, declared_tags: list[str]) -> list[str]:
    tags: list[str] = []
    tags.extend(_VERB_TAGS.get(method.lower(), []))
    for tag in declared_tags:
        if isinstance(tag, str):
            tags.append(_slug(tag))
    for segment in path.strip("/").split("/"):
        if not segment or _PATH_PARAM.match(segment):
            continue
        tags.append(_slug(segment))
    if summary:
        for word in re.findall(r"[A-Za-z]+", summary):
            tags.append(word.lower())
    seen: set[str] = set()
    deduped: list[str] = []
    for t in tags:
        if t and t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def _summarize(method: str, path: str, op: dict[str, Any]) -> str:
    summary_val = op.get("summary")
    if isinstance(summary_val, str) and summary_val.strip():
        return summary_val.strip()
    desc_val = op.get("description")
    if isinstance(desc_val, str) and desc_val.strip():
        return desc_val.split("\n", 1)[0].strip()
    return f"{method.upper()} {path}"


def enrich_spec(spec: dict[str, Any]) -> list[Operation]:
    """Walk an OpenAPI 3.x document and produce normalized Operation records.

    Deterministic — no LLM calls. The chunker turns these into embeddings.
    """
    operations: list[Operation] = []
    security_schemes = _collect_security_schemes(spec)
    paths = spec.get("paths") or {}
    if not isinstance(paths, dict):
        return []

    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        path_level_params = item.get("parameters", []) or []
        for method in HTTP_METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            operation_id = (
                op.get("operationId") if isinstance(op.get("operationId"), str) else None
            ) or _generate_operation_id(method, path)
            summary = _summarize(method, path, op)
            desc_raw = op.get("description")
            description: str = desc_raw if isinstance(desc_raw, str) else ""
            declared_tags = [t for t in (op.get("tags") or []) if isinstance(t, str)]
            params = list(path_level_params) + list(op.get("parameters") or [])
            security = (
                op.get("security")
                if isinstance(op.get("security"), list)
                else (spec.get("security") or [])
            )
            scheme_keys: list[str] = []
            for entry in security or []:
                if isinstance(entry, dict):
                    scheme_keys.extend(entry.keys())
            scheme_keys = [k for k in scheme_keys if k in security_schemes]

            operations.append(
                Operation(
                    operation_id=operation_id,
                    method=method.upper(),
                    path=path,
                    summary=summary,
                    description=description,
                    tags=declared_tags,
                    parameters=params,
                    request_body=op.get("requestBody")
                    if isinstance(op.get("requestBody"), dict)
                    else None,
                    responses=op.get("responses") or {},
                    security=security or [],
                    auth_scheme_keys=scheme_keys,
                    semantic_tags=_semantic_tags(method, path, summary, declared_tags),
                )
            )
    return operations


__all__ = ["HTTP_METHODS", "Operation", "enrich_spec"]
