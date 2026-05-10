from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from harnex_api.services.ingestion.enricher import Operation


@dataclass(frozen=True)
class SpecChunk:
    """One operation, ready to be embedded and persisted to operation_chunks.

    Chunks are keyed on the spec catalog (not tenant/connection) so an
    identical spec_hash from two different tenants reuses the same chunk
    rows and the same embeddings.
    """

    id: str
    operation_id: str
    method: str
    path: str
    summary: str
    description: str
    tags: list[str]
    semantic_tags: list[str]
    auth_scheme_keys: list[str]
    embedding_text: str
    schema_hash: str
    parameters: list[dict[str, Any]] = field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[str, Any] = field(default_factory=dict)


def _embedding_text(connector_key: str | None, op: Operation) -> str:
    """Compose deterministic text for embedding. Order matters because some
    embedding models weight earlier tokens slightly more.
    """
    pieces: list[str] = []
    if connector_key:
        pieces.append(f"connector: {connector_key}")
    pieces.append(f"{op.method} {op.path}")
    pieces.append(f"summary: {op.summary}")
    if op.description:
        pieces.append(f"description: {op.description}")
    if op.tags:
        pieces.append("tags: " + ", ".join(op.tags))
    if op.semantic_tags:
        pieces.append("semantic: " + ", ".join(op.semantic_tags))
    param_names = [p.get("name") for p in op.parameters if isinstance(p, dict) and p.get("name")]
    if param_names:
        pieces.append("params: " + ", ".join(str(n) for n in param_names))
    return "\n".join(pieces)


def _schema_hash(op: Operation) -> str:
    payload = {
        "method": op.method,
        "path": op.path,
        "parameters": [
            {k: p.get(k) for k in ("name", "in", "required") if k in p}
            for p in op.parameters
            if isinstance(p, dict)
        ],
        "request_body": op.request_body,
        "responses": list((op.responses or {}).keys()),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def chunk_id(spec_hash: str, operation_id: str, method: str, path: str) -> str:
    raw = f"{spec_hash}|{operation_id}|{method}|{path}".encode()
    return hashlib.sha256(raw).hexdigest()[:32]


def operations_to_chunks(
    *,
    spec_hash: str,
    connector_key: str | None,
    operations: list[Operation],
) -> list[SpecChunk]:
    chunks: list[SpecChunk] = []
    for op in operations:
        cid = chunk_id(spec_hash, op.operation_id, op.method, op.path)
        chunks.append(
            SpecChunk(
                id=cid,
                operation_id=op.operation_id,
                method=op.method,
                path=op.path,
                summary=op.summary,
                description=op.description,
                tags=list(op.tags),
                semantic_tags=list(op.semantic_tags),
                auth_scheme_keys=list(op.auth_scheme_keys),
                embedding_text=_embedding_text(connector_key, op),
                schema_hash=_schema_hash(op),
                parameters=list(op.parameters),
                request_body=op.request_body,
                responses=dict(op.responses),
            )
        )
    return chunks


__all__ = ["SpecChunk", "chunk_id", "operations_to_chunks"]
