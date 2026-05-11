from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, cast

import httpx
import yaml
from openapi_spec_validator import validate as validate_openapi

from harnex_api.connectors.base import ConnectionConfig, LoadedSpec


class SpecFetchError(Exception):
    """Raised when a spec cannot be retrieved."""


class SpecValidationError(Exception):
    """Raised when a fetched document is not valid OpenAPI/Swagger."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


@dataclass(frozen=True)
class ParseResult:
    document: dict[str, Any]
    original_format: str
    raw_hash: str


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decode(data: bytes) -> dict[str, Any]:
    text = data.decode("utf-8", errors="replace").lstrip()
    if text.startswith("{") or text.startswith("["):
        loaded = json.loads(text)
        if not isinstance(loaded, dict):
            raise SpecValidationError("spec root must be a mapping")
        return cast(dict[str, Any], loaded)
    parsed = yaml.safe_load(text)
    if not isinstance(parsed, dict):
        raise SpecValidationError("spec root must be a mapping")
    return cast(dict[str, Any], parsed)


def _detect_format(doc: dict[str, Any]) -> str:
    if isinstance(doc.get("openapi"), str) and doc["openapi"].startswith("3."):
        return "openapi-3"
    if doc.get("swagger") == "2.0":
        return "swagger-2"
    return "unknown"


def _upconvert_swagger_2(doc: dict[str, Any]) -> dict[str, Any]:
    """Minimal Swagger 2.0 -> OpenAPI 3.0 upconversion.

    This handles the fields ingestion actually uses: paths/operations,
    parameters, request bodies, responses, securitySchemes. Production should
    swap to a dedicated converter library if richer fidelity is needed —
    `prance` gives us validation/dereferencing but not conversion in pure
    Python, so we keep this conservative and self-contained.
    """
    out: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": doc.get("info", {"title": "Untitled", "version": "0"}),
    }

    scheme = (doc.get("schemes") or ["https"])[0]
    host = doc.get("host", "")
    base_path = doc.get("basePath", "")
    if host:
        out["servers"] = [{"url": f"{scheme}://{host}{base_path}"}]
    elif base_path:
        out["servers"] = [{"url": base_path}]

    if "definitions" in doc:
        out.setdefault("components", {})["schemas"] = doc["definitions"]
    if "securityDefinitions" in doc:
        sec_schemes: dict[str, Any] = {}
        for name, sd in doc["securityDefinitions"].items():
            t = sd.get("type")
            if t == "apiKey":
                sec_schemes[name] = {"type": "apiKey", "in": sd.get("in"), "name": sd.get("name")}
            elif t == "basic":
                sec_schemes[name] = {"type": "http", "scheme": "basic"}
            elif t == "oauth2":
                sec_schemes[name] = {"type": "oauth2", "flows": sd.get("flows", {})}
        if sec_schemes:
            out.setdefault("components", {})["securitySchemes"] = sec_schemes

    out_paths: dict[str, Any] = {}
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        new_item: dict[str, Any] = {}
        for method, op in item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                new_item[method] = op
                continue
            new_op: dict[str, Any] = {
                k: v for k, v in op.items() if k not in {"parameters", "consumes", "produces"}
            }
            params: list[dict[str, Any]] = []
            body_param: dict[str, Any] | None = None
            for p in op.get("parameters", []):
                if not isinstance(p, dict):
                    continue
                if p.get("in") == "body":
                    body_param = p
                else:
                    params.append({k: v for k, v in p.items() if k not in {"type", "format"}})
                    if "schema" not in params[-1] and "type" in p:
                        params[-1]["schema"] = {
                            k: v for k, v in p.items() if k in {"type", "format", "enum"}
                        }
            if params:
                new_op["parameters"] = params
            if body_param is not None:
                consumes = op.get("consumes") or doc.get("consumes") or ["application/json"]
                content = {ct: {"schema": body_param.get("schema", {})} for ct in consumes}
                new_op["requestBody"] = {
                    "required": body_param.get("required", False),
                    "content": content,
                }
            new_item[method] = new_op
        out_paths[path] = new_item
    out["paths"] = out_paths
    return out


def parse_spec_bytes(data: bytes) -> ParseResult:
    raw_hash = _hash_bytes(data)
    doc = _decode(data)
    fmt = _detect_format(doc)
    if fmt == "swagger-2":
        doc = _upconvert_swagger_2(doc)
    elif fmt == "unknown":
        raise SpecValidationError(
            "document is neither OpenAPI 3.x nor Swagger 2.0",
            errors=[{"field": "openapi/swagger", "message": "missing version marker"}],
        )
    try:
        validate_openapi(doc)
    except Exception as exc:  # openapi_spec_validator raises a tree of errors
        raise SpecValidationError(
            "spec failed OpenAPI validation",
            errors=[{"message": str(exc)}],
        ) from exc
    return ParseResult(document=doc, original_format=fmt, raw_hash=raw_hash)


async def fetch_spec_from_url(url: str, *, timeout_seconds: float = 30.0) -> LoadedSpec:
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.content
    except httpx.HTTPError as exc:
        raise SpecFetchError(f"failed to fetch spec at {url}: {exc}") from exc
    parsed = parse_spec_bytes(data)
    return LoadedSpec(
        document=parsed.document,
        source="url",
        raw_hash=parsed.raw_hash,
        original_format=parsed.original_format,
    )


def parse_uploaded_spec(data: bytes) -> LoadedSpec:
    parsed = parse_spec_bytes(data)
    return LoadedSpec(
        document=parsed.document,
        source="upload",
        raw_hash=parsed.raw_hash,
        original_format=parsed.original_format,
    )


async def fetch_spec_for_connection(connection: ConnectionConfig) -> LoadedSpec | None:
    """Used by GenericConnector and any connector that defers to user-supplied
    spec sources. Returns None for bare-URL connections without a spec."""
    # Uploaded specs are persisted on the connection row; prefer them over a
    # spec_url because the user explicitly chose upload mode.
    if connection.spec_blob:
        return parse_uploaded_spec(connection.spec_blob)
    if connection.spec_url:
        return await fetch_spec_from_url(connection.spec_url)
    return None


__all__ = [
    "ParseResult",
    "SpecFetchError",
    "SpecValidationError",
    "fetch_spec_for_connection",
    "fetch_spec_from_url",
    "parse_spec_bytes",
    "parse_uploaded_spec",
]
